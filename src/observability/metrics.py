"""
Metrics Collection - Phase 0 WP0D

Collects and exports metrics for live execution monitoring.

Standard Metrics:
- orders_per_minute: Order submission rate
- error_rate: Error occurrence rate
- reconnects_count: Exchange reconnection count
- latency_p95: 95th percentile latency (ms)
- latency_p99: 99th percentile latency (ms)
"""

import time
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import deque
import statistics


class MetricType(str, Enum):
    """Metric type identifiers."""
    COUNTER = "counter"  # Monotonic counter (errors, orders, reconnects)
    GAUGE = "gauge"  # Point-in-time value (queue size, active orders)
    HISTOGRAM = "histogram"  # Distribution (latency, size)
    RATE = "rate"  # Derived rate metric (orders/min, errors/min)


@dataclass
class MetricValue:
    """Single metric value with timestamp."""
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
        }


@dataclass
class Metric:
    """Metric definition and values."""
    name: str
    type: MetricType
    description: str
    unit: str
    values: List[MetricValue] = field(default_factory=list)

    def add_value(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Add a value to this metric."""
        self.values.append(MetricValue(value=value, labels=labels or {}))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "unit": self.unit,
            "values": [v.to_dict() for v in self.values],
        }


class MetricsCollector:
    """
    Collects metrics for live execution monitoring.

    Usage:
        >>> collector = MetricsCollector()
        >>> collector.record_order()
        >>> collector.record_error()
        >>> collector.record_latency(15.5)  # ms
        >>> snapshot = collector.get_snapshot()
    """

    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.start_time = time.time()

        # Initialize standard metrics
        self._init_standard_metrics()

        # Latency tracking (for percentiles)
        self._latency_values: deque = deque(maxlen=1000)  # Keep last 1000

    def _init_standard_metrics(self) -> None:
        """Initialize standard metrics for Phase 0."""
        self.metrics["orders_total"] = Metric(
            name="orders_total",
            type=MetricType.COUNTER,
            description="Total number of orders submitted",
            unit="count",
        )
        self.metrics["errors_total"] = Metric(
            name="errors_total",
            type=MetricType.COUNTER,
            description="Total number of errors",
            unit="count",
        )
        self.metrics["reconnects_total"] = Metric(
            name="reconnects_total",
            type=MetricType.COUNTER,
            description="Total number of exchange reconnections",
            unit="count",
        )
        self.metrics["latency_ms"] = Metric(
            name="latency_ms",
            type=MetricType.HISTOGRAM,
            description="Latency distribution",
            unit="milliseconds",
        )

    def record_order(self, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record an order submission.

        Args:
            labels: Optional labels (e.g., {"strategy": "ma_crossover"})
        """
        self.metrics["orders_total"].add_value(1.0, labels)

    def record_error(
        self,
        error_type: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record an error occurrence.

        Args:
            error_type: Type of error (optional)
            labels: Optional labels
        """
        if labels is None:
            labels = {}
        if error_type:
            labels["error_type"] = error_type
        self.metrics["errors_total"].add_value(1.0, labels)

    def record_reconnect(self, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record an exchange reconnection.

        Args:
            labels: Optional labels (e.g., {"exchange": "kraken"})
        """
        self.metrics["reconnects_total"].add_value(1.0, labels)

    def record_latency(
        self,
        latency_ms: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a latency measurement.

        Args:
            latency_ms: Latency in milliseconds
            labels: Optional labels
        """
        self.metrics["latency_ms"].add_value(latency_ms, labels)
        self._latency_values.append(latency_ms)

    def get_orders_per_minute(self) -> float:
        """Calculate orders per minute rate."""
        elapsed_minutes = (time.time() - self.start_time) / 60.0
        if elapsed_minutes == 0:
            return 0.0
        total_orders = len(self.metrics["orders_total"].values)
        return total_orders / elapsed_minutes

    def get_error_rate(self) -> float:
        """
        Calculate error rate (errors per minute).

        Returns:
            Errors per minute
        """
        elapsed_minutes = (time.time() - self.start_time) / 60.0
        if elapsed_minutes == 0:
            return 0.0
        total_errors = len(self.metrics["errors_total"].values)
        return total_errors / elapsed_minutes

    def get_latency_percentile(self, percentile: float) -> Optional[float]:
        """
        Calculate latency percentile.

        Args:
            percentile: Percentile to calculate (0-100)

        Returns:
            Latency value at percentile (ms), or None if no data
        """
        if not self._latency_values:
            return None

        sorted_values = sorted(self._latency_values)
        index = int(len(sorted_values) * (percentile / 100.0))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

    def get_snapshot(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.

        Returns:
            Dict with all metrics and derived values
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "metrics": {
                name: metric.to_dict() for name, metric in self.metrics.items()
            },
            "derived": {
                "orders_per_minute": self.get_orders_per_minute(),
                "error_rate_per_minute": self.get_error_rate(),
                "reconnects_count": len(self.metrics["reconnects_total"].values),
                "latency_p95_ms": self.get_latency_percentile(95),
                "latency_p99_ms": self.get_latency_percentile(99),
                "latency_avg_ms": (
                    statistics.mean(self._latency_values)
                    if self._latency_values
                    else None
                ),
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self._init_standard_metrics()
        self._latency_values.clear()
        self.start_time = time.time()


def export_metrics_snapshot(
    collector: MetricsCollector,
    output_path: Path,
) -> None:
    """
    Export metrics snapshot to JSON file.

    Args:
        collector: MetricsCollector instance
        output_path: Path to output JSON file

    Example:
        >>> collector = MetricsCollector()
        >>> # ... record some metrics ...
        >>> export_metrics_snapshot(collector, Path("reports/observability/metrics_snapshot.json"))
    """
    snapshot = collector.get_snapshot()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(snapshot, f, indent=2)
