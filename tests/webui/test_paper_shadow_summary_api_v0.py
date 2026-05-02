"""Paper/Shadow Summary API v0 — GET /api/observability/paper-shadow-summary (read-only, env-gated)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.paper_shadow_summary_readmodel_v0 import SCHEMA_VERSION

pytestmark = pytest.mark.web

FIXTURES = project_root / "tests" / "fixtures" / "paper_shadow_summary_readmodel_v0"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_BUNDLE_ROOT", raising=False)
    return TestClient(create_app())


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_BUNDLE_ROOT", raising=False)


@pytest.fixture(autouse=True)
def _fixed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "PEAK_TRADE_FIXED_GENERATED_AT_UTC",
        "2026-05-02T12:00:00+00:00",
    )


def test_summary_disabled_when_env_unset(client: TestClient) -> None:
    r = client.get("/api/observability/paper-shadow-summary")
    assert r.status_code == 503
    body = r.json()
    assert body["runtime_source_status"] == "disabled"
    assert "paper_shadow_summary_source_disabled" in body["warnings"]
    assert body["errors"] == ["runtime_source_unavailable"]
    assert body["schema_version"] == SCHEMA_VERSION
    assert body["generated_at_utc"] == "2026-05-02T12:00:00+00:00"


def test_summary_disabled_when_enabled_not_one(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_ENABLED", "0")
    r = client.get("/api/observability/paper-shadow-summary")
    assert r.status_code == 503
    assert r.json()["runtime_source_status"] == "disabled"


def test_summary_unconfigured_when_enabled_without_root(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_ENABLED", "1")
    monkeypatch.delenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_BUNDLE_ROOT", raising=False)
    r = client.get("/api/observability/paper-shadow-summary")
    assert r.status_code == 503
    body = r.json()
    assert body["runtime_source_status"] == "unconfigured"
    assert "paper_shadow_summary_bundle_root_unconfigured" in body["warnings"]


def test_summary_unconfigured_when_root_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_ENABLED", "1")
    missing = tmp_path / "no_such_bundle"
    monkeypatch.setenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_BUNDLE_ROOT", str(missing))
    r = client.get("/api/observability/paper-shadow-summary")
    assert r.status_code == 503
    assert r.json()["runtime_source_status"] == "unconfigured"


def test_summary_200_complete_minimal_bundle(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_env(monkeypatch)
    bundle = tmp_path / "bundle"
    shutil.copytree(FIXTURES / "complete_minimal", bundle)
    monkeypatch.setenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_PAPER_SHADOW_SUMMARY_BUNDLE_ROOT", str(bundle))
    r = client.get("/api/observability/paper-shadow-summary")
    assert r.status_code == 200
    body = r.json()
    assert body["schema_version"] == SCHEMA_VERSION
    assert body["stale"] is True
    assert body["manifest_present"] is True
    assert body["paper_fills_present"] is True
    assert body["artifact_count"] == 10
    assert body["paper_fill_count"] == 2
    assert "runtime_source_status" not in body
