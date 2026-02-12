"""Tests for P31 metrics v1."""

from __future__ import annotations

import math
import pytest

from src.backtest.p31.metrics_v1 import compute_returns, max_drawdown, sharpe, summary_kpis


def test_compute_returns_empty_or_short():
    assert compute_returns([]) == []
    assert compute_returns([100.0]) == []


def test_compute_returns_simple():
    eq = [100.0, 110.0, 99.0]
    rets = compute_returns(eq)
    assert len(rets) == 2
    assert math.isclose(rets[0], 0.10, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(rets[1], 99.0 / 110.0 - 1.0, rel_tol=1e-12, abs_tol=1e-12)


def test_compute_returns_rejects_non_positive_prev():
    with pytest.raises(ValueError):
        compute_returns([0.0, 1.0])
    with pytest.raises(ValueError):
        compute_returns([100.0, 0.0, 1.0])  # prev becomes 0


def test_max_drawdown_monotonic_up_is_zero():
    assert math.isclose(max_drawdown([100.0, 101.0, 200.0]), 0.0, rel_tol=0.0, abs_tol=0.0)


def test_max_drawdown_peak_to_trough():
    eq = [100.0, 120.0, 90.0, 110.0]
    # peak=120 -> trough=90 => dd=1-90/120=0.25
    assert math.isclose(max_drawdown(eq), 0.25, rel_tol=1e-12, abs_tol=1e-12)


def test_sharpe_zero_for_insufficient_or_zero_var():
    assert sharpe([]) == 0.0
    assert sharpe([0.01]) == 0.0
    assert sharpe([0.01, 0.01, 0.01]) == 0.0


def test_sharpe_positive_for_positive_excess_mean():
    r = [0.01, 0.02, -0.005, 0.015]
    s = sharpe(r, risk_free=0.0)
    assert s != 0.0
    assert math.isfinite(s)


def test_summary_kpis_smoke():
    eq = [100.0, 110.0, 105.0]
    k = summary_kpis(eq)
    assert set(k.keys()) == {"total_return", "max_drawdown", "sharpe", "n_steps"}
    assert math.isclose(k["total_return"], 105.0 / 100.0 - 1.0, rel_tol=1e-12, abs_tol=1e-12)
    assert k["n_steps"] == 3.0
