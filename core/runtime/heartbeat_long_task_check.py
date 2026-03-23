from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .long_task_registry import LongTaskRegistry


def _parse_iso(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def check_long_tasks(now: datetime | None = None, interval_minutes: int = 10) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    registry = LongTaskRegistry()
    results = []
    for task in registry.list_active():
        status = task.get("status")
        if status not in {"running", "failed", "interrupted", "completed"}:
            continue

        last_reported_at = _parse_iso(task.get("last_reported_at"))
        due = last_reported_at is None or now - last_reported_at >= timedelta(minutes=interval_minutes)
        terminal = status in {"failed", "interrupted", "completed"}
        if status == "running" and due:
            results.append({"kind": "progress_due", "task": task})
            registry.mark_reported(task["task_id"], now.isoformat())
        elif terminal:
            results.append({"kind": "terminal", "task": task})
            registry.archive_and_remove(task["task_id"])
    return results
