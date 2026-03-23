"""Unified skill contracts for governance/control-plane boundaries.

This module defines the narrow contract between the global governance layer
(SkillManager) and domain-specific adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Literal, runtime_checkable


@dataclass(frozen=True)
class CapabilityProfile:
    execution_mode: Literal["fast_only", "slow_only", "both"] = "both"
    requires_memory: bool = False
    side_effect_level: Literal["none", "low", "high"] = "none"
    recovery_required: bool = False
    deprecated: bool = False


@dataclass(frozen=True)
class ToolSchema:
    """LLM-facing tool schema exposed by a skill adapter."""

    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    capabilities: CapabilityProfile = field(default_factory=CapabilityProfile)


@dataclass(frozen=True)
class ExecutionResult:
    """Unified execution result returned by all skill adapters."""

    ok: bool
    data: Any = None
    error: Optional[str] = None
    code: str = "OK"
    meta: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, data: Any = None, **meta: Any) -> "ExecutionResult":
        return cls(ok=True, data=data, meta=meta)

    @classmethod
    def failure(cls, error: str, code: str = "ERROR", **meta: Any) -> "ExecutionResult":
        return cls(ok=False, error=error, code=code, meta=meta)


@dataclass(frozen=True)
class GlobalContext:
    """Minimal capability bag passed to skills on init.

    Keep this intentionally small to avoid domain pollution.
    Add narrow capabilities instead of a giant mutable context object.
    """

    config: Dict[str, Any] = field(default_factory=dict)
    logger: Any = None
    telemetry: Any = None
    storage: Any = None


@runtime_checkable
class ISkill(Protocol):
    """The only contract governance depends on."""

    name: str
    description: str

    def get_tool_schemas(self) -> List[ToolSchema]:
        ...

    def init(self, context: GlobalContext) -> None:
        ...

    def shutdown(self) -> None:
        ...

    def execute(self, tool_name: str, params: Dict[str, Any]) -> ExecutionResult:
        ...
