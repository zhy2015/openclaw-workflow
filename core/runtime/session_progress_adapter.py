from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from core.infra.notification import NotificationEvent
from core.runtime.progress_delivery import ProgressDeliveryBridge


@dataclass
class SessionDeliveryContext:
    channel: str
    target: str | None = None
    thread_id: str | None = None
    account_id: str | None = None


class SessionProgressAdapter:
    """Bind notification events to a concrete session sender supplied by the runtime edge."""

    def __init__(self, sender: Callable[[str], None], context: SessionDeliveryContext):
        self.sender = sender
        self.context = context
        self.bridge = ProgressDeliveryBridge()

    def attach(self):
        def on_alert(event: NotificationEvent):
            self.sender(self._format_alert(event))

        def on_milestones(events: list[NotificationEvent]):
            for event in events:
                self.sender(self._format_milestone(event))

        self.bridge.register_handlers(alert_handler=on_alert, milestone_handler=on_milestones)

    def _format_alert(self, event: NotificationEvent) -> str:
        return f"[progress-alert] {event.message}"

    def _format_milestone(self, event: NotificationEvent) -> str:
        return f"[progress] {event.message}"
