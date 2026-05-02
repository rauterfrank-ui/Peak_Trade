"""Double-Play Market Dashboard v1 (GET /market/double-play) — SSR cockpit + DP rail."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_double_play_market_dashboard_v1_cockpit_layout_ok_defaults(client: TestClient) -> None:
    r = client.get("/market/double-play")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    body = r.text

    assert 'data-double-play-market-dashboard-v0="true"' in body
    assert 'data-double-play-market-composition-ssr-v1="true"' in body
    assert 'data-double-play-market-ssr-only="true"' in body
    assert 'data-double-play-market-no-fetch="true"' in body
    assert 'data-double-play-market-readonly="true"' in body
    assert 'data-double-play-market-no-live="true"' in body
    assert 'data-double-play-market-no-orders="true"' in body
    assert 'data-double-play-market-no-authority="true"' in body
    assert 'data-double-play-market-embedded-chart="true"' in body
    assert 'data-double-play-display-ssr-v1="true"' in body
    assert 'data-double-play-market-display-json-link="true"' in body
    assert 'data-double-play-market-market-link="true"' in body

    assert 'data-double-play-market-cockpit-layout-v1-1="true"' in body
    assert 'data-double-play-market-cockpit-header="true"' in body
    assert 'data-double-play-market-cockpit-grid="true"' in body
    assert 'data-double-play-market-cockpit-chart-column="true"' in body
    assert 'data-double-play-market-cockpit-rail="true"' in body
    assert 'data-double-play-market-cockpit-safety-chips="true"' in body
    assert 'data-double-play-market-cockpit-diagnostics-secondary="true"' in body

    assert "Double-Play Market Dashboard v1" in body
    assert "Cockpit" in body
    assert "Snapshot bei Seitenladen" in body

    assert "No orders" in body
    assert "No live" in body
    assert "No strategy authority" in body
    assert "No side-switch authority" in body
    assert "No Scope/Capital approval" in body
    assert "No Risk/KillSwitch override" in body

    assert 'id="chart-dp-market-v0-close"' in body
    assert 'id="dp-market-ssr-payload"' in body

    assert "/market?source=dummy&amp;symbol=BTC%2FEUR&amp;timeframe=1d&amp;limit=120" in body
    assert (
        "/api/market/ohlcv?source=dummy&amp;symbol=BTC%2FEUR&amp;timeframe=1d&amp;limit=120" in body
    )
    assert "/api/master-v2/double-play/dashboard-display.json" in body

    assert 'data-double-play-panel="futures_input"' in body
    assert "display_ready" in body.lower()

    lower = body.lower()
    assert "<form" not in lower
    assert 'method="post"' not in lower
    assert "<button" not in lower
    assert 'type="submit"' not in lower
    assert "fetch(" not in body
    assert "setinterval" not in lower
    assert "live_authorization" not in lower


def test_double_play_market_dashboard_bad_timeframe_422(client: TestClient) -> None:
    r = client.get("/market/double-play", params={"timeframe": "bogus"})
    assert r.status_code == 422
