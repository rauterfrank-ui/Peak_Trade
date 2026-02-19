"""Contract: Live gate evaluation emits structured result with is_eligible and reasons."""

from __future__ import annotations

from src.live.live_gates import (
    LiveGateResult,
    check_data_quality_gate,
    check_strategy_live_eligibility,
)


def test_gating_result_contains_reasonable_fields() -> None:
    """
    Contract: live gate evaluation emits a structured result including:
    - is_eligible (bool)
    - reasons (list[str]) or a reason string
    """
    # Use check_data_quality_gate as canonical gate (takes asof_utc, context)
    res = check_data_quality_gate(
        asof_utc="2026-02-19T00:00:00Z",
        context={"enabled": False, "armed": False},
    )
    assert isinstance(res, LiveGateResult)
    assert hasattr(res, "is_eligible")
    assert isinstance(res.is_eligible, bool)
    assert hasattr(res, "reasons")
    assert isinstance(res.reasons, list)


def test_strategy_eligibility_returns_live_gate_result() -> None:
    """check_strategy_live_eligibility returns LiveGateResult with is_eligible, reasons."""
    res = check_strategy_live_eligibility("rsi_reversion")
    assert isinstance(res, LiveGateResult)
    assert hasattr(res, "is_eligible")
    assert isinstance(res.is_eligible, bool)
    assert hasattr(res, "reasons")
    assert isinstance(res.reasons, list)
