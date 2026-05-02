"""Double-Play Market Dashboard v0 (GET /market/double-play) — static shell, no POST/fetch."""

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


def test_double_play_market_dashboard_v0_ok(client: TestClient) -> None:
    r = client.get("/market/double-play")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    body = r.text
    lower = body.lower()

    assert 'data-double-play-market-dashboard-v0="true"' in body
    assert 'data-double-play-market-readonly="true"' in body
    assert 'data-double-play-market-no-live="true"' in body
    assert 'data-double-play-market-no-orders="true"' in body
    assert 'data-double-play-market-no-authority="true"' in body
    assert 'data-double-play-market-no-fetch="true"' in body
    assert 'data-double-play-market-display-json-link="true"' in body
    assert 'data-double-play-market-market-link="true"' in body

    assert "Double-Play Market Dashboard v0" in body
    assert "Static read-only composition shell" in body
    assert "No orders" in body
    assert "No Live/Testnet action" in body
    assert "No strategy authority" in body
    assert "No side-switch authority" in body
    assert "No Scope/Capital approval" in body
    assert "No Risk/KillSwitch override" in body
    assert "No automatic fetch" in body
    assert "No server-side JSON aggregation" in body
    assert "Market Surface remains the chart surface" in body
    assert "Double-Play display JSON remains display-only" in body

    assert "/market?source=dummy&amp;symbol=BTC/EUR&amp;timeframe=1d&amp;limit=120" in body
    assert (
        "/api/market/ohlcv?source=dummy&amp;symbol=BTC/EUR&amp;timeframe=1d&amp;limit=120" in body
    )
    assert "/api/master-v2/double-play/dashboard-display.json" in body

    assert "<form" not in lower
    assert 'method="post"' not in lower
    assert "<button" not in lower
    assert 'type="submit"' not in lower
    assert "fetch(" not in body
    assert "live_authorization" not in lower
