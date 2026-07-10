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

from __future__ import annotations

import importlib.util
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_PROMETHEUS_INIT_LOCK = Lock()
_PROMETHEUS_IMPORT_CACHE: Optional[Dict[str, Any]] = None
_PROMETHEUS_IMPORT_FAILED = object()


def get_utc_now() -> datetime:
    """Get current UTC time."""
    if hasattr(datetime, "UTC"):
        return datetime.now(datetime.UTC)
    return datetime.utcnow()


def _prometheus_spec_available() -> bool:
    """Check install surface without importing prometheus_client."""
    return importlib.util.find_spec("prometheus_client") is not None


def _load_prometheus_client_module() -> Optional[Dict[str, Any]]:
    """Import prometheus_client at most once per process; ImportError activates fallback."""
    global _PROMETHEUS_IMPORT_CACHE

    if _PROMETHEUS_IMPORT_CACHE is _PROMETHEUS_IMPORT_FAILED:
        return None
    if _PROMETHEUS_IMPORT_CACHE is not None:
        return _PROMETHEUS_IMPORT_CACHE

    with _PROMETHEUS_INIT_LOCK:
        if _PROMETHEUS_IMPORT_CACHE is _PROMETHEUS_IMPORT_FAILED:
            return None
        if _PROMETHEUS_IMPORT_CACHE is not None:
            return _PROMETHEUS_IMPORT_CACHE

        try:
            from prometheus_client import (
                CONTENT_TYPE_LATEST,
                CollectorRegistry,
                Counter,
                Gauge,
                Histogram,
                generate_latest,
            )
        except ImportError:
            _PROMETHEUS_IMPORT_CACHE = _PROMETHEUS_IMPORT_FAILED
            return None

        _PROMETHEUS_IMPORT_CACHE = {
            "Counter": Counter,
            "Gauge": Gauge,
            "Histogram": Histogram,
            "CollectorRegistry": CollectorRegistry,
            "generate_latest": generate_latest,
            "CONTENT_TYPE_LATEST": CONTENT_TYPE_LATEST,
        }
        return _PROMETHEUS_IMPORT_CACHE


def is_prometheus_available() -> bool:
    """Return True when prometheus_client is installed and importable."""
    if not _prometheus_spec_available():
        return False
    return _load_prometheus_client_module() is not None


def __getattr__(name: str) -> Any:
    if name == "PROMETHEUS_AVAILABLE":
        return is_prometheus_available()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
            "labels": dict(self.labels),
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

    Prometheus initialization is deferred until a Prometheus-backed operation
    is requested on this collector instance. In-memory collection always works.
    """

    def __init__(self, namespace: str = "peak_trade"):
        """
        Initialize metrics collector.

        Args:
            namespace: Namespace prefix for all metrics
        """
        self.namespace = namespace
        self.lock = Lock()
        self._prometheus_init_lock = Lock()
        self._prometheus_initialized = False
        self.registry = None

        # In-memory storage for metrics (fallback when Prometheus not available)
        self.snapshots: Dict[str, list] = {}

    def _ensure_prometheus_backend(self) -> bool:
        """Initialize Prometheus metrics once per collector when client is available."""
        if self._prometheus_initialized:
            return self.registry is not None

        if not _prometheus_spec_available():
            self._prometheus_initialized = True
            return False

        with self._prometheus_init_lock:
            if self._prometheus_initialized:
                return self.registry is not None

            prom = _load_prometheus_client_module()
            if prom is None:
                self._prometheus_initialized = True
                return False

            self.registry = prom["CollectorRegistry"]()
            self._init_prometheus_metrics(prom)
            self._prometheus_initialized = True
            logger.info(
                "MetricsCollector initialized Prometheus backend (namespace: %s)",
                self.namespace,
            )
            return True

    def _init_prometheus_metrics(self, prom: Dict[str, Any]) -> None:
        """Initialize Prometheus metrics using a loaded prometheus_client module."""
        Counter = prom["Counter"]
        Gauge = prom["Gauge"]
        Histogram = prom["Histogram"]

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
        if self._ensure_prometheus_backend():
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
        if self._ensure_prometheus_backend():
            self.circuit_breaker_failures.labels(name=name).inc()

        self._store_snapshot("circuit_breaker_failure", 1.0, {"name": name})

    def record_rate_limit_hit(self, limiter: str, endpoint: str = "") -> None:
        """
        Record a rate limit hit (request made).

        Args:
            limiter: Rate limiter name
            endpoint: Optional endpoint name
        """
        if self._ensure_prometheus_backend():
            self.rate_limit_hits.labels(limiter=limiter, endpoint=endpoint).inc()

        self._store_snapshot("rate_limit_hit", 1.0, {"limiter": limiter, "endpoint": endpoint})

    def record_rate_limit_rejection(self, limiter: str, endpoint: str = "") -> None:
        """
        Record a rate limit rejection.

        Args:
            limiter: Rate limiter name
            endpoint: Optional endpoint name
        """
        if self._ensure_prometheus_backend():
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
        if self._ensure_prometheus_backend():
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

            if self._ensure_prometheus_backend():
                self.request_latency.labels(operation=operation).observe(duration)

            self._store_snapshot("request_latency", duration, {"operation": operation})

    def record_operation_failure(self, operation: str, error_type: str) -> None:
        """
        Record an operation failure.

        Args:
            operation: Operation name
            error_type: Type of error
        """
        if self._ensure_prometheus_backend():
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
        if self._ensure_prometheus_backend():
            self.operation_successes.labels(operation=operation).inc()

        self._store_snapshot("operation_success", 1.0, {"operation": operation})

    def record_health_check(self, check_name: str, healthy: bool) -> None:
        """
        Record health check status.

        Args:
            check_name: Health check name
            healthy: Whether check passed
        """
        if self._ensure_prometheus_backend():
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

            # Limit and convert to dicts.
            # `limit == 0` must return no snapshots; `lst[-0:]` would incorrectly return all.
            return {
                metric_name: [s.to_dict() for s in ([] if limit == 0 else snapshots_list[-limit:])]
                for metric_name, snapshots_list in snapshots.items()
            }

    def export_prometheus(self) -> tuple:
        """
        Export metrics in Prometheus format.

        Returns:
            Tuple of (content, content_type) for HTTP response
        """
        if not self._ensure_prometheus_backend():
            return ("# Prometheus client not installed\n", "text/plain; charset=utf-8")

        prom = _load_prometheus_client_module()
        assert prom is not None
        return prom["generate_latest"](self.registry), prom["CONTENT_TYPE_LATEST"]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics.

        Returns:
            Dictionary with metric summaries
        """
        summary = {
            "namespace": self.namespace,
            "prometheus_available": is_prometheus_available(),
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
    "is_prometheus_available",
]
# PROMETHEUS_AVAILABLE is exported lazily via __getattr__ for deferred probing.
