from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_PATH = REPO_ROOT / "runtime_state" / "active_long_tasks.json"
ARCHIVE_ROOT = REPO_ROOT / "runtime_state" / "archive"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LongTaskRecord:
    task_id: str
    title: str
    status: str
    created_at: str
    updated_at: str
    last_reported_at: str | None = None
    query_hint: str | None = None
    resume_hint: str | None = None
    progress_file: str | None = None
    source: str | None = None
    meta: dict[str, Any] | None = None


class LongTaskRegistry:
    def __init__(self, active_path: Path = ACTIVE_PATH, archive_root: Path = ARCHIVE_ROOT):
        self.active_path = active_path
        self.archive_root = archive_root
        self.active_path.parent.mkdir(parents=True, exist_ok=True)
        self.archive_root.mkdir(parents=True, exist_ok=True)
        if not self.active_path.exists():
            self.active_path.write_text(json.dumps({"_meta": {}, "tasks": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    def _read(self) -> dict[str, Any]:
        return json.loads(self.active_path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]):
        self.active_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert(self, record: LongTaskRecord):
        data = self._read()
        tasks = data.get("tasks", [])
        payload = record.__dict__.copy()
        for idx, item in enumerate(tasks):
            if item.get("task_id") == record.task_id:
                tasks[idx] = payload
                data["tasks"] = tasks
                self._write(data)
                return
        tasks.append(payload)
        data["tasks"] = tasks
        self._write(data)

    def list_active(self) -> list[dict[str, Any]]:
        data = self._read()
        return data.get("tasks", [])

    def mark_reported(self, task_id: str, when_iso: str | None = None):
        when_iso = when_iso or _now_iso()
        data = self._read()
        for item in data.get("tasks", []):
            if item.get("task_id") == task_id:
                item["last_reported_at"] = when_iso
                item["updated_at"] = when_iso
                break
        self._write(data)

    def archive_and_remove(self, task_id: str):
        data = self._read()
        tasks = data.get("tasks", [])
        kept = []
        target = None
        for item in tasks:
            if item.get("task_id") == task_id:
                target = item
            else:
                kept.append(item)
        data["tasks"] = kept
        self._write(data)
        if not target:
            return None
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        day_dir = self.archive_root / day
        day_dir.mkdir(parents=True, exist_ok=True)
        archive_path = day_dir / f"task_{task_id}.json"
        archive_path.write_text(json.dumps(target, ensure_ascii=False, indent=2), encoding="utf-8")
        return archive_path
