from __future__ import annotations

from typing import Any, Callable, Awaitable

from core.infra.notification import NotificationEvent, get_notification_manager


class ProgressDeliveryBridge:
    """Attach concrete delivery handlers to the existing notification manager."""

    def __init__(self):
        self.manager = get_notification_manager()

    def register_handlers(
        self,
        *,
        alert_handler: Callable[[NotificationEvent], Any] | None = None,
        milestone_handler: Callable[[list[NotificationEvent]], Any] | None = None,
    ):
        if alert_handler is not None:
            self.manager.register_alert_handler(alert_handler)
        if milestone_handler is not None:
            self.manager.register_milestone_handler(milestone_handler)
