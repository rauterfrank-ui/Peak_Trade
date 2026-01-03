"""
Tests für Tracking (NoopTracker + BacktestEngine Integration)
==============================================================
Stellt sicher, dass:
1. NoopTracker keine Exceptions wirft
2. BacktestEngine mit NoopTracker identische Ergebnisse liefert wie ohne Tracker
3. Tracking-Interface korrekt funktioniert
"""

import pandas as pd
import pytest

from src.core.tracking import (
    NoopTracker,
    build_tracker_from_config,
    log_backtest_metadata,
)
from src.backtest import BacktestEngine
from src.core.peak_config import PeakConfig


class TestNoopTracker:
    """Tests für NoopTracker."""

    def test_noop_tracker_does_nothing(self):
        """NoopTracker wirft keine Exceptions und macht nichts."""
        tracker = NoopTracker()

        # Alle Methoden sollten ohne Fehler durchlaufen
        tracker.start_run("test_run")
        tracker.log_params({"foo": "bar", "num": 42})
        tracker.log_metrics({"sharpe": 1.8, "win_rate": 0.55})
        tracker.log_artifact("/tmp/nonexistent.txt")
        tracker.end_run()

        # Kein Output, keine Exceptions → Success

    def test_noop_tracker_with_large_data(self):
        """NoopTracker kann große Daten verarbeiten ohne Overhead."""
        tracker = NoopTracker()

        # Große Parameter-Dicts
        large_params = {f"param_{i}": i for i in range(1000)}
        large_metrics = {f"metric_{i}": float(i) for i in range(1000)}

        tracker.start_run("large_data_test")
        tracker.log_params(large_params)
        tracker.log_metrics(large_metrics)
        tracker.end_run()

        # Sollte instant sein (kein I/O)


class TestBuildTrackerFromConfig:
    """Tests für build_tracker_from_config."""

    def test_build_tracker_disabled(self):
        """Wenn tracking.enabled=false → NoopTracker."""
        config = PeakConfig(raw={"tracking": {"enabled": False}})
        tracker = build_tracker_from_config(config)

        assert isinstance(tracker, NoopTracker)

    def test_build_tracker_noop_backend(self):
        """Wenn backend='noop' → NoopTracker."""
        config = PeakConfig(raw={"tracking": {"enabled": True, "backend": "noop"}})
        tracker = build_tracker_from_config(config)

        assert isinstance(tracker, NoopTracker)

    def test_build_tracker_missing_config(self):
        """Wenn tracking-Config fehlt → NoopTracker."""
        config = PeakConfig(raw={})
        tracker = build_tracker_from_config(config)

        assert isinstance(tracker, NoopTracker)

    def test_build_tracker_unknown_backend(self):
        """Wenn unbekanntes Backend → NoopTracker + Warning."""
        config = PeakConfig(raw={"tracking": {"enabled": True, "backend": "unknown"}})
        tracker = build_tracker_from_config(config)

        assert isinstance(tracker, NoopTracker)


class TestLogBacktestMetadata:
    """Tests für log_backtest_metadata Helper."""

    def test_log_backtest_metadata_with_noop(self):
        """log_backtest_metadata mit NoopTracker wirft keine Exceptions."""
        tracker = NoopTracker()

        # Sollte keine Exceptions werfen
        log_backtest_metadata(
            tracker=tracker,
            config={"fast_window": 20, "slow_window": 50},
            strategy_name="ma_crossover",
            commit_sha="abc123",
        )


class TestBacktestEngineWithTracker:
    """Tests für BacktestEngine mit Tracker-Hook."""

    @pytest.fixture
    def sample_data(self):
        """Erzeugt Sample-OHLCV-Daten für Tests."""
        dates = pd.date_range("2023-01-01", periods=100, freq="1h")
        data = {
            "open": [100.0] * 100,
            "high": [105.0] * 100,
            "low": [95.0] * 100,
            "close": [100.0 + i * 0.5 for i in range(100)],  # Aufwärtstrend
            "volume": [1000.0] * 100,
        }
        return pd.DataFrame(data, index=dates)

    def test_backtest_with_noop_tracker_no_exceptions(self, sample_data):
        """BacktestEngine mit NoopTracker wirft keine Exceptions."""
        tracker = NoopTracker()
        engine = BacktestEngine(tracker=tracker, use_execution_pipeline=False)

        # Simple Buy-and-Hold Strategie
        def buy_and_hold(df, params):
            return pd.Series(1, index=df.index)  # Immer long

        result = engine.run_realistic(
            df=sample_data,
            strategy_signal_fn=buy_and_hold,
            strategy_params={"strategy_name": "buy_and_hold"},
        )

        # Sollte erfolgreich durchlaufen
        assert result is not None
        assert "total_return" in result.stats
        assert "sharpe" in result.stats

    def test_backtest_determinism_with_tracker(self, sample_data):
        """BacktestEngine mit Tracker liefert identische Ergebnisse."""

        # Simple MA Crossover
        def ma_crossover(df, params):
            fast = df["close"].rolling(params["fast"]).mean()
            slow = df["close"].rolling(params["slow"]).mean()
            signals = pd.Series(0, index=df.index)
            signals[fast > slow] = 1
            signals[fast <= slow] = -1
            return signals

        params = {"fast": 5, "slow": 20, "stop_pct": 0.02}

        # Run 1: Ohne Tracker
        engine1 = BacktestEngine(tracker=None, use_execution_pipeline=False)
        result1 = engine1.run_realistic(
            df=sample_data, strategy_signal_fn=ma_crossover, strategy_params=params
        )

        # Run 2: Mit NoopTracker
        tracker = NoopTracker()
        engine2 = BacktestEngine(tracker=tracker, use_execution_pipeline=False)
        result2 = engine2.run_realistic(
            df=sample_data, strategy_signal_fn=ma_crossover, strategy_params=params
        )

        # Ergebnisse sollten identisch sein
        assert result1.stats["total_return"] == result2.stats["total_return"]
        assert result1.stats["sharpe"] == result2.stats["sharpe"]
        assert result1.stats["total_trades"] == result2.stats["total_trades"]

        # Equity-Curves sollten identisch sein
        assert (result1.equity_curve == result2.equity_curve).all()

    def test_backtest_with_tracker_execution_pipeline(self, sample_data):
        """BacktestEngine mit Tracker + ExecutionPipeline."""
        tracker = NoopTracker()
        engine = BacktestEngine(tracker=tracker, use_execution_pipeline=True)

        def buy_and_hold(df, params):
            return pd.Series(1, index=df.index)

        result = engine.run_realistic(
            df=sample_data,
            strategy_signal_fn=buy_and_hold,
            strategy_params={"strategy_name": "buy_and_hold"},
            symbol="BTC/EUR",
            fee_bps=10.0,
        )

        # Sollte erfolgreich durchlaufen
        assert result is not None
        assert "total_return" in result.stats
        assert "total_orders" in result.stats  # ExecutionPipeline-spezifisch

    def test_backtest_tracker_none_works(self, sample_data):
        """BacktestEngine mit tracker=None funktioniert (Backward-Compat)."""
        engine = BacktestEngine(tracker=None, use_execution_pipeline=False)

        def buy_and_hold(df, params):
            return pd.Series(1, index=df.index)

        result = engine.run_realistic(
            df=sample_data,
            strategy_signal_fn=buy_and_hold,
            strategy_params={"strategy_name": "buy_and_hold"},
        )

        # Sollte erfolgreich durchlaufen
        assert result is not None
        assert "total_return" in result.stats
