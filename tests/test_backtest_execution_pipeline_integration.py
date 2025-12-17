#!/usr/bin/env python3
# tests/test_backtest_execution_pipeline_integration.py
"""
Peak_Trade: Tests fuer BacktestEngine ExecutionPipeline Integration (Phase 16B)
===============================================================================

Tests fuer:
- BacktestEngine mit use_execution_pipeline=True (Default)
- BacktestEngine mit use_execution_pipeline=False (Legacy)
- Backward-Kompatibilitaet use_order_layer Alias
- Execution Logging (log_executions=True)
- run_realistic() mit ExecutionPipeline
- get_execution_logs() / clear_execution_logs()

WICHTIG: Keine echten Orders - alles Paper/Sandbox.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Projekt-Root zum Python-Path hinzufuegen
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _create_sample_ohlcv(
    n_bars: int = 50,
    start_price: float = 50000.0,
    volatility: float = 0.02,
) -> pd.DataFrame:
    """Erstellt einen Sample-OHLCV-DataFrame fuer Tests."""
    np.random.seed(42)

    dates = pd.date_range(
        start="2024-01-01",
        periods=n_bars,
        freq="1h",
    )

    # Random Walk fuer Preise
    returns = np.random.normal(0, volatility, n_bars)
    close = start_price * np.cumprod(1 + returns)
    high = close * (1 + np.abs(np.random.normal(0, volatility / 2, n_bars)))
    low = close * (1 - np.abs(np.random.normal(0, volatility / 2, n_bars)))
    open_ = close * (1 + np.random.normal(0, volatility / 3, n_bars))
    volume = np.random.uniform(100, 1000, n_bars)

    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=dates,
    )


def _simple_signal_fn(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Einfache Test-Strategie: Kaufen bei steigenden Preisen, Verkaufen bei fallenden.
    """
    close = df["close"]
    ma_period = params.get("ma_period", 5)
    ma = close.rolling(ma_period).mean()

    signals = pd.Series(0, index=df.index)
    signals[close > ma] = 1
    signals[close < ma] = -1

    return signals


# ============================================================================
# BacktestEngine Integration Tests (Phase 16B)
# ============================================================================

class TestBacktestEngineExecutionPipelineFlag:
    """Tests fuer use_execution_pipeline Flag."""

    def test_default_use_execution_pipeline_is_true(self):
        """use_execution_pipeline ist standardmaessig True."""
        from src.backtest.engine import BacktestEngine

        engine = BacktestEngine()
        assert engine.use_execution_pipeline is True

    def test_use_execution_pipeline_can_be_set_false(self):
        """use_execution_pipeline kann auf False gesetzt werden."""
        from src.backtest.engine import BacktestEngine

        engine = BacktestEngine(use_execution_pipeline=False)
        assert engine.use_execution_pipeline is False

    def test_use_order_layer_alias_works(self):
        """use_order_layer Alias funktioniert fuer backward compat."""
        from src.backtest.engine import BacktestEngine

        # Mit use_order_layer=True
        engine = BacktestEngine(use_order_layer=True)
        assert engine.use_execution_pipeline is True
        assert engine.use_order_layer is True

        # Mit use_order_layer=False
        engine2 = BacktestEngine(use_order_layer=False)
        assert engine2.use_execution_pipeline is False
        assert engine2.use_order_layer is False


class TestBacktestEngineLogExecutions:
    """Tests fuer log_executions Flag."""

    def test_default_log_executions_is_false(self):
        """log_executions ist standardmaessig False."""
        from src.backtest.engine import BacktestEngine

        engine = BacktestEngine()
        assert engine.log_executions is False

    def test_log_executions_can_be_enabled(self):
        """log_executions kann aktiviert werden."""
        from src.backtest.engine import BacktestEngine

        engine = BacktestEngine(log_executions=True)
        assert engine.log_executions is True

    def test_execution_logs_empty_initially(self):
        """_execution_logs ist initial leer."""
        from src.backtest.engine import BacktestEngine

        engine = BacktestEngine()
        assert engine.get_execution_logs() == []

    def test_execution_logs_populated_with_log_executions(self):
        """Execution-Logs werden bei log_executions=True gefuellt."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=30)
        engine = BacktestEngine(
            use_execution_pipeline=True,
            log_executions=True,
        )

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 3},
            symbol="BTC/EUR",
        )

        logs = engine.get_execution_logs()
        assert len(logs) > 0, "Execution-Logs sollten nicht leer sein"
        assert "run_id" in logs[0]
        assert "symbol" in logs[0]
        assert "total_orders" in logs[0]

    def test_clear_execution_logs(self):
        """clear_execution_logs() loescht alle Logs."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=30)
        engine = BacktestEngine(
            use_execution_pipeline=True,
            log_executions=True,
        )

        engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 3},
        )

        assert len(engine.get_execution_logs()) > 0

        engine.clear_execution_logs()
        assert len(engine.get_execution_logs()) == 0


class TestRunRealisticWithExecutionPipeline:
    """Tests fuer run_realistic() mit ExecutionPipeline."""

    def test_run_realistic_with_execution_pipeline(self):
        """run_realistic() funktioniert mit use_execution_pipeline=True."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=50)
        engine = BacktestEngine(use_execution_pipeline=True)

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5},
            symbol="BTC/EUR",
            fee_bps=10.0,
            slippage_bps=5.0,
        )

        # Basis-Checks
        assert result is not None
        assert result.equity_curve is not None
        assert len(result.equity_curve) > 0
        assert result.stats is not None
        assert "total_trades" in result.stats

        # Mode sollte execution_pipeline_backtest sein
        assert result.metadata.get("mode") == "execution_pipeline_backtest"

    def test_run_realistic_with_legacy_mode(self):
        """run_realistic() funktioniert mit use_execution_pipeline=False."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=50)
        engine = BacktestEngine(use_execution_pipeline=False)

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5, "stop_pct": 0.02},
        )

        # Basis-Checks
        assert result is not None
        assert result.equity_curve is not None
        assert result.stats is not None

        # Mode sollte realistic sein
        assert result.metadata.get("mode") == "realistic_with_risk_management"

    def test_run_realistic_execution_pipeline_generates_orders(self):
        """ExecutionPipeline generiert Orders."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=50)
        engine = BacktestEngine(use_execution_pipeline=True)

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 3},
            symbol="BTC/EUR",
        )

        # Execution-Summary sollte Orders enthalten
        exec_summary = result.metadata.get("execution_summary", {})
        total_orders = exec_summary.get("total_orders", 0)

        # Bei einer Moving-Average-Strategie sollten einige Orders generiert werden
        assert total_orders > 0, "Es sollten Orders generiert worden sein"

    def test_run_realistic_execution_pipeline_tracks_fills(self):
        """ExecutionPipeline tracked Fills in execution_results."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=50)
        engine = BacktestEngine(use_execution_pipeline=True)

        engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 3},
            symbol="BTC/EUR",
        )

        # execution_results sollte gefuellt sein
        assert len(engine.execution_results) > 0

    def test_run_realistic_with_fees_and_slippage(self):
        """Fees und Slippage werden korrekt angewendet."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=50)

        # Mit Fees
        engine_with_fees = BacktestEngine(use_execution_pipeline=True)
        result_fees = engine_with_fees.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5},
            fee_bps=20.0,  # 0.2% Fees
        )

        # Ohne Fees
        engine_no_fees = BacktestEngine(use_execution_pipeline=True)
        result_no_fees = engine_no_fees.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5},
            fee_bps=0.0,
        )

        # Fees sollten in stats auftauchen
        fees_with = result_fees.stats.get("total_fees", 0)
        fees_without = result_no_fees.stats.get("total_fees", 0)

        assert fees_without == 0.0
        # Mit Fees sollte es > 0 sein (wenn Trades stattfanden)
        if result_fees.stats.get("total_trades", 0) > 0:
            assert fees_with > 0


class TestExecutionPipelineInstance:
    """Tests fuer die ExecutionPipeline-Instanz in der Engine."""

    def test_execution_pipeline_instance_created(self):
        """ExecutionPipeline-Instanz wird erstellt."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=30)
        engine = BacktestEngine(use_execution_pipeline=True)

        engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5},
        )

        assert engine.execution_pipeline is not None

    def test_execution_pipeline_not_created_in_legacy_mode(self):
        """ExecutionPipeline wird im Legacy-Modus nicht erstellt."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=30)
        engine = BacktestEngine(use_execution_pipeline=False)

        engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5, "stop_pct": 0.02},
        )

        # Im Legacy-Modus bleibt execution_pipeline None
        assert engine.execution_pipeline is None


class TestBackwardCompatibility:
    """Tests fuer Backward-Kompatibilitaet."""

    def test_run_with_order_layer_still_works(self):
        """run_with_order_layer() funktioniert noch (deprecated)."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=30)
        engine = BacktestEngine()

        # Sollte funktionieren, aber deprecated Warning ausgeben
        result = engine.run_with_order_layer(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5},
            symbol="BTC/EUR",
        )

        assert result is not None
        assert result.equity_curve is not None

    def test_old_tests_still_pass_with_use_order_layer(self):
        """Bestehende Tests mit use_order_layer=True funktionieren."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=30)
        engine = BacktestEngine(use_order_layer=True)

        result = engine.run_with_order_layer(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5},
        )

        assert result is not None
        assert result.stats is not None


class TestResultMetadata:
    """Tests fuer Result-Metadata."""

    def test_metadata_contains_run_id(self):
        """Metadata enthaelt run_id."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=30)
        engine = BacktestEngine(use_execution_pipeline=True)

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5},
        )

        assert "run_id" in result.metadata
        assert result.metadata["run_id"].startswith("backtest_")

    def test_metadata_contains_execution_summary(self):
        """Metadata enthaelt execution_summary."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=30)
        engine = BacktestEngine(use_execution_pipeline=True)

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5},
        )

        assert "execution_summary" in result.metadata
        summary = result.metadata["execution_summary"]
        assert "total_orders" in summary
        assert "filled_orders" in summary
        assert "rejected_orders" in summary

    def test_metadata_contains_fee_and_slippage_info(self):
        """Metadata enthaelt fee_bps und slippage_bps."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=30)
        engine = BacktestEngine(use_execution_pipeline=True)

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 5},
            fee_bps=15.0,
            slippage_bps=10.0,
        )

        assert result.metadata.get("fee_bps") == 15.0
        assert result.metadata.get("slippage_bps") == 10.0


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Edge-Case Tests."""

    def test_no_trades_generated(self):
        """Engine funktioniert auch wenn keine Trades generiert werden."""
        from src.backtest.engine import BacktestEngine

        # DataFrame wo Signal immer 0 bleibt
        df = _create_sample_ohlcv(n_bars=20)

        def no_signal_fn(df: pd.DataFrame, params: dict) -> pd.Series:
            return pd.Series(0, index=df.index)

        engine = BacktestEngine(use_execution_pipeline=True)
        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=no_signal_fn,
            strategy_params={},
        )

        assert result is not None
        assert result.stats.get("total_trades", 0) == 0
        assert result.stats.get("total_orders", 0) == 0

    def test_single_bar_dataframe(self):
        """Engine funktioniert mit nur einer Bar."""
        from src.backtest.engine import BacktestEngine

        df = _create_sample_ohlcv(n_bars=1)
        engine = BacktestEngine(use_execution_pipeline=True)

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=_simple_signal_fn,
            strategy_params={"ma_period": 1},
        )

        assert result is not None
        assert len(result.equity_curve) >= 1
