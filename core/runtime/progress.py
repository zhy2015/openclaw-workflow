from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class ProgressCheckpoint:
    task_id: str
    intent: str
    stage: str
    status: str
    progress_hint: float = 0.0
    message: str | None = None
    workflow_id: str | None = None
    request_id: str | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    meta: dict[str, Any] = field(default_factory=dict)


class ProgressTracker:
    def __init__(self, root: str = "/root/.openclaw/workspace/logs/progress"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        return self.root / f"{task_id}.json"

    def save(self, checkpoint: ProgressCheckpoint) -> Path:
        checkpoint.updated_at = datetime.now(timezone.utc).isoformat()
        path = self._path(checkpoint.task_id)
        path.write_text(json.dumps(asdict(checkpoint), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load(self, task_id: str) -> Optional[ProgressCheckpoint]:
        path = self._path(task_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProgressCheckpoint(**data)
