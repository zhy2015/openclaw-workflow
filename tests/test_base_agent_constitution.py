from __future__ import annotations

import asyncio
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.agent.base_agent import BaseAgent
from core.infra.skill_contracts import CapabilityProfile, ExecutionResult, GlobalContext, ToolSchema
from core.infra.skill_manager import SkillManager
from core.runtime.constitution import ConstitutionRuntime


class DummySkill:
    name = "dummy"
    description = "dummy skill"

    def get_tool_schemas(self):
        return [
            ToolSchema(name="ping", description="Ping", parameters={}),
            ToolSchema(
                name="memory_tool",
                description="Memory tool",
                parameters={},
                capabilities=CapabilityProfile(requires_memory=True),
            ),
        ]

    def init(self, context: GlobalContext):
        pass

    def shutdown(self):
        pass

    def execute(self, tool_name, params):
        return ExecutionResult.success({"tool": tool_name, "params": params})


class ProbeAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="probe", agent_type="test")

    async def process(self, context, **kwargs):
        return {"status": "noop"}


def _build_agent() -> ProbeAgent:
    manager = SkillManager()
    manager.register(DummySkill())
    agent = ProbeAgent()
    agent._constitution = ConstitutionRuntime(skill_manager=manager)
    return agent


def test_base_agent_invoke_skill_fast_path():
    agent = _build_agent()
    result = asyncio.run(agent._invoke_skill("dummy", "ping", {"x": 1}))
    assert result.ok is True
    assert result.data["tool"] == "ping"


def test_base_agent_invoke_skill_requires_memory_gate():
    agent = _build_agent()
    result = asyncio.run(agent._invoke_skill("dummy", "memory_tool", {}, references_memory=True, recall_performed=False))
    assert result.ok is False
    assert result.code == "POLICY_VIOLATION"


def test_base_agent_invoke_skill_allows_with_recall():
    agent = _build_agent()
    result = asyncio.run(agent._invoke_skill("dummy", "memory_tool", {}, references_memory=True, recall_performed=True))
    assert result.ok is True
