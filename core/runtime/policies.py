from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import RouteDecision, TaskEnvelope


class PolicyViolation(Exception):
    pass


@dataclass(frozen=True)
class PolicyContext:
    route: RouteDecision | None = None
    recall_performed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryPolicyEngine:
    """Minimal memory gate skeleton.

    Current enforcement rule:
    - if task.references_memory is True, recall must have been performed
    """

    def requires_recall(self, task: TaskEnvelope) -> bool:
        return task.references_memory

    def validate(self, task: TaskEnvelope, context: PolicyContext | None = None) -> None:
        context = context or PolicyContext()
        if self.requires_recall(task) and not context.recall_performed:
            raise PolicyViolation("Memory recall required before execution")
