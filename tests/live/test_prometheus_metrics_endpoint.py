from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

# Skip if FastAPI not installed - must be done before any FastAPI imports
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient


def test_metrics_route_absent_when_disabled_or_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Default behavior: /metrics is not registered unless explicitly enabled AND prometheus_client exists.
    This test must be stable even when prometheus_client is not installed.
    """
    monkeypatch.setenv("PEAK_TRADE_PROMETHEUS_ENABLED", "0")

    from src.live.web.app import create_app

    app = create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    r = client.get("/metrics")
    assert r.status_code == 404


def test_metrics_route_present_when_enabled_and_prometheus_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Simulate prometheus_client availability via a small fake module, and verify:
    - /metrics exists when PEAK_TRADE_PROMETHEUS_ENABLED=1
    - middleware increments the request counter
    """
    store = {"requests_total": 0, "in_flight": 0}

    class _Counter:
        def __init__(self, name: str, doc: str, labelnames=()):
            self._name = name
            self._labelnames = tuple(labelnames)

        def labels(self, **_labels):
            class _L:
                def inc(self_inner, amount: float = 1.0) -> None:
                    store["requests_total"] += int(amount)

            return _L()

    class _Histogram:
        def __init__(self, name: str, doc: str, labelnames=(), buckets=()):
            self._name = name

        def labels(self, **_labels):
            class _L:
                def observe(self_inner, _val: float) -> None:
                    return None

            return _L()

    class _Gauge:
        def __init__(self, name: str, doc: str):
            self._name = name

        def inc(self) -> None:
            store["in_flight"] += 1

        def dec(self) -> None:
            store["in_flight"] = max(0, store["in_flight"] - 1)

    prom = types.ModuleType("prometheus_client")
    prom.Counter = _Counter  # type: ignore[attr-defined]
    prom.Histogram = _Histogram  # type: ignore[attr-defined]
    prom.Gauge = _Gauge  # type: ignore[attr-defined]
    prom.CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"  # type: ignore[attr-defined]

    expo = types.ModuleType("prometheus_client.exposition")

    def _generate_latest() -> bytes:
        return (
            "# TYPE peak_trade_http_requests_total counter\n"
            f"peak_trade_http_requests_total {store['requests_total']}\n"
        ).encode("utf-8")

    expo.generate_latest = _generate_latest  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "prometheus_client", prom)
    monkeypatch.setitem(sys.modules, "prometheus_client.exposition", expo)
    monkeypatch.setenv("PEAK_TRADE_PROMETHEUS_ENABLED", "1")

    import src.live.web.metrics_prom as metrics_prom
    import src.live.web.app as app_mod

    importlib.reload(metrics_prom)
    importlib.reload(app_mod)

    app = app_mod.create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    # trigger at least one request
    assert client.get("/health").status_code == 200

    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    assert "peak_trade_http_requests_total" in r.text
    assert store["requests_total"] >= 1
