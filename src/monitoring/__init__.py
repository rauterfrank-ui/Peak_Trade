"""
Peak_Trade Monitoring Module
=============================
Provides monitoring infrastructure including Prometheus metrics export,
performance tracking, and integration with existing resilience patterns.

Components:
- PrometheusExporter: Metrics export for Prometheus
- Middleware: Decorators for performance monitoring
"""

from src.monitoring.prometheus_exporter import PrometheusExporter, prometheus_exporter
from src.monitoring.middleware import monitor_performance

__all__ = [
    "PrometheusExporter",
    "prometheus_exporter",
    "monitor_performance",
]
