"""Responsive viewport fit for Market Landscape V2 (presentation-only).

WP_ID=MARKET_DASHBOARD_LANDSCAPE_RESPONSIVE_VIEWPORT_FIT_V1
"""

from __future__ import annotations

import re
from pathlib import Path

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app

REPO = Path(__file__).resolve().parents[2]
CSS = REPO / "static" / "css" / "market_dashboard_landscape_v2.css"

_VIEWPORT_FIT_JS = """
() => {
  const root = document.querySelector('.mdl-v2--workstation-v2');
  const stage = document.querySelector('.mdl-v2-chart__stage');
  const doc = document.documentElement;
  const stageStyle = stage ? getComputedStyle(stage) : null;
  return {
    has_workstation: Boolean(root),
    mdl_width: root ? root.getBoundingClientRect().width : null,
    stage_max_height: stageStyle ? stageStyle.maxHeight : null,
    stage_rect_height: stage ? stage.getBoundingClientRect().height : null,
    horizontal_overflow: doc.scrollWidth - doc.clientWidth,
  };
}
"""


def _css_without_comments() -> str:
    return re.sub(r"/\*.*?\*/", "", CSS.read_text(encoding="utf-8"), flags=re.S)


def test_workstation_viewport_fit_css_contract() -> None:
    code = _css_without_comments()
    assert ".mdl-v2--workstation-v2" in code
    assert re.search(
        r"\.mdl-v2--workstation-v2\s*\{[^}]*--mdl-stage-height:\s*clamp\(",
        code,
        flags=re.S,
    )
    assert re.search(
        r"\.mdl-v2--workstation-v2\s+\.mdl-v2-chart__stage\s*\{[^}]*max-height:\s*none",
        code,
        flags=re.S,
    )
    assert re.search(
        r"\.mdl-v2--workstation-v2\s+\.mdl-v2-primary\s*\{[^}]*flex:\s*1\s+1\s+auto",
        code,
        flags=re.S,
    )
    assert re.search(
        r"\.mdl-v2--workstation-v2\s+\.mdl-v2-workspace\s*\{[^}]*min-height:\s*0",
        code,
        flags=re.S,
    )
    assert "--mdl-stage-height: 300px" in CSS.read_text(encoding="utf-8")
    assert "max-height: var(--mdl-stage-height)" in CSS.read_text(encoding="utf-8")


def test_market_route_still_workstation_shell() -> None:
    html = TestClient(create_app()).get("/market").text
    assert "mdl-v2--workstation-v2" in html
    assert 'data-market-dashboard-authority="false"' in html


def _render_landscape_html() -> str:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    from src.webui.market_dashboard_landscape_v2 import (
        MarketDashboardReadServiceV1,
        present_market_landscape_v2,
    )

    stamp = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
    page = MarketDashboardReadServiceV1().load_page_snapshot(generated_at=stamp)
    context = present_market_landscape_v2(page)
    env = Environment(
        loader=FileSystemLoader(str(REPO / "templates" / "peak_trade_dashboard")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env.get_template("market_landscape_v2.html").render(
        status={"project": "Peak_Trade"},
        **context,
    )


@pytest.mark.parametrize(
    ("width", "height", "min_stage_px"),
    (
        (1920, 1080, 480),
        (1512, 982, 300),
        (960, 720, 260),
    ),
)
def test_viewport_fit_playwright_layout(width: int, height: int, min_stage_px: int) -> None:
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    html = _render_landscape_html()

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()

            def _handler(route, request, _html=html):  # type: ignore[no-untyped-def]
                url = request.url
                if url.endswith("/market") or "market_landscape" in url:
                    route.fulfill(status=200, content_type="text/html", body=_html)
                    return
                if "/static/" in url:
                    rel = url.split("/static/", 1)[1]
                    path = REPO / "static" / rel
                    if path.is_file():
                        route.fulfill(path=str(path))
                        return
                route.continue_()

            page.route("**/*", _handler)
            page.goto("http://127.0.0.1:8765/market", wait_until="load")
            metrics = page.evaluate(_VIEWPORT_FIT_JS)
        finally:
            context.close()
            browser.close()

    assert metrics["has_workstation"] is True
    assert metrics["horizontal_overflow"] <= 1
    assert metrics["mdl_width"] is not None
    assert metrics["mdl_width"] >= width * 0.92
    assert metrics["stage_max_height"] == "none"
    assert metrics["stage_rect_height"] >= min_stage_px
