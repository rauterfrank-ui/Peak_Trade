"""Tombstone: legacy Market Dashboard product remains deleted.

Landscape V2 GET /market (Phase 3 shell) is the authorized successor route.
Legacy aliases, packages, templates, and product markers must stay absent.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app

REPO = Path(__file__).resolve().parents[2]
APP_PATH = REPO / "src" / "webui" / "app.py"
BASE_HTML = REPO / "templates" / "peak_trade_dashboard" / "base.html"
TOMBSTONE = REPO / "docs" / "webui" / "MARKET_DASHBOARD_REMOVED.md"
SHELL_ROUTER = REPO / "src" / "webui" / "market_dashboard_landscape_shell_router_v2.py"

DELETED_PACKAGES = (
    "src.webui.market_surface",
    "src.webui.market_dashboard_product_surface_v1",
    "src.webui.market_dashboard_readmodels_v1",
    "src.webui.market_futures_ohlcv_readmodel_v0",
    "src.webui.market_ranking_funnel_readmodel_v0",
    "src.webui.market_visual_operator_surface_v1",
    "src.webui.market_depth_api_v0",
    "src.webui.futures_read_only_market_dashboard_runtime_v0",
)

DELETED_TEMPLATES = (
    "market_dashboard_product_v1.html",
    "market_v0.html",
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_landscape_market_route_returns_200(client: TestClient) -> None:
    response = client.get("/market")
    assert response.status_code == 200
    assert 'data-market-landscape-v2="true"' in response.text
    assert response.history == []


def test_market_aliases_return_404(client: TestClient) -> None:
    for path in (
        "/market/double-play",
        "/market/futures",
        "/api/market/ohlcv",
        "/api/market/depth",
    ):
        response = client.get(path)
        assert response.status_code == 404, path
        assert response.history == []


def test_no_legacy_market_router_registration() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert "create_market_router" not in text
    assert "market_surface" not in text
    assert "market_dashboard_landscape_shell_router_v2" in text
    router = SHELL_ROUTER.read_text(encoding="utf-8")
    assert '@router.get("/market"' in router
    assert "@router.post" not in router


def test_deleted_packages_not_importable() -> None:
    for mod in DELETED_PACKAGES:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(mod)


def test_deleted_templates_absent() -> None:
    tmpl_dir = REPO / "templates" / "peak_trade_dashboard"
    for name in DELETED_TEMPLATES:
        assert not (tmpl_dir / name).exists()
    assert not (REPO / "static" / "css" / "market_dashboard_product_v1.css").exists()
    assert (tmpl_dir / "market_landscape_v2.html").is_file()


def test_no_legacy_nav_resurrect_aliases() -> None:
    html = BASE_HTML.read_text(encoding="utf-8")
    # Global chrome may later link Landscape; must not resurrect legacy APIs.
    assert "/api/market/ohlcv" not in html
    hub = REPO / "templates" / "peak_trade_dashboard" / "observability_hub.html"
    hub_text = hub.read_text(encoding="utf-8")
    assert "/api/market/ohlcv" not in hub_text


def test_no_reset_shell_or_legacy_product_surface_markers(client: TestClient) -> None:
    html = client.get("/market").text.lower()
    assert "architecture reset in progress" not in html
    assert "data-market-architecture-reset-shell-v1" not in html
    assert "data-market-dashboard-product-surface-v1" not in html
    assert "data-market-landscape-v2" in html


def test_tombstone_doc_present() -> None:
    assert TOMBSTONE.is_file()
    text = TOMBSTONE.read_text(encoding="utf-8")
    assert "intentionally" in text.lower()
    assert "GET /market" in text
    assert "&#47;market" not in text
    assert "Landscape V2" in text or "landscape v2" in text.lower()


def test_no_legacy_dashboard_product_tests_or_fixtures_remain() -> None:
    assert not (REPO / "tests" / "fixtures" / "market_futures_ohlcv_readmodel_v0").exists()
    assert not (REPO / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0").exists()
    remaining = sorted((REPO / "tests" / "webui").glob("test_market_dashboard_*.py"))
    assert remaining == [REPO / "tests" / "webui" / "test_market_dashboard_tombstone_v1.py"]
