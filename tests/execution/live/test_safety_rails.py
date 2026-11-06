"""Tests for Finish C3 safety rails (mock-only)."""

from __future__ import annotations

import pytest

from src.execution.live.safety import (
    BoundedRetryTracker,
    LIVE_ENABLED_FORBIDDEN_DEFAULT,
    SafetyViolation,
    assert_live_stays_disabled,
    assert_non_negative_balance,
    assert_non_negative_qty,
    fill_id_is_duplicate,
    fill_id_would_duplicate,
    order_invariant_issues_for_reconcile,
)


def test_live_enabled_forbidden_default_constant() -> None:
    assert LIVE_ENABLED_FORBIDDEN_DEFAULT is False


def test_assert_live_stays_disabled_rejects_true() -> None:
    assert_live_stays_disabled(False)
    with pytest.raises(SafetyViolation, match="live_enabled_must_be_false"):
        assert_live_stays_disabled(True)


def test_non_negative_qty() -> None:
    assert_non_negative_qty(0.0)
    assert_non_negative_qty(1.5)
    with pytest.raises(SafetyViolation, match="negative_qty"):
        assert_non_negative_qty(-0.01)


def test_non_negative_balance() -> None:
    assert_non_negative_balance(0.0)
    with pytest.raises(SafetyViolation, match="negative_balance"):
        assert_non_negative_balance(-1.0)


def test_duplicate_fill_idempotency() -> None:
    seen: set[str] = set()
    assert fill_id_is_duplicate(seen, "a") is False
    assert fill_id_is_duplicate(seen, "a") is True
    assert "a" in seen


def test_fill_id_would_duplicate_pure() -> None:
    seen = {"x"}
    assert fill_id_would_duplicate(seen, "x") is True
    assert fill_id_would_duplicate(seen, "y") is False


def test_bounded_retry_tracker_stops() -> None:
    t = BoundedRetryTracker(max_attempts=3)
    assert not t.should_stop()
    t.record_attempt()
    assert not t.should_stop()
    t.record_attempt()
    assert not t.should_stop()
    t.record_attempt()
    assert t.should_stop()
    assert t.attempts == 3


def test_bounded_retry_max_one() -> None:
    t = BoundedRetryTracker(max_attempts=1)
    t.record_attempt()
    assert t.should_stop()


def test_order_invariant_issues_empty_when_ok() -> None:
    assert order_invariant_issues_for_reconcile("o1", 1.0, 0.5) == []


def test_order_invariant_negative_qty() -> None:
    inv = order_invariant_issues_for_reconcile("o1", -1.0, 0.0)
    assert len(inv) == 1
    assert inv[0][0] == "invariant_negative_qty"


def test_order_invariant_filled_exceeds_qty() -> None:
    inv = order_invariant_issues_for_reconcile("o1", 1.0, 1.5)
    assert len(inv) == 1
    assert inv[0][0] == "invariant_filled_exceeds_qty"


def test_order_invariant_non_finite_qty() -> None:
    inv = order_invariant_issues_for_reconcile("o1", float("inf"), 0.0)
    assert len(inv) == 1
    assert inv[0][0] == "invariant_non_finite_qty"
