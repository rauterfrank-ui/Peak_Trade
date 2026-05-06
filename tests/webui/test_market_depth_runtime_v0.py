"""Market Depth runtime helper v0 — no FastAPI/TestClient coupling."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.webui.market_depth_runtime_v0 import market_depth_json_payload_v0

pytestmark = pytest.mark.web

FIXTURES = project_root / "tests" / "fixtures" / "market_depth_readmodel_v0"


@pytest.fixture(autouse=True)
def _fixed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "PEAK_TRADE_FIXED_GENERATED_AT_UTC",
        "2026-05-02T12:00:00+00:00",
    )


def _clear_md_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", raising=False)


def test_runtime_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_md_env(monkeypatch)
    status, body = market_depth_json_payload_v0()
    assert status == 503
    assert body["runtime_source_status"] == "disabled"
    assert body["generated_at_iso"] == "2026-05-02T12:00:00+00:00"


def test_runtime_builder_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _clear_md_env(monkeypatch)
    bundle = tmp_path / "mal"
    shutil.copytree(FIXTURES / "malformed_levels", bundle)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(bundle))
    status, body = market_depth_json_payload_v0()
    assert status == 503
    assert body["runtime_source_status"] == "builder_error"


def test_runtime_success_minimal(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _clear_md_env(monkeypatch)
    bundle = tmp_path / "bundle"
    shutil.copytree(FIXTURES / "complete_minimal", bundle)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(bundle))
    status, body = market_depth_json_payload_v0()
    assert status == 200
    assert body["symbol"] == "BTC/EUR"
    assert body["runtime_source_status"] == "offline_bundle"
