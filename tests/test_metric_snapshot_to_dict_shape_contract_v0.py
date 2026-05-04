"""
Contract tests for MetricSnapshot.to_dict() shape (v0).

Does not cover MetricsCollector.get_summary() (see #3269 contract tests).
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.metrics import MetricSnapshot

_EXPECTED_KEYS = frozenset({"labels", "name", "timestamp", "value"})


def test_metric_snapshot_to_dict_shape_v0() -> None:
    name = "peak_trade_metric_snapshot_contract_v0"
    value = 42.5
    labels = {"env": "test"}
    ts = datetime(2026, 5, 2, 15, 30, 45, tzinfo=timezone.utc)

    snap = MetricSnapshot(name=name, value=value, labels=labels, timestamp=ts)
    d = snap.to_dict()

    assert isinstance(d, dict)
    assert frozenset(d.keys()) == _EXPECTED_KEYS

    assert isinstance(d["name"], str)
    assert d["name"] == name

    assert d["value"] == value

    assert isinstance(d["labels"], dict)
    assert d["labels"] == labels

    assert isinstance(d["timestamp"], str)
    assert len(d["timestamp"]) > 0
    parsed = datetime.fromisoformat(d["timestamp"])
    assert parsed == ts


def test_metric_snapshot_to_dict_labels_output_isolation_contract_v0() -> None:
    name = "peak_trade_metric_snapshot_labels_isolation_v0"
    value = 1.0
    labels = {"env": "test", "shard": "0"}
    ts = datetime(2026, 5, 4, 12, 0, 0, tzinfo=timezone.utc)
    snap = MetricSnapshot(name=name, value=value, labels=labels, timestamp=ts)
    d = snap.to_dict()

    assert d["labels"] == labels
    assert d["labels"] is not snap.labels
    d["labels"]["env"] = "mutated"
    assert snap.labels["env"] == "test"
