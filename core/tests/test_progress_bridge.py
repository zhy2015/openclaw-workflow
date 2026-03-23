from __future__ import annotations

import asyncio
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.runtime.progress import ProgressCheckpoint
from core.runtime.progress_bridge import ProgressBridge


class _Calls:
    alerts = []
    milestones = []


async def _fake_alert(workflow_id, node_id, message, data=None):
    _Calls.alerts.append((workflow_id, node_id, message, data))


async def _fake_milestone(workflow_id, node_id, message, data=None, tokens_consumed=0):
    _Calls.milestones.append((workflow_id, node_id, message, data, tokens_consumed))


def test_progress_bridge_emits_milestone_and_alert(monkeypatch):
    import core.runtime.progress_bridge as pb

    monkeypatch.setattr(pb, "notify_alert", _fake_alert)
    monkeypatch.setattr(pb, "notify_milestone", _fake_milestone)

    bridge = ProgressBridge()
    cp1 = ProgressCheckpoint(task_id="t1", request_id="t1", intent="demo", stage="story_plan_ready", status="running", progress_hint=0.1)
    cp2 = ProgressCheckpoint(task_id="t1", request_id="t1", intent="demo", stage="final_concat_running", status="failed", progress_hint=0.8, message="sigterm")

    payload1 = asyncio.run(bridge.emit_for_checkpoint(cp1))
    payload2 = asyncio.run(bridge.emit_for_checkpoint(cp2))

    assert payload1 is not None
    assert payload2 is not None
    assert len(_Calls.milestones) == 1
    assert len(_Calls.alerts) == 1
