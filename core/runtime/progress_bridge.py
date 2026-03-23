from __future__ import annotations

from datetime import datetime, timezone

from core.infra.notification import notify_alert, notify_milestone

from .progress import ProgressCheckpoint
from .progress_notifier import ProgressNotifier
from .progress_policy import ProgressPolicy, policy_from_dict
from .progress_watcher import ProgressWatcher, WatcherState


class ProgressBridge:
    """Bridge progress checkpoints into notification events."""

    def __init__(self, policy: ProgressPolicy | None = None):
        self.policy = policy or ProgressPolicy()
        self.watcher = ProgressWatcher(self.policy)
        self.notifier = ProgressNotifier()
        self.state_by_task: dict[str, WatcherState] = {}

    async def emit_for_checkpoint(self, checkpoint: ProgressCheckpoint) -> dict | None:
        policy = policy_from_dict((checkpoint.meta or {}).get("progress_policy"))
        if policy != self.policy:
            self.policy = policy
            self.watcher = ProgressWatcher(policy)

        state = self.state_by_task.get(checkpoint.task_id) or WatcherState()
        event, new_state = self.watcher.evaluate(checkpoint, state, now=datetime.now(timezone.utc))
        self.state_by_task[checkpoint.task_id] = new_state
        if event is None:
            return None

        payload = self.notifier.build_payload(event)
        if event.kind in {"task_failed", "task_interrupted"}:
            await notify_alert(checkpoint.task_id, checkpoint.stage, payload["text"], payload)
        else:
            await notify_milestone(checkpoint.task_id, checkpoint.stage, payload["text"], payload)
        return payload
