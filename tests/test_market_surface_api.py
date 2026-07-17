#!/usr/bin/env python3
"""Tests für read-only Market Surface (GET /market reset shell, GET /api/market/ohlcv)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


class TestMarketSurfaceJson:
    def test_ohlcv_dummy_ok_shape(self, client: TestClient) -> None:
        resp = client.get(
            "/api/market/ohlcv",
            params={
                "symbol": "BTC/USD",
                "timeframe": "1h",
                "limit": 30,
                "source": "dummy",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "dummy"
        assert data["symbol"] == "BTC/USD"
        assert data["timeframe"] == "1h"
        assert data["limit_requested"] == 30
        assert data["bars_returned"] == 30
        assert "generated_at_utc" in data
        assert "meta" in data
        assert len(data["bars"]) == 30
        b0 = data["bars"][0]
        assert set(b0.keys()) >= {"ts", "open", "high", "low", "close", "volume"}

    def test_ohlcv_invalid_timeframe_422(self, client: TestClient) -> None:
        r = client.get("/api/market/ohlcv", params={"timeframe": "2h", "source": "dummy"})
        assert r.status_code == 422

    def test_ohlcv_invalid_source_422(self, client: TestClient) -> None:
        r = client.get("/api/market/ohlcv", params={"source": "paper"})
        assert r.status_code == 422


class TestMarketSurfaceHtml:
    def test_market_page_product_surface_ignores_dummy_query(self, client: TestClient) -> None:
        """PR-D: GET /market is the product surface; query params cannot re-enter legacy composition."""
        resp = client.get("/market", params={"source": "dummy", "symbol": "ETHUSDT", "limit": 20})
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        body = resp.text
        assert "Market Dashboard" in body
        assert "ARCHITECTURE RESET IN PROGRESS" not in body
        assert "READ ONLY" in body
        assert 'data-market-dashboard-product-surface-v1="true"' in body
        assert 'data-market-architecture-reset-shell-v1="true"' not in body
        assert 'id="market-v0-shell"' not in body
        assert "source=dummy" not in body
        assert "<form" not in body.lower()
        assert 'type="submit"' not in body.lower()
        assert "<button" not in body.lower()

    def test_market_page_depth_route_and_xhr_absent_on_product_surface(
        self,
        client: TestClient,
    ) -> None:
        resp = client.get("/market", params={"source": "dummy", "symbol": "ETHUSDT", "limit": 20})
        assert resp.status_code == 200
        body = resp.text
        assert "/api/market/depth" not in body
        assert "fetch(" not in body
        assert "XMLHttpRequest" not in body

    def test_market_html_query_noise_still_200(self, client: TestClient) -> None:
        """Invalid legacy query params are ignored; product surface always returns 200."""
        r = client.get("/market", params={"source": "dummy", "timeframe": "bad"})
        assert r.status_code == 200
        assert 'data-market-dashboard-product-surface-v1="true"' in r.text
        assert "ARCHITECTURE RESET IN PROGRESS" not in r.text
        r2 = client.get("/market", params={"source": "invalid", "timeframe": "1d"})
        assert r2.status_code == 200
        assert 'data-market-dashboard-product-surface-v1="true"' in r2.text
        assert "ARCHITECTURE RESET IN PROGRESS" not in r2.text


def test_market_v0_template_file_remains_offline_reset_shell_not_legacy_composition() -> None:
    """Offline market_v0.html remains the PR-A reset shell; legacy markers stay quarantined."""
    tmpl_dir = Path(__file__).resolve().parents[1] / "templates" / "peak_trade_dashboard"
    active = (tmpl_dir / "market_v0.html").read_text(encoding="utf-8")
    assert "ARCHITECTURE RESET IN PROGRESS" in active
    assert "NO TRADING AUTHORITY" in active
    assert 'id="market-v0-shell"' not in active
    assert "{% include" not in active
    quarantine = (
        tmpl_dir / "partials" / "market_v0_legacy_composition_not_routed_v1.html"
    ).read_text(encoding="utf-8")
    assert "LEGACY / NOT ROUTED" in quarantine
    assert 'id="market-v0-shell"' in quarantine
