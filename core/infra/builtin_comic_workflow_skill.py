from __future__ import annotations

from core.infra.skill_contracts import ExecutionResult, GlobalContext, ISkill, ToolSchema


class BuiltinComicWorkflowSkill(ISkill):
    name = "builtin-comic-workflow"
    description = "Deterministic built-in adapters for comic workflow scaffolding"

    def init(self, context: GlobalContext) -> None:
        self._context = context

    def shutdown(self) -> None:
        self._context = None

    def get_tool_schemas(self):
        return [
            ToolSchema(name="classify", description="Classify comic intent", parameters={}),
            ToolSchema(name="script_scaffold", description="Create script scaffold", parameters={}),
            ToolSchema(name="character_scaffold", description="Create character scaffold", parameters={}),
            ToolSchema(name="render_plan", description="Create render routing plan", parameters={}),
            ToolSchema(name="package_plan", description="Create packaging summary", parameters={}),
        ]

    def execute(self, tool_name: str, params: dict):
        topic = params.get("topic", "untitled")
        comic_type = params.get("comic_type", "story")
        if tool_name == "classify":
            route = "baoyu-comic" if comic_type in {"knowledge", "tutorial", "biography"} else "comi-cog"
            return ExecutionResult.success({
                "topic": topic,
                "comic_type": comic_type,
                "route": route,
            })
        if tool_name == "script_scaffold":
            return ExecutionResult.success({
                "script_outline": f"script-outline::{topic}",
                "panels": params.get("panels", 6),
            })
        if tool_name == "character_scaffold":
            return ExecutionResult.success({
                "character_ref": f"character-ref::{topic}",
                "style": params.get("style", "manga"),
            })
        if tool_name == "render_plan":
            route = params.get("route", "comi-cog")
            return ExecutionResult.success({
                "render_tool": route,
                "render_spec": f"render::{route}::{topic}",
            })
        if tool_name == "package_plan":
            return ExecutionResult.success({
                "deliverable": f"comic-package::{topic}",
                "format": params.get("format", "pdf"),
            })
        return ExecutionResult.failure(f"Unknown tool: {tool_name}", code="UNKNOWN_TOOL")
