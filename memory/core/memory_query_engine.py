#!/usr/bin/env python3
"""Compatibility wrapper: route legacy imports to the skill-owned query engine."""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_DIR = Path("/root/.openclaw/workspace/skills/memory-master")
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from memory_query_engine import MemoryQueryEngine, SearchResult  # noqa: E402,F401


if __name__ == "__main__":
    engine = MemoryQueryEngine()
    print(engine.index_memory(force_rebuild=True))
    print(engine.get_stats())
    engine.close()
