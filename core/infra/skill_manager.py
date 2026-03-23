"""Global skill governance entrypoint.

Control-plane only: registration, visibility aggregation, and dispatch.
It must not depend on any domain-specific business logic.
"""

from __future__ import annotations

from typing import Dict, List

from core.runtime.policies import PolicyContext, PolicyViolation

from .skill_contracts import CapabilityProfile, ExecutionResult, GlobalContext, ISkill, ToolSchema


class SkillManager:
    def __init__(self, context: GlobalContext | None = None):
        self._skills: Dict[str, ISkill] = {}
        self._tool_schemas: Dict[tuple[str, str], ToolSchema] = {}
        self._context = context or GlobalContext()

    def register(self, skill: ISkill) -> None:
        if skill.name in self._skills:
            raise ValueError(f"Skill already registered: {skill.name}")
        skill.init(self._context)
        self._skills[skill.name] = skill
        for schema in skill.get_tool_schemas():
            self._tool_schemas[(skill.name, schema.name)] = schema

    def unregister(self, skill_name: str) -> None:
        skill = self._skills.pop(skill_name, None)
        if skill is not None:
            skill.shutdown()
        for key in list(self._tool_schemas.keys()):
            if key[0] == skill_name:
                self._tool_schemas.pop(key, None)

    def list_skills(self) -> List[str]:
        return list(self._skills.keys())

    def get_all_tool_schemas(self) -> List[ToolSchema]:
        schemas: List[ToolSchema] = []
        for skill in self._skills.values():
            schemas.extend(skill.get_tool_schemas())
        return schemas

    def get_tool_schema(self, skill_name: str, tool_name: str) -> ToolSchema | None:
        return self._tool_schemas.get((skill_name, tool_name))

    def _validate_capabilities(
        self,
        skill_name: str,
        tool_name: str,
        capabilities: CapabilityProfile,
        policy_context: PolicyContext | None,
    ) -> None:
        route = policy_context.route if policy_context else None

        if capabilities.deprecated:
            raise PolicyViolation(f"Tool is deprecated: {skill_name}.{tool_name}")

        if capabilities.requires_memory and not (policy_context and policy_context.recall_performed):
            raise PolicyViolation(f"Memory recall required: {skill_name}.{tool_name}")

        if route:
            if route.mode == "fast" and capabilities.execution_mode == "slow_only":
                raise PolicyViolation(f"Fast path forbidden for slow_only tool: {skill_name}.{tool_name}")
            if route.mode == "slow" and capabilities.execution_mode == "fast_only":
                raise PolicyViolation(f"Slow path forbidden for fast_only tool: {skill_name}.{tool_name}")

    def _run_pre_dispatch_policy(self, skill_name: str, tool_name: str, params: dict, policy_context: PolicyContext | None = None) -> None:
        schema = self.get_tool_schema(skill_name, tool_name)
        if schema is None:
            raise PolicyViolation(f"Tool not found: {skill_name}.{tool_name}")

        if policy_context is not None:
            route = policy_context.route
            if route and route.mode == "fast" and route.requires_memory and not policy_context.recall_performed:
                raise PolicyViolation("Fast-path dispatch blocked: memory recall required")

        self._validate_capabilities(skill_name, tool_name, schema.capabilities, policy_context)

    def dispatch(
        self,
        skill_name: str,
        tool_name: str,
        params: dict | None = None,
        *,
        policy_context: PolicyContext | None = None,
    ) -> ExecutionResult:
        skill = self._skills.get(skill_name)
        if skill is None:
            return ExecutionResult.failure(f"Skill not found: {skill_name}", code="SKILL_NOT_FOUND")
        final_params = params or {}
        try:
            self._run_pre_dispatch_policy(skill_name, tool_name, final_params, policy_context)
        except PolicyViolation as e:
            return ExecutionResult.failure(str(e), code="POLICY_VIOLATION")
        return skill.execute(tool_name, final_params)
