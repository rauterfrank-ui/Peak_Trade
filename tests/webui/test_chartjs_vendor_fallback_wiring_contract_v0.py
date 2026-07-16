"""Static structure contract for Chart.js self-hosted primary wiring (Phase 1B; no CDN)."""

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

FORBIDDEN_CDN_HOSTS = (
    "cdn.jsdelivr.net",
    "cdn.tailwindcss.com",
    "unpkg.com",
    "cdnjs.cloudflare.com",
)
VENDOR_PRIMARY_PATH = "/static/vendor/chartjs/4.4.1/chart.umd.min.js"

CHARTJS_SHELLS = (
    ("/market", "market-v0-shell", "peak-trade-market-chartjs-vendor-v1"),
    (
        "/market/double-play",
        "double-play-market-v0-shell",
        "peak-trade-double-play-chartjs-vendor-v1",
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


@pytest.mark.parametrize("path,shell_id,script_id", CHARTJS_SHELLS)
def test_chartjs_vendor_primary_self_only_v1(
    client: TestClient, path: str, shell_id: str, script_id: str
) -> None:
    html = _html(client, path)
    assert VENDOR_PRIMARY_PATH in html
    assert f'id="{script_id}"' in html
    assert f'id="{shell_id}"' in html
    assert 'data-chartjs-vendor-primary-v1="true"' in html
    assert 'data-chartjs-self-only-v1="true"' in html
    assert 'data-chartjs-vendor-monitored-v1="true"' in html
    assert f'<script src="{VENDOR_PRIMARY_PATH}"' in html.replace("\n", " ") or (
        f'src="{VENDOR_PRIMARY_PATH}"' in html
    )
    for host in FORBIDDEN_CDN_HOSTS:
        assert host not in html


@pytest.mark.parametrize("path", (p for p, _, _ in CHARTJS_SHELLS))
def test_chartjs_vendor_primary_marker_non_authorizing_v1(client: TestClient, path: str) -> None:
    html = _html(client, path)
    for token in FORBIDDEN_AUTHORITY_TOKENS:
        assert token not in html


def test_chartjs_vendor_primary_r_and_d_charts_v1(client: TestClient) -> None:
    html = _html(client, "/r_and_d/charts")
    if 'data-r-and-d-charts-empty="true"' in html:
        pytest.skip("empty charts repo — vendor script only renders with plot data")
    assert 'data-chartjs-vendor-primary-v1="true"' in html
    assert VENDOR_PRIMARY_PATH in html
    assert "cdn.jsdelivr.net" not in html


def test_chartjs_vendor_primary_docs_marker_documented_v1() -> None:
    surface = (project_root / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")
    assert "data-chartjs-vendor-primary-v1" in surface
    assert "self-only" in surface.lower() or "SELF_ONLY" in surface
    assert "non-authorizing" in surface.lower() or "non-authority" in surface.lower()


def test_chartjs_phase_1b_vendor_primary_supersedes_cdn_docs_v1() -> None:
    """Phase 1B docs must not claim CDN-primary jsdelivr as current target state."""
    surface = (project_root / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")
    section_start = surface.index("#### Chart.js vendor primary self-only wiring v1 (Phase 1B)")
    section_end = surface.index("#### CDN-blocking evidence criteria (v1)")
    phase_1b = surface[section_start:section_end]
    assert "vendor-primary" in phase_1b.lower() or "VENDOR_PRIMARY" in phase_1b
    assert "/static/vendor/chartjs/4.4.1/chart.umd.min.js" in phase_1b or (
        "static&#47;vendor&#47;chartjs" in phase_1b
    )
    assert "cdn.jsdelivr.net" not in phase_1b
    assert "non-authorizing" in phase_1b.lower()


def test_docs_truth_map_chartjs_phase_1b_vendor_primary_v1() -> None:
    truth_map = (project_root / "docs/ops/registry/DOCS_TRUTH_MAP.md").read_text(encoding="utf-8")
    row_start = truth_map.index("Chart.js local fallback planning charter v0")
    row_end = truth_map.index("\n", row_start)
    chartjs_row = truth_map[row_start:row_end]
    assert "PHASE_1B_VENDOR_PRIMARY" in chartjs_row or "vendor-primary" in chartjs_row.lower()
    assert "self-only" in chartjs_row.lower() or "SELF_ONLY" in chartjs_row
    assert "non-authorizing" in chartjs_row.lower()


def test_market_surface_double_play_v12_phase_1b_vendor_primary_v1() -> None:
    surface = (project_root / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")
    section_start = surface.index(
        "## Double-Play Market Dashboard v1.2 candlestick and visual panels"
    )
    section_end = surface.index("## Double-Play Market Dashboard v1.3 rail field mapping")
    v12 = surface[section_start:section_end]
    for stale in (
        "chart.js cdn nur",
        "cdn nur für",
        "cdn-primary bleibt",
    ):
        assert stale.lower() not in v12.lower()
    assert "vendor-primary" in v12.lower() or "self-only" in v12.lower()
    assert "non-authorizing" in v12.lower()
