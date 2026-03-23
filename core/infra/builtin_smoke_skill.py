from __future__ import annotations

from core.infra.skill_contracts import ExecutionResult, GlobalContext, ISkill, ToolSchema


class BuiltinSmokeSkill(ISkill):
    name = "builtin-smoke"
    description = "Deterministic built-in skill for workflow smoke validation"

    def init(self, context: GlobalContext) -> None:
        self._context = context

    def shutdown(self) -> None:
        self._context = None

    def get_tool_schemas(self):
        return [
            ToolSchema(name="ping", description="Return a simple pong payload", parameters={}),
            ToolSchema(name="echo", description="Echo a message", parameters={}),
            ToolSchema(name="join", description="Join two strings", parameters={}),
            ToolSchema(name="fail", description="Force a failure", parameters={}),
        ]

    def execute(self, tool_name: str, params: dict):
        if tool_name == "ping":
            return ExecutionResult.success({"pong": True, "message": params.get("x", params.get("message", ""))})
        if tool_name == "echo":
            return ExecutionResult.success({"echo": params.get("message")})
        if tool_name == "join":
            return ExecutionResult.success({"joined": f"{params.get('left', '')}|{params.get('right', '')}"})
        if tool_name == "fail":
            return ExecutionResult.failure("forced failure", code="FORCED_FAIL")
        return ExecutionResult.failure(f"Unknown tool: {tool_name}", code="UNKNOWN_TOOL")
