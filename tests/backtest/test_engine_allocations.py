from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
import pytest


def _equity_from_returns(
    index: pd.DatetimeIndex, initial: float, returns: list[float]
) -> pd.Series:
    if len(returns) != len(index) - 1:
        raise ValueError("returns length must be len(index)-1")
    equity = [float(initial)]
    for r in returns:
        equity.append(equity[-1] * (1.0 + float(r)))
    return pd.Series(equity, index=index, dtype=float)


def test_weights_inverse_vol_sum_to_one_and_deterministic() -> None:
    import src.backtest.engine as eng

    idx = pd.date_range("2024-01-01", periods=201, freq="1h")
    # s1: higher vol returns
    r1 = pd.Series(([0.01, -0.01] * 100) + [0.01], index=idx, dtype=float)
    # s2: lower vol returns
    r2 = pd.Series(([0.002, -0.002] * 100) + [0.002], index=idx, dtype=float)

    returns_map: Dict[str, pd.Series] = {"s1": r1, "s2": r2}
    w = eng._weights_inverse_vol(returns_map)

    assert set(w.keys()) == {"s1", "s2"}
    assert all(np.isfinite(list(w.values())))
    assert all(v >= 0 for v in w.values())
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert w == eng._weights_inverse_vol(returns_map)  # deterministic
    assert w["s2"] > w["s1"]  # lower vol => higher weight


def test_weights_sharpe_long_only_clips_negative_and_renorms() -> None:
    import src.backtest.engine as eng

    idx = pd.date_range("2024-01-01", periods=200, freq="1h")
    # s1 positive mean, s2 negative mean
    r1 = pd.Series(np.full(len(idx), 0.001), index=idx, dtype=float)
    r2 = pd.Series(np.full(len(idx), -0.001), index=idx, dtype=float)
    returns_map = {"s1": r1, "s2": r2}

    w = eng._weights_sharpe_long_only(returns_map, risk_free_rate=0.0)
    assert w["s2"] == pytest.approx(0.0)
    assert w["s1"] == pytest.approx(1.0)
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_weights_sharpe_all_zero_raises() -> None:
    import src.backtest.engine as eng

    idx = pd.date_range("2024-01-01", periods=200, freq="1h")
    r1 = pd.Series(np.full(len(idx), -0.001), index=idx, dtype=float)
    r2 = pd.Series(np.full(len(idx), -0.002), index=idx, dtype=float)
    returns_map = {"s1": r1, "s2": r2}

    with pytest.raises(ValueError, match="Sharpe scores <= 0"):
        eng._weights_sharpe_long_only(returns_map, risk_free_rate=0.0)


def test_combine_equities_single_weighting_point() -> None:
    import src.backtest.engine as eng

    idx = pd.date_range("2024-01-01", periods=6, freq="1h")
    e1 = _equity_from_returns(idx, 100.0, [0.01, 0.0, -0.005, 0.01, 0.0])
    e2 = _equity_from_returns(idx, 100.0, [0.002, 0.0, 0.001, 0.0, 0.002])
    equities = {"s1": e1, "s2": e2}
    weights = {"s1": 0.25, "s2": 0.75}

    combined = eng._combine_equities_weighted(equities, weights)
    expected = weights["s1"] * e1 + weights["s2"] * e2
    pd.testing.assert_series_equal(combined, expected)


def test_preview_returns_insufficient_raises() -> None:
    import src.backtest.engine as eng

    idx = pd.date_range("2024-01-01", periods=10, freq="1h")
    e = _equity_from_returns(idx, 100.0, [0.001] * (len(idx) - 1))
    with pytest.raises(ValueError, match="insufficient equity bars"):
        _ = eng._equity_to_returns_preview(e, estimation_bars=200)
