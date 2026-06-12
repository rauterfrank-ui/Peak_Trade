"""Unified single-page Market Dashboard — GET /market embeds DP + F5; legacy routes redirect."""

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

MARKET_URL = "/market?source=dummy&symbol=BTC/EUR&timeframe=1d&limit=120"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_market_unified_sections_present(client: TestClient) -> None:
    html = client.get(MARKET_URL).text
    assert 'data-market-single-page-unified-v1="true"' in html
    assert 'id="double-play"' in html
    assert 'id="futures"' in html
    assert 'data-market-single-page-section-double-play-v1="true"' in html
    assert 'data-market-single-page-section-futures-v1="true"' in html
    assert 'data-market-safety-status-bar-v1="true"' in html


def test_market_embeds_double_play_markers(client: TestClient) -> None:
    html = client.get(MARKET_URL).text
    assert 'data-double-play-market-dashboard-v0="true"' in html
    assert 'data-double-play-bull-bear-cards-v1="true"' in html
    assert "Candlestick view" in html


def test_market_embeds_futures_markers(client: TestClient) -> None:
    html = client.get(MARKET_URL).text
    assert 'data-f5-market-dashboard-v0="true"' in html
    assert 'data-f5-instrument-metadata-section="true"' in html


def test_legacy_double_play_redirect_preserves_query(client: TestClient) -> None:
    r = client.get("/market/double-play", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["location"]
    assert loc.startswith("/market?")
    assert "source=kraken" in loc
    assert "symbol=BTC" in loc
    assert "timeframe=1d" in loc
    assert "limit=120" in loc
    assert loc.endswith("#double-play")


def test_legacy_futures_redirect_to_anchor(client: TestClient) -> None:
    r = client.get("/market/futures", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/market#futures"


def test_legacy_futures_redirect_preserves_query(client: TestClient) -> None:
    r = client.get("/market/futures?foo=bar", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/market?foo=bar#futures"
