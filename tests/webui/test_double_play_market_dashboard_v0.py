"""Double-Play Market Dashboard — legacy route redirect + PR-E product-surface closeout.

Legacy standalone shell `double_play_market_dashboard_v0.html` was deleted in PR-E
(unrendered; `/market/double-play` is RedirectResponse only). Layout assertions that
expected the old DP cockpit on GET /market are replaced by product-surface guards.
"""

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

LEGACY_DP_MARKERS = (
    'data-double-play-market-dashboard-v0="true"',
    'data-double-play-market-composition-ssr-v1="true"',
    'data-double-play-market-cockpit-layout-v1-1="true"',
    'data-double-play-market-candlestick-v1-2="true"',
    'id="chart-dp-market-v0-close"',
    'id="dp-market-ssr-payload"',
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_double_play_legacy_route_redirects_to_market_anchor(client: TestClient) -> None:
    r = client.get("/market/double-play", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].endswith("#double-play")


def test_double_play_legacy_shell_deleted() -> None:
    assert not (
        project_root / "templates/peak_trade_dashboard/double_play_market_dashboard_v0.html"
    ).exists()


def test_market_product_surface_has_no_legacy_dp_cockpit(client: TestClient) -> None:
    r = client.get("/market?source=dummy&symbol=BTC/EUR&timeframe=1d&limit=120")
    assert r.status_code == 200
    body = r.text
    assert 'data-market-dashboard-product-surface-v1="true"' in body
    for marker in LEGACY_DP_MARKERS:
        assert marker not in body
    lower = body.lower()
    assert "<form" not in lower
    assert 'method="post"' not in lower
    assert "<button" not in lower
    assert 'type="submit"' not in lower
    assert "fetch(" not in body
    assert "setinterval" not in lower
    assert "live_authorization" not in lower


def test_double_play_redirect_lands_on_product_surface(client: TestClient) -> None:
    r = client.get("/market/double-play", follow_redirects=True)
    assert r.status_code == 200
    assert 'data-market-dashboard-product-surface-v1="true"' in r.text
    for marker in LEGACY_DP_MARKERS:
        assert marker not in r.text


def test_double_play_market_dashboard_bad_timeframe_422(client: TestClient) -> None:
    """Legacy path still validates query params before redirect."""
    r = client.get("/market/double-play", params={"timeframe": "bogus"})
    assert r.status_code == 422
