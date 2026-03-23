from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_iso(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def format_long_task_alerts(items: list[dict[str, Any]], now: datetime | None = None) -> str | None:
    if not items:
        return None
    now = now or datetime.now(timezone.utc)
    lines: list[str] = []
    for item in items:
        kind = item.get("kind")
        task = item.get("task") or {}
        title = task.get("title") or task.get("task_id") or "long-task"
        status = task.get("status") or "unknown"
        created_at = _parse_iso(task.get("created_at"))
        age_min = None
        if created_at:
            age_min = int((now - created_at).total_seconds() // 60)
        query_hint = task.get("query_hint")
        resume_hint = task.get("resume_hint")
        stage = ((task.get("meta") or {}).get("stage"))

        if kind == "progress_due":
            line = f"⏱️ 长任务仍在运行：{title}"
            if age_min is not None:
                line += f"，已运行约 {age_min} 分钟"
            if stage:
                line += f"，当前阶段 {stage}"
            if query_hint:
                line += f"。查询：{query_hint}"
            lines.append(line)
        elif kind == "terminal":
            line = f"📌 长任务已结束：{title}，状态 {status}"
            if stage:
                line += f"，结束阶段 {stage}"
            if status in {"failed", "interrupted"} and resume_hint:
                line += f"。恢复：{resume_hint}"
            lines.append(line)

    return "\n".join(lines) if lines else None
