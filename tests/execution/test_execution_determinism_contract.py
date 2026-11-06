from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from src.execution.orchestrator import ExecutionMode, ExecutionOrchestrator, OrderIntent
from src.execution.contracts import OrderSide
from src.execution.venue_adapters.simulated import SimulatedVenueAdapter


def _read_jsonl(path: Path) -> list[dict]:
    lines = []
    if not path.exists():
        return lines
    for raw in path.read_text().splitlines():
        if raw.strip():
            lines.append(json.loads(raw))
    return lines


def _normalize_events(events: list[dict]) -> list[dict]:
    # Contract: ts_utc is allowed to vary; tests must ignore it.
    out = []
    for e in events:
        e2 = dict(e)
        e2.pop("ts_utc", None)
        out.append(e2)
    return out


def test_execution_events_jsonl_deterministic_across_runs(tmp_path: Path):
    log_a = tmp_path / "a.jsonl"
    log_b = tmp_path / "b.jsonl"

    intent = OrderIntent(
        run_id="run_001",
        session_id="sess_001",
        intent_id="intent_001",
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.010"),
    )

    orch_a = ExecutionOrchestrator(
        adapter=SimulatedVenueAdapter(),
        execution_mode=ExecutionMode.PAPER,
        execution_events_log_path=str(log_a),
    )
    orch_b = ExecutionOrchestrator(
        adapter=SimulatedVenueAdapter(),
        execution_mode=ExecutionMode.PAPER,
        execution_events_log_path=str(log_b),
    )

    res_a = orch_a.submit_intent(intent)
    res_b = orch_b.submit_intent(intent)

    assert res_a.success is True
    assert res_b.success is True
    assert res_a.order is not None
    assert res_b.order is not None

    # Order ID must be deterministic (no uuid)
    assert res_a.order.client_order_id == res_b.order.client_order_id

    events_a = _normalize_events(_read_jsonl(log_a))
    events_b = _normalize_events(_read_jsonl(log_b))

    assert events_a == events_b

    # Ordering key contract (must already be in order)
    sorted_events = sorted(
        events_a,
        key=lambda e: (
            e.get("run_id"),
            e.get("session_id"),
            e.get("ts_sim"),
            e.get("event_type"),
            e.get("event_id"),
        ),
    )
    assert events_a == sorted_events
