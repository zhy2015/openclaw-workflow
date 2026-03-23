from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.runtime.long_task_registry import LongTaskRecord, LongTaskRegistry
from core.runtime.heartbeat_long_task_check import check_long_tasks


def test_long_task_registry_upsert_report_and_archive(tmp_path, monkeypatch):
    active = tmp_path / "active_long_tasks.json"
    archive = tmp_path / "archive"
    registry = LongTaskRegistry(active_path=active, archive_root=archive)
    registry.upsert(LongTaskRecord(
        task_id="t1",
        title="demo",
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        query_hint="cat progress.json",
        resume_hint="python workflow.py --resume project.json",
    ))
    assert len(registry.list_active()) == 1
    registry.mark_reported("t1")
    assert registry.list_active()[0]["last_reported_at"] is not None


def test_heartbeat_long_task_check_reports_and_archives(tmp_path, monkeypatch):
    active = tmp_path / "active_long_tasks.json"
    archive = tmp_path / "archive"
    registry = LongTaskRegistry(active_path=active, archive_root=archive)
    now = datetime.now(timezone.utc)
    registry.upsert(LongTaskRecord(
        task_id="t1",
        title="running task",
        status="running",
        created_at=(now - timedelta(minutes=20)).isoformat(),
        updated_at=(now - timedelta(minutes=20)).isoformat(),
        last_reported_at=(now - timedelta(minutes=11)).isoformat(),
    ))
    registry.upsert(LongTaskRecord(
        task_id="t2",
        title="done task",
        status="completed",
        created_at=(now - timedelta(minutes=20)).isoformat(),
        updated_at=now.isoformat(),
    ))

    import core.runtime.heartbeat_long_task_check as mod
    monkeypatch.setattr(mod, "LongTaskRegistry", lambda: LongTaskRegistry(active_path=active, archive_root=archive))
    results = check_long_tasks(now=now, interval_minutes=10)
    kinds = [item["kind"] for item in results]
    assert "progress_due" in kinds
    assert "terminal" in kinds
    archived = list((archive / now.strftime("%Y-%m-%d")).glob("task_t2.json"))
    assert len(archived) == 1
