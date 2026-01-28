from __future__ import annotations

from dataclasses import replace
from typing import Any

import pandas as pd
import pytest

from src.backtest import stats as stats_mod
from src.backtest.result import BacktestResult


def _equity_from_returns(
    index: pd.DatetimeIndex, initial: float, returns: list[float]
) -> pd.Series:
    if len(returns) != len(index) - 1:
        raise ValueError("returns length must be len(index)-1")
    equity = [float(initial)]
    for r in returns:
        equity.append(equity[-1] * (1.0 + float(r)))
    return pd.Series(equity, index=index, dtype=float)


def _make_result(index: pd.DatetimeIndex, initial: float, returns: list[float]) -> BacktestResult:
    equity = _equity_from_returns(index, initial, returns)
    drawdown = stats_mod.compute_drawdown(equity)
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    return BacktestResult(
        equity_curve=equity,
        drawdown=drawdown,
        trades=None,
        stats={
            "total_return": total_return,
            "sharpe": 1.0,
            "max_drawdown": float(drawdown.min()) if len(drawdown) else 0.0,
            "total_trades": 1,
            "win_rate": 0.5,
            "profit_factor": 1.0,
            "blocked_trades": 0,
        },
        metadata={"mode": "test_stub"},
    )


def test_two_pass_risk_parity_inverse_vol_and_single_weighting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.backtest import engine as bt_engine

    # Deterministic OHLCV
    idx = pd.date_range("2025-01-01", periods=30, freq="h")
    df = pd.DataFrame(
        {"open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
        index=idx,
    )

    strategies = ["s1", "s2"]

    # Preview estimation uses first 10 bars => 9 returns
    estimation_bars = 10
    # s1: higher volatility pattern
    s1_rets = [0.01, -0.005] * 4 + [0.01]
    # s2: lower volatility, still non-zero std
    s2_rets = [0.002, 0.0018] * 4 + [0.002]

    # Final run uses full df => 29 returns (reuse a simple repeating pattern)
    s1_rets_full = (s1_rets * 4)[: len(idx) - 1]
    s2_rets_full = (s2_rets * 4)[: len(idx) - 1]

    seen_initial_cash: list[float] = []

    def _stub_run_single(*, df: pd.DataFrame, strategy_name: str, **_kwargs: Any) -> BacktestResult:
        # run_portfolio_from_config overwrites cfg["backtest"]["initial_cash"] before calling us.
        initial = float(cfg["backtest"]["initial_cash"])
        seen_initial_cash.append(initial)

        if len(df) == estimation_bars:
            if strategy_name == "s1":
                return _make_result(df.index, initial, s1_rets)
            if strategy_name == "s2":
                return _make_result(df.index, initial, s2_rets)
        else:
            if strategy_name == "s1":
                return _make_result(df.index, initial, s1_rets_full)
            if strategy_name == "s2":
                return _make_result(df.index, initial, s2_rets_full)
        raise AssertionError("unexpected stub invocation")

    cfg: dict[str, Any] = {
        "backtest": {"initial_cash": 10000.0},
        "portfolio": {
            "enabled": True,
            "allocation_method": "risk_parity",
            "total_capital": 10000.0,
            "allocation_estimation_bars": estimation_bars,
            "max_strategies_active": 10,
        },
        "strategies": {"active": [], "available": []},
    }

    monkeypatch.setattr(
        bt_engine, "run_single_strategy_from_registry", _stub_run_single, raising=True
    )

    result = bt_engine.run_portfolio_from_config(
        df=df,
        cfg=cfg,
        portfolio_name="default",
        strategy_filter=strategies,
    )

    # Single-weighting contract: initial cash is NOT pre-scaled by weights.
    assert all(v == pytest.approx(10000.0) for v in seen_initial_cash)

    # risk_parity v1 is inverse-vol: s2 lower vol => higher weight.
    assert result.allocation["s2"] > result.allocation["s1"]
    assert sum(result.allocation.values()) == pytest.approx(1.0)
    assert all(w >= 0.0 for w in result.allocation.values())

    # Combined equity must equal weighted sum of strategy equities (single weighting point).
    combined_expected = (
        result.strategy_results["s1"].equity_curve * result.allocation["s1"]
        + result.strategy_results["s2"].equity_curve * result.allocation["s2"]
    )
    pd.testing.assert_series_equal(result.combined_equity, combined_expected)


def test_two_pass_sharpe_weighted_negative_scores_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.backtest import engine as bt_engine

    idx = pd.date_range("2025-01-01", periods=12, freq="h")
    df = pd.DataFrame(
        {"open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
        index=idx,
    )

    strategies = ["s1", "s2"]
    estimation_bars = 10

    # Both strategies have negative mean returns (after rf=0) -> clipped Sharpe scores sum to 0.
    neg_rets = [-0.001, -0.002] * 4 + [-0.001]

    def _stub_run_single(*, df: pd.DataFrame, strategy_name: str, **_kwargs: Any) -> BacktestResult:
        initial = float(cfg["backtest"]["initial_cash"])
        if len(df) == estimation_bars:
            return _make_result(df.index, initial, neg_rets)
        return _make_result(df.index, initial, (neg_rets * 4)[: len(df.index) - 1])

    cfg: dict[str, Any] = {
        "backtest": {"initial_cash": 10000.0},
        "portfolio": {
            "enabled": True,
            "allocation_method": "sharpe_weighted",
            "total_capital": 10000.0,
            "allocation_estimation_bars": estimation_bars,
            "risk_free_rate": 0.0,
            "max_strategies_active": 10,
        },
        "strategies": {"active": [], "available": []},
    }

    monkeypatch.setattr(
        bt_engine, "run_single_strategy_from_registry", _stub_run_single, raising=True
    )

    with pytest.raises(ValueError, match="Sharpe scores <= 0"):
        bt_engine.run_portfolio_from_config(
            df=df,
            cfg=cfg,
            portfolio_name="default",
            strategy_filter=strategies,
        )


def test_two_pass_insufficient_data_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.backtest import engine as bt_engine

    idx = pd.date_range("2025-01-01", periods=5, freq="h")
    df = pd.DataFrame(
        {"open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
        index=idx,
    )

    cfg: dict[str, Any] = {
        "backtest": {"initial_cash": 10000.0},
        "portfolio": {
            "enabled": True,
            "allocation_method": "risk_parity",
            "total_capital": 10000.0,
            "allocation_estimation_bars": 10,
            "max_strategies_active": 10,
        },
        "strategies": {"active": [], "available": []},
    }

    # should fail before calling into strategy runner
    with pytest.raises(ValueError, match="Insufficient data for allocation preview"):
        bt_engine.run_portfolio_from_config(
            df=df,
            cfg=cfg,
            portfolio_name="default",
            strategy_filter=["s1", "s2"],
        )


def test_two_pass_deterministic_weights(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.backtest import engine as bt_engine

    idx = pd.date_range("2025-01-01", periods=30, freq="h")
    df = pd.DataFrame(
        {"open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
        index=idx,
    )

    strategies = ["s1", "s2"]
    estimation_bars = 10
    s1_rets = [0.01, -0.005] * 4 + [0.01]
    s2_rets = [0.002, 0.0018] * 4 + [0.002]
    s1_rets_full = (s1_rets * 4)[: len(idx) - 1]
    s2_rets_full = (s2_rets * 4)[: len(idx) - 1]

    def _stub_run_single(*, df: pd.DataFrame, strategy_name: str, **_kwargs: Any) -> BacktestResult:
        initial = float(cfg["backtest"]["initial_cash"])
        if len(df) == estimation_bars:
            return _make_result(df.index, initial, s1_rets if strategy_name == "s1" else s2_rets)
        return _make_result(
            df.index, initial, s1_rets_full if strategy_name == "s1" else s2_rets_full
        )

    cfg: dict[str, Any] = {
        "backtest": {"initial_cash": 10000.0},
        "portfolio": {
            "enabled": True,
            "allocation_method": "risk_parity",
            "total_capital": 10000.0,
            "allocation_estimation_bars": estimation_bars,
            "max_strategies_active": 10,
        },
        "strategies": {"active": [], "available": []},
    }

    monkeypatch.setattr(
        bt_engine, "run_single_strategy_from_registry", _stub_run_single, raising=True
    )

    r1 = bt_engine.run_portfolio_from_config(
        df=df,
        cfg=cfg,
        portfolio_name="default",
        strategy_filter=strategies,
    )
    r2 = bt_engine.run_portfolio_from_config(
        df=df,
        cfg=cfg,
        portfolio_name="default",
        strategy_filter=strategies,
    )

    assert r1.allocation == r2.allocation
