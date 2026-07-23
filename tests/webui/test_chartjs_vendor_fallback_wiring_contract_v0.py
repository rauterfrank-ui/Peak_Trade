"""Static structure contract for Chart.js self-hosted primary wiring (no CDN).

Market Dashboard shells were removed; remaining coverage is non-market WebUI.
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

FORBIDDEN_CDN_HOSTS = (
    "cdn.jsdelivr.net",
    "cdn.tailwindcss.com",
    "unpkg.com",
    "cdnjs.cloudflare.com",
)
VENDOR_PRIMARY_PATH = "/static/vendor/chartjs/4.4.1/chart.umd.min.js"

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


def test_market_dashboard_chartjs_shells_absent(client: TestClient) -> None:
    # Landscape V2 shell is present at /market; legacy Chart.js market shells stay gone.
    response = client.get("/market")
    assert response.status_code == 200
    body = response.text.lower()
    assert "peak-trade-market-chartjs-vendor-v1" not in body
    assert "market-v0-shell" not in body
    for path in ("/market/double-play",):
        legacy = client.get(path)
        assert legacy.status_code == 404
        legacy_body = legacy.text.lower()
        assert "peak-trade-market-chartjs-vendor-v1" not in legacy_body
        assert "market-v0-shell" not in legacy_body


def test_chartjs_vendor_primary_r_and_d_charts_v1(client: TestClient) -> None:
    html = _html(client, "/r_and_d/charts")
    if 'data-r-and-d-charts-empty="true"' in html:
        pytest.skip("empty charts repo — vendor script only renders with plot data")
    assert 'data-chartjs-vendor-primary-v1="true"' in html
    assert VENDOR_PRIMARY_PATH in html
    for host in FORBIDDEN_CDN_HOSTS:
        assert host not in html
    for token in FORBIDDEN_AUTHORITY_TOKENS:
        assert token not in html


def test_market_surface_docs_removed_for_chartjs_contract() -> None:
    tombstone = project_root / "docs/webui/MARKET_DASHBOARD_REMOVED.md"
    assert tombstone.is_file()
    assert not (project_root / "docs/webui/MARKET_SURFACE_V0.md").exists()
    text = tombstone.read_text(encoding="utf-8")
    assert "intentionally removed" in text.lower() or "intentionally absent" in text.lower()


def test_docs_truth_map_chartjs_phase_1b_vendor_primary_v1() -> None:
    truth_map = (project_root / "docs/ops/registry/DOCS_TRUTH_MAP.md").read_text(encoding="utf-8")
    row_start = truth_map.index("Chart.js local fallback planning charter v0")
    row_end = truth_map.index("\n", row_start)
    chartjs_row = truth_map[row_start:row_end]
    assert "PHASE_1B_VENDOR_PRIMARY" in chartjs_row or "vendor-primary" in chartjs_row.lower()
    assert "self-only" in chartjs_row.lower() or "SELF_ONLY" in chartjs_row
    assert "non-authorizing" in chartjs_row.lower()
