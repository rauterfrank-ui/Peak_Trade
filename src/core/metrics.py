"""
Peak_Trade Metrics Collection Module
===================================
Centralized Prometheus metrics collection for resilience monitoring.

Provides metrics for:
- Circuit Breaker state changes and failures
- Rate limit hits and rejections
- Request latencies
- Failure rates

Usage:
    from src.core.metrics import metrics

    # Record circuit breaker state change
    metrics.record_circuit_breaker_state_change("backtest", "open")

    # Record rate limit hit
    metrics.record_rate_limit_hit("api_fetch")

    # Record request latency
    with metrics.track_latency("data_fetch"):
        fetch_data()
"""

import logging
import time
from typing import Dict, Optional, Any
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import prometheus_client, but make it optional
try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning(
        "prometheus_client not installed. Metrics will be collected in-memory only. "
        "Install with: pip install prometheus-client"
    )


def get_utc_now() -> datetime:
    """Get current UTC time."""
    if hasattr(datetime, "UTC"):
        return datetime.now(datetime.UTC)
    else:
        return datetime.utcnow()


@dataclass
class MetricSnapshot:
    """Snapshot of a metric at a point in time."""

    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=get_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
        }


class MetricsCollector:
    """
    Centralized metrics collector with Prometheus support.

    Collects metrics for resilience monitoring:
    - Circuit breaker events
    - Rate limiting
    - Request latencies
    - Failure rates

    If prometheus_client is available, exposes metrics for Prometheus scraping.
    Otherwise, stores metrics in-memory for manual inspection.
    """

    def __init__(self, namespace: str = "peak_trade"):
        """
        Initialize metrics collector.

        Args:
            namespace: Namespace prefix for all metrics
        """
        self.namespace = namespace
        self.lock = Lock()

        # In-memory storage for metrics (fallback when Prometheus not available)
        self.snapshots: Dict[str, list] = {}

        if PROMETHEUS_AVAILABLE:
            self.registry = CollectorRegistry()
            self._init_prometheus_metrics()
            logger.info(
                f"MetricsCollector initialized with Prometheus support (namespace: {namespace})"
            )
        else:
            self.registry = None
            logger.info(f"MetricsCollector initialized in-memory mode (namespace: {namespace})")

    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        # Circuit Breaker Metrics
        self.circuit_breaker_state = Gauge(
            f"{self.namespace}_circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=half_open, 2=open)",
            ["name"],
            registry=self.registry,
        )

        self.circuit_breaker_failures = Counter(
            f"{self.namespace}_circuit_breaker_failures_total",
            "Total circuit breaker failures",
            ["name"],
            registry=self.registry,
        )

        self.circuit_breaker_state_changes = Counter(
            f"{self.namespace}_circuit_breaker_state_changes_total",
            "Total circuit breaker state changes",
            ["name", "from_state", "to_state"],
            registry=self.registry,
        )

        # Rate Limiter Metrics
        self.rate_limit_hits = Counter(
            f"{self.namespace}_rate_limit_hits_total",
            "Total rate limit hits",
            ["limiter", "endpoint"],
            registry=self.registry,
        )

        self.rate_limit_rejections = Counter(
            f"{self.namespace}_rate_limit_rejections_total",
            "Total rate limit rejections",
            ["limiter", "endpoint"],
            registry=self.registry,
        )

        self.rate_limit_tokens = Gauge(
            f"{self.namespace}_rate_limit_tokens_available",
            "Available tokens in rate limiter",
            ["limiter"],
            registry=self.registry,
        )

        # Request Latency Metrics
        self.request_latency = Histogram(
            f"{self.namespace}_request_duration_seconds",
            "Request duration in seconds",
            ["operation"],
            registry=self.registry,
            buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
        )

        # Failure Rate Metrics
        self.operation_failures = Counter(
            f"{self.namespace}_operation_failures_total",
            "Total operation failures",
            ["operation", "error_type"],
            registry=self.registry,
        )

        self.operation_successes = Counter(
            f"{self.namespace}_operation_successes_total",
            "Total operation successes",
            ["operation"],
            registry=self.registry,
        )

        # Health Check Metrics
        self.health_check_status = Gauge(
            f"{self.namespace}_health_check_status",
            "Health check status (0=unhealthy, 1=healthy)",
            ["check_name"],
            registry=self.registry,
        )

    def record_circuit_breaker_state_change(
        self, name: str, from_state: str, to_state: str
    ) -> None:
        """
        Record a circuit breaker state change.

        Args:
            name: Circuit breaker name
            from_state: Previous state
            to_state: New state
        """
        if PROMETHEUS_AVAILABLE:
            self.circuit_breaker_state_changes.labels(
                name=name, from_state=from_state, to_state=to_state
            ).inc()

            # Update state gauge (closed=0, half_open=1, open=2)
            state_values = {"closed": 0, "half_open": 1, "open": 2}
            self.circuit_breaker_state.labels(name=name).set(state_values.get(to_state.lower(), 0))

        self._store_snapshot(
            "circuit_breaker_state_change",
            1.0,
            {"name": name, "from_state": from_state, "to_state": to_state},
        )

        logger.info(f"Metric: Circuit breaker '{name}' state change: {from_state} -> {to_state}")

    def record_circuit_breaker_failure(self, name: str) -> None:
        """
        Record a circuit breaker failure.

        Args:
            name: Circuit breaker name
        """
        if PROMETHEUS_AVAILABLE:
            self.circuit_breaker_failures.labels(name=name).inc()

        self._store_snapshot("circuit_breaker_failure", 1.0, {"name": name})

    def record_rate_limit_hit(self, limiter: str, endpoint: str = "") -> None:
        """
        Record a rate limit hit (request made).

        Args:
            limiter: Rate limiter name
            endpoint: Optional endpoint name
        """
        if PROMETHEUS_AVAILABLE:
            self.rate_limit_hits.labels(limiter=limiter, endpoint=endpoint).inc()

        self._store_snapshot("rate_limit_hit", 1.0, {"limiter": limiter, "endpoint": endpoint})

    def record_rate_limit_rejection(self, limiter: str, endpoint: str = "") -> None:
        """
        Record a rate limit rejection.

        Args:
            limiter: Rate limiter name
            endpoint: Optional endpoint name
        """
        if PROMETHEUS_AVAILABLE:
            self.rate_limit_rejections.labels(limiter=limiter, endpoint=endpoint).inc()

        self._store_snapshot(
            "rate_limit_rejection", 1.0, {"limiter": limiter, "endpoint": endpoint}
        )

        logger.warning(f"Metric: Rate limit rejection - limiter: {limiter}, endpoint: {endpoint}")

    def update_rate_limit_tokens(self, limiter: str, tokens: float) -> None:
        """
        Update available tokens gauge.

        Args:
            limiter: Rate limiter name
            tokens: Current token count
        """
        if PROMETHEUS_AVAILABLE:
            self.rate_limit_tokens.labels(limiter=limiter).set(tokens)

        self._store_snapshot("rate_limit_tokens", tokens, {"limiter": limiter})

    @contextmanager
    def track_latency(self, operation: str):
        """
        Context manager to track operation latency.

        Args:
            operation: Operation name

        Example:
            with metrics.track_latency("data_fetch"):
                fetch_data()
        """
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start

            if PROMETHEUS_AVAILABLE:
                self.request_latency.labels(operation=operation).observe(duration)

            self._store_snapshot("request_latency", duration, {"operation": operation})

    def record_operation_failure(self, operation: str, error_type: str) -> None:
        """
        Record an operation failure.

        Args:
            operation: Operation name
            error_type: Type of error
        """
        if PROMETHEUS_AVAILABLE:
            self.operation_failures.labels(operation=operation, error_type=error_type).inc()

        self._store_snapshot(
            "operation_failure", 1.0, {"operation": operation, "error_type": error_type}
        )

    def record_operation_success(self, operation: str) -> None:
        """
        Record an operation success.

        Args:
            operation: Operation name
        """
        if PROMETHEUS_AVAILABLE:
            self.operation_successes.labels(operation=operation).inc()

        self._store_snapshot("operation_success", 1.0, {"operation": operation})

    def record_health_check(self, check_name: str, healthy: bool) -> None:
        """
        Record health check status.

        Args:
            check_name: Health check name
            healthy: Whether check passed
        """
        if PROMETHEUS_AVAILABLE:
            self.health_check_status.labels(check_name=check_name).set(1.0 if healthy else 0.0)

        self._store_snapshot("health_check", 1.0 if healthy else 0.0, {"check_name": check_name})

    def _store_snapshot(self, name: str, value: float, labels: Dict[str, str]) -> None:
        """Store metric snapshot in-memory."""
        with self.lock:
            if name not in self.snapshots:
                self.snapshots[name] = []

            snapshot = MetricSnapshot(name=name, value=value, labels=labels)
            self.snapshots[name].append(snapshot)

            # Keep only last 1000 snapshots per metric
            if len(self.snapshots[name]) > 1000:
                self.snapshots[name] = self.snapshots[name][-1000:]

    def get_snapshots(self, name: Optional[str] = None, limit: int = 100) -> Dict[str, list]:
        """
        Get recent metric snapshots.

        Args:
            name: Optional metric name to filter by
            limit: Maximum snapshots per metric

        Returns:
            Dictionary of metric snapshots
        """
        with self.lock:
            if name:
                snapshots = {name: self.snapshots.get(name, [])}
            else:
                snapshots = dict(self.snapshots)

            # Limit and convert to dicts
            return {
                metric_name: [s.to_dict() for s in snapshots_list[-limit:]]
                for metric_name, snapshots_list in snapshots.items()
            }

    def export_prometheus(self) -> tuple:
        """
        Export metrics in Prometheus format.

        Returns:
            Tuple of (content, content_type) for HTTP response
        """
        if not PROMETHEUS_AVAILABLE:
            return ("# Prometheus client not installed\n", "text/plain; charset=utf-8")

        return generate_latest(self.registry), CONTENT_TYPE_LATEST

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics.

        Returns:
            Dictionary with metric summaries
        """
        summary = {
            "namespace": self.namespace,
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "timestamp": get_utc_now().isoformat(),
            "metrics": {},
        }

        with self.lock:
            for name, snapshots_list in self.snapshots.items():
                if snapshots_list:
                    summary["metrics"][name] = {
                        "count": len(snapshots_list),
                        "latest": snapshots_list[-1].to_dict(),
                    }

        return summary


# Global metrics instance
metrics = MetricsCollector()


__all__ = [
    "MetricsCollector",
    "MetricSnapshot",
    "metrics",
    "PROMETHEUS_AVAILABLE",
]
