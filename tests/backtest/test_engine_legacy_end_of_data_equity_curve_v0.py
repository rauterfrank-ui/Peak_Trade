"""Regression tests for legacy BacktestEngine end_of_data equity_curve materialization."""

from __future__ import annotations

import pandas as pd
import pytest

from src.backtest.engine import BacktestEngine
from src.research.cross_sectional_single_slot_accounting_reconciliation_v0 import (
    reconcile_legacy_backtest_result_accounting_v0,
)


def _bars(closes: list[float]) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=len(closes), freq="1h", tz="UTC")
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c + 1.0 for c in closes],
            "low": [c - 1.0 for c in closes],
            "close": closes,
            "volume": [1000.0] * len(closes),
        },
        index=index,
    )


def _long_entry_hold_to_end_strategy() -> callable:
    def strategy_fn(df: pd.DataFrame, params: dict) -> pd.Series:
        signals = pd.Series(0, index=df.index, dtype=int)
        signals.iloc[1] = 1
        return signals

    return strategy_fn


def _flat_strategy() -> callable:
    def strategy_fn(df: pd.DataFrame, params: dict) -> pd.Series:
        return pd.Series(0, index=df.index, dtype=int)

    return strategy_fn


def _engine_config(initial_cash: float = 10_000.0) -> dict:
    return {
        "backtest": {
            "initial_cash": initial_cash,
            "fee_bps": 0.0,
            "slippage_bps": 0.0,
        },
        "risk": {
            "risk_per_trade": 0.01,
            "max_position_size": 0.25,
            "min_position_value": 50.0,
            "min_stop_distance": 0.001,
        },
    }


def _run_legacy(engine: BacktestEngine, **kwargs):
    return engine.run_realistic(
        fee_bps=0.0,
        slippage_bps=0.0,
        explicit_zero_cost_non_economic=True,
        **kwargs,
    )


class TestLegacyEndOfDataEquityCurve:
    def test_open_position_at_period_end_updates_final_equity_curve_point(self) -> None:
        df = _bars([100.0, 101.0, 105.0])
        engine = BacktestEngine(use_execution_pipeline=False)
        engine.config = _engine_config()
        result = _run_legacy(
            engine,
            df=df,
            strategy_signal_fn=_long_entry_hold_to_end_strategy(),
            strategy_params={"stop_pct": 0.5},
        )
        assert result.trades is not None
        assert len(result.trades) == 1
        assert result.trades.iloc[0]["exit_reason"] == "end_of_data"

        initial_cash = float(engine.config["backtest"]["initial_cash"])
        trade_pnl_sum = float(result.trades["pnl"].sum())
        final_equity = float(result.equity_curve.iloc[-1])
        assert final_equity == pytest.approx(initial_cash + trade_pnl_sum)
        assert final_equity != pytest.approx(initial_cash)

    def test_no_open_position_at_period_end_unchanged(self) -> None:
        df = _bars([100.0, 101.0, 102.0])
        engine = BacktestEngine(use_execution_pipeline=False)
        engine.config = _engine_config()
        result = _run_legacy(
            engine,
            df=df,
            strategy_signal_fn=_flat_strategy(),
            strategy_params={"stop_pct": 0.02},
        )
        assert result.trades is None or len(result.trades) == 0
        initial_cash = float(engine.config["backtest"]["initial_cash"])
        assert float(result.equity_curve.iloc[-1]) == pytest.approx(initial_cash)

    def test_ledger_equity_reconciliation_passes_after_end_of_data_close(self) -> None:
        df = _bars([100.0, 101.0, 105.0])
        engine = BacktestEngine(use_execution_pipeline=False)
        engine.config = _engine_config()
        result = _run_legacy(
            engine,
            df=df,
            strategy_signal_fn=_long_entry_hold_to_end_strategy(),
            strategy_params={"stop_pct": 0.5},
        )
        reconciliation = reconcile_legacy_backtest_result_accounting_v0(
            result,
            initial_cash=float(engine.config["backtest"]["initial_cash"]),
        )
        assert reconciliation.reconciled is True
        assert abs(reconciliation.accounting_delta) <= reconciliation.tolerance_abs

    def test_no_double_equity_booking_on_forced_close(self) -> None:
        df = _bars([100.0, 101.0, 105.0])
        engine = BacktestEngine(use_execution_pipeline=False)
        engine.config = _engine_config()
        result = _run_legacy(
            engine,
            df=df,
            strategy_signal_fn=_long_entry_hold_to_end_strategy(),
            strategy_params={"stop_pct": 0.5},
        )
        trade_pnl = float(result.trades.iloc[0]["pnl"])
        penultimate_equity = float(result.equity_curve.iloc[-2])
        final_equity = float(result.equity_curve.iloc[-1])
        assert final_equity == pytest.approx(penultimate_equity + trade_pnl)


class TestExecutionPipelineEndOfDataEquityCurve:
    def test_long_open_position_at_period_end_materializes_realized_equity(self) -> None:
        df = _bars([100.0, 101.0, 105.0])

        def long_entry_hold_strategy(_df: pd.DataFrame, _params: dict) -> pd.Series:
            return pd.Series(1, index=_df.index, dtype=int)

        engine = BacktestEngine(use_execution_pipeline=True)
        engine.config = _engine_config()
        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=long_entry_hold_strategy,
            strategy_params={},
            symbol="ETH/USDT",
            fee_bps=0.0,
            slippage_bps=0.0,
            explicit_zero_cost_non_economic=True,
        )
        assert result.trades is not None
        end_of_data = result.trades[result.trades["exit_reason"] == "end_of_data"]
        assert len(end_of_data) == 1
        assert end_of_data.iloc[0]["side"] == "long"

        initial_cash = float(engine.config["backtest"]["initial_cash"])
        trade_pnl_sum = float(result.trades["pnl"].sum())
        final_equity = float(result.equity_curve.iloc[-1])
        assert final_equity == pytest.approx(initial_cash + trade_pnl_sum)

    def test_short_open_position_at_period_end_materializes_realized_equity(self) -> None:
        df = _bars([100.0, 99.0, 98.0])

        def short_entry_hold_strategy(_df: pd.DataFrame, _params: dict) -> pd.Series:
            signals = pd.Series(-1, index=_df.index, dtype=int)
            return signals

        engine = BacktestEngine(use_execution_pipeline=True)
        engine.config = _engine_config()
        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=short_entry_hold_strategy,
            strategy_params={},
            symbol="ETH/USDT",
            fee_bps=0.0,
            slippage_bps=0.0,
            explicit_zero_cost_non_economic=True,
        )
        assert result.trades is not None
        end_of_data = result.trades[result.trades["exit_reason"] == "end_of_data"]
        assert len(end_of_data) == 1
        assert end_of_data.iloc[0]["side"] == "short"

        initial_cash = float(engine.config["backtest"]["initial_cash"])
        trade_pnl_sum = float(result.trades["pnl"].sum())
        final_equity = float(result.equity_curve.iloc[-1])
        assert final_equity == pytest.approx(initial_cash + trade_pnl_sum)
