from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.infra.notification import NotificationEvent, NotificationLevel
from core.runtime.session_progress_adapter import SessionDeliveryContext, SessionProgressAdapter


def test_session_progress_adapter_formats_and_delivers_messages():
    sent = []

    def sender(text: str):
        sent.append(text)

    adapter = SessionProgressAdapter(sender, SessionDeliveryContext(channel="feishu", target="user:demo"))
    adapter.attach()

    alert = NotificationEvent(level=NotificationLevel.ALERT, workflow_id="wf", node_id="n1", message="任务进度：failed | 80%")
    milestone = NotificationEvent(level=NotificationLevel.MILESTONE, workflow_id="wf", node_id="n2", message="任务进度：running | 40%")

    adapter.bridge.manager._dispatch_alert(alert)
    adapter.bridge.manager._dispatch_milestones([milestone])

    assert any(text.startswith("[progress-alert]") for text in sent)
    assert any(text.startswith("[progress]") for text in sent)
