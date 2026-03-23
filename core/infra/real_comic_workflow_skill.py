from __future__ import annotations

from core.infra.comic_adapters import (
    AdapterError,
    AdapterTimeout,
    AdapterValidationError,
    AnimeAvatarAdapter,
    BaoyuComicAdapter,
    ComicScriptAdapter,
    ComiCogAdapter,
)
from core.infra.comic_compiler import ComicScriptCompiler, build_hidream_payloads
from core.infra.comic_hidream_adapter import ComicHiDreamAdapter
from core.infra.skill_contracts import CapabilityProfile, ExecutionResult, GlobalContext, ISkill, ToolSchema


class RealComicWorkflowSkill(ISkill):
    name = "real-comic-workflow"
    description = "Adapter-backed real comic workflow integration layer"

    def init(self, context: GlobalContext) -> None:
        self._context = context
        config = context.config if context and context.config else {}
        workspace_root = config.get("workspace_root")
        skills_root = config.get("skills_root")
        if not workspace_root:
            raise RuntimeError("workspace_root missing for real-comic-workflow")
        self._comic_script = ComicScriptAdapter(workspace_root=workspace_root, skills_root=skills_root)
        self._anime_avatar = AnimeAvatarAdapter(workspace_root=workspace_root, skills_root=skills_root)
        self._comi_cog = ComiCogAdapter(workspace_root=workspace_root, skills_root=skills_root)
        self._baoyu = BaoyuComicAdapter(workspace_root=workspace_root, skills_root=skills_root)
        self._compiler = ComicScriptCompiler()
        if not skills_root:
            raise RuntimeError("skills_root missing for real-comic-workflow")
        self._comic_hidream = ComicHiDreamAdapter(skills_root)

    def shutdown(self) -> None:
        self._context = None

    def get_tool_schemas(self):
        low_side_effect = CapabilityProfile(side_effect_level="low")
        high_side_effect = CapabilityProfile(side_effect_level="high")
        return [
            ToolSchema(name="script_generate", description="Generate comic script scaffold via comic-script", parameters={}, capabilities=low_side_effect),
            ToolSchema(name="avatar_prompt_generate", description="Build avatar generation prompt via anime-avatar-generation", parameters={}, capabilities=low_side_effect),
            ToolSchema(name="comic_render_prompt", description="Build comic render prompt via comi-cog", parameters={}, capabilities=low_side_effect),
            ToolSchema(name="knowledge_comic_plan", description="Create knowledge comic execution plan via baoyu-comic", parameters={}, capabilities=low_side_effect),
            ToolSchema(name="compile_storyboard", description="Compile topic into strong structured storyboard JSON", parameters={}, capabilities=low_side_effect),
            ToolSchema(name="build_hidream_payloads", description="Convert compiled storyboard into hidream-api-gen payloads", parameters={}, capabilities=low_side_effect),
            ToolSchema(name="adapt_hidream_requests", description="Adapt generic comic payloads into concrete HiDream requests", parameters={}, capabilities=low_side_effect),
            ToolSchema(name="submit_hidream_requests", description="Submit concrete HiDream requests", parameters={}, capabilities=high_side_effect),
        ]

    def execute(self, tool_name: str, params: dict):
        try:
            if tool_name == "script_generate":
                return ExecutionResult.success(self._comic_script.generate_script_scaffold(params))
            if tool_name == "avatar_prompt_generate":
                return ExecutionResult.success(self._anime_avatar.build_avatar_prompt(params))
            if tool_name == "comic_render_prompt":
                return ExecutionResult.success(self._comi_cog.build_render_prompt(params))
            if tool_name == "knowledge_comic_plan":
                return ExecutionResult.success(self._baoyu.plan_knowledge_comic(params))
            if tool_name == "compile_storyboard":
                topic = params.get("topic")
                if not isinstance(topic, str) or not topic.strip():
                    return ExecutionResult.failure("topic must be a non-empty string", code="ADAPTER_VALIDATION_ERROR")
                return ExecutionResult.success(self._compiler.compile(topic.strip()))
            if tool_name == "build_hidream_payloads":
                compiled = params.get("compiled_storyboard")
                if not isinstance(compiled, dict) or "global_settings" not in compiled or "panel_array" not in compiled:
                    return ExecutionResult.failure("compiled_storyboard must be a compiled storyboard dict", code="ADAPTER_VALIDATION_ERROR")
                return ExecutionResult.success(build_hidream_payloads(compiled))
            if tool_name == "adapt_hidream_requests":
                hidream_payloads = params.get("hidream_payloads")
                if not isinstance(hidream_payloads, dict) or "character_sheet_payload" not in hidream_payloads or "panel_payloads" not in hidream_payloads:
                    return ExecutionResult.failure("hidream_payloads must include character_sheet_payload and panel_payloads", code="ADAPTER_VALIDATION_ERROR")
                return ExecutionResult.success(self._comic_hidream.adapt_payloads(hidream_payloads))
            if tool_name == "submit_hidream_requests":
                request_bundle = params.get("request_bundle")
                if not isinstance(request_bundle, dict) or "character_sheet_request" not in request_bundle or "panel_requests" not in request_bundle:
                    return ExecutionResult.failure("request_bundle must include character_sheet_request and panel_requests", code="ADAPTER_VALIDATION_ERROR")
                return ExecutionResult.success(self._comic_hidream.submit_bundle(request_bundle))
            return ExecutionResult.failure(f"Unknown tool: {tool_name}", code="UNKNOWN_TOOL")
        except AdapterValidationError as e:
            return ExecutionResult.failure(str(e), code="ADAPTER_VALIDATION_ERROR")
        except AdapterTimeout as e:
            return ExecutionResult.failure(str(e), code="ADAPTER_TIMEOUT")
        except AdapterError as e:
            return ExecutionResult.failure(str(e), code="ADAPTER_ERROR")
        except Exception as e:
            return ExecutionResult.failure(str(e), code="ADAPTER_UNEXPECTED_ERROR")
