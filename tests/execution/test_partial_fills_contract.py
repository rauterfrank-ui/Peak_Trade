"""Contract tests for partial fill schema support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PartialFillEvent:
    """Minimal schema for a partial fill event (contract)."""

    fill_id: str
    order_id: str
    qty: float
    remaining_qty: float
    fill_price: float
    side: str


def test_partial_fill_schema_has_required_fields() -> None:
    """Partial fill events must support fill_id, remaining_qty."""
    ev = PartialFillEvent(
        fill_id="fill-001",
        order_id="ord-001",
        qty=0.5,
        remaining_qty=0.5,
        fill_price=50000.0,
        side="BUY",
    )
    assert ev.fill_id == "fill-001"
    assert ev.remaining_qty == 0.5
    assert ev.qty == 0.5


def test_partial_fill_list_representation() -> None:
    """Order with multiple partial fills: list of fills with remaining_qty."""
    fills = [
        {"fill_id": "f1", "qty": 0.3, "remaining_qty": 0.7, "fill_price": 50000.0},
        {"fill_id": "f2", "qty": 0.4, "remaining_qty": 0.3, "fill_price": 50010.0},
        {"fill_id": "f3", "qty": 0.3, "remaining_qty": 0.0, "fill_price": 50005.0},
    ]
    for f in fills:
        assert "fill_id" in f
        assert "remaining_qty" in f
        assert "qty" in f
    assert fills[-1]["remaining_qty"] == 0.0


def test_execution_event_kind_fill_supports_payload() -> None:
    """ExecutionEvent kind 'fill' payload can carry fill_id, remaining_qty."""
    from src.execution.events import ExecutionEvent, EventKind
    from datetime import datetime

    payload: dict[str, Any] = {
        "fill_id": "fill-001",
        "remaining_qty": 0.5,
        "order_id": "ord-1",
        "qty": 0.5,
        "fill_price": 50000.0,
    }
    ev = ExecutionEvent(
        ts=datetime.utcnow(),
        session_id="s1",
        symbol="BTC-USD",
        mode="paper",
        kind="fill",
        payload=payload,
    )
    assert ev.kind == "fill"
    assert ev.payload.get("fill_id") == "fill-001"
    assert ev.payload.get("remaining_qty") == 0.5
