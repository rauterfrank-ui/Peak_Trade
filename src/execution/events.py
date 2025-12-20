# src/execution/events.py
"""
Execution Event Schema for Telemetry & Live-Track Bridge.

Phase 16B: Execution Pipeline emits structured events for observability,
monitoring, and live-track integration.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Literal


EventKind = Literal["gate", "intent", "order", "fill", "error"]


@dataclass
class ExecutionEvent:
    """
    Structured execution event for telemetry.

    Emitted by ExecutionPipeline at key decision points:
    - After each gate decision
    - When intent created
    - When order created
    - When fill returned (simulated or real)
    - On errors

    Attributes:
        ts: Event timestamp
        session_id: Session/run identifier
        symbol: Trading symbol (e.g., "BTC-USD")
        mode: Execution mode (paper/backtest/live)
        kind: Event type (gate/intent/order/fill/error)
        payload: Event-specific data
    """

    ts: datetime
    session_id: str
    symbol: str
    mode: str
    kind: EventKind
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for JSON serialization.

        Returns:
            Dictionary with ts as ISO string
        """
        d = asdict(self)
        d["ts"] = self.ts.isoformat()
        return d


def event_to_dict(event: ExecutionEvent) -> Dict[str, Any]:
    """
    Helper: Convert ExecutionEvent to dict for JSON serialization.

    Args:
        event: ExecutionEvent to convert

    Returns:
        Dictionary with ts as ISO string
    """
    return event.to_dict()
