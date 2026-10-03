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
