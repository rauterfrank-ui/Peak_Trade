"""
Observability Module - Phase 0 WP0D

Provides structured logging and metrics for live execution monitoring.

Public API:
- get_logger(): Get structured logger with context fields
- MetricsCollector: Collect and export metrics
- export_metrics_snapshot(): Generate metrics snapshot for evidence
"""

from .logging import (
    get_logger,
    ObservabilityContext,
    set_context,
    clear_context,
)
from .metrics import (
    MetricsCollector,
    MetricType,
    export_metrics_snapshot,
)

__all__ = [
    # Logging
    "get_logger",
    "ObservabilityContext",
    "set_context",
    "clear_context",
    # Metrics
    "MetricsCollector",
    "MetricType",
    "export_metrics_snapshot",
]
