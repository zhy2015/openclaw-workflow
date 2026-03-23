from __future__ import annotations

from .types import RouteDecision, TaskEnvelope


class TaskRouter:
    """Fast/slow path classifier.

    Current version is intentionally conservative:
    - explicit complexity_hint=slow -> slow
    - memory / side effects / workflow-like task types -> slow
    - otherwise fast
    """

    SLOW_TASK_TYPES = {"workflow", "multi_step", "pipeline", "background_job"}

    def decide(self, task: TaskEnvelope) -> RouteDecision:
        if task.complexity_hint == "slow":
            return RouteDecision(
                mode="slow",
                reason="explicit_slow_hint",
                requires_memory=task.references_memory,
                requires_wal=True,
                requires_sandbox=True,
                target_skill=task.target_skill,
                target_tool=task.target_tool,
            )

        if task.task_type in self.SLOW_TASK_TYPES or task.requires_side_effects:
            return RouteDecision(
                mode="slow",
                reason="task_type_or_side_effects",
                requires_memory=task.references_memory,
                requires_wal=True,
                requires_sandbox=True,
                target_skill=task.target_skill,
                target_tool=task.target_tool,
            )

        return RouteDecision(
            mode="fast",
            reason="default_fast_path",
            requires_memory=task.references_memory,
            requires_wal=False,
            requires_sandbox=False,
            target_skill=task.target_skill,
            target_tool=task.target_tool,
        )
