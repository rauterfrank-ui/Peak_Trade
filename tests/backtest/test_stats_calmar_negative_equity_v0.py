"""Regression tests for compute_calmar_ratio catastrophic negative-equity guard.

Covers the dual-leg spread v1 offline re-evaluation blocker where total_return <= -1.0
produced a complex annual_return and raised TypeError during stats materialization.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from src.backtest.stats import (
    _CALMAR_CATASTROPHIC_NEGATIVE_RETURN_SENTINEL,
    compute_backtest_stats,
    compute_calmar_ratio,
)


def test_compute_calmar_ratio_dual_leg_spread_reeval_blocked_negative_equity_returns_finite_float():
    """Blocked re-eval class: negative ending equity must not raise and must stay finite."""
    # Mirrors blocked eval: 10000 -> -1468 (~-114.7% total return) with drawdown.
    equity = pd.Series(
        [10000.0, 9500.0, 8000.0, 5000.0, 1000.0, -500.0, -1468.17],
        index=pd.date_range("2024-05-01", periods=7, freq="h", tz="UTC"),
    )

    calmar = compute_calmar_ratio(equity, periods_per_year=8760)

    assert isinstance(calmar, float)
    assert math.isfinite(calmar)
    assert calmar <= 0.0
    assert calmar == _CALMAR_CATASTROPHIC_NEGATIVE_RETURN_SENTINEL


def test_compute_calmar_ratio_total_return_exactly_minus_one_returns_finite_negative_sentinel():
    equity = pd.Series(
        [100.0, 0.0, -10.0], index=pd.date_range("2024-05-01", periods=3, freq="h", tz="UTC")
    )

    calmar = compute_calmar_ratio(equity, periods_per_year=8760)

    assert math.isfinite(calmar)
    assert calmar == _CALMAR_CATASTROPHIC_NEGATIVE_RETURN_SENTINEL


def test_compute_calmar_ratio_positive_return_unchanged():
    equity = pd.Series([100.0, 110.0, 105.0, 120.0])

    calmar = compute_calmar_ratio(equity, periods_per_year=252)

    assert calmar == pytest.approx(98547872.25414029, rel=1e-9)


def test_compute_calmar_ratio_zero_drawdown_returns_zero():
    equity = pd.Series([100.0, 101.0, 102.0, 103.0])

    assert compute_calmar_ratio(equity, periods_per_year=252) == 0.0


def test_compute_calmar_ratio_zero_years_returns_zero():
    equity = pd.Series([100.0])

    assert compute_calmar_ratio(equity, periods_per_year=252) == 0.0


def test_compute_backtest_stats_negative_equity_no_type_error():
    equity = pd.Series(
        [10000.0, 5000.0, -1000.0, -1468.17],
        index=pd.date_range("2024-05-01", periods=4, freq="h", tz="UTC"),
    )
    trades = [{"pnl": -500.0}, {"pnl": -300.0}]

    stats = compute_backtest_stats(trades, equity, periods_per_year=8760)

    assert "calmar" in stats
    assert isinstance(stats["calmar"], float)
    assert math.isfinite(stats["calmar"])
    assert stats["calmar"] <= 0.0
