from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.runtime.heartbeat_long_task_report import format_long_task_alerts


def test_format_long_task_alerts_for_running_and_terminal():
    now = datetime.now(timezone.utc)
    text = format_long_task_alerts([
        {
            "kind": "progress_due",
            "task": {
                "title": "story-video::demo",
                "status": "running",
                "created_at": (now - timedelta(minutes=18)).isoformat(),
                "query_hint": "cat manifest.json",
                "meta": {"stage": "asset_generation_running"},
            },
        },
        {
            "kind": "terminal",
            "task": {
                "title": "story-video::demo2",
                "status": "interrupted",
                "created_at": (now - timedelta(minutes=25)).isoformat(),
                "resume_hint": "python workflow.py --resume project.json",
                "meta": {"stage": "scene_compose_running"},
            },
        },
    ], now=now)
    assert "长任务仍在运行" in text
    assert "asset_generation_running" in text
    assert "长任务已结束" in text
    assert "恢复：python workflow.py --resume project.json" in text
