"""Contract: Max drawdown gate blocks when drawdown exceeds configured limit."""

from __future__ import annotations

from src.risk.limits import RiskLimits


def test_maxdd_gate_blocks_when_drawdown_exceeded() -> None:
    """
    Contract: If drawdown exceeds configured max, eligibility must fail.
    RiskLimits.check_drawdown returns True=OK, False=violated.
    """
    # [100, 80] = 20% drawdown; max_dd_pct=10 means 10% limit
    # 20% >= 10% -> violated -> False
    ok = RiskLimits.check_drawdown(equity_curve=[100, 80], max_dd_pct=10.0)
    assert not ok  # violated (numpy may return np.bool_)


def test_maxdd_gate_passes_when_under_limit() -> None:
    """When drawdown under limit, check returns True."""
    ok = RiskLimits.check_drawdown(equity_curve=[100, 95, 90], max_dd_pct=15.0)
    assert ok  # OK (numpy may return np.bool_)
