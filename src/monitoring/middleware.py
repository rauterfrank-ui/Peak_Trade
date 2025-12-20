"""
Performance Monitoring Middleware
==================================
Decorators and utilities for monitoring operation performance
and integrating with Prometheus metrics.
"""

from functools import wraps
import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def monitor_performance(operation: str):
    """
    Decorator to monitor operation performance.
    
    Records the duration of the operation and exports it to Prometheus.
    
    Args:
        operation: Name of the operation being monitored
        
    Returns:
        Decorated function
        
    Example:
        @monitor_performance("database_query")
        def fetch_data():
            # Your operation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                
                # Import here to avoid circular dependencies
                try:
                    from src.monitoring.prometheus_exporter import prometheus_exporter
                    prometheus_exporter.record_request(
                        endpoint=operation,
                        method="success",
                        duration_seconds=duration
                    )
                except ImportError:
                    logger.warning("PrometheusExporter not available, skipping metric recording")
                
                return result
            except Exception as e:
                duration = time.time() - start
                
                # Record error duration
                try:
                    from src.monitoring.prometheus_exporter import prometheus_exporter
                    prometheus_exporter.record_request(
                        endpoint=operation,
                        method="error",
                        duration_seconds=duration
                    )
                except ImportError:
                    logger.warning("PrometheusExporter not available, skipping metric recording")
                
                raise
        return wrapper
    return decorator
