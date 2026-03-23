#!/usr/bin/env python3
"""Unified memory query engine backed by FTS5."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SearchResult:
    uri: str
    title: str
    content: str
    score: float
    metadata: Dict


class MemoryQueryEngine:
    def __init__(self, workspace_root: str = "/root/.openclaw/workspace", db_path: Optional[str] = None):
        self.workspace = Path(workspace_root)
        self.memory_root = self.workspace / "memory"
        self.db_path = db_path or str(self.memory_root / "index" / "memory_fts5.db")
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_index USING fts5(
                uri,
                title,
                content,
                source,
                mtype,
                tokenize='porter unicode61'
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_meta (
                uri TEXT PRIMARY KEY,
                path TEXT,
                last_modified REAL,
                indexed_at REAL
            )
            """
        )
        self.conn.commit()

    def index_memory(self, force_rebuild: bool = False) -> Dict:
        if force_rebuild:
            self.conn.execute("DELETE FROM memory_index")
            self.conn.execute("DELETE FROM memory_meta")
            self.conn.commit()

        indexed_files = 0
        indexed_sections = 0

        targets = [
            (self.memory_root / "core", "core"),
            (self.memory_root / "daily", "daily"),
            (self.memory_root / "distilled", "distilled"),
            (self.memory_root / "archive", "archive"),
            (self.memory_root / "metrics", "metrics"),
        ]

        for directory, namespace in targets:
            if not directory.exists():
                continue
            for f in sorted(directory.glob("*.md")):
                indexed_sections += self._index_markdown(f, f"memory://{namespace}/{f.name}")
                indexed_files += 1
            for f in sorted(directory.glob("*.csv")):
                self._index_csv(f, f"memory://{namespace}/{f.name}")
                indexed_files += 1

        self.conn.commit()
        return {
            "status": "success",
            "indexed_files": indexed_files,
            "indexed_sections": indexed_sections,
            "db_path": self.db_path,
        }

    def _index_markdown(self, file_path: Path, uri: str) -> int:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        title = ""
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            title = title_match.group(1)

        self.conn.execute("DELETE FROM memory_index WHERE source = ?", (str(file_path),))
        sections = [s.strip() for s in re.split(r"\n(?=## )", content) if s.strip()]
        count = 0
        for i, section in enumerate(sections):
            section_title = title
            first_line = section.splitlines()[0] if section.splitlines() else ""
            if first_line.startswith("## "):
                section_title = first_line[3:].strip()
            elif not section_title:
                section_title = file_path.stem

            self.conn.execute(
                "INSERT INTO memory_index (uri, title, content, source, mtype) VALUES (?, ?, ?, ?, ?)",
                (f"{uri}#{i}", section_title, section, str(file_path), "markdown"),
            )
            count += 1

        self.conn.execute(
            "INSERT OR REPLACE INTO memory_meta (uri, path, last_modified, indexed_at) VALUES (?, ?, ?, strftime('%s','now'))",
            (uri, str(file_path), file_path.stat().st_mtime),
        )
        return count

    def _index_csv(self, file_path: Path, uri: str):
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        self.conn.execute("DELETE FROM memory_index WHERE source = ?", (str(file_path),))
        self.conn.execute(
            "INSERT INTO memory_index (uri, title, content, source, mtype) VALUES (?, ?, ?, ?, ?)",
            (uri, file_path.stem, content, str(file_path), "csv"),
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO memory_meta (uri, path, last_modified, indexed_at) VALUES (?, ?, ?, strftime('%s','now'))",
            (uri, str(file_path), file_path.stat().st_mtime),
        )

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        cursor = self.conn.execute(
            """
            SELECT uri, title, content, source, bm25(memory_index) AS score
            FROM memory_index
            WHERE memory_index MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        )

        results: List[SearchResult] = []
        for uri, title, content, source, score in cursor.fetchall():
            results.append(
                SearchResult(
                    uri=uri,
                    title=title,
                    content=content[:500] + "..." if len(content) > 500 else content,
                    score=abs(score) if score else 0.0,
                    metadata={"source": source},
                )
            )
        return results

    def search_as_dict(self, query: str, limit: int = 10) -> Dict:
        return {
            "status": "success",
            "query": query,
            "limit": limit,
            "results": [asdict(r) for r in self.search(query=query, limit=limit)],
        }

    def get_stats(self) -> Dict:
        total_docs = self.conn.execute("SELECT COUNT(*) FROM memory_index").fetchone()[0]
        total_sources = self.conn.execute("SELECT COUNT(DISTINCT source) FROM memory_index").fetchone()[0]
        return {
            "status": "success",
            "total_documents": total_docs,
            "total_sources": total_sources,
            "db_path": self.db_path,
        }

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    engine = MemoryQueryEngine()
    print(engine.index_memory(force_rebuild=True))
    print(engine.get_stats())
    engine.close()
