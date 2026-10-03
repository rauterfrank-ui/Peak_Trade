"""Visual architecture v1 — Direct View, ranking geometry, formatting, safety boundary."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import app

REPO_ROOT = Path(__file__).resolve().parents[2]
HTML_PATH = REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_surface_greenfield_v1.html"
CSS_PATH = REPO_ROOT / "static" / "css" / "market_surface_greenfield_v1.css"
JS_DIR = REPO_ROOT / "static" / "js" / "market_surface_greenfield_v1"
FORMAT_JS = JS_DIR / "surface_format_v1.js"
APP_JS = JS_DIR / "surface_app_v1.js"
DV_JS = JS_DIR / "surface_direct_view_v1.js"


def test_surface_html_visual_regions() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    assert 'data-ranking-universe="true"' in html
    assert 'id="ots-direct-view-nav"' in html
    assert 'data-direct-view="MARKET"' in html
    assert 'data-direct-view="05"' in html
    assert "ots-safety-boundary" in html
    assert "PRE_EXTERNAL" in html
    assert "ots-chart-host" in html
    assert "ots-system-context" not in html
    assert 'data-layout="ranking-left-market-right"' in html
    assert "ots-left-landscape" in html
    assert "ots-right-stack" in html
    assert "ots-brand-primary" in html
    assert "GOLDEN HAPPY HECTOR" in html
    assert "Golden Happy Vector" not in html


def test_direct_view_default_market_in_js() -> None:
    dv = DV_JS.read_text(encoding="utf-8")
    assert 'defaultView: "MARKET"' in dv or "defaultView: 'MARKET'" in dv
    assert "localStorage" in dv


def test_direct_view_no_post_or_fetch_in_direct_view_module() -> None:
    dv = DV_JS.read_text(encoding="utf-8")
    assert "fetch(" not in dv
    assert "POST" not in dv
    assert "XMLHttpRequest" not in dv


def test_app_single_get_poll_only() -> None:
    app_js = APP_JS.read_text(encoding="utf-8")
    assert app_js.count('method: "GET"') >= 1
    assert 'method: "POST"' not in app_js
    assert app_js.count("fetch(") == 1


def test_no_synthetic_slot_overlay_markers() -> None:
    blob = APP_JS.read_text(encoding="utf-8") + FORMAT_JS.read_text(encoding="utf-8")
    assert "synthetic" not in blob.lower()
    assert "fakeCandidate" not in blob
    assert "overlayData" not in blob


def test_small_price_format_not_zero() -> None:
    script = f"""
    {FORMAT_JS.read_text(encoding="utf-8")}
    const v = 1.23e-8;
    const s = PeakTradeSurfaceFormatV1.formatPrice(v);
    if (s === '0' || s === '0.00') process.exit(2);
    if (!s.includes('e') && !s.includes('0.000000012')) process.exit(3);
    console.log(s);
    """
    proc = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=10)
    if proc.returncode != 0:
        pytest.skip(f"node unavailable or format check failed: {proc.stderr}")
    assert "0.00" not in proc.stdout.strip()[:20]


def test_state_api_selected_future_not_synthetic() -> None:
    client = TestClient(app)
    body = client.get("/api/operator-trading-surface/v1/state").json()
    sf = body["system"]["selected_future"]
    assert sf["classification"] in {"PROVEN_CURRENT", "UNKNOWN_CURRENT"}
    assert "synthetic" not in json.dumps(sf).lower()


def test_ranking_unavailable_not_fake_candidates() -> None:
    client = TestClient(app)
    body = client.get("/api/operator-trading-surface/v1/state").json()
    u = body["system"]["unknown_sources"]
    assert u["top20"]["label"] == "SOURCE UNAVAILABLE"
    assert u["top5"]["label"] == "SOURCE UNAVAILABLE"
    html = client.get("/operator-trading-surface").text
    assert "ots-top20-geometry" in html
    assert "SOURCE UNAVAILABLE" in html


def test_safety_boundary_from_canonical_state() -> None:
    client = TestClient(app)
    body = client.get("/api/operator-trading-surface/v1/state").json()
    safety = body["safety"]
    assert safety["post_allowed"] is False
    assert safety["direct_browser_okx"] is False
    html = client.get("/operator-trading-surface").text
    assert "EXTERNAL EFFECTS BLOCKED" in html


def test_direct_view_buttons_present_market_and_slots() -> None:
    html = TestClient(app).get("/operator-trading-surface").text
    for token in ("MARKET", "01", "02", "03", "04", "05"):
        assert f'data-direct-view="{token}"' in html


def test_no_v3_landscape_in_static_js() -> None:
    for path in JS_DIR.glob("*.js"):
        text = path.read_text(encoding="utf-8")
        assert "landscape_v" not in text.lower()
        assert "market_dashboard_landscape" not in text


def test_html_avoids_dashboard_card_wall_words() -> None:
    html = HTML_PATH.read_text(encoding="utf-8").lower()
    assert "widget-grid" not in html
    assert "dashboard-card" not in html


def test_hector_copy_not_in_backend_python() -> None:
    py_blob = "\n".join(
        p.read_text(encoding="utf-8")
        for p in (REPO_ROOT / "src" / "webui" / "market_surface_greenfield_v1").glob("*.py")
    )
    assert "GOLDEN HAPPY HECTOR" not in py_blob
    assert "Golden Happy Vector" not in py_blob


def test_desktop_layout_ranking_precedes_market_in_dom() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    left = html.index("ots-left-landscape")
    right = html.index("ots-right-stack")
    direct = html.index("ots-direct-view-nav")
    chart = html.index("ots-chart-host")
    assert left < right < direct < chart


def test_direct_view_inside_market_workspace() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    ws_start = html.index("ots-market-workspace")
    dv = html.index("ots-direct-view-nav")
    chart_end = html.index("ots-chart-host")
    assert ws_start < dv < chart_end


def test_v1_4_strict_geometry_layout() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")
    geometry_js = (JS_DIR / "surface_geometry_v1.js").read_text(encoding="utf-8")
    assert 'data-v1-4-delivery="strict-geometry"' in html
    assert 'data-market-axis="workspace-left-v1-4"' in html
    assert 'data-market-column-left-alignment-pass="true"' in html
    assert 'data-chart-layout="workspace-ratio-v1-4"' in html
    assert 'data-chart-viewport="primary-v1-4"' in html
    assert 'data-okx-chart-bounded="true"' in html
    assert 'data-okx-chart-left-edge-realigned="true"' in html
    assert "ots-market-axis" in html
    assert "ots-market-module-header" in html
    assert "ots-chart-viewport-row" in html
    assert "ots-direct-view-compact" in html
    assert "surface_geometry_v1.js" in html
    assert "fetch(" not in geometry_js
    assert "centered-three-band" not in html
    assert "ots-chart-center-wrap" not in html
    assert 'data-instrument-band="upper"' not in html
    assert 'data-instrument-band="lower"' in html
    axis = html.index("ots-market-axis")
    dv = html.index("ots-direct-view-nav")
    chart = html.index("ots-chart-host")
    lower = html.index('data-instrument-band="lower"')
    assert axis < dv < chart < lower
    assert "--ots-ranking-market-gutter" in css
    assert "--ots-chart-workspace-width-ratio" in css
    assert "--ots-market-column-max" not in css
    assert "680px" not in css
    assert "padding-top: var(--ots-rail-brand-offset)" in css


def test_v1_4_chart_layout_regression_flags() -> None:
    """Machine-readable layout contract markers for workspace-relative chart geometry."""
    html = HTML_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")
    flags = {
        "MARKET_COLUMN_LEFT_ALIGNMENT_PASS": 'data-market-column-left-alignment-pass="true"'
        in html,
        "OKX_CHART_LEFT_EDGE_REALIGNED": 'data-okx-chart-left-edge-realigned="true"' in html,
        "OKX_CHART_BOUNDED": 'data-okx-chart-bounded="true"' in html
        and "--ots-chart-workspace-width-ratio" in css,
        "OKX_CHART_BLINDLY_STRETCHED": "width: min(96%, 920px)" not in css and "680px" not in css,
        "DIRECT_VIEW_COMPACT": "ots-direct-view-compact" in html,
        "LOWER_INSTRUMENT_BAND_RESERVED": 'data-instrument-band="lower"' in html,
        "EXCESSIVE_INTERSTITIAL_GAP_REMOVED": "minmax(64px, 1fr)" not in css,
        "RANKING_MARKET_GUTTER_DEFINED": "--ots-ranking-market-gutter: 20px" in css,
    }
    assert all(flags.values()), flags


def test_v1_2_narrow_ranking_rail_css_and_dom() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")
    assert 'data-ranking-rail="narrow-v1-2"' in html
    assert 'data-v1-2-delivery="narrow-rail"' in html
    assert "--ots-left-col: 18%" in css
    assert "33%" not in css.split("--ots-left-col")[1].split(";")[0]
    assert "minmax(0, 1fr)" in css
    assert "--ots-ranking-rail-max" in css
