from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.runtime.progress import ProgressCheckpoint
from core.runtime.progress_policy import ProgressPolicy
from core.runtime.progress_watcher import ProgressWatcher, WatcherState
from core.runtime.progress_notifier import ProgressNotifier


def test_progress_watcher_emits_stage_change_event():
    watcher = ProgressWatcher(ProgressPolicy(report_every_seconds=600))
    cp = ProgressCheckpoint(task_id="t1", request_id="t1", intent="demo", stage="story_plan_ready", status="running", progress_hint=0.1)
    event, state = watcher.evaluate(cp, WatcherState())
    assert event is not None
    assert event.kind == "stage_changed"
    assert state.last_stage == "story_plan_ready"


def test_progress_watcher_emits_periodic_progress_due():
    watcher = ProgressWatcher(ProgressPolicy(report_every_seconds=600, notify_on_stage_change=False))
    now = datetime.now(timezone.utc)
    cp = ProgressCheckpoint(task_id="t1", request_id="t1", intent="demo", stage="asset_generation_running", status="running", progress_hint=0.4)
    state = WatcherState(last_notified_at=now - timedelta(seconds=601), last_stage="asset_generation_running", last_status="running")
    event, _ = watcher.evaluate(cp, state, now=now)
    assert event is not None
    assert event.kind == "progress_due"


def test_progress_watcher_emits_failure_event_and_notifier_formats_text():
    watcher = ProgressWatcher(ProgressPolicy())
    notifier = ProgressNotifier()
    cp = ProgressCheckpoint(task_id="t1", request_id="t1", intent="demo", stage="final_concat_running", status="failed", progress_hint=0.8, message="sigterm")
    event, _ = watcher.evaluate(cp, WatcherState())
    assert event is not None
    assert event.kind == "task_failed"
    text = notifier.format_text(event)
    assert "final_concat_running" in text
    assert "failed" in text
    assert "sigterm" in text
