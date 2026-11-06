"""
Contract tests for MetricsCollector.export_prometheus() export shape (v0).

Does not duplicate get_summary (#3269) nor MetricSnapshot.to_dict (#3270).

export_prometheus returns (body, content_type): see src/core/metrics.py.
"""

from __future__ import annotations

from src.core.metrics import PROMETHEUS_AVAILABLE, MetricsCollector

_NS = "peak_trade_export_prometheus_contract_v0"


def test_metrics_collector_export_prometheus_contract_v0() -> None:
    collector = MetricsCollector(namespace=_NS)
    out = collector.export_prometheus()

    assert isinstance(out, tuple)
    assert len(out) == 2
    body, content_type = out
    assert isinstance(content_type, str)

    if not PROMETHEUS_AVAILABLE:
        assert body == "# Prometheus client not installed\n"
        assert content_type == "text/plain; charset=utf-8"
        return

    from prometheus_client import CONTENT_TYPE_LATEST

    assert content_type == CONTENT_TYPE_LATEST

    raw = body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body
    assert isinstance(raw, str)
    assert len(raw) > 0

    # Stable markers from exposition text (namespace prefixes metric families).
    assert _NS in raw

    uppercase = raw.upper()
    assert "# HELP" in uppercase or "TYPE " in uppercase
