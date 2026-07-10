"""Regression tests for legacy BacktestEngine gross_pnl trade-record emission v0."""

from __future__ import annotations

import pandas as pd
import pytest

from src.backtest.engine import BacktestEngine
from src.research.cross_sectional_single_slot_accounting_reconciliation_v0 import (
    reconcile_legacy_backtest_result_accounting_v0,
)
from src.research.trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0 import (
    materialize_trade_ledger_v1_records_v0,
)


def _bars(closes: list[float]) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=len(closes), freq="1h", tz="UTC")
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c + 2.0 for c in closes],
            "low": [c - 2.0 for c in closes],
            "close": closes,
            "volume": [1000.0] * len(closes),
        },
        index=index,
    )


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


def _long_entry_exit_strategy(entry_idx: int, exit_idx: int) -> callable:
    def strategy_fn(df: pd.DataFrame, params: dict) -> pd.Series:
        signals = pd.Series(0, index=df.index, dtype=int)
        signals.iloc[entry_idx] = 1
        signals.iloc[exit_idx] = -1
        return signals

    return strategy_fn


def _run_legacy(
    engine: BacktestEngine,
    df: pd.DataFrame,
    strategy_signal_fn: callable,
    *,
    fee_bps: float = 0.0,
    slippage_bps: float = 0.0,
) -> object:
    return engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_signal_fn,
        strategy_params={"stop_pct": 0.5},
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        explicit_zero_cost_non_economic=(fee_bps == 0.0 and slippage_bps == 0.0),
    )


def _run_pipeline(
    engine: BacktestEngine,
    df: pd.DataFrame,
    strategy_signal_fn: callable,
    *,
    fee_bps: float = 0.0,
    slippage_bps: float = 0.0,
) -> object:
    return engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_signal_fn,
        strategy_params={},
        symbol="ETH/USDT",
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        explicit_zero_cost_non_economic=(fee_bps == 0.0 and slippage_bps == 0.0),
    )


class TestLegacyGrossPnlTradeRecordEmission:
    def test_profitable_long_trade_emits_positive_gross_pnl(self) -> None:
        df = _bars([100.0, 101.0, 110.0])
        engine = BacktestEngine(use_execution_pipeline=False)
        engine.config = _engine_config()
        result = _run_legacy(
            engine,
            df,
            _long_entry_exit_strategy(entry_idx=1, exit_idx=2),
        )
        trade = result.trades.iloc[0]
        assert trade["gross_pnl"] > 0.0
        assert trade["gross_pnl"] == pytest.approx(trade["pnl"])
        assert trade["entry_cost"] == pytest.approx(0.0)
        assert trade["exit_cost"] == pytest.approx(0.0)

    def test_losing_long_trade_emits_negative_gross_pnl(self) -> None:
        df = _bars([100.0, 101.0, 95.0])
        engine = BacktestEngine(use_execution_pipeline=False)
        engine.config = _engine_config()
        result = _run_legacy(
            engine,
            df,
            _long_entry_exit_strategy(entry_idx=1, exit_idx=2),
        )
        trade = result.trades.iloc[0]
        assert trade["gross_pnl"] < 0.0
        assert trade["gross_pnl"] == pytest.approx(trade["pnl"])

    def test_zero_cost_gross_equals_net(self) -> None:
        df = _bars([100.0, 101.0, 105.0])
        engine = BacktestEngine(use_execution_pipeline=False)
        engine.config = _engine_config()
        result = _run_legacy(
            engine,
            df,
            _long_entry_exit_strategy(entry_idx=1, exit_idx=2),
        )
        trade = result.trades.iloc[0]
        assert trade["gross_pnl"] == pytest.approx(trade["pnl"])

    def test_gross_pnl_before_cost_fields(self) -> None:
        df = _bars([100.0, 101.0, 105.0, 106.0])
        engine = BacktestEngine(use_execution_pipeline=True)
        engine.config = _engine_config()
        result = _run_pipeline(
            engine,
            df,
            _long_entry_exit_strategy(entry_idx=1, exit_idx=2),
            fee_bps=10.0,
            slippage_bps=5.0,
        )
        trade = result.trades.iloc[0]
        assert "gross_pnl" in trade
        assert "entry_cost" in trade
        assert "exit_cost" in trade
        assert trade["gross_pnl"] != pytest.approx(trade["pnl"])
        assert trade["gross_pnl"] - trade["exit_cost"] == pytest.approx(trade["pnl"])

    def test_trade_accounting_reconciles(self) -> None:
        df = _bars([100.0, 101.0, 105.0])
        engine = BacktestEngine(use_execution_pipeline=False)
        engine.config = _engine_config()
        result = _run_legacy(
            engine,
            df,
            _long_entry_exit_strategy(entry_idx=1, exit_idx=2),
        )
        reconciliation = reconcile_legacy_backtest_result_accounting_v0(
            result,
            initial_cash=float(engine.config["backtest"]["initial_cash"]),
        )
        assert reconciliation.reconciled is True
        assert reconciliation.realized_gross_pnl != 0.0
        assert reconciliation.realized_gross_pnl == pytest.approx(
            float(result.trades["gross_pnl"].sum())
        )

    def test_portfolio_equity_reconciliation_unchanged(self) -> None:
        df = _bars([100.0, 101.0, 105.0])
        engine = BacktestEngine(use_execution_pipeline=False)
        engine.config = _engine_config()
        result = _run_legacy(
            engine,
            df,
            _long_entry_exit_strategy(entry_idx=1, exit_idx=2),
        )
        initial_cash = float(engine.config["backtest"]["initial_cash"])
        assert float(result.equity_curve.iloc[-1]) == pytest.approx(
            initial_cash + float(result.trades["pnl"].sum())
        )

    def test_materializer_reads_gross_pnl_field(self) -> None:
        df = _bars([100.0, 101.0, 105.0])
        engine = BacktestEngine(use_execution_pipeline=False)
        engine.config = _engine_config()
        result = _run_legacy(
            engine,
            df,
            _long_entry_exit_strategy(entry_idx=1, exit_idx=2),
        )
        records = materialize_trade_ledger_v1_records_v0(
            trades_df=result.trades,
            evaluation_id="eval-test",
            candidate_id="candidate-test",
            strategy_id="armstrong_cycle",
            strategy_version="v1",
            instrument_id="ETH/USDT",
            venue="okx",
            binding_set={},
            equity_curve=result.equity_curve,
            input_digest="input",
            config_digest="config",
            implementation_digest="impl",
            required_fields=("gross_pnl", "net_pnl", "fees"),
        )
        assert records[0]["gross_pnl"] == pytest.approx(float(result.trades.iloc[0]["gross_pnl"]))

    def test_deterministic_repeat(self) -> None:
        df = _bars([100.0, 101.0, 105.0, 106.0])
        engine_a = BacktestEngine(use_execution_pipeline=False)
        engine_a.config = _engine_config()
        engine_b = BacktestEngine(use_execution_pipeline=False)
        engine_b.config = _engine_config()
        result_a = _run_legacy(
            engine_a,
            df,
            _long_entry_exit_strategy(entry_idx=1, exit_idx=2),
        )
        result_b = _run_legacy(
            engine_b,
            df,
            _long_entry_exit_strategy(entry_idx=1, exit_idx=2),
        )
        assert result_a.trades.to_dict(orient="records") == result_b.trades.to_dict(
            orient="records"
        )


class TestExecutionPipelineGrossPnlTradeRecordEmission:
    def test_profitable_short_trade_emits_positive_gross_pnl(self) -> None:
        df = _bars([100.0, 99.0, 95.0])

        def short_entry_hold_strategy(_df: pd.DataFrame, _params: dict) -> pd.Series:
            return pd.Series(-1, index=_df.index, dtype=int)

        engine = BacktestEngine(use_execution_pipeline=True)
        engine.config = _engine_config()
        result = _run_pipeline(engine, df, short_entry_hold_strategy)
        end_of_data = result.trades[result.trades["exit_reason"] == "end_of_data"]
        assert len(end_of_data) == 1
        assert end_of_data.iloc[0]["side"] == "short"
        assert end_of_data.iloc[0]["gross_pnl"] > 0.0

    def test_losing_short_trade_emits_negative_gross_pnl(self) -> None:
        df = _bars([100.0, 99.0, 103.0])

        def short_entry_hold_strategy(_df: pd.DataFrame, _params: dict) -> pd.Series:
            return pd.Series(-1, index=_df.index, dtype=int)

        engine = BacktestEngine(use_execution_pipeline=True)
        engine.config = _engine_config()
        result = _run_pipeline(engine, df, short_entry_hold_strategy)
        end_of_data = result.trades[result.trades["exit_reason"] == "end_of_data"]
        assert len(end_of_data) == 1
        assert end_of_data.iloc[0]["side"] == "short"
        assert end_of_data.iloc[0]["gross_pnl"] < 0.0

    def test_nonzero_costs_gross_differs_from_net(self) -> None:
        df = _bars([100.0, 101.0, 105.0, 106.0])
        engine = BacktestEngine(use_execution_pipeline=True)
        engine.config = _engine_config()
        result = _run_pipeline(
            engine,
            df,
            _long_entry_exit_strategy(entry_idx=1, exit_idx=2),
            fee_bps=10.0,
            slippage_bps=5.0,
        )
        trade = result.trades.iloc[0]
        assert trade["gross_pnl"] != pytest.approx(trade["pnl"])
        assert trade["exit_cost"] > 0.0
