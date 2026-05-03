"""
Contract tests for MetricsCollector.get_summary() top-level shape (v0).

Does not validate timestamp parsing (implementation uses isoformat strings).
"""

from __future__ import annotations

from src.core.metrics import PROMETHEUS_AVAILABLE, MetricsCollector

_NS = "peak_trade_contract_shape_v0"
_EXPECTED_KEYS = frozenset({"metrics", "namespace", "prometheus_available", "timestamp"})


def test_metrics_collector_get_summary_top_level_shape() -> None:
    collector = MetricsCollector(namespace=_NS)
    summary = collector.get_summary()

    assert isinstance(summary, dict)
    assert frozenset(summary.keys()) == _EXPECTED_KEYS

    assert isinstance(summary["namespace"], str)
    assert summary["namespace"] == _NS

    assert isinstance(summary["prometheus_available"], bool)
    assert summary["prometheus_available"] is PROMETHEUS_AVAILABLE

    assert isinstance(summary["timestamp"], str)
    assert len(summary["timestamp"]) > 0

    assert isinstance(summary["metrics"], dict)
