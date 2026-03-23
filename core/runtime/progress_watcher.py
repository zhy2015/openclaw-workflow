from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from .progress import ProgressCheckpoint
from .progress_notifier import ProgressEvent
from .progress_policy import ProgressPolicy


@dataclass
class WatcherState:
    last_notified_at: datetime | None = None
    last_stage: str | None = None
    last_status: str | None = None


class ProgressWatcher:
    def __init__(self, policy: ProgressPolicy):
        self.policy = policy

    def _parse_ts(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    def evaluate(self, checkpoint: ProgressCheckpoint, state: Optional[WatcherState] = None, now: Optional[datetime] = None) -> tuple[Optional[ProgressEvent], WatcherState]:
        state = state or WatcherState()
        now = now or datetime.now(timezone.utc)

        if checkpoint.status == "failed" and self.policy.notify_on_failure:
            event = ProgressEvent(kind="task_failed", checkpoint=checkpoint, reason="failure")
            state.last_notified_at = now
            state.last_stage = checkpoint.stage
            state.last_status = checkpoint.status
            return event, state

        if checkpoint.status == "interrupted" and self.policy.notify_on_interrupt:
            event = ProgressEvent(kind="task_interrupted", checkpoint=checkpoint, reason="interrupt")
            state.last_notified_at = now
            state.last_stage = checkpoint.stage
            state.last_status = checkpoint.status
            return event, state

        if self.policy.notify_on_stage_change and checkpoint.stage != state.last_stage:
            event = ProgressEvent(kind="stage_changed", checkpoint=checkpoint, reason="stage_change")
            state.last_notified_at = now
            state.last_stage = checkpoint.stage
            state.last_status = checkpoint.status
            return event, state

        due_at = (state.last_notified_at or self._parse_ts(checkpoint.updated_at) or now) + timedelta(seconds=self.policy.report_every_seconds)
        if checkpoint.status == "running" and now >= due_at:
            event = ProgressEvent(kind="progress_due", checkpoint=checkpoint, reason="timer")
            state.last_notified_at = now
            state.last_stage = checkpoint.stage
            state.last_status = checkpoint.status
            return event, state

        state.last_stage = checkpoint.stage
        state.last_status = checkpoint.status
        return None, state
