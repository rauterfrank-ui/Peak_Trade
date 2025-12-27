#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tests/test_execution_pipeline_smoke.py
"""
Peak_Trade: Smoke-Tests fuer Execution-Pipeline (Phase 16A)
===========================================================

Tests fuer:
- ExecutionPipeline Initialisierung
- SignalEvent Dataclass
- Signal-to-Order Konvertierung
- ExecutionPipeline.for_paper() Factory
- execute_orders()
- execute_from_signals() Integration
- BacktestEngine.run_with_order_layer() Integration

WICHTIG: Keine echten Orders - alles Paper/Sandbox.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

# Projekt-Root zum Python-Path hinzufuegen
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ============================================================================
# ExecutionPipeline Tests
# ============================================================================


class TestSignalEvent:
    """Tests fuer SignalEvent Dataclass."""

    def test_signal_event_creation(self):
        """SignalEvent kann erstellt werden."""
        from src.execution import SignalEvent

        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=1,
            price=50000.0,
            previous_signal=0,
        )

        assert event.symbol == "BTC/EUR"
        assert event.signal == 1
        assert event.price == 50000.0
        assert event.previous_signal == 0

    def test_signal_event_is_entry_long(self):
        """is_entry_long erkennt Long-Entry."""
        from src.execution import SignalEvent

        # Entry: 0 -> 1
        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=1,
            price=50000.0,
            previous_signal=0,
        )
        assert event.is_entry_long is True

    def test_signal_event_is_exit_long(self):
        """is_exit_long erkennt Long-Exit."""
        from src.execution import SignalEvent

        # Exit: 1 -> 0
        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=0,
            price=50000.0,
            previous_signal=1,
        )
        assert event.is_exit_long is True

    def test_signal_event_is_entry_short(self):
        """is_entry_short erkennt Short-Entry."""
        from src.execution import SignalEvent

        # Entry: 0 -> -1
        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=-1,
            price=50000.0,
            previous_signal=0,
        )
        assert event.is_entry_short is True

    def test_signal_event_is_exit_short(self):
        """is_exit_short erkennt Short-Exit."""
        from src.execution import SignalEvent

        # Exit: -1 -> 0
        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=0,
            price=50000.0,
            previous_signal=-1,
        )
        assert event.is_exit_short is True

    def test_signal_event_is_flip_long_to_short(self):
        """is_flip_long_to_short erkennt Signal-Flip."""
        from src.execution import SignalEvent

        # Flip: 1 -> -1
        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=-1,
            price=50000.0,
            previous_signal=1,
        )
        assert event.is_flip_long_to_short is True

    def test_signal_event_is_flip_short_to_long(self):
        """is_flip_short_to_long erkennt Signal-Flip."""
        from src.execution import SignalEvent

        # Flip: -1 -> 1
        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=1,
            price=50000.0,
            previous_signal=-1,
        )
        assert event.is_flip_short_to_long is True

    def test_signal_event_no_change(self):
        """Signal ohne Aenderung hat keine Entry/Exit-Properties true."""
        from src.execution import SignalEvent

        # Kein Change: 1 -> 1
        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=1,
            price=50000.0,
            previous_signal=1,
        )
        assert event.is_entry_long is False
        assert event.is_exit_long is False
        assert event.is_entry_short is False
        assert event.is_exit_short is False
        assert event.is_flip_long_to_short is False
        assert event.is_flip_short_to_long is False
        assert event.has_signal_change is False

    def test_signal_event_has_signal_change(self):
        """has_signal_change erkennt Signal-Aenderung."""
        from src.execution import SignalEvent

        # Change: 0 -> 1
        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=1,
            price=50000.0,
            previous_signal=0,
        )
        assert event.has_signal_change is True


class TestExecutionPipelineConfig:
    """Tests fuer ExecutionPipelineConfig."""

    def test_config_defaults(self):
        """ExecutionPipelineConfig hat sinnvolle Defaults."""
        from src.execution.pipeline import ExecutionPipelineConfig

        config = ExecutionPipelineConfig()

        assert config.default_time_in_force == "GTC"
        assert config.allow_partial_fills is True
        assert config.default_order_type == "market"
        assert config.generate_client_ids is True
        assert config.max_position_notional_pct == 1.0
        assert config.slippage_bps == 0.0
        assert config.fee_bps == 0.0

    def test_config_custom_values(self):
        """ExecutionPipelineConfig akzeptiert Custom-Werte."""
        from src.execution.pipeline import ExecutionPipelineConfig

        config = ExecutionPipelineConfig(
            default_time_in_force="IOC",
            allow_partial_fills=False,
            default_order_type="limit",
            generate_client_ids=False,
            max_position_notional_pct=0.5,
        )

        assert config.default_time_in_force == "IOC"
        assert config.allow_partial_fills is False
        assert config.default_order_type == "limit"
        assert config.generate_client_ids is False
        assert config.max_position_notional_pct == 0.5


class TestExecutionPipeline:
    """Tests fuer ExecutionPipeline."""

    def test_pipeline_for_paper_creation(self):
        """ExecutionPipeline.for_paper() erstellt Pipeline mit PaperOrderExecutor."""
        from src.execution import ExecutionPipeline
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,
            slippage_bps=5.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        assert pipeline is not None
        assert pipeline.executor is not None

    def test_pipeline_execute_single_order_via_list(self):
        """Pipeline kann einzelne Order via execute_orders([order]) ausfuehren."""
        from src.execution import ExecutionPipeline
        from src.orders import PaperMarketContext, OrderRequest

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,
            slippage_bps=5.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            order_type="market",
        )

        results = pipeline.execute_orders([order])

        assert len(results) == 1
        assert results[0].status == "filled"
        assert results[0].fill is not None
        assert results[0].fill.quantity == 0.01
        assert results[0].fill.price > 0

    def test_pipeline_execute_multiple_orders(self):
        """Pipeline kann mehrere Orders ausfuehren."""
        from src.execution import ExecutionPipeline
        from src.orders import PaperMarketContext, OrderRequest

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            fee_bps=10.0,
            slippage_bps=5.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        orders = [
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01),
            OrderRequest(symbol="ETH/EUR", side="buy", quantity=0.1),
        ]

        results = pipeline.execute_orders(orders)

        assert len(results) == 2
        assert all(r.status == "filled" for r in results)

    def test_pipeline_signal_to_orders_entry_long(self):
        """signal_to_orders() generiert Order fuer Long-Entry."""
        from src.execution import ExecutionPipeline, SignalEvent
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=1,
            price=50000.0,
            previous_signal=0,
        )

        orders = pipeline.signal_to_orders(
            event=event,
            position_size=0.01,
            current_position=0.0,
        )

        assert len(orders) == 1
        assert orders[0].side == "buy"
        assert orders[0].quantity == 0.01

    def test_pipeline_signal_to_orders_exit_long(self):
        """signal_to_orders() generiert Order fuer Long-Exit."""
        from src.execution import ExecutionPipeline, SignalEvent
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=0,
            price=50000.0,
            previous_signal=1,
        )

        orders = pipeline.signal_to_orders(
            event=event,
            position_size=0.01,
            current_position=0.01,  # Hat Long-Position
        )

        assert len(orders) == 1
        assert orders[0].side == "sell"
        assert orders[0].quantity == 0.01

    def test_pipeline_signal_to_orders_flip(self):
        """signal_to_orders() generiert 2 Orders fuer Flip (Exit + Entry)."""
        from src.execution import ExecutionPipeline, SignalEvent
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        # Flip: Long -> Short
        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=-1,
            price=50000.0,
            previous_signal=1,
        )

        orders = pipeline.signal_to_orders(
            event=event,
            position_size=0.01,
            current_position=0.01,  # Hat Long-Position
        )

        # Sollte 2 Orders generieren: Exit Long + Entry Short
        assert len(orders) == 2
        assert orders[0].side == "sell"  # Exit Long
        assert orders[1].side == "sell"  # Entry Short

    def test_pipeline_signal_to_orders_no_change(self):
        """signal_to_orders() generiert keine Order bei gleichem Signal."""
        from src.execution import ExecutionPipeline, SignalEvent
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        # Kein Change: 1 -> 1
        event = SignalEvent(
            timestamp=datetime.now(),
            symbol="BTC/EUR",
            signal=1,
            price=50000.0,
            previous_signal=1,
        )

        orders = pipeline.signal_to_orders(
            event=event,
            position_size=0.01,
            current_position=0.01,
        )

        assert len(orders) == 0

    def test_pipeline_get_execution_summary(self):
        """get_execution_summary() liefert Statistiken."""
        from src.execution import ExecutionPipeline
        from src.orders import PaperMarketContext, OrderRequest

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        # Einige Orders ausfuehren
        orders = [
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01),
            OrderRequest(symbol="BTC/EUR", side="sell", quantity=0.01),
        ]
        pipeline.execute_orders(orders)

        summary = pipeline.get_execution_summary()

        assert "total_orders" in summary
        assert summary["total_orders"] == 2
        assert "filled_orders" in summary
        assert summary["filled_orders"] == 2


class TestExecutionPipelineExecuteFromSignals:
    """Tests fuer execute_from_signals() Methode."""

    def test_execute_from_signals_basic(self):
        """execute_from_signals() verarbeitet Signal-Serie."""
        from src.execution import ExecutionPipeline, ExecutionPipelineConfig
        from src.orders import PaperMarketContext

        # Sample-Daten erstellen
        dates = pd.date_range(start="2024-01-01", periods=10, freq="h")
        signals = pd.Series([0, 1, 1, 1, 0, -1, -1, 0, 1, 0], index=dates)
        prices = pd.Series([50000 + i * 100 for i in range(10)], index=dates)

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50500.0},
            fee_bps=10.0,
            slippage_bps=5.0,
        )

        # Config mit max_position_notional_pct fuer Position-Sizing
        config = ExecutionPipelineConfig(max_position_notional_pct=0.01)
        pipeline = ExecutionPipeline.for_paper(ctx, config)

        results = pipeline.execute_from_signals(
            signals=signals,
            prices=prices,
            symbol="BTC/EUR",
        )

        # Sollte mehrere Executions haben (Entries und Exits)
        assert len(results) > 0
        # Alle sollten filled sein
        assert all(r.status == "filled" for r in results)

    def test_execute_from_signals_tracks_position(self):
        """execute_from_signals() trackt Position korrekt."""
        from src.execution import ExecutionPipeline, ExecutionPipelineConfig
        from src.orders import PaperMarketContext

        # Einfache Entry -> Exit Sequenz
        dates = pd.date_range(start="2024-01-01", periods=5, freq="h")
        signals = pd.Series([0, 1, 1, 0, 0], index=dates)
        prices = pd.Series([50000, 50100, 50200, 50300, 50400], index=dates)

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,
        )

        config = ExecutionPipelineConfig(max_position_notional_pct=0.01)
        pipeline = ExecutionPipeline.for_paper(ctx, config)

        results = pipeline.execute_from_signals(
            signals=signals,
            prices=prices,
            symbol="BTC/EUR",
        )

        # Sollte 2 Executions haben: Entry bei idx 1, Exit bei idx 3
        assert len(results) == 2

        # Erste Order sollte BUY sein
        assert results[0].request.side == "buy"
        # Zweite Order sollte SELL sein
        assert results[1].request.side == "sell"


# ============================================================================
# BacktestEngine Integration Tests
# ============================================================================


class TestBacktestEngineOrderLayerIntegration:
    """Tests fuer BacktestEngine mit Order-Layer."""

    def test_backtest_engine_with_use_order_layer_flag(self):
        """BacktestEngine akzeptiert use_order_layer Flag."""
        from src.backtest.engine import BacktestEngine

        engine = BacktestEngine(use_order_layer=True)
        assert engine.use_order_layer is True

        engine_legacy = BacktestEngine(use_order_layer=False)
        assert engine_legacy.use_order_layer is False

    def test_backtest_engine_run_with_order_layer_method_exists(self):
        """BacktestEngine hat run_with_order_layer() Methode."""
        from src.backtest.engine import BacktestEngine

        engine = BacktestEngine(use_order_layer=True)
        assert hasattr(engine, "run_with_order_layer")
        assert callable(engine.run_with_order_layer)

    def test_backtest_engine_run_with_order_layer_basic(self):
        """BacktestEngine.run_with_order_layer() fuehrt Backtest aus."""
        from src.backtest.engine import BacktestEngine

        # Sample-OHLCV-Daten
        dates = pd.date_range(start="2024-01-01", periods=100, freq="h")
        np.random.seed(42)
        close = 50000 * np.cumprod(1 + np.random.normal(0.0001, 0.01, 100))
        df = pd.DataFrame(
            {
                "open": close * (1 + np.random.uniform(-0.001, 0.001, 100)),
                "high": close * (1 + np.abs(np.random.normal(0, 0.005, 100))),
                "low": close * (1 - np.abs(np.random.normal(0, 0.005, 100))),
                "close": close,
                "volume": np.random.uniform(100, 1000, 100),
            },
            index=dates,
        )

        # Einfache Strategie-Funktion (erwartet df und params dict)
        def simple_strategy(df: pd.DataFrame, params: dict) -> pd.DataFrame:
            """Simple MA-Crossover."""
            fast = df["close"].rolling(5).mean()
            slow = df["close"].rolling(20).mean()
            signal = (fast > slow).astype(int)
            return pd.DataFrame({"signal": signal}, index=df.index)

        engine = BacktestEngine(use_order_layer=True)

        result = engine.run_with_order_layer(
            df=df,
            strategy_signal_fn=simple_strategy,
            strategy_params={},
            symbol="BTC/EUR",
            fee_bps=10.0,
            slippage_bps=5.0,
        )

        # Result sollte Stats haben
        assert result is not None
        assert hasattr(result, "stats")
        assert "total_return" in result.stats
        assert "total_trades" in result.stats

    def test_backtest_engine_execution_results_tracked(self):
        """BacktestEngine trackt execution_results."""
        from src.backtest.engine import BacktestEngine

        # Sample-Daten
        dates = pd.date_range(start="2024-01-01", periods=50, freq="h")
        np.random.seed(42)
        close = 50000 * np.cumprod(1 + np.random.normal(0.0001, 0.01, 50))
        df = pd.DataFrame(
            {
                "open": close,
                "high": close * 1.005,
                "low": close * 0.995,
                "close": close,
                "volume": np.random.uniform(100, 1000, 50),
            },
            index=dates,
        )

        def simple_strategy(df: pd.DataFrame, params: dict) -> pd.DataFrame:
            fast = df["close"].rolling(3).mean()
            slow = df["close"].rolling(10).mean()
            signal = (fast > slow).astype(int)
            return pd.DataFrame({"signal": signal}, index=df.index)

        engine = BacktestEngine(use_order_layer=True)

        engine.run_with_order_layer(
            df=df,
            strategy_signal_fn=simple_strategy,
            strategy_params={},
            symbol="BTC/EUR",
        )

        # execution_results sollte befuellt sein
        assert hasattr(engine, "execution_results")
        assert isinstance(engine.execution_results, list)


# ============================================================================
# Demo-Script Test
# ============================================================================


class TestDemoScript:
    """Tests fuer das Demo-Script."""

    def test_demo_script_imports(self):
        """Demo-Script kann importiert werden."""
        import scripts.demo_order_pipeline_backtest as demo

        assert hasattr(demo, "main")
        assert hasattr(demo, "parse_args")
        assert hasattr(demo, "generate_sample_data")

    def test_demo_script_generate_sample_data(self):
        """generate_sample_data() generiert valide OHLCV-Daten."""
        from scripts.demo_order_pipeline_backtest import generate_sample_data

        df = generate_sample_data(symbol="BTC/EUR", bars=100, timeframe="1h")

        assert len(df) == 100
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

        # OHLCV-Konsistenz
        assert (df["high"] >= df["open"]).all()
        assert (df["high"] >= df["close"]).all()
        assert (df["low"] <= df["open"]).all()
        assert (df["low"] <= df["close"]).all()

    def test_demo_script_parse_args_defaults(self):
        """parse_args() hat sinnvolle Defaults."""
        from scripts.demo_order_pipeline_backtest import parse_args

        args = parse_args([])

        assert args.strategy == "ma_crossover"
        assert args.symbol == "BTC/EUR"
        assert args.timeframe == "1h"
        assert args.bars == 200
        assert args.fee_bps == 10.0
        assert args.slippage_bps == 5.0


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Edge-Case Tests."""

    def test_empty_signals_series(self):
        """Pipeline handhabt leere Signal-Serie."""
        from src.execution import ExecutionPipeline
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        # Leere Serie
        signals = pd.Series([], dtype=float)
        prices = pd.Series([], dtype=float)

        results = pipeline.execute_from_signals(
            signals=signals,
            prices=prices,
            symbol="BTC/EUR",
        )

        assert results == []

    def test_all_zero_signals(self):
        """Pipeline handhabt nur-Null-Signale."""
        from src.execution import ExecutionPipeline
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        dates = pd.date_range(start="2024-01-01", periods=10, freq="h")
        signals = pd.Series([0] * 10, index=dates)
        prices = pd.Series([50000] * 10, index=dates)

        results = pipeline.execute_from_signals(
            signals=signals,
            prices=prices,
            symbol="BTC/EUR",
        )

        # Keine Trades bei nur Null-Signalen
        assert results == []

    def test_order_with_unknown_symbol_rejected(self):
        """Order mit unbekanntem Symbol wird rejected."""
        from src.execution import ExecutionPipeline
        from src.orders import PaperMarketContext, OrderRequest

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},  # Nur BTC/EUR bekannt
            fee_bps=10.0,
        )

        pipeline = ExecutionPipeline.for_paper(ctx)

        order = OrderRequest(
            symbol="UNKNOWN/EUR",  # Nicht in prices
            side="buy",
            quantity=1.0,
        )

        results = pipeline.execute_orders([order])

        # Sollte rejected sein, da kein Preis verfuegbar
        assert len(results) == 1
        assert results[0].status == "rejected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
