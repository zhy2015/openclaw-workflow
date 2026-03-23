from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from core.infra.registry.manager import RegistryManager
from core.infra.skill_contracts import ExecutionResult, GlobalContext, ISkill, ToolSchema


@dataclass
class LegacyActionSchema:
    skill_name: str
    tool_name: str
    description: str
    parameters: Dict[str, Any]


class LegacyManifestSkillAdapter(ISkill):
    def __init__(self, registry: RegistryManager, manifest: dict):
        self._registry = registry
        self._manifest = manifest
        self.name = manifest["name"]
        self.description = manifest.get("description", "legacy manifest skill")
        self._context: GlobalContext | None = None

    def get_tool_schemas(self) -> List[ToolSchema]:
        schemas: List[ToolSchema] = []
        for action_name, action in (self._manifest.get("actions") or {}).items():
            if not isinstance(action, dict):
                continue
            schemas.append(
                ToolSchema(
                    name=action_name,
                    description=action.get("description", f"Legacy action {action_name}"),
                    parameters=action.get("args", {}),
                )
            )
        return schemas

    def init(self, context: GlobalContext) -> None:
        self._context = context

    def shutdown(self) -> None:
        self._context = None

    def execute(self, tool_name: str, params: Dict[str, Any]) -> ExecutionResult:
        uri = f"skill://{self.name}/{tool_name}"
        try:
            data = self._registry.execute(uri, **params)
            return ExecutionResult.success(data, legacy_bridge=True, legacy_uri=uri)
        except Exception as e:
            return ExecutionResult.failure(str(e), code="LEGACY_EXECUTION_ERROR", legacy_bridge=True, legacy_uri=uri)


class LegacyRegistryAdapterFactory:
    """Bridge legacy manifest skills into ISkill adapters."""

    def __init__(self, registry: RegistryManager | None = None):
        self.registry = registry or RegistryManager()
        self.registry.scan()

    def build_adapters(self) -> list[LegacyManifestSkillAdapter]:
        adapters: list[LegacyManifestSkillAdapter] = []
        for skill_name in self.registry.list_skills():
            manifest = self.registry.get_manifest(skill_name)
            if not manifest:
                continue
            adapters.append(LegacyManifestSkillAdapter(self.registry, manifest))
        return adapters

    def list_legacy_skills(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for skill_name in self.registry.list_skills():
            manifest = self.registry.get_manifest(skill_name) or {}
            items.append(
                {
                    "name": skill_name,
                    "category": manifest.get("category", "uncategorized"),
                    "execution_type": manifest.get("execution_type", "python_import"),
                }
            )
        return items
