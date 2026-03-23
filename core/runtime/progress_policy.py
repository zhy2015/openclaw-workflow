from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressPolicy:
    report_every_seconds: int = 600
    notify_on_stage_change: bool = True
    notify_on_failure: bool = True
    notify_on_interrupt: bool = True
    long_task_threshold_seconds: int = 60


def policy_from_dict(data: dict | None) -> ProgressPolicy:
    data = data or {}
    return ProgressPolicy(
        report_every_seconds=int(data.get("report_every_seconds", 600)),
        notify_on_stage_change=bool(data.get("notify_on_stage_change", True)),
        notify_on_failure=bool(data.get("notify_on_failure", True)),
        notify_on_interrupt=bool(data.get("notify_on_interrupt", True)),
        long_task_threshold_seconds=int(data.get("long_task_threshold_seconds", 60)),
    )
