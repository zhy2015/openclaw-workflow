#!/usr/bin/env python3
"""
Memory Master Skill
记忆管理大师 - 本地记忆整理/蒸馏/索引/搜索

升级目标：
1. 保持与现有 workspace 记忆目录兼容
2. 吸收上游 memory-master 的 write/consolidate/archive/index/search/status 能力
3. 让 heartbeat / 手工调用都能直接复用
4. 尽量轻量，不强绑更重的运行时
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Set

import numpy as np

from memory_query_engine import MemoryQueryEngine


class MemoryMaster:
    """记忆管理核心类"""

    def __init__(self, workspace_root: str = "/root/.openclaw/workspace"):
        self.workspace = Path(workspace_root)
        self.memory_root = self.workspace / "memory"
        self.core_dir = self.memory_root / "core"
        self.daily_dir = self.memory_root / "daily"
        self.archive_dir = self.memory_root / "archive"
        self.distilled_dir = self.memory_root / "distilled"
        self.index_dir = self.memory_root / "index"

        self.core_memory = self.core_dir / "MEMORY.md"
        self.db_path = self.index_dir / "vector_index.db"
        self.index_file = self.index_dir / "memory_index.json"
        self.processed_record = self.index_dir / "processed_logs.json"

        for d in [self.core_dir, self.daily_dir, self.archive_dir, self.distilled_dir, self.index_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _today_file(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.daily_dir / f"{today}.md"

    def _extract_date(self, filename: str) -> str:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
        return match.group(1) if match else "unknown"

    def write_daily(self, content: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        daily_file = self._today_file()
        timestamp = self._now()

        entry = f"\n## {timestamp}\n\n{content.strip()}\n"
        if metadata:
            if metadata.get("tags"):
                entry += f"\n**Tags**: {', '.join(metadata['tags'])}\n"
            if metadata.get("source"):
                entry += f"**Source**: {metadata['source']}\n"

        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(entry)

        return {
            "status": "success",
            "action": "write",
            "file": str(daily_file),
            "timestamp": timestamp,
        }

    def consolidate(self, dry_run: bool = False, mark_processed: bool = True) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "action": "consolidate",
            "timestamp": self._now(),
            "logs_processed": 0,
            "insights_extracted": 0,
            "insights_merged": 0,
            "dry_run": dry_run,
            "processed_files": [],
            "insights_preview": [],
        }

        unprocessed = self._get_unprocessed_logs()
        result["logs_processed"] = len(unprocessed)
        result["processed_files"] = [f.name for f in unprocessed]

        if not unprocessed:
            result["status"] = "success"
            result["message"] = "No new logs to process"
            return result

        insights = self._extract_insights(unprocessed)
        result["insights_extracted"] = len(insights)
        result["insights_preview"] = insights[:10]

        if insights and not dry_run:
            merged = self._merge_to_core(insights)
            result["insights_merged"] = merged
            if mark_processed:
                self._mark_processed(unprocessed)

        result["status"] = "success"
        result["message"] = f"Processed {len(unprocessed)} logs, extracted {len(insights)} insights"
        return result

    def archive_old_logs(self, days: int = 7) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "action": "archive",
            "timestamp": self._now(),
            "threshold_days": days,
            "archived_count": 0,
            "archived_files": [],
        }

        cutoff = datetime.now() - timedelta(days=days)
        for f in self.daily_dir.glob("*.md"):
            date_str = self._extract_date(f.name)
            if date_str == "unknown":
                continue
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            if file_date < cutoff:
                dest = self.archive_dir / f.name
                shutil.move(str(f), str(dest))
                result["archived_count"] += 1
                result["archived_files"].append(f.name)

        result["status"] = "success"
        result["message"] = f"Archived {result['archived_count']} old logs"
        return result

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        engine = MemoryQueryEngine(str(self.workspace))
        try:
            search_result = engine.search_as_dict(query=query, limit=limit)
            search_result["action"] = "search"
            search_result["timestamp"] = self._now()
            search_result["message"] = f"Found {len(search_result['results'])} results"
            return search_result
        finally:
            engine.close()

    def build_index(self) -> Dict[str, Any]:
        vector_result: Dict[str, Any] = {
            "action": "index",
            "timestamp": self._now(),
            "indexed_chunks": 0,
            "indexed_files": [],
        }

        conn = self._init_db()
        dirs_to_index = [self.daily_dir, self.archive_dir, self.distilled_dir, self.core_dir]

        for d in dirs_to_index:
            if not d.exists():
                continue
            for f in d.glob("*.md"):
                added = self._index_file(f, conn)
                if added:
                    vector_result["indexed_files"].append({"file": f.name, "chunks": added})
                vector_result["indexed_chunks"] += added

        conn.close()

        fts_engine = MemoryQueryEngine(str(self.workspace))
        try:
            fts_result = fts_engine.index_memory(force_rebuild=True)
            stats = fts_engine.get_stats()
        finally:
            fts_engine.close()

        self._update_index_meta(vector_result)

        vector_result["fts"] = fts_result
        vector_result["fts_stats"] = stats
        vector_result["status"] = "success"
        vector_result["message"] = (
            f"Indexed {vector_result['indexed_chunks']} vector chunks and "
            f"{fts_result['indexed_sections']} FTS sections"
        )
        return vector_result

    def get_status(self) -> Dict[str, Any]:
        status: Dict[str, Any] = {
            "action": "status",
            "timestamp": self._now(),
            "directories": {},
            "files": {},
            "index": {},
        }

        for name, d in [
            ("daily", self.daily_dir),
            ("archive", self.archive_dir),
            ("distilled", self.distilled_dir),
            ("core", self.core_dir),
        ]:
            if d.exists():
                status["directories"][name] = len(list(d.glob("*.md")))

        if self.core_memory.exists():
            content = self.core_memory.read_text(encoding="utf-8")
            status["files"]["core_memory_path"] = str(self.core_memory)
            status["files"]["core_memory_size"] = len(content)
            status["files"]["core_memory_lines"] = len(content.splitlines())

        if self.processed_record.exists():
            processed = self._load_processed_record()
            status["files"]["processed_logs"] = len(processed)

        if self.db_path.exists():
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM memory_chunks")
            status["index"]["total_chunks"] = c.fetchone()[0]
            conn.close()
        else:
            status["index"]["total_chunks"] = 0

        status["status"] = "success"
        status["message"] = "Memory system status retrieved"
        return status

    def _get_unprocessed_logs(self) -> List[Path]:
        if not self.daily_dir.exists():
            return []
        processed = self._load_processed_record()
        logs = [f for f in self.daily_dir.glob("*.md") if f.name not in processed]
        return sorted(logs)

    def _load_processed_record(self) -> Set[str]:
        if self.processed_record.exists():
            with open(self.processed_record, encoding="utf-8") as f:
                try:
                    return set(json.load(f))
                except json.JSONDecodeError:
                    return set()
        return set()

    def _extract_insights(self, log_files: List[Path]) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []

        patterns = [
            ("failure_pattern", r"FAILED.*?[:：]\s*(.+)"),
            ("success_pattern", r"SUCCESS.*?[\(（](.+?)[\)）]"),
            ("decision", r"DECISION.*?[:：]\s*(.+)"),
            ("learning", r"LEARNED.*?[:：]\s*(.+)"),
        ]

        metric_patterns = [
            ("metric", r"Skills registered:\s*(\d+)"),
            ("metric", r"Total skills:\s*(\d+\s*→\s*\d+)"),
        ]

        for log_file in log_files:
            content = log_file.read_text(encoding="utf-8", errors="ignore")
            for insight_type, pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for m in matches:
                    value = m.strip()
                    if value:
                        insights.append({
                            "type": insight_type,
                            "content": value,
                            "source": log_file.name,
                            "date": self._extract_date(log_file.name),
                        })

            for insight_type, pattern in metric_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for m in matches:
                    value = m.strip()
                    if value:
                        if pattern.endswith(r"(\d+)"):
                            value = f"Total skills: {value}"
                        insights.append({
                            "type": insight_type,
                            "content": value,
                            "source": log_file.name,
                            "date": self._extract_date(log_file.name),
                        })

        deduped: List[Dict[str, Any]] = []
        seen = set()
        for ins in insights:
            key = (ins["type"], ins["content"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(ins)
        return deduped

    def _merge_to_core(self, insights: List[Dict[str, Any]]) -> int:
        existing = ""
        if self.core_memory.exists():
            existing = self.core_memory.read_text(encoding="utf-8")

        new_insights = [ins for ins in insights if ins["content"] not in existing]
        if not new_insights:
            return 0

        with open(self.core_memory, "a", encoding="utf-8") as f:
            f.write(f"\n\n## Auto-Extracted Insights - {self._now()}\n\n")
            for ins in new_insights:
                f.write(f"- **{ins['type']}** ({ins['date']}): {ins['content']}\n")

        return len(new_insights)

    def _mark_processed(self, log_files: List[Path]) -> None:
        processed = self._load_processed_record()
        for f in log_files:
            processed.add(f.name)
        with open(self.processed_record, "w", encoding="utf-8") as f:
            json.dump(sorted(list(processed)), f, indent=2, ensure_ascii=False)

    def _init_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_chunks (
                id TEXT PRIMARY KEY,
                source_file TEXT,
                content TEXT,
                timestamp DATETIME,
                embedding BLOB
            )
            """
        )
        conn.commit()
        return conn

    def _get_embedding(self, text: str) -> np.ndarray:
        np.random.seed(int(hashlib.md5(text.encode()).hexdigest()[:8], 16))
        return np.random.rand(384).astype(np.float32)

    def _split_content(self, content: str) -> List[str]:
        content = content.strip()
        if not content:
            return []

        chunks = [c.strip() for c in re.split(r"\n(?=## |### |- )", content) if c.strip()]
        if chunks:
            return chunks
        return [content]

    def _index_file(self, filepath: Path, conn: sqlite3.Connection) -> int:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        chunks = self._split_content(content)

        c = conn.cursor()
        added = 0
        for chunk in chunks:
            chunk_id = hashlib.md5(f"{filepath.name}:{chunk}".encode()).hexdigest()
            c.execute("SELECT id FROM memory_chunks WHERE id=?", (chunk_id,))
            if c.fetchone():
                continue

            emb = self._get_embedding(chunk)
            c.execute(
                "INSERT INTO memory_chunks (id, source_file, content, timestamp, embedding) VALUES (?, ?, ?, ?, ?)",
                (chunk_id, filepath.name, chunk[:4000], datetime.now().isoformat(), emb.tobytes()),
            )
            added += 1

        conn.commit()
        return added

    def _semantic_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        query_emb = self._get_embedding(query)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT source_file, content, embedding FROM memory_chunks")

        results: List[Dict[str, Any]] = []
        for source, content, emb_bytes in c.fetchall():
            emb = np.frombuffer(emb_bytes, dtype=np.float32)
            similarity = float(np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb)))
            results.append({
                "source": source,
                "content": content[:200] + "..." if len(content) > 200 else content,
                "similarity": similarity,
            })

        conn.close()
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def _update_index_meta(self, build_result: Dict[str, Any]) -> None:
        meta = {
            "last_updated": self._now(),
            "core_memory": str(self.core_memory),
            "total_daily_logs": len(list(self.daily_dir.glob("*.md"))),
            "total_archived": len(list(self.archive_dir.glob("*.md"))),
            "total_distilled": len(list(self.distilled_dir.glob("*.md"))),
            "indexed_chunks": build_result.get("indexed_chunks", 0),
        }
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)


# ===== Skill entry points =====

def write(content: str, tags: List[str] | None = None, source: str | None = None) -> Dict[str, Any]:
    master = MemoryMaster()
    metadata: Dict[str, Any] = {}
    if tags:
        metadata["tags"] = tags
    if source:
        metadata["source"] = source
    return master.write_daily(content, metadata=metadata or None)


def consolidate(dry_run: bool = False) -> Dict[str, Any]:
    return MemoryMaster().consolidate(dry_run=dry_run)


def archive_old_logs(days: int = 7) -> Dict[str, Any]:
    return MemoryMaster().archive_old_logs(days=days)


def search(query: str, limit: int = 5) -> Dict[str, Any]:
    return MemoryMaster().search(query=query, limit=limit)


def build_index() -> Dict[str, Any]:
    return MemoryMaster().build_index()


def get_status() -> Dict[str, Any]:
    return MemoryMaster().get_status()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python memory_master.py <action> [args...]")
        print("Actions: write, consolidate, archive, search, index, status")
        sys.exit(1)

    action = sys.argv[1]
    master = MemoryMaster()

    if action == "write":
        content = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Empty entry"
        print(json.dumps(master.write_daily(content), indent=2, ensure_ascii=False))
    elif action == "consolidate":
        dry_run = "--dry-run" in sys.argv
        print(json.dumps(master.consolidate(dry_run=dry_run), indent=2, ensure_ascii=False))
    elif action == "archive":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        print(json.dumps(master.archive_old_logs(days=days), indent=2, ensure_ascii=False))
    elif action == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "test"
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        print(json.dumps(master.search(query=query, limit=limit), indent=2, ensure_ascii=False))
    elif action == "index":
        print(json.dumps(master.build_index(), indent=2, ensure_ascii=False))
    elif action == "status":
        print(json.dumps(master.get_status(), indent=2, ensure_ascii=False))
    else:
        print(f"Unknown action: {action}")
