"""
Monitoring Module for Peak Trade
==================================

Provides structured logging, performance metrics, and alerting capabilities.

Components:
    - Logger: Structured JSON logging
    - Metrics: Performance metrics collection
    - Alerts: Alert system for critical events
"""

from src.infra.monitoring.logger import get_structured_logger, configure_logging
from src.infra.monitoring.metrics import MetricsCollector, track_performance
from src.infra.monitoring.alerts import AlertManager, AlertSeverity

__all__ = [
    "get_structured_logger",
    "configure_logging",
    "MetricsCollector",
    "track_performance",
    "AlertManager",
    "AlertSeverity",
]
