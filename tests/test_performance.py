"""
Tests for Performance Monitoring Module

This module tests the performance monitoring infrastructure including:
- PerformanceMonitor class for metrics collection and analysis
- Context managers and decorators for timing operations
- Statistical summary generation (mean, median, percentiles)
- Global performance monitor singleton
- Integration with various operation patterns

Test patterns:
- Unit tests for individual components
- Integration tests for end-to-end workflows
- Edge case testing for empty data, single items, etc.
- Performance validation for monitoring overhead

Setup requirements:
- No special setup required
- Uses time.sleep() for timing validation (may be slow)
- Some tests may be timing-sensitive
"""

import pytest
import time
from src.core.performance import (
    PerformanceMonitor,
    PerformanceMetric,
    MetricSummary,
    performance_monitor,
    performance_timer,
)


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor class."""

    def test_init(self):
        """Test monitor initialization."""
        monitor = PerformanceMonitor(max_metrics=1000)
        assert monitor.max_metrics == 1000
        assert monitor._total_measurements == 0

    def test_record_metric(self):
        """Test recording a single metric."""
        monitor = PerformanceMonitor()
        monitor.record("test_op", 100.0, {"key": "value"})

        metrics = monitor.get_metrics("test_op")
        assert "test_op" in metrics
        assert len(metrics["test_op"]) == 1
        assert metrics["test_op"][0].duration_ms == 100.0
        assert metrics["test_op"][0].metadata == {"key": "value"}

    def test_record_multiple_metrics(self):
        """Test recording multiple metrics."""
        monitor = PerformanceMonitor()

        for i in range(5):
            monitor.record("test_op", float(i * 10))

        metrics = monitor.get_metrics("test_op")
        assert len(metrics["test_op"]) == 5
        assert monitor._total_measurements == 5

    def test_max_metrics_limit(self):
        """Test that metrics are trimmed when exceeding max."""
        monitor = PerformanceMonitor(max_metrics=3)

        for i in range(5):
            monitor.record("test_op", float(i))

        metrics = monitor.get_metrics("test_op")
        # Should only keep the last 3
        assert len(metrics["test_op"]) == 3
        assert metrics["test_op"][-1].duration_ms == 4.0

    def test_measure_context_manager(self):
        """Test measure context manager."""
        monitor = PerformanceMonitor()

        with monitor.measure("test_op"):
            time.sleep(0.01)  # Sleep for 10ms

        metrics = monitor.get_metrics("test_op")
        assert len(metrics["test_op"]) == 1
        # Should be at least 10ms
        assert metrics["test_op"][0].duration_ms >= 10.0

    def test_measure_with_metadata(self):
        """Test measure with metadata."""
        monitor = PerformanceMonitor()

        with monitor.measure("test_op", metadata={"user": "test"}):
            pass

        metrics = monitor.get_metrics("test_op")
        assert metrics["test_op"][0].metadata == {"user": "test"}

    def test_timer_decorator(self):
        """Test timer decorator."""
        monitor = PerformanceMonitor()

        @monitor.timer("decorated_op")
        def test_func():
            time.sleep(0.01)
            return "result"

        result = test_func()
        assert result == "result"

        metrics = monitor.get_metrics("decorated_op")
        assert len(metrics["decorated_op"]) == 1
        assert metrics["decorated_op"][0].duration_ms >= 10.0

    def test_get_summary(self):
        """Test getting summary statistics."""
        monitor = PerformanceMonitor()

        # Record some metrics with known values
        durations = [10.0, 20.0, 30.0, 40.0, 50.0]
        for duration in durations:
            monitor.record("test_op", duration)

        summary = monitor.get_summary("test_op")
        assert "test_op" in summary

        s = summary["test_op"]
        assert s.count == 5
        assert s.mean_ms == 30.0
        assert s.median_ms == 30.0
        assert s.min_ms == 10.0
        assert s.max_ms == 50.0

    def test_get_summary_percentiles(self):
        """Test percentile calculations in summary."""
        monitor = PerformanceMonitor()

        # Create a distribution
        for i in range(100):
            monitor.record("test_op", float(i))

        summary = monitor.get_summary("test_op")
        s = summary["test_op"]

        assert s.count == 100
        assert s.p95_ms >= 94.0  # 95th percentile should be around 95
        assert s.p99_ms >= 98.0  # 99th percentile should be around 99

    def test_get_summary_all_operations(self):
        """Test getting summary for all operations."""
        monitor = PerformanceMonitor()

        monitor.record("op1", 100.0)
        monitor.record("op2", 200.0)
        monitor.record("op3", 300.0)

        summary = monitor.get_summary()
        assert len(summary) == 3
        assert "op1" in summary
        assert "op2" in summary
        assert "op3" in summary

    def test_clear_specific_metric(self):
        """Test clearing a specific metric."""
        monitor = PerformanceMonitor()

        monitor.record("op1", 100.0)
        monitor.record("op2", 200.0)

        monitor.clear("op1")

        metrics = monitor.get_metrics()
        assert "op1" not in metrics
        assert "op2" in metrics
        assert monitor._total_measurements == 1

    def test_clear_all_metrics(self):
        """Test clearing all metrics."""
        monitor = PerformanceMonitor()

        monitor.record("op1", 100.0)
        monitor.record("op2", 200.0)

        monitor.clear()

        metrics = monitor.get_metrics()
        assert len(metrics) == 0
        assert monitor._total_measurements == 0

    def test_print_summary_no_metrics(self, capsys):
        """Test print_summary with no metrics."""
        monitor = PerformanceMonitor()
        monitor.print_summary()

        captured = capsys.readouterr()
        assert "No metrics recorded" in captured.out

    def test_print_summary_with_metrics(self, capsys):
        """Test print_summary with metrics."""
        monitor = PerformanceMonitor()
        monitor.record("test_op", 100.0)
        monitor.print_summary()

        captured = capsys.readouterr()
        assert "Performance Summary" in captured.out
        assert "test_op" in captured.out


class TestGlobalPerformanceMonitor:
    """Tests for global performance monitor instance."""

    def test_global_monitor_exists(self):
        """Test that global monitor is available."""
        assert performance_monitor is not None
        assert isinstance(performance_monitor, PerformanceMonitor)

    def test_performance_timer_decorator(self):
        """Test global performance_timer decorator."""
        # Clear any existing metrics first
        performance_monitor.clear()

        @performance_timer("global_test")
        def test_func():
            time.sleep(0.01)
            return "result"

        result = test_func()
        assert result == "result"

        metrics = performance_monitor.get_metrics("global_test")
        assert len(metrics["global_test"]) == 1
        assert metrics["global_test"][0].duration_ms >= 10.0

        # Clean up
        performance_monitor.clear()


class TestPerformanceMetric:
    """Tests for PerformanceMetric dataclass."""

    def test_create_metric(self):
        """Test creating a performance metric."""
        metric = PerformanceMetric(
            name="test_op", duration_ms=100.0, timestamp=time.time(), metadata={"key": "value"}
        )

        assert metric.name == "test_op"
        assert metric.duration_ms == 100.0
        assert metric.metadata == {"key": "value"}

    def test_metric_default_metadata(self):
        """Test metric with default empty metadata."""
        metric = PerformanceMetric(name="test_op", duration_ms=100.0, timestamp=time.time())

        assert metric.metadata == {}


class TestMetricSummary:
    """Tests for MetricSummary dataclass."""

    def test_create_summary(self):
        """Test creating a metric summary."""
        summary = MetricSummary(
            name="test_op",
            count=10,
            total_ms=1000.0,
            mean_ms=100.0,
            median_ms=95.0,
            min_ms=50.0,
            max_ms=200.0,
            p95_ms=180.0,
            p99_ms=195.0,
        )

        assert summary.name == "test_op"
        assert summary.count == 10
        assert summary.mean_ms == 100.0
        assert summary.p95_ms == 180.0


class TestPerformanceIntegration:
    """Integration tests for performance monitoring."""

    def test_multiple_operations_tracking(self):
        """Test tracking multiple different operations."""
        monitor = PerformanceMonitor()

        # Simulate different operations
        for i in range(3):
            with monitor.measure("db_query"):
                time.sleep(0.005)

            with monitor.measure("api_call"):
                time.sleep(0.01)

            with monitor.measure("computation"):
                time.sleep(0.002)

        summary = monitor.get_summary()

        # Should have 3 operations
        assert len(summary) == 3
        assert summary["db_query"].count == 3
        assert summary["api_call"].count == 3
        assert summary["computation"].count == 3

        # API calls should be slower than computations
        assert summary["api_call"].mean_ms > summary["computation"].mean_ms

    def test_nested_measurements(self):
        """Test nested performance measurements."""
        monitor = PerformanceMonitor()

        with monitor.measure("outer"):
            time.sleep(0.01)
            with monitor.measure("inner"):
                time.sleep(0.005)
            time.sleep(0.01)

        metrics = monitor.get_metrics()

        # Both should be recorded
        assert len(metrics["outer"]) == 1
        assert len(metrics["inner"]) == 1

        # Outer should take longer than inner
        assert metrics["outer"][0].duration_ms > metrics["inner"][0].duration_ms

    def test_exception_handling_in_context(self):
        """Test that metrics are recorded even when exceptions occur."""
        monitor = PerformanceMonitor()

        try:
            with monitor.measure("failing_op"):
                time.sleep(0.01)
                raise ValueError("Test error")
        except ValueError:
            pass

        # Metric should still be recorded
        metrics = monitor.get_metrics("failing_op")
        assert len(metrics["failing_op"]) == 1
        assert metrics["failing_op"][0].duration_ms >= 10.0
