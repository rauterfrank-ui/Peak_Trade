#!/usr/bin/env python3
"""Tests für read-only Market Surface v0 (GET /market, GET /api/market/ohlcv)."""

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
    def test_market_page_dummy_ok_markers(self, client: TestClient) -> None:
        resp = client.get("/market", params={"source": "dummy", "limit": 20})
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        body = resp.text
        assert 'data-section="market-v0"' in body
        assert 'data-market-surface-v0="true"' in body
        assert 'data-market-readonly="true"' in body
        assert 'data-market-non-authorizing="true"' in body
        assert 'data-market-source-kind="dummy-offline-synthetic"' in body
        assert 'data-market-safety-banner="true"' in body
        assert 'data-market-source="dummy"' in body
        assert 'data-market-bars="20"' in body
        assert 'data-chart="market-v0-close-line"' in body
        assert 'id="market-v0-payload"' in body
        assert "read-only · non-authorizing" in body
        assert "Keine Orders" in body or "keine Orders" in body
        assert "Testnet" in body
        assert "Live" in body
        assert "Capital" in body or "Scope" in body
        assert "KillSwitch" in body or "Risk" in body
        assert "chart.js@4.4.1" in body.lower() or "chart.umd.min.js" in body
        assert 'method="POST"' not in body


def test_market_v0_template_kraken_banner_markers_in_source() -> None:
    """Kraken-Pfad ohne Netzwerk: Banner-Zweig muss im Template existieren."""
    tmpl_path = (
        Path(__file__).resolve().parents[1]
        / "templates"
        / "peak_trade_dashboard"
        / "market_v0.html"
    )
    txt = tmpl_path.read_text(encoding="utf-8")
    assert 'data-market-source-kind="kraken-public-ohlcv-network"' in txt
    assert "Futures" in txt
    assert "read-only · non-authorizing" in txt
