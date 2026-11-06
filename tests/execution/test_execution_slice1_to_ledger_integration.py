from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from src.execution.contracts import OrderSide
from src.execution.ledger import LegacyLedgerEngine as LedgerEngine, iter_beta_exec_v1_events
from src.execution.orchestrator import ExecutionMode, ExecutionOrchestrator, OrderIntent
from src.execution.venue_adapters.simulated import SimulatedVenueAdapter


def test_slice1_beta_events_to_slice2_ledger_snapshot(tmp_path: Path):
    log_path = tmp_path / "execution_events.jsonl"

    intent = OrderIntent(
        run_id="run_slice2_001",
        session_id="sess_slice2_001",
        intent_id="intent_slice2_001",
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

    beta_events = iter_beta_exec_v1_events(res.metadata.get("beta_events", []))
    assert any(e.get("event_type") == "FILL" for e in beta_events)

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

    # Position quantity matches Slice-1 PositionLedger (same WAC semantics for this simple long case).
    pos_orch = orch.position_ledger.get_position("BTC/EUR")
    assert pos_orch is not None
    pos_led = eng.state.positions.get("BTC/EUR")
    assert pos_led is not None
    assert pos_led.quantity == pos_orch.quantity
    assert pos_led.avg_cost == pos_orch.avg_entry_price

    # Snapshot export is stable.
    ts_sim = max(e["ts_sim"] for e in beta_events)
    a = eng.export_snapshot_json(ts_sim=ts_sim)
    b = eng.export_snapshot_json(ts_sim=ts_sim)
    assert a == b
