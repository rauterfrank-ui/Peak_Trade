"""
Performance Metrics Collector
===============================

Collects and aggregates performance metrics for monitoring and analysis.

Usage:
    from src.infra.monitoring import MetricsCollector, track_performance
    
    # Using decorator
    @track_performance("api_call")
    def call_api():
        # API call here
        pass
    
    # Direct usage
    metrics = MetricsCollector()
    metrics.record_latency("operation", 0.123)
    metrics.increment_counter("requests")
"""

from __future__ import annotations

import functools
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class LatencyStats:
    """Statistics for latency measurements."""
    
    count: int = 0
    total: float = 0.0
    min: float = float("inf")
    max: float = 0.0
    
    @property
    def mean(self) -> float:
        """Calculate mean latency."""
        return self.total / self.count if self.count > 0 else 0.0
    
    def record(self, latency: float) -> None:
        """Record a latency measurement."""
        self.count += 1
        self.total += latency
        self.min = min(self.min, latency)
        self.max = max(self.max, latency)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "mean_ms": self.mean * 1000,
            "min_ms": self.min * 1000 if self.min != float("inf") else 0,
            "max_ms": self.max * 1000,
            "total_seconds": self.total,
        }


class MetricsCollector:
    """
    Collects and aggregates performance metrics.
    
    Thread-safe metrics collection for monitoring application performance.
    """
    
    def __init__(self, name: str = "default"):
        """
        Initialize metrics collector.
        
        Args:
            name: Name for this collector
        """
        self.name = name
        self._latencies: Dict[str, LatencyStats] = defaultdict(LatencyStats)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._lock = Lock()
    
    def record_latency(self, metric_name: str, latency_seconds: float) -> None:
        """
        Record a latency measurement.
        
        Args:
            metric_name: Name of the metric
            latency_seconds: Latency in seconds
        """
        with self._lock:
            self._latencies[metric_name].record(latency_seconds)
    
    def increment_counter(self, counter_name: str, value: int = 1) -> None:
        """
        Increment a counter.
        
        Args:
            counter_name: Name of the counter
            value: Amount to increment by
        """
        with self._lock:
            self._counters[counter_name] += value
    
    def set_gauge(self, gauge_name: str, value: float) -> None:
        """
        Set a gauge value.
        
        Args:
            gauge_name: Name of the gauge
            value: Value to set
        """
        with self._lock:
            self._gauges[gauge_name] = value
    
    def get_latency_stats(self, metric_name: str) -> Optional[LatencyStats]:
        """
        Get latency statistics for a metric.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            LatencyStats if available, None otherwise
        """
        with self._lock:
            return self._latencies.get(metric_name)
    
    def get_counter(self, counter_name: str) -> int:
        """
        Get counter value.
        
        Args:
            counter_name: Name of the counter
            
        Returns:
            Counter value
        """
        with self._lock:
            return self._counters.get(counter_name, 0)
    
    def get_gauge(self, gauge_name: str) -> Optional[float]:
        """
        Get gauge value.
        
        Args:
            gauge_name: Name of the gauge
            
        Returns:
            Gauge value if available, None otherwise
        """
        with self._lock:
            return self._gauges.get(gauge_name)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.
        
        Returns:
            Dictionary of all metrics
        """
        with self._lock:
            return {
                "name": self.name,
                "timestamp": datetime.now().isoformat(),
                "latencies": {
                    name: stats.to_dict()
                    for name, stats in self._latencies.items()
                },
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._latencies.clear()
            self._counters.clear()
            self._gauges.clear()


# Global metrics collector
_global_metrics = MetricsCollector(name="global")


def get_global_metrics() -> MetricsCollector:
    """
    Get the global metrics collector.
    
    Returns:
        Global MetricsCollector instance
    """
    return _global_metrics


def track_performance(metric_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to track function performance.
    
    Args:
        metric_name: Name for the performance metric
        
    Returns:
        Decorated function
        
    Example:
        @track_performance("database_query")
        def query_database():
            # Database query
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                _global_metrics.record_latency(metric_name, elapsed)
                _global_metrics.increment_counter(f"{metric_name}_calls")
        
        return wrapper
    
    return decorator
