from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .progress import ProgressCheckpoint


@dataclass
class ProgressEvent:
    kind: str
    checkpoint: ProgressCheckpoint
    reason: str


class ProgressNotifier:
    """Formats user-visible progress notifications. Delivery bridge is intentionally separate."""

    def format_text(self, event: ProgressEvent) -> str:
        cp = event.checkpoint
        pct = int((cp.progress_hint or 0.0) * 100)
        base = f"任务进度：{cp.stage} | {cp.status} | {pct}%"
        if cp.message:
            base += f" | {cp.message}"
        return base

    def build_payload(self, event: ProgressEvent) -> dict[str, Any]:
        return {
            "kind": event.kind,
            "reason": event.reason,
            "task_id": event.checkpoint.task_id,
            "text": self.format_text(event),
            "stage": event.checkpoint.stage,
            "status": event.checkpoint.status,
            "progress_hint": event.checkpoint.progress_hint,
            "meta": event.checkpoint.meta,
        }
