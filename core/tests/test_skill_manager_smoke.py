from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.infra.skill_contracts import CapabilityProfile, ExecutionResult, GlobalContext, ToolSchema
from core.infra.skill_manager import SkillManager
from core.runtime.policies import PolicyContext
from core.runtime.types import RouteDecision


class DummySkill:
    name = "dummy"
    description = "dummy skill"

    def __init__(self):
        self.inited = False
        self.stopped = False

    def get_tool_schemas(self):
        return [
            ToolSchema(name="ping", description="Ping", parameters={}),
            ToolSchema(
                name="slow_tool",
                description="Slow only tool",
                parameters={},
                capabilities=CapabilityProfile(execution_mode="slow_only"),
            ),
            ToolSchema(
                name="memory_tool",
                description="Needs memory",
                parameters={},
                capabilities=CapabilityProfile(requires_memory=True),
            ),
            ToolSchema(
                name="deprecated_tool",
                description="Deprecated",
                parameters={},
                capabilities=CapabilityProfile(deprecated=True),
            ),
        ]

    def init(self, context: GlobalContext):
        self.inited = True

    def shutdown(self):
        self.stopped = True

    def execute(self, tool_name, params):
        if tool_name in {"ping", "slow_tool", "memory_tool", "deprecated_tool"}:
            return ExecutionResult.success({"tool": tool_name, "params": params})
        return ExecutionResult.failure("unknown tool", code="UNKNOWN_TOOL")


def test_skill_manager_register_and_dispatch():
    manager = SkillManager()
    skill = DummySkill()
    manager.register(skill)

    assert skill.inited is True
    assert manager.list_skills() == ["dummy"]
    result = manager.dispatch("dummy", "ping", {"x": 1})
    assert result.ok is True
    assert result.data["tool"] == "ping"


def test_skill_manager_missing_skill_returns_failure():
    manager = SkillManager()
    result = manager.dispatch("missing", "ping", {})
    assert result.ok is False
    assert result.code == "SKILL_NOT_FOUND"


def test_skill_manager_missing_tool_returns_policy_failure():
    manager = SkillManager()
    manager.register(DummySkill())
    result = manager.dispatch("dummy", "missing_tool", {})
    assert result.ok is False
    assert result.code == "POLICY_VIOLATION"


def test_slow_only_tool_blocked_on_fast_path():
    manager = SkillManager()
    manager.register(DummySkill())
    route = RouteDecision(mode="fast", reason="test")
    result = manager.dispatch("dummy", "slow_tool", {}, policy_context=PolicyContext(route=route))
    assert result.ok is False
    assert result.code == "POLICY_VIOLATION"


def test_requires_memory_tool_blocked_without_recall():
    manager = SkillManager()
    manager.register(DummySkill())
    route = RouteDecision(mode="fast", reason="test", requires_memory=True)
    result = manager.dispatch("dummy", "memory_tool", {}, policy_context=PolicyContext(route=route, recall_performed=False))
    assert result.ok is False
    assert result.code == "POLICY_VIOLATION"


def test_requires_memory_tool_allows_with_recall():
    manager = SkillManager()
    manager.register(DummySkill())
    route = RouteDecision(mode="fast", reason="test", requires_memory=True)
    result = manager.dispatch("dummy", "memory_tool", {}, policy_context=PolicyContext(route=route, recall_performed=True))
    assert result.ok is True


def test_deprecated_tool_rejected():
    manager = SkillManager()
    manager.register(DummySkill())
    result = manager.dispatch("dummy", "deprecated_tool", {})
    assert result.ok is False
    assert result.code == "POLICY_VIOLATION"
