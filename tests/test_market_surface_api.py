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
        resp = client.get("/market", params={"source": "dummy", "symbol": "ETHUSDT", "limit": 20})
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        body = resp.text
        assert 'data-section="market-v0"' in body
        assert 'data-market-surface-v0="true"' in body
        assert 'data-market-v1-dashboard-shell="true"' in body
        assert 'data-market-v1-context="true"' in body
        assert 'data-market-v1-readonly-banner="true"' in body
        assert body.count('data-market-v1-stat-card="true"') >= 6
        assert 'data-market-v1-api-reference="true"' in body
        assert 'data-market-v0-surface-links="true"' in body
        assert 'data-market-v0-dashboard-surface="true"' in body
        assert 'data-market-v0-rd-charts-surface="true"' in body
        assert 'data-market-v0-data-surfaces="true"' in body
        assert 'data-market-v0-ohlcv-surface="true"' in body
        assert 'data-market-v0-depth-surface="true"' in body
        assert 'data-market-v0-visual-cockpit="true"' in body
        assert 'data-market-v0-visual-surface-strip="true"' in body
        assert 'data-market-v0-dashboard-preview="true"' in body
        assert 'data-market-v0-rd-preview="true"' in body
        assert 'data-market-v0-ohlcv-preview="true"' in body
        assert 'data-market-v0-depth-preview="true"' in body
        assert 'data-market-v0-ssr-metrics-strip="true"' in body
        assert 'data-market-v0-in-chart-ohlc-svg-v1="true"' in body
        assert 'data-market-v0-close-chart-integrated-frame="true"' in body
        assert 'data-market-v0-in-chart-ohlc-svg-root="true"' in body
        assert (
            'data-market-v0-in-chart-ohlc-candle-up="true"' in body
            or 'data-market-v0-in-chart-ohlc-candle-down="true"' in body
        )
        assert "chartjs-chart-financial" not in body.lower()
        assert 'data-market-v11-chart-library-status="true"' in body
        assert 'data-market-v11-payload-bars="true"' in body
        assert 'data-market-v11-render-fallback="true"' in body
        assert "Chart diagnostics" in body
        assert "Chart.js status" in body
        assert "Embedded bars" in body
        assert "Chart render status" in body
        assert "Chart library missing or blocked" in body
        assert "Chart render error" in body
        assert "No backend/API/provider change" in body
        assert 'data-market-readonly="true"' in body
        assert 'data-market-non-authorizing="true"' in body
        assert 'data-market-source-kind="dummy-offline-synthetic"' in body
        assert 'data-market-safety-banner="true"' in body
        assert 'data-market-source="dummy"' in body
        assert 'data-market-bars="20"' in body
        assert 'data-chart="market-v0-close-line"' in body
        assert 'id="market-v0-payload"' in body
        assert "read-only · non-authorizing" in body
        assert "Read-only market display" in body
        assert "No orders" in body
        assert "No strategy authority" in body
        assert "No Live/Testnet action" in body
        assert "No Risk/KillSwitch override" in body
        assert "/api/market/ohlcv" in body
        assert "Keine Orders" in body or "keine Orders" in body
        assert "Testnet" in body
        assert "Live" in body
        assert "Capital" in body or "Scope" in body
        assert "KillSwitch" in body or "Risk" in body
        assert "chart.js@4.4.1" in body.lower() or "chart.umd.min.js" in body
        assert 'data-chartjs-cdn-script-v0="true"' in body
        assert 'data-chartjs-cdn-monitored-v0="true"' in body
        assert 'id="peak-trade-market-chartjs-cdn-v0"' in body
        assert 'id="market-v0-shell"' in body
        assert "data-chartjs-cdn-load-error" in body
        assert "onerror=" in body.lower()
        lower = body.lower()
        assert "<form" not in lower
        assert 'method="post"' not in lower
        assert "<button" not in lower
        assert 'type="submit"' not in lower
        assert "fetch(" not in body
        assert 'method="POST"' not in body
        assert 'id="market-v0-chart-status"' in body
        assert 'data-market-chart-status="ready"' in body
        assert "Chart bereit — read-only OHLCV-Anzeige." in body
        assert 'data-market-depth-panel="true"' in body
        assert 'data-market-depth-status="disabled"' in body
        assert 'data-market-v0-orderbook-topn="true"' in body
        assert 'data-market-v0-orderbook-has-levels="false"' in body
        assert 'data-market-v0-orderbook-empty="true"' in body
        assert 'data-market-v0-ladder-empty-explain="true"' in body
        assert "Depth SSR is" in body
        assert 'data-market-depth-operator-hint="true"' in body

    def test_market_page_depth_ssr_forbids_client_depth_route_and_xhr(
        self,
        client: TestClient,
    ) -> None:
        """Depth is embedded SSR-only; page must not steer browsers to the JSON route or XHR."""

        resp = client.get("/market", params={"source": "dummy", "symbol": "ETHUSDT", "limit": 20})
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        body = resp.text

        assert "/api/market/depth" not in body
        assert "fetch(" not in body
        assert "XMLHttpRequest" not in body

    def test_market_depth_ssr_context_contract_v0_future_seam(
        self,
        client: TestClient,
    ) -> None:
        """Contract: GET /market carries narrow depth markers and no client Depth fetch."""
        resp = client.get("/market", params={"source": "dummy", "symbol": "ETHUSDT", "limit": 20})
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        body = resp.text

        assert "/api/market/depth" not in body
        assert "fetch(" not in body
        assert "XMLHttpRequest" not in body

        assert 'data-market-depth-panel="true"' in body
        assert 'data-market-depth-status="' in body

    def test_market_depth_ssr_page_stays_200_when_helper_returns_diagnostic_tuple(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Page HTTP status stays 200 when JSON route would use 503 (monkeypatch, no bundles)."""

        def _fake_diagnostic() -> tuple[int, dict[str, object]]:
            return 503, {
                "readmodel_id": "market_depth_readmodel.v0",
                "generated_at_iso": "2026-05-06T12:00:00+00:00",
                "runtime_source_status": "builder_error",
                "warnings": ["market_depth_bundle_build_failed"],
                "stale_reason": "bundle_build_failed",
            }

        monkeypatch.setattr(
            "src.webui.market_surface.market_depth_json_payload_v0",
            _fake_diagnostic,
        )

        resp = client.get("/market", params={"source": "dummy", "symbol": "ETHUSDT", "limit": 20})
        assert resp.status_code == 200
        body = resp.text
        assert 'data-market-depth-status="builder_error"' in body
        assert 'data-market-v0-orderbook-has-levels="false"' in body
        assert 'data-market-v0-orderbook-empty="true"' in body
        assert "/api/market/depth" not in body
        assert "failed build" in body
        assert "validation" in body
        assert 'data-market-depth-operator-hint="true"' in body

    def test_market_depth_ssr_ok_branch_uses_display_status_ok(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When helper succeeds, SSR shows display_status ok (mocked tuple, env-independent)."""

        def _fake_ok() -> tuple[int, dict[str, object]]:
            return 200, {
                "readmodel_id": "market_depth_readmodel.v0",
                "symbol": "BTC/EUR",
                "depth": {"levels_returned": {"bids": 2, "asks": 3}},
            }

        monkeypatch.setattr(
            "src.webui.market_surface.market_depth_json_payload_v0",
            _fake_ok,
        )

        resp = client.get("/market", params={"source": "dummy", "symbol": "ETHUSDT", "limit": 20})
        assert resp.status_code == 200
        body = resp.text
        assert 'data-market-depth-status="ok"' in body
        assert 'data-market-v0-orderbook-has-levels="false"' in body
        assert 'data-market-v0-orderbook-empty="true"' in body
        assert "/api/market/depth" not in body
        assert "no bid/ask rows" in body
        assert 'data-market-depth-operator-hint="true"' in body

    def test_market_dashboard_orderbook_topn_ssr_with_fixture_bundle(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bundle = (
            Path(__file__).resolve().parents[1]
            / "tests"
            / "fixtures"
            / "market_depth_readmodel_v0"
            / "complete_minimal"
        )
        monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
        monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(bundle.resolve()))
        monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-05-02T12:00:00+00:00")
        client = TestClient(create_app())

        resp = client.get("/market", params={"source": "dummy", "symbol": "ETHUSDT", "limit": 20})
        assert resp.status_code == 200
        body = resp.text
        assert 'data-market-v0-orderbook-topn="true"' in body
        assert 'data-market-v0-orderbook-has-levels="true"' in body
        assert 'data-market-v0-orderbook-bids="true"' in body
        assert 'data-market-v0-orderbook-asks="true"' in body
        assert 'data-market-v0-orderbook-empty="true"' not in body
        assert "63010" in body
        assert "63020" in body
        assert 'data-market-depth-status="ok"' in body
        assert "/api/market/depth" not in body
        assert "fetch(" not in body
        assert "XMLHttpRequest" not in body

    def test_market_html_invalid_timeframe_422(self, client: TestClient) -> None:
        r = client.get("/market", params={"source": "dummy", "timeframe": "bad"})
        assert r.status_code == 422

    def test_market_html_invalid_source_422(self, client: TestClient) -> None:
        r = client.get("/market", params={"source": "invalid", "timeframe": "1d"})
        assert r.status_code == 422


def test_market_v0_template_kraken_banner_markers_in_source() -> None:
    """Kraken-Pfad ohne Netzwerk: Banner-Zweig muss im Template-Stack existieren."""
    tmpl_dir = Path(__file__).resolve().parents[1] / "templates" / "peak_trade_dashboard"
    txt = (tmpl_dir / "market_v0.html").read_text(encoding="utf-8")
    txt += (tmpl_dir / "partials" / "market_legacy_operator_panels_v0.html").read_text(
        encoding="utf-8"
    )
    assert 'data-market-source-kind="kraken-public-ohlcv-network"' in txt
    assert 'data-market-v1-dashboard-shell="true"' in txt
    assert 'data-market-v1-readonly-banner="true"' in txt
    assert 'data-market-v1-context="true"' in txt
    assert 'data-market-v1-api-reference="true"' in txt
    assert 'data-market-v0-surface-links="true"' in txt
    assert 'data-market-v0-dashboard-surface="true"' in txt
    assert 'data-market-v0-rd-charts-surface="true"' in txt
    assert 'data-market-v0-data-surfaces="true"' in txt
    assert 'data-market-v0-ohlcv-surface="true"' in txt
    assert 'data-market-v0-depth-surface="true"' in txt
    assert 'data-market-v0-visual-cockpit="true"' in txt
    assert 'data-market-v0-visual-surface-strip="true"' in txt
    assert 'data-market-v0-dashboard-preview="true"' in txt
    assert 'data-market-v0-rd-preview="true"' in txt
    assert 'data-market-v0-ohlcv-preview="true"' in txt
    assert 'data-market-v0-depth-preview="true"' in txt
    assert 'data-market-v0-ssr-metrics-strip="true"' in txt
    assert 'data-market-v0-in-chart-ohlc-svg-v1="true"' in txt
    assert 'data-market-v0-close-chart-integrated-frame="true"' in txt
    assert 'data-market-v0-in-chart-ohlc-svg-root="true"' in txt
    assert (
        'data-market-v0-in-chart-ohlc-candle-up="true"' in txt
        or 'data-market-v0-in-chart-ohlc-candle-down="true"' in txt
    )
    assert "chartjs-chart-financial" not in txt.lower()
    assert 'data-market-v11-chart-diagnostics="true"' in txt
    assert 'data-market-v11-chart-library-status="true"' in txt
    assert 'data-market-v11-payload-bars="true"' in txt
    assert 'data-market-v11-render-fallback="true"' in txt
    assert txt.count('data-market-v1-stat-card="true"') >= 6
    assert "Read-only market display" in txt
    assert "Futures" in txt
    assert "read-only · non-authorizing" in txt
    assert 'id="market-v0-chart-status"' in txt
    assert "data-market-chart-status" in txt
    assert "data-market-empty-state" in txt
    assert "Chart bereit — read-only OHLCV-Anzeige." in txt
    assert "Keine OHLCV-Bars für diese Abfrage verfügbar." in txt
    assert "Chart-Daten konnten nicht gerendert werden; keine Trading-Aktion verfügbar." in txt
    assert 'data-market-depth-panel="true"' in txt
    assert "data-market-depth-status" in txt
    assert 'data-market-v0-orderbook-topn="true"' in txt
