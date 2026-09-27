"""Presentation guards: Landscape V3 must not regress to card/tile dashboard layout."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_v3.safety_v1 import REPO_ROOT, V3_JS, V3_TEMPLATE

V3_CSS = REPO_ROOT / "static" / "css" / "market_dashboard_landscape_v3.css"

_FORBIDDEN = (
    "v3-sections-root",
    "v3-section",
    "v3-chart-panel",
    "v3-main",
    "v3-primary",
    "v3-badge",
)


def test_assets_reject_tile_dashboard_composition() -> None:
    html = V3_TEMPLATE.read_text(encoding="utf-8")
    css = V3_CSS.read_text(encoding="utf-8")
    js = V3_JS.read_text(encoding="utf-8")
    for token in _FORBIDDEN:
        assert token not in html
        assert token not in css
        assert token not in js
    assert 'data-landscape-composition="continuous"' in html
    assert "renderAnalyticalBands" in js
    assert ".v3-band" in css
    assert "border-radius" not in css


def test_served_market_v3_is_continuous_landscape() -> None:
    client = TestClient(create_app())
    body = client.get("/market/v3").text
    for token in _FORBIDDEN:
        assert token not in body
    assert 'id="v3-chart-canvas"' in body
    css = client.get("/static/css/market_dashboard_landscape_v3.css").text
    js = client.get("/static/js/market_dashboard_landscape_v3.js").text
    assert re.search(r"\.v3-band\b", css)
    assert "v3-section" not in js
