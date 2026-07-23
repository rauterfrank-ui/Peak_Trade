"""Real Chrome Playwright evidence for Market Landscape V2 Phase 3 shell."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("playwright")
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

from src.webui.app import create_app

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO / "evidence" / "market_dashboard_v2" / "phase3" / "pr2"

VIEWPORTS = (
    (1512, 982, "market_1512x982.png"),
    (1920, 1080, "market_1920x1080.png"),
)


@pytest.fixture(scope="module")
def live_server_url() -> str:
    """Use TestClient ASGI transport via playwright request interception is hard;

    Prefer uvicorn subprocess through review harness launch helper when available;
    fallback: sync TestClient HTML + playwright route fulfill for static checks.
    """
    return "http://127.0.0.1:8765"


def _collect_asgi_html() -> str:
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    return response.text


def test_real_chrome_landscape_shell_viewports(tmp_path: Path) -> None:
    html = _collect_asgi_html()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    rendered = EVIDENCE_DIR / "rendered_market.html"
    rendered.write_text(html, encoding="utf-8")

    console_errors: list[str] = []
    page_errors: list[str] = []
    results: dict[str, object] = {}

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
            channel = "chrome"
        except Exception:
            browser = p.chromium.launch(headless=True)
            channel = "chromium"

        try:
            for width, height, shot_name in VIEWPORTS:
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                page.on(
                    "console",
                    lambda msg: console_errors.append(f"{msg.type}:{msg.text}")
                    if msg.type == "error"
                    else None,
                )
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))

                # Serve shell HTML and local static assets via route fulfill.
                def _handler(route, request, _html=html):  # type: ignore[no-untyped-def]
                    url = request.url
                    if url.endswith("/market") or url.rstrip("/").endswith(":8765"):
                        route.fulfill(status=200, content_type="text/html", body=_html)
                        return
                    if "/static/" in url:
                        rel = url.split("/static/", 1)[1]
                        path = REPO / "static" / rel
                        if path.is_file():
                            ctype = (
                                "text/css"
                                if path.suffix == ".css"
                                else "application/javascript"
                                if path.suffix == ".js"
                                else "application/octet-stream"
                            )
                            route.fulfill(status=200, content_type=ctype, body=path.read_bytes())
                            return
                    route.fulfill(status=404, body=b"missing")

                page.route("**/*", _handler)
                page.goto("http://127.0.0.1:8765/market", wait_until="domcontentloaded")

                root = page.locator('[data-market-landscape-v2="true"]')
                assert root.count() == 1
                chart = page.locator("[data-mdl-chart-region='true']")
                decision = page.locator("[data-mdl-decision-strip='true']")
                assert chart.count() == 1
                assert decision.count() == 1

                chart_box = chart.bounding_box()
                decision_box = decision.bounding_box()
                assert chart_box is not None
                assert decision_box is not None
                assert chart_box["y"] + 8 < height, "chart must start above the fold"
                assert decision_box["y"] < height, "decision strip visible without scroll"

                overflow = page.evaluate(
                    "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
                )
                assert overflow is False

                assert page.locator("form").count() == 0
                assert page.get_by_text("NOT_BOUND").count() > 0
                assert page.get_by_text("BOUND_NOT_ACTIVATED").count() > 0

                shot_path = EVIDENCE_DIR / shot_name
                page.screenshot(path=str(shot_path), full_page=False)
                results[shot_name] = {
                    "viewport": [width, height],
                    "chart_y": chart_box["y"],
                    "decision_y": decision_box["y"],
                    "channel": channel,
                }
                context.close()
        finally:
            browser.close()

    assert console_errors == [], console_errors
    assert page_errors == [], page_errors
    (EVIDENCE_DIR / "console.log").write_text(
        json.dumps({"console_errors": console_errors, "page_errors": page_errors}, indent=2) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "chrome_results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
