from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.infra.skill_contracts import ExecutionResult, GlobalContext, ToolSchema
from core.infra.skill_manager import SkillManager
from core.runtime.constitution import ConstitutionRuntime
from core.runtime.types import TaskEnvelope


class DummySkill:
    name = "dummy"
    description = "dummy skill"

    def get_tool_schemas(self):
        return [ToolSchema(name="ping", description="Ping", parameters={})]

    def init(self, context: GlobalContext):
        pass

    def shutdown(self):
        pass

    def execute(self, tool_name, params):
        return ExecutionResult.success({"pong": True})


def test_constitution_writes_progress_checkpoint(tmp_path):
    manager = SkillManager()
    manager.register(DummySkill())
    runtime = ConstitutionRuntime(skill_manager=manager, workspace_root=str(WORKSPACE_ROOT))
    runtime.progress.root = tmp_path
    task = TaskEnvelope(
        task_type="skill_call",
        intent="dummy.ping",
        target_skill="dummy",
        target_tool="ping",
    )
    result = asyncio.run(runtime.invoke(task))
    assert result.ok is True

    progress_file = tmp_path / f"{task.request_id}.json"
    assert progress_file.exists()
    data = json.loads(progress_file.read_text(encoding="utf-8"))
    assert data["task_id"] == task.request_id
    assert data["status"] == "done"
    assert data["stage"] == "fast_dispatch"
