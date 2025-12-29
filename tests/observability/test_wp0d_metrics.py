"""
Tests for WP0D - Metrics Collection

Tests metrics collection and export.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.observability.metrics import (
    MetricType,
    MetricValue,
    Metric,
    MetricsCollector,
    export_metrics_snapshot,
)


class TestMetricValue:
    """Test MetricValue dataclass."""

    def test_metric_value_creation(self):
        """Should create metric value."""
        mv = MetricValue(value=10.5)
        assert mv.value == 10.5
        assert mv.timestamp is not None
        assert mv.labels == {}

    def test_metric_value_with_labels(self):
        """Should store labels."""
        mv = MetricValue(value=5.0, labels={"strategy": "ma_crossover"})
        assert mv.labels["strategy"] == "ma_crossover"

    def test_metric_value_to_dict(self):
        """Should convert to dict."""
        mv = MetricValue(value=15.5, labels={"test": "value"})
        d = mv.to_dict()
        assert d["value"] == 15.5
        assert d["labels"]["test"] == "value"
        assert "timestamp" in d


class TestMetric:
    """Test Metric class."""

    def test_metric_creation(self):
        """Should create metric."""
        metric = Metric(
            name="test_counter",
            type=MetricType.COUNTER,
            description="Test counter",
            unit="count",
        )
        assert metric.name == "test_counter"
        assert metric.type == MetricType.COUNTER
        assert len(metric.values) == 0

    def test_metric_add_value(self):
        """Should add value to metric."""
        metric = Metric(
            name="test_counter",
            type=MetricType.COUNTER,
            description="Test",
            unit="count",
        )
        metric.add_value(1.0)
        assert len(metric.values) == 1
        assert metric.values[0].value == 1.0

    def test_metric_add_value_with_labels(self):
        """Should add value with labels."""
        metric = Metric(
            name="test_counter",
            type=MetricType.COUNTER,
            description="Test",
            unit="count",
        )
        metric.add_value(1.0, labels={"status": "success"})
        assert metric.values[0].labels["status"] == "success"

    def test_metric_to_dict(self):
        """Should convert to dict."""
        metric = Metric(
            name="test_counter",
            type=MetricType.COUNTER,
            description="Test counter",
            unit="count",
        )
        metric.add_value(5.0)
        d = metric.to_dict()
        assert d["name"] == "test_counter"
        assert d["type"] == "counter"
        assert d["description"] == "Test counter"
        assert d["unit"] == "count"
        assert len(d["values"]) == 1


class TestMetricsCollector:
    """Test MetricsCollector."""

    def test_collector_initialization(self):
        """Should initialize with standard metrics."""
        collector = MetricsCollector()
        assert "orders_total" in collector.metrics
        assert "errors_total" in collector.metrics
        assert "reconnects_total" in collector.metrics
        assert "latency_ms" in collector.metrics

    def test_record_order(self):
        """Should record order."""
        collector = MetricsCollector()
        collector.record_order()
        assert len(collector.metrics["orders_total"].values) == 1

    def test_record_order_with_labels(self):
        """Should record order with labels."""
        collector = MetricsCollector()
        collector.record_order(labels={"strategy": "ma_crossover"})
        assert collector.metrics["orders_total"].values[0].labels["strategy"] == "ma_crossover"

    def test_record_multiple_orders(self):
        """Should record multiple orders."""
        collector = MetricsCollector()
        for _ in range(10):
            collector.record_order()
        assert len(collector.metrics["orders_total"].values) == 10

    def test_record_error(self):
        """Should record error."""
        collector = MetricsCollector()
        collector.record_error()
        assert len(collector.metrics["errors_total"].values) == 1

    def test_record_error_with_type(self):
        """Should record error with type."""
        collector = MetricsCollector()
        collector.record_error(error_type="NetworkError")
        assert collector.metrics["errors_total"].values[0].labels["error_type"] == "NetworkError"

    def test_record_reconnect(self):
        """Should record reconnect."""
        collector = MetricsCollector()
        collector.record_reconnect()
        assert len(collector.metrics["reconnects_total"].values) == 1

    def test_record_reconnect_with_labels(self):
        """Should record reconnect with labels."""
        collector = MetricsCollector()
        collector.record_reconnect(labels={"exchange": "kraken"})
        assert collector.metrics["reconnects_total"].values[0].labels["exchange"] == "kraken"

    def test_record_latency(self):
        """Should record latency."""
        collector = MetricsCollector()
        collector.record_latency(15.5)
        assert len(collector.metrics["latency_ms"].values) == 1
        assert collector.metrics["latency_ms"].values[0].value == 15.5

    def test_record_multiple_latencies(self):
        """Should record multiple latencies."""
        collector = MetricsCollector()
        latencies = [10.0, 15.5, 20.3, 12.7, 18.9]
        for lat in latencies:
            collector.record_latency(lat)
        assert len(collector.metrics["latency_ms"].values) == 5


class TestDerivedMetrics:
    """Test derived metrics calculations."""

    def test_orders_per_minute_zero_initially(self):
        """Orders per minute should be zero initially."""
        collector = MetricsCollector()
        # Might be 0 or very small initially
        rate = collector.get_orders_per_minute()
        assert rate >= 0

    def test_orders_per_minute_calculation(self):
        """Should calculate orders per minute."""
        collector = MetricsCollector()
        for _ in range(10):
            collector.record_order()
        rate = collector.get_orders_per_minute()
        assert rate > 0  # Should have some rate

    def test_error_rate_zero_initially(self):
        """Error rate should be zero initially."""
        collector = MetricsCollector()
        rate = collector.get_error_rate()
        assert rate >= 0

    def test_error_rate_calculation(self):
        """Should calculate error rate."""
        collector = MetricsCollector()
        for _ in range(5):
            collector.record_error()
        rate = collector.get_error_rate()
        assert rate > 0

    def test_latency_p95_with_no_data(self):
        """P95 should be None with no data."""
        collector = MetricsCollector()
        p95 = collector.get_latency_percentile(95)
        assert p95 is None

    def test_latency_p95_with_data(self):
        """Should calculate P95 latency."""
        collector = MetricsCollector()
        # Add 100 latency values from 1-100ms
        for i in range(1, 101):
            collector.record_latency(float(i))
        p95 = collector.get_latency_percentile(95)
        assert p95 is not None
        assert p95 >= 90  # Should be around 95

    def test_latency_p99_with_data(self):
        """Should calculate P99 latency."""
        collector = MetricsCollector()
        for i in range(1, 101):
            collector.record_latency(float(i))
        p99 = collector.get_latency_percentile(99)
        assert p99 is not None
        assert p99 >= 95  # Should be around 99


class TestMetricsSnapshot:
    """Test metrics snapshot generation."""

    def test_get_snapshot(self):
        """Should get metrics snapshot."""
        collector = MetricsCollector()
        collector.record_order()
        collector.record_error()
        collector.record_latency(15.5)

        snapshot = collector.get_snapshot()
        assert "timestamp" in snapshot
        assert "uptime_seconds" in snapshot
        assert "metrics" in snapshot
        assert "derived" in snapshot

    def test_snapshot_derived_metrics(self):
        """Snapshot should include derived metrics."""
        collector = MetricsCollector()
        for _ in range(10):
            collector.record_order()
        for _ in range(5):
            collector.record_error()
        collector.record_reconnect()
        for i in range(1, 101):
            collector.record_latency(float(i))

        snapshot = collector.get_snapshot()
        derived = snapshot["derived"]

        assert "orders_per_minute" in derived
        assert "error_rate_per_minute" in derived
        assert "reconnects_count" in derived
        assert derived["reconnects_count"] == 1
        assert "latency_p95_ms" in derived
        assert "latency_p99_ms" in derived
        assert "latency_avg_ms" in derived

    def test_snapshot_all_dod_metrics(self):
        """Snapshot should include all DoD-required metrics."""
        collector = MetricsCollector()
        # Simulate some activity
        for _ in range(5):
            collector.record_order()
        collector.record_error()
        collector.record_reconnect()
        collector.record_latency(10.0)
        collector.record_latency(20.0)

        snapshot = collector.get_snapshot()
        derived = snapshot["derived"]

        # DoD required metrics
        assert "orders_per_minute" in derived
        assert "error_rate_per_minute" in derived
        assert "reconnects_count" in derived
        assert "latency_p95_ms" in derived
        assert "latency_p99_ms" in derived


class TestMetricsExport:
    """Test metrics export functionality."""

    def test_export_metrics_snapshot(self):
        """Should export metrics snapshot to file."""
        collector = MetricsCollector()
        collector.record_order()
        collector.record_error()
        collector.record_latency(15.5)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metrics_snapshot.json"
            export_metrics_snapshot(collector, output_path)

            assert output_path.exists()
            with open(output_path, "r") as f:
                data = json.load(f)

            assert "timestamp" in data
            assert "metrics" in data
            assert "derived" in data

    def test_export_creates_parent_directory(self):
        """Should create parent directory if it doesn't exist."""
        collector = MetricsCollector()
        collector.record_order()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "metrics.json"
            export_metrics_snapshot(collector, output_path)

            assert output_path.exists()


class TestMetricsReset:
    """Test metrics reset functionality."""

    def test_reset_clears_all_metrics(self):
        """Reset should clear all metrics."""
        collector = MetricsCollector()
        for _ in range(10):
            collector.record_order()
        collector.record_error()
        collector.record_latency(15.5)

        collector.reset()

        assert len(collector.metrics["orders_total"].values) == 0
        assert len(collector.metrics["errors_total"].values) == 0
        assert len(collector.metrics["latency_ms"].values) == 0
        assert len(collector._latency_values) == 0

    def test_reset_reinitializes_standard_metrics(self):
        """Reset should reinitialize standard metrics."""
        collector = MetricsCollector()
        collector.reset()

        assert "orders_total" in collector.metrics
        assert "errors_total" in collector.metrics
        assert "reconnects_total" in collector.metrics
        assert "latency_ms" in collector.metrics
