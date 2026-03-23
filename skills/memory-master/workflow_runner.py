#!/usr/bin/env python3
"""Lightweight workflow runner for memory-master."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict

from memory_master import MemoryMaster


class WorkflowNode:
    def __init__(self, node_id: str, action: str, inputs: Dict[str, Any] | None = None):
        self.node_id = node_id
        self.action = action
        self.inputs = inputs or {}


class WorkflowPipeline:
    def __init__(self, pipeline_id: str, name: str, nodes: list[WorkflowNode]):
        self.pipeline_id = pipeline_id
        self.name = name
        self.nodes = nodes


class WorkflowRunner:
    def __init__(self, workspace: str):
        self.mm = MemoryMaster(workspace)
        self.actions = {
            "write": self._write,
            "consolidate": self._consolidate,
            "archive": self._archive,
            "index": self._index,
            "search": self._search,
            "status": self._status,
        }

    def _write(self, **kwargs):
        return self.mm.write_daily(kwargs.get("content", ""), metadata=kwargs.get("metadata"))

    def _consolidate(self, **kwargs):
        return self.mm.consolidate(dry_run=kwargs.get("dry_run", False))

    def _archive(self, **kwargs):
        return self.mm.archive_old_logs(days=int(kwargs.get("days", 7)))

    def _index(self, **kwargs):
        return self.mm.build_index()

    def _search(self, **kwargs):
        return self.mm.search(query=kwargs.get("query", ""), limit=int(kwargs.get("limit", 5)))

    def _status(self, **kwargs):
        return self.mm.get_status()

    async def run(self, pipeline: WorkflowPipeline):
        results = {}
        for node in pipeline.nodes:
            handler = self.actions.get(node.action)
            if not handler:
                raise KeyError(f"Unknown action: {node.action}")
            results[node.node_id] = handler(**node.inputs)
            await asyncio.sleep(0)
        return results


def load_pipeline(path: str | Path) -> WorkflowPipeline:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    nodes = [WorkflowNode(node["node_id"], node["action"], node.get("inputs", {})) for node in data.get("nodes", [])]
    return WorkflowPipeline(data["pipeline_id"], data.get("name", data["pipeline_id"]), nodes)


async def main_async(args):
    runner = WorkflowRunner(args.workspace)
    pipeline = load_pipeline(args.pipeline)
    result = await runner.run(pipeline)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Run memory-master workflow pipelines")
    parser.add_argument("pipeline", help="Path to pipeline JSON definition")
    parser.add_argument("--workspace", default="/root/.openclaw/workspace", help="Workspace root")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
