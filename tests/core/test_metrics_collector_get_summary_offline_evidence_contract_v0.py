"""Contract tests for deterministic offline resilience metrics summary (v0)."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.core.metrics import MetricsCollector, _build_resilience_summary_from_snapshots
from src.research.step29m_ehlers_cycle_filter_v1_offline_economic_baseline_materialization_v0 import (
    METRICS_SUMMARY_FILENAME,
    RESILIENCE_SUMMARY_SCHEMA_VERSION,
    materialize_resilience_metrics_summary_json_v0,
)
from scripts.ops import primary_evidence_retention_v0 as retention

REPO_ROOT = Path(__file__).resolve().parents[2]
_NS = "peak_trade_get_summary_offline_evidence_contract_v0"
_EXPECTED_TOP_LEVEL_KEYS = frozenset(
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


def _populate_resilience_metrics(collector: MetricsCollector) -> None:
    collector.record_circuit_breaker_state_change("cb_a", "closed", "open")
    collector.record_circuit_breaker_failure("cb_a")
    collector.record_rate_limit_hit("rl_a", "fetch")
    collector.record_rate_limit_rejection("rl_a", "fetch")
    collector.update_rate_limit_tokens("rl_a", 7.5)
    collector.record_operation_success("op_a")
    collector.record_operation_failure("op_a", "ValueError")
    collector.record_health_check("db", healthy=True)
    with collector.track_latency("op_a"):
        pass


def test_get_summary_empty_contract_v0() -> None:
    collector = MetricsCollector(namespace=_NS)
    summary = collector.get_summary()

    assert frozenset(summary.keys()) == _EXPECTED_TOP_LEVEL_KEYS
    assert summary["schema_version"] == RESILIENCE_SUMMARY_SCHEMA_VERSION
    assert summary["namespace"] == _NS
    assert summary["empty"] is True
    assert summary["circuit_breaker"] == {"failures": [], "state_changes": []}
    assert summary["rate_limit"] == {"hits": [], "rejections": [], "tokens": []}
    assert summary["operations"] == {"failures": [], "successes": []}
    assert summary["latency"] == {"operations": []}
    assert summary["health_checks"] == []


def test_get_summary_deterministic_and_json_serializable_contract_v0() -> None:
    collector = MetricsCollector(namespace=_NS)
    _populate_resilience_metrics(collector)

    first = collector.get_summary()
    second = collector.get_summary()
    serialized = json.dumps(first, sort_keys=True, separators=(",", ":"))

    assert first == second
    assert json.loads(serialized) == first
    assert first["empty"] is False
    assert first["operations"]["successes"] == [{"count": 1, "operation": "op_a"}]
    assert first["operations"]["failures"] == [
        {"count": 1, "error_type": "ValueError", "operation": "op_a"}
    ]
    assert first["latency"]["operations"][0]["operation"] == "op_a"
    assert first["latency"]["operations"][0]["count"] == 1


def test_get_summary_does_not_mutate_collected_metrics_contract_v0() -> None:
    collector = MetricsCollector(namespace=_NS)
    _populate_resilience_metrics(collector)

    before = collector.get_snapshots()
    for _ in range(3):
        collector.get_summary()
    after = collector.get_snapshots()

    assert before == after


def test_get_summary_does_not_import_prometheus_contract_v0() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import builtins, sys\n"
                "real=builtins.__import__\n"
                "def blocked(name,*a,**k):\n"
                "  if name=='prometheus_client' or name.startswith('prometheus_client.'):\n"
                "    raise ImportError('blocked')\n"
                "  return real(name,*a,**k)\n"
                "builtins.__import__=blocked\n"
                "from src.core.metrics import MetricsCollector\n"
                "summary=MetricsCollector(namespace='blocked').get_summary()\n"
                "assert summary['empty'] is True\n"
                "assert 'prometheus_client' not in sys.modules\n"
                "print('OK')"
            ),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_get_summary_unrelated_initialization_errors_not_swallowed_contract_v0(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_mod = importlib.import_module("src.core.metrics")
    collector = metrics_mod.MetricsCollector(namespace=_NS)

    monkeypatch.setattr(metrics_mod, "_prometheus_spec_available", lambda: True)
    monkeypatch.setattr(metrics_mod, "_PROMETHEUS_IMPORT_CACHE", None)

    def broken_loader():
        raise RuntimeError("unrelated init defect")

    monkeypatch.setattr(metrics_mod, "_load_prometheus_client_module", broken_loader)

    summary = collector.get_summary()
    assert summary["empty"] is True

    with pytest.raises(RuntimeError, match="unrelated init defect"):
        collector.export_prometheus()


def test_materialize_resilience_metrics_summary_json_atomic_and_manifested_contract_v0(
    tmp_path: Path,
) -> None:
    collector = MetricsCollector(namespace=_NS)
    _populate_resilience_metrics(collector)

    payload = materialize_resilience_metrics_summary_json_v0(tmp_path, collector)
    target = tmp_path / METRICS_SUMMARY_FILENAME

    assert target.is_file()
    assert list(tmp_path.glob(".tmp_metrics_summary_*")) == []
    assert json.loads(target.read_text(encoding="utf-8")) == payload

    manifest_rc, _ = retention.finalize_durable_bundle_manifest(tmp_path)
    manifest_text = (tmp_path / "MANIFEST.sha256").read_text(encoding="utf-8")

    assert manifest_rc == 0
    assert METRICS_SUMMARY_FILENAME in manifest_text


def test_build_resilience_summary_from_snapshots_matches_collector_contract_v0() -> None:
    collector = MetricsCollector(namespace=_NS)
    _populate_resilience_metrics(collector)

    with collector.lock:
        snapshot_data = {
            name: list(snapshots_list) for name, snapshots_list in collector.snapshots.items()
        }

    assert _build_resilience_summary_from_snapshots(_NS, snapshot_data) == collector.get_summary()
