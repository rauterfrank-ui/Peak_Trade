from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from src.execution.contracts import OrderSide
from src.execution.ledger import LegacyLedgerEngine as LedgerEngine
from src.execution.orchestrator import ExecutionMode, ExecutionOrchestrator, OrderIntent
from src.execution.venue_adapters.simulated import SimulatedVenueAdapter


def _normalize_beta_events(events: list[dict]) -> list[dict]:
    # Slice-1 contract: ts_utc may vary; Slice-2 must ignore it.
    out: list[dict] = []
    for e in events:
        e2 = dict(e)
        e2.pop("ts_utc", None)
        out.append(e2)
    return out


def test_pipeline_beta_events_feed_ledger_engine(tmp_path: Path):
    log_path = tmp_path / "execution_events.jsonl"

    intent = OrderIntent(
        run_id="run_ledger_001",
        session_id="sess_ledger_001",
        intent_id="intent_ledger_001",
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01000000"),
    )

    orch = ExecutionOrchestrator(
        adapter=SimulatedVenueAdapter(market_prices={"BTC/EUR": Decimal("50000.00")}),
        execution_mode=ExecutionMode.PAPER,
        execution_events_log_path=str(log_path),
    )

    res = orch.submit_intent(intent)
    assert res.success is True

    # Use in-memory beta_events from orchestrator (most direct integration point).
    beta_events = _normalize_beta_events(res.metadata.get("beta_events", []))
    assert any(e.get("event_type") == "FILL" for e in beta_events)

    # Feed events to ledger engine
    eng = LedgerEngine(quote_currency="EUR")
    for e in sorted(
        beta_events,
        key=lambda ev: (
            ev.get("run_id"),
            ev.get("session_id"),
            ev.get("ts_sim"),
            ev.get("event_type"),
            ev.get("event_id"),
        ),
    ):
        eng.apply(e)

    # Position quantity should match orchestrator's position ledger (WAC, long-only here)
    pos_orch = orch.position_ledger.get_position("BTC/EUR")
    assert pos_orch is not None
    pos_led = eng.state.positions.get("BTC/EUR")
    assert pos_led is not None
    assert pos_led.quantity == pos_orch.quantity
    assert pos_led.avg_cost == pos_orch.avg_entry_price

    # Deterministic snapshot export (no mark prices needed for this assertion)
    snap_a = eng.export_snapshot_json(ts_sim=max(e["ts_sim"] for e in beta_events))
    snap_b = eng.export_snapshot_json(ts_sim=max(e["ts_sim"] for e in beta_events))
    assert snap_a == snap_b
