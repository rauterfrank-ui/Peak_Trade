"""
Execution events v0 (Phase 16A).

Stable schema for watch-only dashboards and CI-friendly deterministic tests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Literal, Optional

ExecutionEventTypeV0 = Literal[
    "created",
    "validated",
    "submitted",
    "acked",
    "filled",
    "canceled",
    "failed",
]


@dataclass(frozen=True)
class ExecutionEventV0:
    """
    Stable, versioned execution event.

    Required fields are intentionally flat and duplicated across all events to
    simplify downstream ingestion and UI queries.
    """

    schema: Literal["execution_event_v0"] = "execution_event_v0"
    ts: datetime = field(default_factory=datetime.utcnow)
    run_id: str = ""
    correlation_id: str = ""
    event_type: ExecutionEventTypeV0 = "created"
    order_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["ts"] = self.ts.isoformat()
        return d
