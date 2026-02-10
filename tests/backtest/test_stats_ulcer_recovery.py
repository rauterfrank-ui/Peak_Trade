"""
Unit tests for Ulcer Index and Recovery Factor (Block G — Additional Metrics).

Tests on small synthetic equity curves; ensures metrics appear in compute_backtest_stats.
"""

import pandas as pd
import pytest

from src.backtest.stats import (
    compute_ulcer_index,
    compute_recovery_factor,
    compute_backtest_stats,
)


def test_ulcer_index_no_drawdown():
    """Monoton steigende Equity -> Ulcer Index 0."""
    equity = pd.Series([100.0, 101.0, 102.0, 103.0])
    assert compute_ulcer_index(equity) == 0.0


def test_ulcer_index_single_drawdown():
    """Ein Drawdown von 10% -> Ulcer Index = RMS der Drawdowns."""
    # 100 -> 100 -> 90 -> 100: ein Punkt mit dd=-0.1, Rest 0 -> RMS = sqrt(0.01/4) = 0.05
    equity = pd.Series([100.0, 100.0, 90.0, 100.0])
    ui = compute_ulcer_index(equity)
    assert ui >= 0
    assert ui <= 0.2
    assert abs(ui - 0.05) < 0.01


def test_ulcer_index_empty_or_single():
    """Kurze Series -> 0."""
    assert compute_ulcer_index(pd.Series([100.0])) == 0.0
    assert compute_ulcer_index(pd.Series(dtype=float)) == 0.0


def test_recovery_factor_no_drawdown():
    """Kein Drawdown -> Recovery Factor 0 (keine Division durch null)."""
    equity = pd.Series([100.0, 101.0, 102.0])
    assert compute_recovery_factor(equity) == 0.0


def test_recovery_factor_positive_return_and_drawdown():
    """Return 10%, MaxDD -10% -> Recovery Factor 1.0."""
    # 100 -> 90 -> 110: total_return = 0.1, max_dd = -0.1
    equity = pd.Series([100.0, 90.0, 110.0])
    rf = compute_recovery_factor(equity)
    assert rf == pytest.approx(1.0, rel=1e-5)


def test_recovery_factor_large_return_small_dd():
    """Return 20%, MaxDD -5% -> Recovery Factor 4.0."""
    equity = pd.Series([100.0, 95.0, 120.0])
    rf = compute_recovery_factor(equity)
    assert rf == pytest.approx(4.0, rel=1e-5)


def test_recovery_factor_empty_or_single():
    """Kurze Series -> 0."""
    assert compute_recovery_factor(pd.Series([100.0])) == 0.0


def test_compute_backtest_stats_includes_ulcer_and_recovery():
    """compute_backtest_stats enthält ulcer_index und recovery_factor."""
    equity = pd.Series([100.0, 98.0, 102.0, 99.0, 105.0])
    trades = [{"pnl": 2.0}, {"pnl": -1.0}, {"pnl": 3.0}]
    stats = compute_backtest_stats(trades, equity)
    assert "ulcer_index" in stats
    assert "recovery_factor" in stats
    assert stats["ulcer_index"] >= 0
    assert stats["recovery_factor"] >= 0
