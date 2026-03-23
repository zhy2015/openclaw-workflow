#!/usr/bin/env python3
"""Automatic heartbeat maintenance for memory-master."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from memory_master import MemoryMaster


WORKSPACE = Path("/root/.openclaw/workspace")
STATE_FILE = WORKSPACE / "memory/core/heartbeat-state.json"
DAILY_DIR = WORKSPACE / "memory/daily"
DISTILLED_DIR = WORKSPACE / "memory/distilled"
CORE_MEMORY = WORKSPACE / "memory/core/MEMORY.md"


class HeartbeatMaintenance:
    def __init__(self, workspace_root: str = str(WORKSPACE)):
        self.mm = MemoryMaster(workspace_root)
        self.workspace = Path(workspace_root)
        self.state = self._load_state()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _today(self) -> str:
        return self._now().strftime("%Y-%m-%d")

    def _load_state(self) -> Dict[str, Any]:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return {"lastChecks": {}, "maintenance": {}}

    def _save_state(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")

    def _mark_check(self, key: str) -> None:
        self.state.setdefault("lastChecks", {})[key] = int(self._now().timestamp() * 1000)

    def _should_run_daily_distillation(self) -> bool:
        last = self.state.setdefault("maintenance", {}).get("last_daily_distillation")
        return last != self._today()

    def _should_reindex(self) -> bool:
        last = self.state.setdefault("maintenance", {}).get("last_indexed_at")
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
        except ValueError:
            return True
        return (self._now() - last_dt).total_seconds() > 12 * 3600

    def _collapse_noise(self, text: str) -> tuple[str, Dict[str, Any]]:
        lines = text.splitlines()
        block_pattern = re.compile(r"^## 🚨 网关守护事件")
        current_block: List[str] = []
        all_blocks: List[str] = []
        output_lines: List[str] = []

        def flush_block():
            nonlocal current_block
            if current_block:
                all_blocks.append("\n".join(current_block).strip())
                current_block = []

        for line in lines:
            if block_pattern.match(line):
                flush_block()
                current_block = [line]
            elif current_block:
                if line.startswith("## ") and not block_pattern.match(line):
                    flush_block()
                    output_lines.append(line)
                else:
                    current_block.append(line)
            else:
                output_lines.append(line)
        flush_block()

        if not all_blocks:
            return text, {"collapsed": False, "duplicates_removed": 0}

        counts: Dict[str, int] = {}
        ordered: List[str] = []
        for block in all_blocks:
            counts[block] = counts.get(block, 0) + 1
            if counts[block] == 1:
                ordered.append(block)

        summary_blocks = []
        duplicates_removed = 0
        for block in ordered:
            count = counts[block]
            duplicates_removed += max(0, count - 1)
            if count > 1:
                summary_blocks.append(f"{block}\n- 折叠统计: 同类重复告警 {count} 次")
            else:
                summary_blocks.append(block)

        cleaned = "\n".join(summary_blocks + [l for l in output_lines if l.strip()]).strip() + "\n"
        return cleaned, {
            "collapsed": True,
            "duplicates_removed": duplicates_removed,
            "unique_blocks": len(ordered),
            "total_blocks": len(all_blocks),
        }

    def _tighten_daily_retention(self) -> Dict[str, Any]:
        processed = self.mm._load_processed_record()
        today = self._today()
        keep_daily = {today}

        candidates = []
        for f in sorted(DAILY_DIR.glob("*.md")):
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
            if not date_match:
                continue
            candidates.append((date_match.group(1), f))

        # 保留今天 + 最近一天（如果有）作为 active daily
        dated = sorted(candidates, key=lambda x: x[0])
        if len(dated) >= 2:
            keep_daily.add(dated[-2][0])

        moved = []
        removed = []
        noise_compactions = []
        DISTILLED_DIR.mkdir(parents=True, exist_ok=True)

        for date_str, f in dated:
            if date_str in keep_daily:
                continue
            if f.name not in processed:
                continue

            raw = f.read_text(encoding="utf-8", errors="ignore")
            cleaned, meta = self._collapse_noise(raw)
            dest = DISTILLED_DIR / f.name
            dest.write_text(cleaned, encoding="utf-8")
            moved.append(f.name)
            if meta.get("collapsed"):
                noise_compactions.append({"file": f.name, **meta})

            f.unlink()
            removed.append(f.name)

        self.state.setdefault("maintenance", {})["daily_retention"] = {
            "keep_daily_dates": sorted(list(keep_daily)),
            "last_compacted_at": self._now().isoformat(),
        }

        return {
            "moved_to_distilled": moved,
            "removed_from_daily": removed,
            "noise_compactions": noise_compactions,
            "kept_daily_dates": sorted(list(keep_daily)),
        }

    def run(self, force: bool = False) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "action": "heartbeat_maintenance",
            "timestamp": self._now().isoformat(),
            "steps": {},
            "status": "success",
        }

        self._mark_check("memory_maintenance")

        if force or self._should_run_daily_distillation():
            consolidate_result = self.mm.consolidate(dry_run=False)
            retention_result = self._tighten_daily_retention()
            archive_result = self.mm.archive_old_logs(days=7)
            self.state.setdefault("maintenance", {})["last_daily_distillation"] = self._today()
            result["steps"]["consolidate"] = consolidate_result
            result["steps"]["tighten_retention"] = retention_result
            result["steps"]["archive"] = archive_result
        else:
            result["steps"]["consolidate"] = {"status": "skipped", "reason": "already ran today"}
            result["steps"]["tighten_retention"] = {"status": "skipped", "reason": "already ran today"}

        if force or self._should_reindex():
            index_result = self.mm.build_index()
            self.state.setdefault("maintenance", {})["last_indexed_at"] = self._now().isoformat()
            result["steps"]["index"] = index_result
        else:
            result["steps"]["index"] = {"status": "skipped", "reason": "index still fresh"}

        result["steps"]["memory_core"] = {
            "status": "ok",
            "path": str(CORE_MEMORY),
            "exists": CORE_MEMORY.exists(),
        }

        self._save_state()
        return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run heartbeat maintenance for memory-master")
    parser.add_argument("--force", action="store_true", help="Force all maintenance tasks")
    args = parser.parse_args()

    runner = HeartbeatMaintenance()
    print(json.dumps(runner.run(force=args.force), indent=2, ensure_ascii=False))
