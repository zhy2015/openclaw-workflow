from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional
import uuid


@dataclass(frozen=True)
class TaskEnvelope:
    task_type: str
    intent: str
    params: dict[str, Any] = field(default_factory=dict)
    caller: str = "system"
    source: str = "unknown"
    requires_side_effects: bool = False
    references_memory: bool = False
    complexity_hint: Optional[str] = None
    target_skill: Optional[str] = None
    target_tool: Optional[str] = None
    workflow_nodes: list[dict[str, Any]] = field(default_factory=list)
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:10]}")
    progress_policy: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteDecision:
    mode: Literal["fast", "slow"]
    reason: str
    requires_memory: bool = False
    requires_wal: bool = False
    requires_sandbox: bool = False
    target_skill: Optional[str] = None
    target_tool: Optional[str] = None
