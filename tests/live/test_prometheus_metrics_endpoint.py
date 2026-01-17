from __future__ import annotations

from pathlib import Path

import pytest

# Skip if FastAPI not installed - must be done before any FastAPI imports
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient


def test_metrics_endpoint_is_prometheus_compatible(tmp_path: Path) -> None:
    from src.live.web.app import create_app

    app = create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    r = client.get("/metrics")
    assert r.status_code == 200
    ct = (r.headers.get("content-type") or "").lower()
    assert "text/plain" in ct
    assert ("# help" in r.text.lower()) or ("# type" in r.text.lower())


def test_metrics_endpoint_strict_mode_requires_prometheus_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    When REQUIRE_PROMETHEUS_CLIENT=1, /metrics must return 503 if prometheus_client
    is missing/unavailable (strict mode).
    """
    from src.live.web.app import create_app

    # Force strict mode
    monkeypatch.setenv("REQUIRE_PROMETHEUS_CLIENT", "1")

    # Make "from prometheus_client import ..." fail regardless of whether the package
    # is installed in the current environment.
    import builtins

    real_import = builtins.__import__

    def blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "prometheus_client" or name.startswith("prometheus_client."):
            raise ModuleNotFoundError("No module named 'prometheus_client'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    app = create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    r = client.get("/metrics")
    assert r.status_code == 503
    assert "prometheus_client required" in r.text.lower()
