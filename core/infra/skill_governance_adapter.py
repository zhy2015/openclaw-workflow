"""Skill governance adapter for OpenClaw.

Bridges OpenClaw's task-node planning with the skill-governance control-plane:
- loads skills via skill-governance's ManifestRegistry/RegistryManager
- registers ISkill runtimes into SkillManager
- exposes a simple API for routing and dispatch based on TaskContext
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

# Import from the local skill-governance checkout
from skill_governance.contracts.skill_contracts import (
    GlobalContext,
    TaskContext,
    SkillDescriptor,
)
from skill_governance.engine.registry_manager import get_registry
from skill_governance.engine.skill_manager import SkillManager
from skill_governance.engine.skill_index import SkillIndex, SkillMatcher


@dataclass
class GovernanceConfig:
    """Lightweight config for the adapter."""

    allowed_visibility: List[str] | None = None
    allowed_status: List[str] | None = None


class SkillGovernanceAdapter:
    """High-level facade used by agents to choose and call skills."""

    def __init__(self, config: GovernanceConfig | None = None):
        self._config = config or GovernanceConfig(
            allowed_visibility=["public", "internal"],
            allowed_status=["active", "experimental"],
        )
        self._ctx = GlobalContext()
        self._manager = SkillManager(self._ctx)

        self._index: SkillIndex | None = None
        self._matcher: SkillMatcher | None = None

        self._load_and_register_skills()

    def _load_and_register_skills(self) -> None:
        """Scan manifests and register ISkill runtimes into SkillManager."""

        registry = get_registry()

        for name in registry.list_skills():
            manifest = registry.get_manifest(name)
            if not manifest:
                continue

            status = manifest.get("status", "experimental")
            visibility = manifest.get("visibility", "public")
            if self._config.allowed_status and status not in self._config.allowed_status:
                continue
            if self._config.allowed_visibility and visibility not in self._config.allowed_visibility:
                continue

            entry = manifest.get("entry_point")
            if not entry:
                continue

            try:
                module_name, class_name = entry.split(":", 1)
            except ValueError:
                continue

            try:
                import importlib

                module = importlib.import_module(module_name)
                cls = getattr(module, class_name)
                skill = cls()
            except Exception:
                continue

            self._manager.register(skill)

        self._rebuild_index()

    def _rebuild_index(self) -> None:
        descriptors: List[SkillDescriptor] = list(self._manager.get_descriptors().values())

        filtered: List[SkillDescriptor] = []
        for d in descriptors:
            if self._config.allowed_visibility and d.visibility not in self._config.allowed_visibility:
                continue
            if self._config.allowed_status and d.status not in self._config.allowed_status:
                continue
            filtered.append(d)

        self._index = SkillIndex(filtered)
        self._matcher = SkillMatcher(self._index)

    def resolve(
        self,
        task_node: str | None,
        intent: str,
        channel: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ):
        """Return ranked candidate skills for the given task context."""

        if self._matcher is None:
            self._rebuild_index()

        ctx = TaskContext(
            task_node=task_node,
            intent=intent,
            channel=channel,
            metadata=metadata or {},
        )

        return self._matcher.match(ctx)

    def execute(self, skill_name: str, tool_name: str, params: Dict[str, Any] | None = None):
        """Execute a tool inside a chosen skill via SkillManager."""

        return self._manager.dispatch(skill_name, tool_name, params or {})


if __name__ == "__main__":
    # Simple smoke test: route a governance-related intent and run echo
    adapter = SkillGovernanceAdapter()
    candidates = adapter.resolve(
        task_node="governance.demo",
        intent="need some skill 治理 support",
        channel="cli",
        metadata={"user": "local-test"},
    )

    print("Candidates:")
    for c in candidates:
        print(f"- {c.descriptor.name} (score={c.score}, reason={c.reason})")

    if candidates:
        best = candidates[0]
        res = adapter.execute(best.descriptor.name, "echo", {"text": "hello"})
        print("Result:", res.ok, res.data, res.error)
