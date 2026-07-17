"""F5 Futures Read-only Market Dashboard — legacy route redirect + PR-E closeout.

Legacy standalone shell `futures_read_only_market_dashboard_v0.html` was deleted in
PR-E (unrendered; `/market/futures` is RedirectResponse only). Embedded F5 layout
HTTP contracts remain deferred; runtime helpers are preserved.
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

LEGACY_F5_MARKERS = (
    'data-f5-market-dashboard-v0="true"',
    'data-f5-market-dashboard-ssr-only="true"',
    'data-f5-no-live-banner="true"',
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_f5_legacy_route_redirects_to_market_anchor(client: TestClient) -> None:
    r = client.get("/market/futures", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/market#futures"


def test_f5_legacy_shell_deleted() -> None:
    assert not (
        project_root / "templates/peak_trade_dashboard/futures_read_only_market_dashboard_v0.html"
    ).exists()


def test_market_product_surface_has_no_legacy_f5_shell(client: TestClient) -> None:
    r = client.get("/market")
    assert r.status_code == 200
    body = r.text
    assert 'data-market-dashboard-product-surface-v1="true"' in body
    for marker in LEGACY_F5_MARKERS:
        assert marker not in body
    lower = body.lower()
    assert "<form" not in lower
    assert 'method="post"' not in lower
    assert "<button" not in lower
    assert 'type="submit"' not in lower


def test_f5_redirect_lands_on_product_surface(client: TestClient) -> None:
    r = client.get("/market/futures", follow_redirects=True)
    assert r.status_code == 200
    assert 'data-market-dashboard-product-surface-v1="true"' in r.text
    for marker in LEGACY_F5_MARKERS:
        assert marker not in r.text
