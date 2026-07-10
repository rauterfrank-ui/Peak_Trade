"""
Contract tests for MetricsCollector.get_summary() top-level shape (v0).

Deterministic resilience summary for offline evidence persistence.
"""

from __future__ import annotations

from src.core.metrics import MetricsCollector

_NS = "peak_trade_contract_shape_v0"
_EXPECTED_KEYS = frozenset(
    {
        "circuit_breaker",
        "empty",
        "health_checks",
        "latency",
        "namespace",
        "operations",
        "rate_limit",
        "schema_version",
    }
)


def test_metrics_collector_get_summary_top_level_shape() -> None:
    collector = MetricsCollector(namespace=_NS)
    summary = collector.get_summary()

    assert isinstance(summary, dict)
    assert frozenset(summary.keys()) == _EXPECTED_KEYS

    assert isinstance(summary["namespace"], str)
    assert summary["namespace"] == _NS

    assert summary["schema_version"] == "metrics_collector_resilience_summary.v0"
    assert summary["empty"] is True

    assert isinstance(summary["circuit_breaker"], dict)
    assert isinstance(summary["rate_limit"], dict)
    assert isinstance(summary["operations"], dict)
    assert isinstance(summary["latency"], dict)
    assert isinstance(summary["health_checks"], list)
