"""Contract tests for MetricsCollector.get_snapshots() limit semantics (v0).

Covers ``limit=0`` (must not behave like ``lst[-0:]``), positive limits, defaults,
and optional metric-name filtering.
"""

from __future__ import annotations

from src.core.metrics import MetricsCollector

_NS = "peak_trade_get_snapshots_limit_contract_v0"


def test_get_snapshots_limit_zero_returns_empty_per_metric_contract_v0() -> None:
    collector = MetricsCollector(namespace=_NS)
    collector.record_operation_success("op_a")
    collector.record_operation_success("op_b")
    collector.record_health_check("hc1", healthy=True)

    out = collector.get_snapshots(limit=0)
    assert out == {
        "operation_success": [],
        "health_check": [],
    }


def test_get_snapshots_limit_zero_with_name_filter_contract_v0() -> None:
    collector = MetricsCollector(namespace=_NS)
    collector.record_operation_success("x")
    collector.record_operation_success("y")

    out = collector.get_snapshots(name="operation_success", limit=0)
    assert out == {"operation_success": []}


def test_get_snapshots_positive_limit_returns_latest_n_in_order_contract_v0() -> None:
    collector = MetricsCollector(namespace=_NS)
    for op in ("op_a", "op_b", "op_c"):
        collector.record_operation_success(op)

    one = collector.get_snapshots(limit=1)["operation_success"]
    assert len(one) == 1
    assert one[0]["labels"]["operation"] == "op_c"

    two = collector.get_snapshots(limit=2)["operation_success"]
    assert len(two) == 2
    assert [r["labels"]["operation"] for r in two] == ["op_b", "op_c"]


def test_get_snapshots_default_limit_returns_all_recorded_contract_v0() -> None:
    collector = MetricsCollector(namespace=_NS)
    for op in ("o1", "o2", "o3"):
        collector.record_operation_success(op)

    default_out = collector.get_snapshots()["operation_success"]
    explicit_out = collector.get_snapshots(limit=100)["operation_success"]
    assert len(default_out) == 3
    assert default_out == explicit_out
    assert [r["labels"]["operation"] for r in default_out] == ["o1", "o2", "o3"]
