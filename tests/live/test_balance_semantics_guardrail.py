"""
Tests for balance semantics guardrail classifier.

Aligns with docs/ops/reviews/balance_semantics_guardrail_runtime_contract/CONTRACT.md.
"""

from __future__ import annotations

import pytest

from src.live.balance_semantics_guardrail import (
    BalanceSemanticsResult,
    classify_balance_semantics,
)


def test_paper_broker_cash_returns_clear() -> None:
    """PaperBroker cash attribute is explicit and non-ambiguous -> clear."""
    result = classify_balance_semantics(
        balance=1000.0,
        source_metadata={"source_type": "paper_broker_cash"},
    )
    assert result.semantic_state == "balance_semantics_clear"
    assert result.reason_code == "BALANCE_PAPER_BROKER_EXPLICIT"
    assert result.decision_use_allowed is True
    assert "paper_broker" in result.operator_visible_state


def test_fetch_balance_free_explicit_returns_clear() -> None:
    """Explicit free in balance dict -> clear."""
    result = classify_balance_semantics(
        balance={"free": 500.0, "used": 100.0, "total": 600.0},
        source_metadata={"source_type": "fetch_balance"},
    )
    assert result.semantic_state == "balance_semantics_clear"
    assert result.reason_code == "BALANCE_FREE_EXPLICIT"
    assert result.decision_use_allowed is True


def test_fetch_balance_free_zero_returns_clear() -> None:
    """Explicit free=0 is still explicit semantics -> clear."""
    result = classify_balance_semantics(
        balance={"free": 0.0, "used": 100.0, "total": 100.0},
        source_metadata={"source_type": "fetch_balance"},
    )
    assert result.semantic_state == "balance_semantics_clear"
    assert result.decision_use_allowed is True


def test_fetch_balance_cash_fallback_only_returns_blocked() -> None:
    """Only cash, no free -> do not upgrade to free/usable -> blocked."""
    result = classify_balance_semantics(
        balance={"cash": 500.0, "used": 100.0},
        source_metadata={"source_type": "fetch_balance"},
    )
    assert result.semantic_state == "balance_semantics_blocked"
    assert result.reason_code == "BALANCE_CASH_FALLBACK_AMBIGUOUS"
    assert result.decision_use_allowed is False
    assert "blocked" in result.operator_visible_state


def test_fetch_balance_no_free_no_cash_returns_blocked() -> None:
    """No free or cash data -> blocked."""
    result = classify_balance_semantics(
        balance={"used": 100.0},
        source_metadata={"source_type": "fetch_balance"},
    )
    assert result.semantic_state == "balance_semantics_blocked"
    assert result.reason_code == "BALANCE_NO_DATA"
    assert result.decision_use_allowed is False


def test_fetch_balance_free_none_cash_present_returns_blocked() -> None:
    """Free is None, cash present -> would be fallback -> blocked."""
    result = classify_balance_semantics(
        balance={"free": None, "cash": 300.0},
        source_metadata={"source_type": "fetch_balance"},
    )
    assert result.semantic_state == "balance_semantics_blocked"
    assert result.reason_code == "BALANCE_CASH_FALLBACK_AMBIGUOUS"


def test_invalid_payload_none_returns_blocked() -> None:
    """None balance with fetch_balance source -> invalid payload -> blocked."""
    result = classify_balance_semantics(
        balance=None,
        source_metadata={"source_type": "fetch_balance"},
    )
    assert result.semantic_state == "balance_semantics_blocked"
    assert result.reason_code == "BALANCE_INVALID_PAYLOAD"
    assert result.decision_use_allowed is False


def test_invalid_payload_not_dict_returns_blocked() -> None:
    """Non-dict balance with fetch_balance source -> invalid payload -> blocked."""
    result = classify_balance_semantics(
        balance="invalid",
        source_metadata={"source_type": "fetch_balance"},
    )
    assert result.semantic_state == "balance_semantics_blocked"
    assert result.reason_code == "BALANCE_INVALID_PAYLOAD"


def test_default_source_type_is_fetch_balance() -> None:
    """When source_metadata omits source_type, default to fetch_balance."""
    result = classify_balance_semantics(
        balance={"cash": 100.0},
        source_metadata={},
    )
    assert result.semantic_state == "balance_semantics_blocked"
    assert result.reason_code == "BALANCE_CASH_FALLBACK_AMBIGUOUS"


def test_result_is_frozen() -> None:
    """BalanceSemanticsResult is immutable."""
    result = classify_balance_semantics(
        balance={"free": 1.0},
        source_metadata={"source_type": "fetch_balance"},
    )
    with pytest.raises(AttributeError):
        result.semantic_state = "balance_semantics_blocked"  # type: ignore[misc]
