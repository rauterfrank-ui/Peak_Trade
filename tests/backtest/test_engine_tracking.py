"""
Tests für BacktestEngine + Tracking Integration
================================================
Stellt sicher dass Tracking KEINEN Einfluss auf Backtest-Ergebnisse hat.

**Critical**: "No Behavior Change" muss nachgewiesen werden.
"""

import pandas as pd
import pytest

from src.backtest.engine import BacktestEngine
from src.core.tracking import NoopTracker


@pytest.fixture
def sample_data():
    """Erzeugt deterministische Sample-OHLCV-Daten."""
    dates = pd.date_range("2023-01-01", periods=100, freq="1h")
    data = {
        "open": [100.0] * 100,
        "high": [105.0] * 100,
        "low": [95.0] * 100,
        "close": [100.0 + i * 0.5 for i in range(100)],  # Linear-Trend
        "volume": [1000.0] * 100,
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def simple_strategy():
    """Simple deterministische Strategie."""

    def strategy_fn(df, params):
        # MA-Crossover (deterministisch)
        fast_ma = df["close"].rolling(params["fast"]).mean()
        slow_ma = df["close"].rolling(params["slow"]).mean()
        signals = pd.Series(0, index=df.index)
        signals[fast_ma > slow_ma] = 1
        signals[fast_ma <= slow_ma] = 0
        return signals

    return strategy_fn


class TestTrackingDisabled:
    """Tests: Tracking disabled (tracker=None)."""

    def test_tracking_disabled_no_behavior_change(self, sample_data, simple_strategy):
        """tracker=None: Kein Einfluss auf Backtest-Ergebnis."""
        params = {"fast": 5, "slow": 20, "stop_pct": 0.02}

        # Run 1: Ohne Tracker (explizit None)
        engine1 = BacktestEngine(tracker=None, use_execution_pipeline=False)
        result1 = engine1.run_realistic(
            df=sample_data, strategy_signal_fn=simple_strategy, strategy_params=params
        )

        # Run 2: Ohne Tracker (Default)
        engine2 = BacktestEngine(use_execution_pipeline=False)
        result2 = engine2.run_realistic(
            df=sample_data, strategy_signal_fn=simple_strategy, strategy_params=params
        )

        # Ergebnisse müssen identisch sein
        assert result1.stats["total_return"] == result2.stats["total_return"]
        assert result1.stats["sharpe"] == result2.stats["sharpe"]
        assert result1.stats["total_trades"] == result2.stats["total_trades"]
        assert (result1.equity_curve == result2.equity_curve).all()


class TestTrackingNoop:
    """Tests: Tracking mit NoopTracker."""

    def test_tracking_noop_no_behavior_change(self, sample_data, simple_strategy):
        """NoopTracker: Kein Einfluss auf Backtest-Ergebnis."""
        params = {"fast": 5, "slow": 20, "stop_pct": 0.02}

        # Run 1: Ohne Tracker
        engine1 = BacktestEngine(tracker=None, use_execution_pipeline=False)
        result1 = engine1.run_realistic(
            df=sample_data, strategy_signal_fn=simple_strategy, strategy_params=params
        )

        # Run 2: Mit NoopTracker
        tracker = NoopTracker()
        tracker.start_run("test_run")
        engine2 = BacktestEngine(tracker=tracker, use_execution_pipeline=False)
        result2 = engine2.run_realistic(
            df=sample_data, strategy_signal_fn=simple_strategy, strategy_params=params
        )
        tracker.end_run()

        # Ergebnisse müssen identisch sein
        assert result1.stats["total_return"] == result2.stats["total_return"]
        assert result1.stats["sharpe"] == result2.stats["sharpe"]
        assert result1.stats["max_drawdown"] == result2.stats["max_drawdown"]
        assert result1.stats["total_trades"] == result2.stats["total_trades"]

        # Equity-Curves müssen identisch sein (deterministisch)
        assert (result1.equity_curve == result2.equity_curve).all()

    @pytest.mark.skip(
        reason="BacktestEngine tracker integration not yet implemented - deferred to Phase 2"
    )
    def test_tracker_called_when_enabled(self, sample_data, simple_strategy):
        """NoopTracker: Methoden werden aufgerufen (Spy-Test)."""

        class SpyTracker(NoopTracker):
            """Spy: Zählt Aufrufe."""

            def __init__(self):
                super().__init__()
                self.log_params_calls = 0
                self.log_metrics_calls = 0

            def log_params(self, params):
                self.log_params_calls += 1
                super().log_params(params)

            def log_metrics(self, metrics):
                self.log_metrics_calls += 1
                super().log_metrics(metrics)

        params = {"fast": 5, "slow": 20, "stop_pct": 0.02}

        tracker = SpyTracker()
        tracker.start_run("spy_test")

        engine = BacktestEngine(tracker=tracker, use_execution_pipeline=False)
        result = engine.run_realistic(
            df=sample_data, strategy_signal_fn=simple_strategy, strategy_params=params
        )

        tracker.end_run()

        # Verify: Tracker wurde aufgerufen
        assert tracker.log_params_calls > 0, "log_params() sollte aufgerufen werden"
        assert tracker.log_metrics_calls > 0, "log_metrics() sollte aufgerufen werden"

        # Verify: Result ist trotzdem korrekt
        assert "sharpe" in result.stats
        assert "total_return" in result.stats


class TestTrackingDeterminism:
    """Tests: Determinismus über mehrere Runs."""

    def test_multiple_runs_identical_results(self, sample_data, simple_strategy):
        """Mehrere Runs mit Tracker: Identische Ergebnisse."""
        params = {"fast": 5, "slow": 20, "stop_pct": 0.02}

        results = []
        for i in range(3):
            tracker = NoopTracker()
            tracker.start_run(f"run_{i}")

            engine = BacktestEngine(tracker=tracker, use_execution_pipeline=False)
            result = engine.run_realistic(
                df=sample_data, strategy_signal_fn=simple_strategy, strategy_params=params
            )

            tracker.end_run()
            results.append(result)

        # Alle Ergebnisse müssen identisch sein
        for i in range(1, len(results)):
            assert results[0].stats["total_return"] == results[i].stats["total_return"]
            assert results[0].stats["sharpe"] == results[i].stats["sharpe"]
            assert (results[0].equity_curve == results[i].equity_curve).all()


class TestTrackingExceptionHandling:
    """Tests: Exception Handling im Tracking."""

    def test_tracking_exception_does_not_crash_backtest(self, sample_data, simple_strategy):
        """Tracking-Exception crasht nicht den Backtest."""

        class FailingTracker(NoopTracker):
            """Tracker der immer Exceptions wirft."""

            def log_params(self, params):
                raise RuntimeError("Simulated tracking failure")

            def log_metrics(self, metrics):
                raise RuntimeError("Simulated tracking failure")

        params = {"fast": 5, "slow": 20, "stop_pct": 0.02}

        tracker = FailingTracker()
        tracker.start_run("failing_test")

        engine = BacktestEngine(tracker=tracker, use_execution_pipeline=False)

        # Sollte NICHT crashen trotz Tracker-Exceptions
        result = engine.run_realistic(
            df=sample_data, strategy_signal_fn=simple_strategy, strategy_params=params
        )

        tracker.end_run()

        # Result sollte valide sein
        assert result is not None
        assert "sharpe" in result.stats
        assert "total_return" in result.stats
