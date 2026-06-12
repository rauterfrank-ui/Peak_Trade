"""Web UI tests for env-gated market registry projection overlay v0 on GET /market."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app
from src.webui.market_surface import build_market_run_projection_display_context
from tests.fixtures.ops import market_registry_projection_overlay_v0 as overlay_fixtures

BOUNDARY_COPY = (
    "Read-only operational projection. This dashboard does not authorize runtime, "
    "testnet, live trading, broker access, exchange access, or strategy execution. "
    "Repo contracts and durable evidence remain canonical."
)

RUN_PROJECTION_MARKERS = (
    "data-market-v0-run-projection=",
    "data-market-v0-run-projection-readonly=",
    "data-market-v0-run-projection-authority=",
)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON", raising=False)
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient, path: str = "/market") -> str:
    response = client.get(path)
    assert response.status_code == 200
    return response.text


def test_gate_disabled_no_run_projection_section(client: TestClient) -> None:
    html = _html(client)
    for marker in RUN_PROJECTION_MARKERS:
        assert marker not in html
    assert BOUNDARY_COPY not in html


def test_gate_enabled_ready_fixture_shows_panel(
    tmp_path: Path, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload_path, _registry_path = overlay_fixtures.write_ready_bundle(tmp_path / "bundle")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON", str(payload_path))
    html = _html(client)

    assert 'data-market-v0-run-projection="true"' in html
    assert 'data-market-v0-run-projection-readonly="true"' in html
    assert 'data-market-v0-run-projection-authority="false"' in html
    assert 'data-market-v0-run-projection-ready="true"' in html
    assert BOUNDARY_COPY in html
    assert "paper_run" in html
    assert "registry.json" in html or "registry" in html.lower()
    assert str(payload_path.resolve()) not in html
    assert str(_registry_path.resolve()) not in html
    assert "source_files" not in html
    assert "/secret/MANIFEST.sha256" not in html


def test_double_play_excludes_run_projection_markers(
    tmp_path: Path, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload_path, _ = overlay_fixtures.write_ready_bundle(tmp_path / "bundle")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON", str(payload_path))
    response = client.get("/market/double-play", follow_redirects=False)
    assert response.status_code == 302
    assert "#double-play" in response.headers["location"]
    html = response.text
    for marker in RUN_PROJECTION_MARKERS:
        assert marker not in html
    assert BOUNDARY_COPY not in html


def test_blocked_payload_renders_without_registry_row(
    tmp_path: Path, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry_path = overlay_fixtures.write_registry(tmp_path / "archive")
    payload_path = overlay_fixtures.write_payload(
        tmp_path / "payload.json",
        registry_path=registry_path,
        projection_ready=False,
        blocked_reason="missing_manifest",
    )
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON", str(payload_path))
    html = _html(client)
    assert 'data-market-v0-run-projection-ready="false"' in html
    assert "missing_manifest" in html
    assert "Registry v1 row (subset)" not in html


def test_consumer_not_allowed_no_registry_row(
    tmp_path: Path, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry_path = overlay_fixtures.write_registry(tmp_path / "archive")
    payload_path = overlay_fixtures.write_payload(
        tmp_path / "payload.json",
        registry_path=registry_path,
        projection_ready=True,
        market_dashboard_allowed=False,
    )
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON", str(payload_path))
    html = _html(client)
    assert 'data-market-v0-run-projection-ready="false"' in html
    assert "Registry v1 row (subset)" not in html


def test_malformed_payload_page_still_renders(
    tmp_path: Path, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = tmp_path / "payload.json"
    bad.write_text("{not-json", encoding="utf-8")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON", str(bad))
    html = _html(client)
    assert 'data-market-readonly="true"' in html
    assert 'data-market-v0-run-projection-authority="false"' in html
    assert 'data-market-v0-run-projection-ready="false"' in html
    lowered = html.lower()
    assert "<form" not in lowered
    assert "<button" not in lowered


def test_build_context_unit_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload_path, _ = overlay_fixtures.write_ready_bundle(tmp_path / "bundle")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON", str(payload_path))
    ctx = build_market_run_projection_display_context()
    assert ctx["section_visible"] is True
    assert ctx["projection_ready"] is True
    assert ctx["status"] == "ready"
    assert ctx["registry_run"]["run_id"] == "paper_run"


def test_build_context_gate_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", raising=False)
    ctx = build_market_run_projection_display_context()
    assert ctx["section_visible"] is False
