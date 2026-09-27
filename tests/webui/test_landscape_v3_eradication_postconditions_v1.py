"""Postconditions: Landscape V3 fully absent; Landscape V2 code route remains."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_v3_routes_and_static_assets_absent() -> None:
    client = TestClient(create_app())
    assert client.get("/market/v3").status_code == 404
    assert client.get("/api/market/v3/snapshot").status_code == 404
    assert client.get("/static/js/market_dashboard_landscape_v3.js").status_code == 404
    assert client.get("/static/css/market_dashboard_landscape_v3.css").status_code == 404


def test_v2_market_route_still_registered() -> None:
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    assert "market_landscape" in response.text or "data-mdl" in response.text


def test_v3_package_paths_removed_from_repo() -> None:
    assert not (REPO_ROOT / "src/webui/market_dashboard_landscape_v3").exists()
    assert not (REPO_ROOT / "src/webui/market_dashboard_landscape_shell_router_v3.py").exists()
    assert not (REPO_ROOT / "templates/peak_trade_dashboard/market_landscape_v3.html").exists()
