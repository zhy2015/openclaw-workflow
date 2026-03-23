#!/usr/bin/env python3
"""
Closed loop orchestrator for the new core/engine stack only.

- Loads declarative YAML workflows
- Executes via core.engine.DAGEngine
- Persists start/success/failure to core.engine.WALEngine
- Passes node outputs through WorkflowContext
- Never imports archived engines
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.engine.runner import WorkflowRunner


class ClosedLoopOrchestrator:
    def __init__(self, workspace_root: str = "/root/.openclaw/workspace"):
        self.workspace_root = Path(workspace_root)
        self.runner = WorkflowRunner(workspace_root)

    async def execute_yaml(self, workflow_file: str) -> Dict[str, Any]:
        return await self.runner.run_yaml(workflow_file)


async def _main_async(workflow_file: str):
    orchestrator = ClosedLoopOrchestrator()
    result = await orchestrator.execute_yaml(workflow_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    import sys
    workflow_file = sys.argv[1] if len(sys.argv) > 1 else "test_chaining.yaml"
    asyncio.run(_main_async(workflow_file))


if __name__ == "__main__":
    main()
