"""Static structure contract for Chart.js vendor fallback wiring v0 (no browser, no network)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app

CDN_PRIMARY_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"
VENDOR_FALLBACK_PATH = "/static/vendor/chartjs/4.4.1/chart.umd.min.js"

CHARTJS_SHELLS = (
    ("/market", "market-v0-shell", "peak-trade-market-chartjs-cdn-v0"),
    (
        "/market/double-play",
        "double-play-market-v0-shell",
        "peak-trade-double-play-chartjs-cdn-v0",
    ),
)

FORBIDDEN_AUTHORITY_TOKENS = (
    "LIVE_AUTHORIZED_NOW=true",
    "TRUTH_GO_AUTHORIZED",
    "ORDER_AUTHORIZED_NOW",
    "CANCEL_AUTHORIZED_NOW",
    "EXECUTE_AUTHORIZED_NOW",
    "PREFLIGHT_LIFT_AUTHORIZED",
    "DASHBOARD_TRUTH_GO",
    "PROVIDER_TRUTH_GO",
    "TRADING_READINESS_GO",
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def _html(client: TestClient, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    return response.text


@pytest.mark.parametrize("path,cdn_id,shell_id", CHARTJS_SHELLS)
def test_chartjs_cdn_primary_baseline_unchanged_v0(
    client: TestClient, path: str, cdn_id: str, shell_id: str
) -> None:
    html = _html(client, path)
    assert CDN_PRIMARY_URL in html
    assert f'id="{cdn_id}"' in html
    assert f'id="{shell_id}"' in html
    assert 'data-chartjs-cdn-script-v0="true"' in html
    assert 'data-chartjs-cdn-monitored-v0="true"' in html
    assert "data-chartjs-cdn-load-error" in html
    assert "onerror=" in html.lower()


@pytest.mark.parametrize("path,shell_id", ((p, s) for p, s, _ in CHARTJS_SHELLS))
def test_chartjs_vendor_fallback_wiring_onerror_only_v0(
    client: TestClient, path: str, shell_id: str
) -> None:
    html = _html(client, path)
    assert 'data-chartjs-vendor-fallback-loader-v0="true"' in html
    assert "peakTradeChartjsVendorFallbackV0" in html
    assert VENDOR_FALLBACK_PATH in html
    assert f"peakTradeChartjsVendorFallbackV0('{shell_id}')" in html
    assert "data-chartjs-vendor-fallback-v0" in html
    assert "data-chartjs-vendor-fallback-script-v0" in html
    assert "peak-trade-chartjs-vendor-fallback-ready" in html
    assert f'<script src="{VENDOR_FALLBACK_PATH}"' not in html
    assert (
        re.search(
            rf'id="{re.escape(shell_id)}"[^>]*data-chartjs-vendor-fallback-v0="true"',
            html,
        )
        is None
    )


def test_chartjs_vendor_fallback_wiring_r_and_d_charts_v0(client: TestClient) -> None:
    html = _html(client, "/r_and_d/charts")
    if 'data-r-and-d-charts-empty="true"' in html:
        pytest.skip("empty charts repo — fallback scripts only render with plot data")
    assert 'data-chartjs-vendor-fallback-loader-v0="true"' in html
    assert "peakTradeChartjsVendorFallbackV0('r-and-d-charts-shell')" in html
    assert VENDOR_FALLBACK_PATH in html
    assert f'<script src="{VENDOR_FALLBACK_PATH}"' not in html


@pytest.mark.parametrize("path", (p for p, _, _ in CHARTJS_SHELLS))
def test_chartjs_vendor_fallback_marker_non_authorizing_v0(client: TestClient, path: str) -> None:
    html = _html(client, path)
    for token in FORBIDDEN_AUTHORITY_TOKENS:
        assert token not in html


def test_chartjs_cdn_and_vendor_fallback_markers_distinct_v0(client: TestClient) -> None:
    html = _html(client, "/market")
    assert "data-chartjs-cdn-load-error" in html
    assert "data-chartjs-vendor-fallback-v0" in html
    assert html.index("data-chartjs-cdn-load-error") != html.index(
        "data-chartjs-vendor-fallback-v0"
    )


def test_chartjs_vendor_fallback_docs_marker_documented_v0() -> None:
    surface = (project_root / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")
    assert "data-chartjs-vendor-fallback-v0" in surface
    assert "non-authorizing" in surface.lower() or "non-authority" in surface.lower()
