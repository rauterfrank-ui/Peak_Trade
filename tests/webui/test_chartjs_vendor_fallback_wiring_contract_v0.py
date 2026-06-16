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


def test_chartjs_cdn_diagnostics_operator_pointer_no_stale_deferred_v0() -> None:
    """#4101 operator pointer must not claim vendor fallback is deferred/not active post-#4108."""
    surface = (project_root / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")
    section_start = surface.index("#### Operator enablement (chart.js CDN diagnostics v1)")
    section_end = surface.index("### Chart.js local fallback planning charter v0")
    chartjs_cdn = surface[section_start:section_end]

    for stale in (
        "vendor fallback stays deferred",
        "no active local Chart.js vendor fallback",
    ):
        assert stale.lower() not in chartjs_cdn.lower()

    for required in (
        "template-wired",
        "onerror-only",
        "data-chartjs-vendor-fallback-v0",
        "peakTradeChartjsVendorFallbackV0",
        "non-authorizing",
    ):
        assert required.lower() in chartjs_cdn.lower()


def test_docs_truth_map_chartjs_post_merge_no_stale_planning_only_v0() -> None:
    """DOCS_TRUTH_MAP Chart.js row must reflect PR #4108/#4110 on-main wiring."""
    truth_map = (project_root / "docs/ops/registry/DOCS_TRUTH_MAP.md").read_text(encoding="utf-8")
    row_start = truth_map.index("Chart.js local fallback planning charter v0")
    row_end = truth_map.index("\n", row_start)
    chartjs_row = truth_map[row_start:row_end]

    for stale in (
        "planning-only",
        "future implementation preconditions",
        "kein vendor/static/templates",
    ):
        assert stale.lower() not in chartjs_row.lower()

    for required in (
        "PR #4108",
        "CHARTJS_VENDOR_ADDED_ON_MAIN=true",
        "CHARTJS_LOCAL_FALLBACK_WIRING_V1_ON_MAIN=true",
        "jsdelivr",
        "onerror",
        "data-chartjs-vendor-fallback-v0",
        "non-authorizing",
        "separately authorized",
    ):
        assert required.lower() in chartjs_row.lower()


def test_market_surface_double_play_v12_no_stale_cdn_only_fallback_v0() -> None:
    """Double-Play v1.2 must not claim CDN-only or deferred fallback post-#4108."""
    surface = (project_root / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")
    section_start = surface.index(
        "## Double-Play Market Dashboard v1.2 candlestick and visual panels"
    )
    section_end = surface.index("## Double-Play Market Dashboard v1.3 rail field mapping")
    v12 = surface[section_start:section_end]

    for stale in (
        "chart.js cdn nur",
        "cdn nur für",
        "lokaler chart.js-fallback",
    ):
        assert stale.lower() not in v12.lower()

    for required in (
        "jsdelivr",
        "onerror-only",
        "template-wired",
        "non-authorizing",
        "chart.js vendor fallback template wiring v1",
        "pr #4108",
    ):
        assert required.lower() in v12.lower()
