"""Tests for Finish C3 reconciler failure scenarios (mock-only, no I/O)."""

from __future__ import annotations

from src.execution.live.reconcile import (
    BrokerOrder,
    LocalOrder,
    ReconcileMismatch,
    cancel_race_mismatch,
    reconcile_orders,
)
from src.execution.live.safety import BoundedRetryTracker


def test_partial_fill_mismatch() -> None:
    local = [LocalOrder("o1", qty=1.0, filled_qty=0.5, status="open")]
    broker = [BrokerOrder("o1", qty=1.0, filled_qty=0.0, status="open")]
    r = reconcile_orders(local, broker)
    assert any(m.code == "partial_fill_mismatch" for m in r.mismatches)


def test_status_mismatch_includes_cancel_race_surface() -> None:
    local = [LocalOrder("o1", qty=1.0, filled_qty=0.0, status="cancelled")]
    broker = [BrokerOrder("o1", qty=1.0, filled_qty=0.0, status="open")]
    r = reconcile_orders(local, broker)
    assert any(m.code == "status_mismatch" for m in r.mismatches)
    cr = cancel_race_mismatch("cancelled", "open")
    assert cr is not None
    assert cr.code == "cancel_race"


def test_rate_limit_signal() -> None:
    r = reconcile_orders([], [], broker_signal="rate_limit")
    assert len(r.mismatches) == 1
    assert r.mismatches[0].code == "rate_limit"
    assert r.broker_signal == "rate_limit"
    assert any("backoff" in a for a in r.corrective_actions)


def test_timeout_transient_signals() -> None:
    for sig in ("timeout", "transient"):
        r = reconcile_orders([], [], broker_signal=sig)  # type: ignore[arg-type]
        assert r.mismatches[0].code == sig
        assert r.broker_signal == sig


def test_transient_with_bounded_retry_exhaustion() -> None:
    tracker = BoundedRetryTracker(max_attempts=2)
    r = reconcile_orders([], [], broker_signal="transient")
    assert r.broker_signal == "transient"
    tracker.record_attempt()
    assert not tracker.should_stop()
    tracker.record_attempt()
    assert tracker.should_stop()


def test_missing_on_broker() -> None:
    local = [LocalOrder("ghost", 1.0, 0.0, "open")]
    broker: list[BrokerOrder] = []
    r = reconcile_orders(local, broker)
    assert any(m.code == "missing_on_broker" for m in r.mismatches)


def test_ghost_broker_order() -> None:
    local: list[LocalOrder] = []
    broker = [BrokerOrder("extra", 1.0, 0.0, "open")]
    r = reconcile_orders(local, broker)
    assert any(m.code == "ghost_broker_order" for m in r.mismatches)


def test_duplicate_fill_events_idempotency() -> None:
    from src.execution.live.safety import fill_id_is_duplicate

    seen: set[str] = set()
    assert not fill_id_is_duplicate(seen, "fill-1")
    assert fill_id_is_duplicate(seen, "fill-1")


def test_aligned_no_mismatches() -> None:
    local = [LocalOrder("o1", 1.0, 1.0, "filled")]
    broker = [BrokerOrder("o1", 1.0, 1.0, "filled")]
    r = reconcile_orders(local, broker)
    assert r.mismatches == ()


def test_reconcile_mismatch_dataclass() -> None:
    m = ReconcileMismatch("x", "code", "msg")
    assert m.order_id == "x"
