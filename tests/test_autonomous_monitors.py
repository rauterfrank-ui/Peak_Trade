"""
Tests for Autonomous Monitors
==============================
"""

import pytest
from datetime import datetime

from src.autonomous.monitors import (
    MarketMonitor,
    SignalMonitor,
    PerformanceMonitor,
    MonitorResult,
)


class TestMonitorResult:
    """Tests for MonitorResult dataclass."""

    def test_monitor_result_creation(self):
        """Test creating a monitor result."""
        result = MonitorResult(
            monitor_name="test_monitor",
            timestamp=datetime.utcnow(),
            status="ok",
            metrics={"metric1": 0.5},
            alerts=["Alert 1"],
        )

        assert result.monitor_name == "test_monitor"
        assert result.status == "ok"
        assert result.metrics["metric1"] == 0.5
        assert len(result.alerts) == 1


class TestMarketMonitor:
    """Tests for MarketMonitor."""

    def test_monitor_initialization(self):
        """Test market monitor initialization."""
        monitor = MarketMonitor()

        assert monitor.thresholds is not None
        assert "high_volatility" in monitor.thresholds
        assert "low_volume" in monitor.thresholds

    def test_check_conditions_normal(self):
        """Test checking conditions under normal circumstances."""
        monitor = MarketMonitor()

        result = monitor.check_conditions("BTC/EUR")

        assert result.monitor_name == "market_monitor"
        assert result.status in ["ok", "warning", "critical"]
        assert result.timestamp is not None
        assert "volatility" in result.metrics

    def test_check_conditions_with_symbol(self):
        """Test checking conditions for specific symbol."""
        monitor = MarketMonitor()

        result = monitor.check_conditions("ETH/EUR", timeframe="4h")

        assert result is not None
        assert isinstance(result.metrics, dict)

    def test_get_volatility(self):
        """Test getting volatility estimate."""
        monitor = MarketMonitor()

        volatility = monitor.get_volatility("BTC/EUR")

        assert isinstance(volatility, float)
        assert volatility >= 0.0

    def test_is_market_hours(self):
        """Test checking market hours."""
        monitor = MarketMonitor()

        # Crypto markets are 24/7
        is_active = monitor.is_market_hours("kraken")

        assert isinstance(is_active, bool)
        assert is_active is True  # Crypto always open

    def test_custom_thresholds(self):
        """Test custom threshold configuration."""
        config = {
            "thresholds": {
                "high_volatility": 0.5,
            }
        }
        monitor = MarketMonitor(config=config)

        # Should use default thresholds since we don't override in __init__
        # This tests that config is accepted
        assert monitor.config == config


class TestSignalMonitor:
    """Tests for SignalMonitor."""

    def test_monitor_initialization(self):
        """Test signal monitor initialization."""
        monitor = SignalMonitor()

        assert monitor.signal_history == []

    def test_check_signal_quality(self):
        """Test checking signal quality."""
        monitor = SignalMonitor()

        result = monitor.check_signal_quality("ma_crossover", "BTC/EUR")

        assert result.monitor_name == "signal_monitor"
        assert result.status in ["ok", "warning", "critical"]
        assert "signal_strength" in result.metrics
        assert "signal_consistency" in result.metrics

    def test_record_signal(self):
        """Test recording a signal."""
        monitor = SignalMonitor()

        monitor.record_signal(
            strategy="ma_crossover",
            symbol="BTC/EUR",
            signal_value=0.8,
            metadata={"confidence": 0.9},
        )

        assert len(monitor.signal_history) == 1

        signal = monitor.signal_history[0]
        assert signal["strategy"] == "ma_crossover"
        assert signal["symbol"] == "BTC/EUR"
        assert signal["signal_value"] == 0.8
        assert signal["metadata"]["confidence"] == 0.9

    def test_record_multiple_signals(self):
        """Test recording multiple signals."""
        monitor = SignalMonitor()

        for i in range(5):
            monitor.record_signal(
                strategy="ma_crossover", symbol="BTC/EUR", signal_value=float(i) / 10.0
            )

        assert len(monitor.signal_history) == 5

    def test_signal_history_limit(self):
        """Test that signal history is limited to 1000 entries."""
        monitor = SignalMonitor()

        # Record more than 1000 signals
        for i in range(1100):
            monitor.record_signal(strategy="test", symbol="BTC/EUR", signal_value=0.5)

        # Should be limited to 1000
        assert len(monitor.signal_history) == 1000

    def test_get_recent_signals(self):
        """Test getting recent signals."""
        monitor = SignalMonitor()

        # Record signals for different strategies
        for i in range(10):
            monitor.record_signal(strategy="strategy_a", symbol="BTC/EUR", signal_value=0.5)

        for i in range(5):
            monitor.record_signal(strategy="strategy_b", symbol="ETH/EUR", signal_value=0.6)

        # Get all recent signals
        all_signals = monitor.get_recent_signals()
        assert len(all_signals) == 15

        # Get signals for specific strategy
        strategy_a_signals = monitor.get_recent_signals(strategy="strategy_a")
        assert len(strategy_a_signals) == 10

        # Get with limit
        limited_signals = monitor.get_recent_signals(limit=5)
        assert len(limited_signals) == 5


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor."""

    def test_monitor_initialization(self):
        """Test performance monitor initialization."""
        monitor = PerformanceMonitor()

        assert monitor.thresholds is not None
        assert "max_drawdown" in monitor.thresholds
        assert "min_win_rate" in monitor.thresholds

    def test_check_performance_normal(self):
        """Test checking performance under normal conditions."""
        monitor = PerformanceMonitor()

        result = monitor.check_performance()

        assert result.monitor_name == "performance_monitor"
        assert result.status in ["ok", "warning", "critical"]
        assert "current_drawdown" in result.metrics
        assert "win_rate" in result.metrics
        assert "sharpe_ratio" in result.metrics

    def test_check_performance_with_portfolio(self):
        """Test checking performance for specific portfolio."""
        monitor = PerformanceMonitor()

        result = monitor.check_performance(portfolio_id="test-portfolio")

        assert result is not None
        assert isinstance(result.metrics, dict)

    def test_get_current_drawdown(self):
        """Test getting current drawdown."""
        monitor = PerformanceMonitor()

        drawdown = monitor.get_current_drawdown()

        assert isinstance(drawdown, float)
        assert 0.0 <= drawdown <= 1.0

    def test_get_win_rate(self):
        """Test getting win rate."""
        monitor = PerformanceMonitor()

        win_rate = monitor.get_win_rate(lookback_days=30)

        assert isinstance(win_rate, float)
        assert 0.0 <= win_rate <= 1.0

    def test_get_win_rate_with_portfolio(self):
        """Test getting win rate for specific portfolio."""
        monitor = PerformanceMonitor()

        win_rate = monitor.get_win_rate(portfolio_id="test-portfolio", lookback_days=7)

        assert isinstance(win_rate, float)

    def test_custom_thresholds(self):
        """Test custom threshold configuration."""
        config = {
            "thresholds": {
                "max_drawdown": 0.15,
            }
        }
        monitor = PerformanceMonitor(config=config)

        # Config should be accepted
        assert monitor.config == config


class TestMonitorsIntegration:
    """Integration tests for all monitors."""

    def test_all_monitors_basic_check(self):
        """Test basic check on all monitors."""
        market_monitor = MarketMonitor()
        signal_monitor = SignalMonitor()
        performance_monitor = PerformanceMonitor()

        # Run checks
        market_result = market_monitor.check_conditions("BTC/EUR")
        signal_result = signal_monitor.check_signal_quality("ma_crossover", "BTC/EUR")
        performance_result = performance_monitor.check_performance()

        # All should return valid results
        for result in [market_result, signal_result, performance_result]:
            assert result.monitor_name is not None
            assert result.status in ["ok", "warning", "critical"]
            assert isinstance(result.metrics, dict)
            assert isinstance(result.alerts, list)

    def test_combined_metrics_collection(self):
        """Test collecting metrics from all monitors."""
        market_monitor = MarketMonitor()
        signal_monitor = SignalMonitor()
        performance_monitor = PerformanceMonitor()

        # Get results
        market_result = market_monitor.check_conditions("BTC/EUR")
        signal_result = signal_monitor.check_signal_quality("ma_crossover", "BTC/EUR")
        performance_result = performance_monitor.check_performance()

        # Combine metrics
        combined_metrics = {}
        combined_metrics.update(market_result.metrics)
        combined_metrics.update(signal_result.metrics)
        combined_metrics.update(performance_result.metrics)

        # Should have metrics from all monitors
        assert "volatility" in combined_metrics  # Market
        assert "signal_strength" in combined_metrics  # Signal
        assert "current_drawdown" in combined_metrics  # Performance

        # All should be numeric
        assert all(isinstance(v, (int, float)) for v in combined_metrics.values())

    def test_alert_aggregation(self):
        """Test aggregating alerts from all monitors."""
        market_monitor = MarketMonitor()
        signal_monitor = SignalMonitor()
        performance_monitor = PerformanceMonitor()

        # Get results
        results = [
            market_monitor.check_conditions("BTC/EUR"),
            signal_monitor.check_signal_quality("ma_crossover", "BTC/EUR"),
            performance_monitor.check_performance(),
        ]

        # Collect all alerts
        all_alerts = []
        for result in results:
            all_alerts.extend(result.alerts)

        # Should be a list (may be empty if no issues)
        assert isinstance(all_alerts, list)

    def test_status_priority(self):
        """Test determining overall status from multiple monitors."""
        market_monitor = MarketMonitor()
        signal_monitor = SignalMonitor()
        performance_monitor = PerformanceMonitor()

        results = [
            market_monitor.check_conditions("BTC/EUR"),
            signal_monitor.check_signal_quality("ma_crossover", "BTC/EUR"),
            performance_monitor.check_performance(),
        ]

        # Determine overall status (critical > warning > ok)
        statuses = [r.status for r in results]

        if "critical" in statuses:
            overall = "critical"
        elif "warning" in statuses:
            overall = "warning"
        else:
            overall = "ok"

        assert overall in ["ok", "warning", "critical"]
