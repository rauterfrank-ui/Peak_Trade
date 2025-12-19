"""
Peak_Trade Performance Monitoring Module
========================================
Provides performance monitoring, metrics collection, and profiling utilities
for tracking system performance and identifying bottlenecks.

Module Components:
- PerformanceMonitor: Tracks execution times and performance metrics
- performance_timer: Decorator for timing function execution
- MetricsCollector: Aggregates and reports performance metrics

Usage:
    from src.core.performance import performance_monitor, performance_timer
    
    @performance_timer("my_operation")
    def expensive_operation():
        # Your operation here
        pass
    
    # Get metrics
    metrics = performance_monitor.get_metrics()
    summary = performance_monitor.get_summary()
"""

import logging
import time
import functools
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric for a single operation."""
    name: str
    duration_ms: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    name: str
    count: int
    total_ms: float
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    p95_ms: float
    p99_ms: float


class PerformanceMonitor:
    """
    Performance monitoring and metrics collection.
    
    Tracks execution times for operations and provides summary statistics.
    Thread-safe for concurrent use.
    
    Example:
        monitor = PerformanceMonitor()
        
        with monitor.measure("database_query"):
            # Your operation
            pass
        
        # Or use the decorator
        @monitor.timer("api_call")
        def call_api():
            pass
    """
    
    def __init__(self, max_metrics: int = 10000):
        """
        Initialize performance monitor.
        
        Args:
            max_metrics: Maximum number of metrics to keep in memory
        """
        self.max_metrics = max_metrics
        self._metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self._total_measurements = 0
        
        logger.info(f"PerformanceMonitor initialized with max_metrics={max_metrics}")
    
    def record(self, name: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a performance metric.
        
        Args:
            name: Name of the operation
            duration_ms: Duration in milliseconds
            metadata: Optional metadata about the operation
        """
        metric = PerformanceMetric(
            name=name,
            duration_ms=duration_ms,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        self._metrics[name].append(metric)
        self._total_measurements += 1
        
        # Trim if we exceed max metrics
        if len(self._metrics[name]) > self.max_metrics:
            self._metrics[name] = self._metrics[name][-self.max_metrics:]
        
        # Log slow operations (>1000ms)
        if duration_ms > 1000:
            logger.warning(
                f"Slow operation detected: {name} took {duration_ms:.2f}ms"
            )
    
    def measure(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for measuring operation time.
        
        Args:
            name: Name of the operation
            metadata: Optional metadata about the operation
            
        Example:
            with monitor.measure("database_query"):
                # Your operation
                pass
        """
        return _PerformanceContext(self, name, metadata)
    
    def timer(self, name: str):
        """
        Decorator for timing function execution.
        
        Args:
            name: Name for the metric (defaults to function name)
            
        Example:
            @monitor.timer("api_call")
            def call_api():
                pass
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                metric_name = name or func.__name__
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration_ms = (time.perf_counter() - start) * 1000
                    self.record(metric_name, duration_ms)
            return wrapper
        return decorator
    
    def get_metrics(self, name: Optional[str] = None) -> Dict[str, List[PerformanceMetric]]:
        """
        Get raw metrics.
        
        Args:
            name: Optional name to filter by
            
        Returns:
            Dictionary of metrics by name
        """
        if name:
            return {name: self._metrics.get(name, [])}
        return dict(self._metrics)
    
    def get_summary(self, name: Optional[str] = None) -> Dict[str, MetricSummary]:
        """
        Get summary statistics for metrics.
        
        Args:
            name: Optional name to filter by
            
        Returns:
            Dictionary of metric summaries
        """
        summaries = {}
        
        metrics_to_summarize = (
            {name: self._metrics[name]} if name and name in self._metrics
            else self._metrics
        )
        
        for metric_name, metrics in metrics_to_summarize.items():
            if not metrics:
                continue
            
            durations = [m.duration_ms for m in metrics]
            sorted_durations = sorted(durations)
            
            summaries[metric_name] = MetricSummary(
                name=metric_name,
                count=len(durations),
                total_ms=sum(durations),
                mean_ms=statistics.mean(durations),
                median_ms=statistics.median(durations),
                min_ms=min(durations),
                max_ms=max(durations),
                p95_ms=sorted_durations[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0],
                p99_ms=sorted_durations[int(len(durations) * 0.99)] if len(durations) > 1 else durations[0],
            )
        
        return summaries
    
    def clear(self, name: Optional[str] = None) -> None:
        """
        Clear metrics.
        
        Args:
            name: Optional name to clear, if None clears all
        """
        if name:
            if name in self._metrics:
                self._total_measurements -= len(self._metrics[name])
                del self._metrics[name]
        else:
            self._metrics.clear()
            self._total_measurements = 0
        
        logger.info(f"Cleared metrics for: {name or 'all'}")
    
    def print_summary(self, name: Optional[str] = None) -> None:
        """
        Print a formatted summary of metrics.
        
        Args:
            name: Optional name to filter by
        """
        summaries = self.get_summary(name)
        
        if not summaries:
            print("No metrics recorded")
            return
        
        print(f"\n{'='*80}")
        print(f"Performance Summary ({self._total_measurements} total measurements)")
        print(f"{'='*80}")
        print(f"{'Operation':<30} {'Count':>8} {'Mean':>10} {'Median':>10} {'P95':>10} {'P99':>10} {'Max':>10}")
        print(f"{'-'*80}")
        
        for summary in sorted(summaries.values(), key=lambda s: s.mean_ms, reverse=True):
            print(
                f"{summary.name:<30} {summary.count:>8} "
                f"{summary.mean_ms:>9.2f}ms {summary.median_ms:>9.2f}ms "
                f"{summary.p95_ms:>9.2f}ms {summary.p99_ms:>9.2f}ms "
                f"{summary.max_ms:>9.2f}ms"
            )
        print(f"{'='*80}\n")


class _PerformanceContext:
    """Context manager for performance measurements."""
    
    def __init__(self, monitor: PerformanceMonitor, name: str, metadata: Optional[Dict[str, Any]] = None):
        self.monitor = monitor
        self.name = name
        self.metadata = metadata
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        self.monitor.record(self.name, duration_ms, self.metadata)
        return False


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def performance_timer(name: str):
    """
    Decorator for timing function execution using the global monitor.
    
    Args:
        name: Name for the metric
        
    Example:
        @performance_timer("my_operation")
        def my_function():
            pass
    """
    return performance_monitor.timer(name)
