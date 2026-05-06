"""Market Depth API v0 — GET /api/market/depth (read-only, env-gated server bundle only)."""

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

pytestmark = pytest.mark.web

FIXTURES = project_root / "tests" / "fixtures" / "market_depth_readmodel_v0"

_FORBIDDEN_JSON_KEYS = frozenset(
    {
        "live_authorization",
        "live_ready",
        "testnet_ready",
        "trading_ready",
        "execute",
        "execution",
        "order",
        "orders",
        "approve",
        "approved",
        "promote",
        "sign_off",
        "enable_live",
        "confirm_token",
    }
)


def _collect_object_keys(obj: object, out: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                out.add(k)
            _collect_object_keys(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_object_keys(item, out)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", raising=False)
    return TestClient(create_app())


def _clear_md_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", raising=False)


@pytest.fixture(autouse=True)
def _fixed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "PEAK_TRADE_FIXED_GENERATED_AT_UTC",
        "2026-05-02T12:00:00+00:00",
    )


def test_market_depth_disabled_when_env_unset(client: TestClient) -> None:
    r = client.get("/api/market/depth")
    assert r.status_code == 503
    body = r.json()
    assert body["readmodel_id"] == "market_depth_readmodel.v0"
    assert body["generated_at_iso"] == "2026-05-02T12:00:00+00:00"
    assert body["runtime_source_status"] == "disabled"
    assert "market_depth_source_disabled" in body["warnings"]
    assert body["errors"] == ["runtime_source_unavailable"]
    assert body["stale"] is True
    assert r.headers.get("cache-control") == "no-store"


def test_market_depth_disabled_when_enabled_not_one(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_md_env(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    r = client.get("/api/market/depth")
    assert r.status_code == 503
    assert r.json()["runtime_source_status"] == "disabled"


def test_market_depth_unconfigured_when_enabled_without_root(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_md_env(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    monkeypatch.delenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", raising=False)
    r = client.get("/api/market/depth")
    assert r.status_code == 503
    body = r.json()
    assert body["runtime_source_status"] == "unconfigured"
    assert "market_depth_bundle_root_unconfigured" in body["warnings"]


def test_market_depth_unconfigured_when_root_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_md_env(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    missing = tmp_path / "no_such_bundle"
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(missing))
    r = client.get("/api/market/depth")
    assert r.status_code == 503
    assert r.json()["runtime_source_status"] == "unconfigured"


def test_market_depth_unconfigured_when_root_is_file(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_md_env(monkeypatch)
    fpath = tmp_path / "not_a_dir.txt"
    fpath.write_text("x", encoding="utf-8")
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(fpath.resolve()))
    r = client.get("/api/market/depth")
    assert r.status_code == 503
    assert r.json()["runtime_source_status"] == "unconfigured"


def test_market_depth_503_when_bundle_malformed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_md_env(monkeypatch)
    bundle = tmp_path / "mal"
    shutil.copytree(FIXTURES / "malformed_levels", bundle)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(bundle))
    r = client.get("/api/market/depth")
    assert r.status_code == 503
    body = r.json()
    assert body["runtime_source_status"] == "builder_error"
    assert "market_depth_bundle_build_failed" in body["warnings"]
    assert body["errors"] == ["readmodel_build_failed"]


def test_market_depth_200_complete_minimal_bundle(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_md_env(monkeypatch)
    bundle = tmp_path / "bundle"
    shutil.copytree(FIXTURES / "complete_minimal", bundle)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(bundle))
    r = client.get("/api/market/depth")
    assert r.status_code == 200
    body = r.json()
    assert body["readmodel_id"] == "market_depth_readmodel.v0"
    assert body["symbol"] == "BTC/EUR"
    assert body["source"] == "dummy"
    assert body["limit"] == 3
    assert body["generated_at_iso"] == "2026-05-02T12:00:00+00:00"
    assert body["runtime_source_status"] == "offline_bundle"
    assert body["stale"] is True
    assert body["stale_reason"] == "offline_bundle_scan"
    assert body["depth"]["levels_returned"] == {"bids": 3, "asks": 3}
    assert r.headers.get("cache-control") == "no-store"


def test_market_depth_ignores_query_bundle_root_and_limit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_md_env(monkeypatch)
    bundle = tmp_path / "bundle"
    shutil.copytree(FIXTURES / "complete_minimal", bundle)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(bundle))
    plain = client.get("/api/market/depth")
    evil = client.get("/api/market/depth?bundle_root=/tmp/evil&limit=1&source=kraken")
    assert plain.status_code == 200
    assert evil.status_code == 200
    assert plain.json() == evil.json()


def test_market_depth_response_has_no_authority_keys_success_and_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_md_env(monkeypatch)
    bundle = tmp_path / "bundle"
    shutil.copytree(FIXTURES / "complete_minimal", bundle)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(bundle))
    keys_ok: set[str] = set()
    _collect_object_keys(client.get("/api/market/depth").json(), keys_ok)
    keys_diag: set[str] = set()
    _clear_md_env(monkeypatch)
    _collect_object_keys(client.get("/api/market/depth").json(), keys_diag)

    forbidden_hits_ok = sorted(keys_ok & _FORBIDDEN_JSON_KEYS)
    forbidden_hits_diag = sorted(keys_diag & _FORBIDDEN_JSON_KEYS)
    assert forbidden_hits_ok == []
    assert forbidden_hits_diag == []
