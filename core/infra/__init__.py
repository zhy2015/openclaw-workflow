from .skill_contracts import ISkill, ToolSchema, ExecutionResult, GlobalContext
from .skill_manager import SkillManager
from .legacy_registry_adapter import LegacyManifestSkillAdapter, LegacyRegistryAdapterFactory

__all__ = [
    "ISkill",
    "ToolSchema",
    "ExecutionResult",
    "GlobalContext",
    "SkillManager",
    "LegacyManifestSkillAdapter",
    "LegacyRegistryAdapterFactory",
]
