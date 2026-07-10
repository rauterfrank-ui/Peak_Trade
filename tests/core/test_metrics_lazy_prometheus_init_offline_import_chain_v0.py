"""Focused contract tests for lazy Prometheus initialization in src/core/metrics.py (v0)."""

from __future__ import annotations

import importlib
import logging
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
_NS = "peak_trade_lazy_prometheus_init_offline_import_chain_v0"


def _import_with_blocked_prometheus(module_name: str):
    import builtins

    real_import = builtins.__import__

    def blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "prometheus_client" or name.startswith("prometheus_client."):
            raise ImportError("blocked for contract test")
        return real_import(name, globals, locals, fromlist, level)

    builtins.__import__ = blocked_import
    sys.modules.pop("prometheus_client", None)
    for key in list(sys.modules):
        if key == "src.core.metrics" or key.startswith("src.core.metrics."):
            sys.modules.pop(key, None)
        if key == "src.core.resilience_helpers":
            sys.modules.pop(key, None)
        if key == "src.risk.limits":
            sys.modules.pop(key, None)
        if key == "src.backtest.mv2_research_wiring_v1":
            sys.modules.pop(key, None)
    try:
        return importlib.import_module(module_name)
    finally:
        builtins.__import__ = real_import


def test_offline_transitive_import_emits_no_prometheus_warning_v0(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _import_with_blocked_prometheus("src.backtest.mv2_research_wiring_v1")

    assert "prometheus_client" not in sys.modules
    assert not any("prometheus_client not installed" in record.message for record in caplog.records)
    assert not any("prometheus_client not installed" in str(w.message) for w in caught)


def test_metrics_module_import_does_not_import_prometheus_client_v0() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib.util, sys\n"
                "import builtins\n"
                "real=builtins.__import__\n"
                "def blocked(name,*a,**k):\n"
                "  if name=='prometheus_client' or name.startswith('prometheus_client.'):\n"
                "    raise ImportError('blocked')\n"
                "  return real(name,*a,**k)\n"
                "builtins.__import__=blocked\n"
                "import src.core.metrics as m\n"
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


def test_in_memory_metrics_work_without_prometheus_import_v0(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_mod = importlib.import_module("src.core.metrics")
    monkeypatch.setattr(metrics_mod, "_prometheus_spec_available", lambda: False)
    collector = metrics_mod.MetricsCollector(namespace=_NS)

    with collector.track_latency("offline.op"):
        pass
    collector.record_operation_success("offline.op")

    snapshots = collector.get_snapshots("request_latency", limit=1)
    assert snapshots["request_latency"]
    assert collector.export_prometheus()[0] in (
        b"# Prometheus client not installed\n",
        "# Prometheus client not installed\n",
    )


def test_export_prometheus_uses_fallback_without_client_v0(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_mod = importlib.import_module("src.core.metrics")
    monkeypatch.setattr(metrics_mod, "_prometheus_spec_available", lambda: False)
    collector = metrics_mod.MetricsCollector(namespace=_NS)
    body, content_type = collector.export_prometheus()
    raw = body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body
    assert raw == "# Prometheus client not installed\n"
    assert content_type == "text/plain; charset=utf-8"


def test_prometheus_import_attempted_at_most_once_per_process_v0() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib.util\n"
                "if importlib.util.find_spec('prometheus_client') is None:\n"
                "    print('SKIP_NO_PROMETHEUS')\n"
                "    raise SystemExit(0)\n"
                "from src.core.metrics import MetricsCollector\n"
                "import prometheus_client\n"
                "calls = {'n': 0}\n"
                "real_import = __builtins__.__import__\n"
                "def counting(name, *a, **k):\n"
                "    if name == 'prometheus_client':\n"
                "        calls['n'] += 1\n"
                "    return real_import(name, *a, **k)\n"
                "__builtins__.__import__ = counting\n"
                "c = MetricsCollector(namespace='once_test')\n"
                "c.export_prometheus()\n"
                "c.export_prometheus()\n"
                "c.record_operation_success('x')\n"
                "assert calls['n'] == 1\n"
                "print('OK_ONCE')"
            ),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if "SKIP_NO_PROMETHEUS" in proc.stdout:
        pytest.skip("prometheus_client not installed in test interpreter")
    assert proc.returncode == 0, proc.stderr
    assert "OK_ONCE" in proc.stdout


def test_unrelated_initialization_errors_are_not_swallowed_v0(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_mod = importlib.import_module("src.core.metrics")
    collector = metrics_mod.MetricsCollector(namespace=_NS)

    monkeypatch.setattr(metrics_mod, "_prometheus_spec_available", lambda: True)
    monkeypatch.setattr(metrics_mod, "_PROMETHEUS_IMPORT_CACHE", None)

    def broken_loader():
        raise RuntimeError("unrelated init defect")

    monkeypatch.setattr(metrics_mod, "_load_prometheus_client_module", broken_loader)

    with pytest.raises(RuntimeError, match="unrelated init defect"):
        collector.export_prometheus()


def test_public_api_compatibility_preserved_v0() -> None:
    metrics_mod = importlib.import_module("src.core.metrics")
    assert hasattr(metrics_mod, "MetricsCollector")
    assert hasattr(metrics_mod, "MetricSnapshot")
    assert hasattr(metrics_mod, "metrics")
    assert hasattr(metrics_mod, "PROMETHEUS_AVAILABLE")
    assert hasattr(metrics_mod, "is_prometheus_available")
    assert callable(metrics_mod.MetricsCollector().track_latency)
    assert callable(metrics_mod.MetricsCollector().record_operation_success)
    assert callable(metrics_mod.MetricsCollector().export_prometheus)
    assert callable(metrics_mod.MetricsCollector().get_summary)


def test_repeated_in_memory_calls_do_not_repeat_import_or_warnings_v0(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    metrics_mod = importlib.import_module("src.core.metrics")
    monkeypatch.setattr(metrics_mod, "_prometheus_spec_available", lambda: False)
    collector = metrics_mod.MetricsCollector(namespace=_NS)

    for _ in range(5):
        collector.record_operation_success("repeat.op")

    assert not any("prometheus_client not installed" in record.message for record in caplog.records)
