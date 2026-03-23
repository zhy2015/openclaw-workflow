from __future__ import annotations

import asyncio
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.infra.notification import NotificationEvent, NotificationLevel, get_notification_manager
from core.runtime.progress_delivery import ProgressDeliveryBridge


def test_progress_delivery_bridge_registers_handlers():
    bridge = ProgressDeliveryBridge()
    manager = get_notification_manager()
    seen = {"alert": 0, "milestone": 0}

    def on_alert(event):
        seen["alert"] += 1

    def on_milestones(events):
        seen["milestone"] += len(events)

    bridge.register_handlers(alert_handler=on_alert, milestone_handler=on_milestones)

    manager._dispatch_alert(NotificationEvent(level=NotificationLevel.ALERT, workflow_id="wf", node_id="n1", message="boom"))
    manager._dispatch_milestones([NotificationEvent(level=NotificationLevel.MILESTONE, workflow_id="wf", node_id="n2", message="ok")])

    assert seen["alert"] >= 1
    assert seen["milestone"] >= 1
