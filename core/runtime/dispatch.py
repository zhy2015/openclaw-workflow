from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.infra.skill_contracts import ExecutionResult
from core.infra.skill_manager import SkillManager
from core.runtime.policies import PolicyContext


@dataclass
class DispatchTarget:
    skill_name: str
    tool_name: str


class GovernedDispatcher:
    def __init__(self, skill_manager: SkillManager | None = None):
        self.skill_manager = skill_manager or SkillManager()

    @staticmethod
    def parse_legacy_uri(uri: str) -> DispatchTarget:
        prefix = "skill://"
        if not uri.startswith(prefix):
            raise ValueError(f"Unsupported skill URI: {uri}")
        body = uri[len(prefix):]
        if "/" not in body:
            raise ValueError(f"Invalid skill URI: {uri}")
        skill_name, tool_name = body.split("/", 1)
        if not skill_name or not tool_name:
            raise ValueError(f"Invalid skill URI: {uri}")
        return DispatchTarget(skill_name=skill_name, tool_name=tool_name)

    def dispatch(self, skill_name: str, tool_name: str, params: dict[str, Any] | None = None) -> ExecutionResult:
        return self.skill_manager.dispatch(
            skill_name,
            tool_name,
            params or {},
            policy_context=PolicyContext(),
        )
