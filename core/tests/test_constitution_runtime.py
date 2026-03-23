from __future__ import annotations

import asyncio
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
        return [
            ToolSchema(name="ping", description="Ping", parameters={}),
            ToolSchema(name="echo", description="Echo", parameters={}),
            ToolSchema(name="join", description="Join", parameters={}),
            ToolSchema(name="fail", description="Fail", parameters={}),
        ]

    def init(self, context: GlobalContext):
        pass

    def shutdown(self):
        pass

    def execute(self, tool_name, params):
        if tool_name == "ping":
            return ExecutionResult.success({"pong": True, "message": params.get("x", "")})
        if tool_name == "echo":
            return ExecutionResult.success({"echo": params.get("message")})
        if tool_name == "join":
            left = params.get("left", "")
            right = params.get("right", "")
            return ExecutionResult.success({"joined": f"{left}|{right}"})
        if tool_name == "fail":
            return ExecutionResult.failure("forced failure", code="FORCED_FAIL")
        return ExecutionResult.failure("unknown tool", code="UNKNOWN_TOOL")


def _build_runtime() -> ConstitutionRuntime:
    manager = SkillManager()
    manager.register(DummySkill())
    return ConstitutionRuntime(skill_manager=manager, workspace_root=str(WORKSPACE_ROOT))


def test_constitution_fast_path_dispatch():
    runtime = _build_runtime()
    task = TaskEnvelope(
        task_type="skill_call",
        intent="dummy.ping",
        target_skill="dummy",
        target_tool="ping",
        params={"x": 1},
    )
    result = asyncio.run(runtime.invoke(task))
    assert result.ok is True
    assert result.data["pong"] is True


def test_constitution_slow_path_runs_single_node_workflow():
    runtime = _build_runtime()
    task = TaskEnvelope(
        task_type="workflow",
        intent="dummy slow ping",
        target_skill="dummy",
        target_tool="ping",
        params={"x": "1"},
        complexity_hint="slow",
    )
    result = asyncio.run(runtime.invoke(task))
    assert result.ok is True
    assert result.meta.get("route") == "slow"
    assert "workflow_id" in result.meta
    assert result.data["results"]["task"]["pong"] is True


def test_constitution_slow_path_runs_multi_node_workflow():
    runtime = _build_runtime()
    task = TaskEnvelope(
        task_type="workflow",
        intent="dummy multi-step",
        complexity_hint="slow",
        workflow_nodes=[
            {
                "id": "first",
                "skill_name": "dummy",
                "tool_name": "ping",
                "inputs": {"x": "hello"},
                "outputs": ["message"],
                "next": ["second"],
            },
            {
                "id": "second",
                "skill_name": "dummy",
                "tool_name": "echo",
                "inputs": {"message": "first.message"},
                "outputs": ["echo"],
            },
        ],
    )
    result = asyncio.run(runtime.invoke(task))
    assert result.ok is True
    assert result.meta.get("route") == "slow"
    assert result.data["results"]["first"]["message"] == "hello"
    assert result.data["results"]["second"]["echo"] == "hello"


def test_constitution_slow_path_runs_multi_dependency_join():
    runtime = _build_runtime()
    task = TaskEnvelope(
        task_type="workflow",
        intent="dummy join graph",
        complexity_hint="slow",
        workflow_nodes=[
            {
                "id": "left",
                "skill_name": "dummy",
                "tool_name": "ping",
                "inputs": {"x": "L"},
                "outputs": ["message"],
                "next": ["join"],
            },
            {
                "id": "right",
                "skill_name": "dummy",
                "tool_name": "ping",
                "inputs": {"x": "R"},
                "outputs": ["message"],
                "next": ["join"],
            },
            {
                "id": "join",
                "skill_name": "dummy",
                "tool_name": "join",
                "inputs": {"left": "left.message", "right": "right.message"},
                "outputs": ["joined"],
            },
        ],
    )
    result = asyncio.run(runtime.invoke(task))
    assert result.ok is True
    assert result.data["results"]["join"]["joined"] == "L|R"


def test_constitution_slow_path_failure_bubbles_up():
    runtime = _build_runtime()
    task = TaskEnvelope(
        task_type="workflow",
        intent="dummy fail path",
        complexity_hint="slow",
        workflow_nodes=[
            {
                "id": "first",
                "skill_name": "dummy",
                "tool_name": "ping",
                "inputs": {"x": "ok"},
                "outputs": ["message"],
                "next": ["boom"],
            },
            {
                "id": "boom",
                "skill_name": "dummy",
                "tool_name": "fail",
                "inputs": {},
            },
        ],
    )
    result = asyncio.run(runtime.invoke(task))
    assert result.ok is False
    assert result.code == "SLOW_PATH_ERROR"
