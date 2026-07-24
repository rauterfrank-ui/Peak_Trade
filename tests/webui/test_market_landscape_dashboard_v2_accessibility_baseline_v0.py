"""Phase 5 TASK_7 — keyboard / focus / accessibility baseline contracts.

Static HTML + template guards (always). Optional Real-Chrome keyboard evidence
when Playwright is available; writes under evidence/.../task7_accessibility/.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app

REPO = Path(__file__).resolve().parents[2]
TEMPLATE = REPO / "templates" / "peak_trade_dashboard" / "market_landscape_v2.html"
CSS = REPO / "static" / "css" / "market_dashboard_landscape_v2.css"
JS = REPO / "static" / "js" / "market_dashboard_landscape_v2.js"
EVIDENCE_DIR = REPO / "evidence" / "market_dashboard_v2" / "phase5" / "task7_accessibility"

VIEWPORTS = (
    (1512, 982, "market_focus_1512x982.png"),
    (1920, 1080, "market_focus_1920x1080.png"),
)

POSITIVE_TABINDEX = re.compile(r"""tabindex\s*=\s*["']?\s*[1-9]""", re.IGNORECASE)
CLICKABLE_DIV_SPAN = re.compile(
    r"""<(?:div|span)\b[^>]*(?:\bonclick\b|role=["']button["']|tabindex=["']0["'])""",
    re.IGNORECASE,
)
ID_ATTR = re.compile(r"""\bid=["']([^"']+)["']""", re.IGNORECASE)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_template_static_accessibility_anti_patterns() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    assert POSITIVE_TABINDEX.search(text) is None
    assert CLICKABLE_DIV_SPAN.search(text) is None
    assert "<button" not in text.lower()
    assert 'method="post"' not in text.lower()
    assert re.search(r"<form\b", text, flags=re.IGNORECASE) is None
    # Nested <main> forbidden — base.html already owns the page landmark.
    assert re.search(r"<main\b", text, flags=re.IGNORECASE) is None
    assert 'data-mdl-a11y-baseline="task7"' in text
    assert '<h1 class="mdl-v2-kicker">Market Landscape</h1>' in text
    assert "<details" in text
    assert "<summary>Engineering · provenance / schemas / diagnostics</summary>" in text
    assert 'id="mdl-v2-engineering-body"' in text
    assert 'data-mdl-engineering-body="true"' in text
    # Read-only status facts stay non-interactive (no tabindex on status rows).
    assert "tabindex=" not in text.lower()


def test_css_does_not_globally_suppress_outline() -> None:
    css = CSS.read_text(encoding="utf-8")
    # Universal reset must not set outline: none on all descendants.
    reset_block = css.split(".mdl-v2 *,", 1)[1].split("}", 1)[0]
    assert "outline: none" not in reset_block
    assert "outline:none" not in reset_block.replace(" ", "")
    assert "a:focus-visible" in css
    assert "summary:focus-visible" in css
    assert "outline: 2px solid" in css
    assert "outline-offset: 3px" in css


def test_js_escape_restores_focus_to_summary() -> None:
    js = JS.read_text(encoding="utf-8")
    assert 'event.key !== "Escape"' in js
    assert "engineering.open = false" in js
    assert "summary.focus()" in js
    assert "fetch(" not in js
    assert "XMLHttpRequest" not in js
    assert "place_order" not in js
    assert "activate_runtime" not in js


def test_get_market_accessibility_baseline_contract(client: TestClient) -> None:
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text

    assert html.lower().count("<main") == 1
    assert html.lower().count("</main>") == 1

    # Exactly one page-level heading in the Landscape surface.
    landscape = html.split('data-market-landscape-v2="true"', 1)[1]
    assert landscape.count("<h1") == 1
    assert '<h1 class="mdl-v2-kicker">Market Landscape</h1>' in landscape

    # Semantic landmarks (region markers + native elements).
    for marker in (
        'data-mdl-region="GLOBAL_SYSTEM_STRIP"',
        'data-mdl-region="UNIVERSE_RANK_RAIL"',
        'data-mdl-region="PRIMARY_MARKET_WORKSPACE"',
        'data-mdl-region="SYSTEM_CONTEXT_RAIL"',
        'data-mdl-region="CANONICAL_DECISION_STRIP"',
        'data-mdl-region="SECONDARY_STATUS_REGION"',
        'data-mdl-region="EVENT_DECISION_TIMELINE"',
        'data-mdl-region="ENGINEERING_DRAWER"',
        'aria-label="Global system strip"',
        'aria-label="Universe and rank"',
        'aria-label="Primary market workspace"',
        'aria-label="System context"',
        'aria-label="Canonical decision strip"',
        'aria-label="Operations band"',
        'aria-label="Event and decision timeline"',
        "<aside",
        "<header",
        "<section",
        "<details",
        "<summary>",
    ):
        assert marker in html, marker

    assert POSITIVE_TABINDEX.search(html) is None
    assert CLICKABLE_DIV_SPAN.search(html) is None

    ids = ID_ATTR.findall(html)
    assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"

    # Engineering drawer: native disclosure with accessible name; closed by default.
    eng_open_tag = html.split('data-mdl-engineering="true"', 1)[0].rsplit("<details", 1)[-1]
    eng_open_tag = "<details" + eng_open_tag.split(">", 1)[0] + ">"
    assert " open" not in eng_open_tag
    assert "<summary>Engineering · provenance / schemas / diagnostics</summary>" in html
    assert 'id="mdl-v2-engineering-body"' in html

    # No order / runtime / activation / command controls.
    assert "<button" not in html.lower()
    assert "place_order" not in html
    assert "submit_order" not in html
    assert "activate_runtime" not in html
    assert "arm_live" not in html
    assert "Trigger Kill" not in html
    assert re.search(r"<form\b", html, flags=re.IGNORECASE) is None

    # Status facts remain read-only markup (dt/dd / spans), not focusable controls.
    assert 'data-mdl-field="decision"' in html
    assert 'data-mdl-field="reason_codes"' in html
    assert 'data-mdl-field="blockers"' in html
    assert 'data-mdl-field="source_health"' in html
    assert 'data-mdl-field="safety"' in html


def test_real_chrome_keyboard_focus_accessibility_baseline(tmp_path: Path) -> None:
    pytest.importorskip("playwright")
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from playwright.sync_api import sync_playwright

    from src.webui.market_dashboard_landscape_producer_binding_v2 import (
        bind_market_universe_slots,
    )
    from src.webui.market_dashboard_landscape_v2 import (
        MarketDashboardReadServiceV1,
        present_market_landscape_v2,
    )

    stamp = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
    slots = bind_market_universe_slots(generated_at=stamp)
    page_snap = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=stamp,
        slot_overrides=slots,
    )
    context = present_market_landscape_v2(page_snap)
    env = Environment(
        loader=FileSystemLoader(str(REPO / "templates" / "peak_trade_dashboard")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    html = env.get_template("market_landscape_v2.html").render(
        status={"project": "Peak_Trade"},
        **context,
    )

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "rendered_market.html").write_text(html, encoding="utf-8")

    console_errors: list[str] = []
    page_errors: list[str] = []
    keyboard_notes: dict[str, object] = {}

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
            channel = "chrome"
        except Exception:
            browser = p.chromium.launch(headless=True)
            channel = "chromium"

        try:
            for width, height, shot_name in VIEWPORTS:
                ctx = browser.new_context(viewport={"width": width, "height": height})
                page = ctx.new_page()
                page.on(
                    "console",
                    lambda msg: (
                        console_errors.append(f"{msg.type}:{msg.text}")
                        if msg.type == "error"
                        else None
                    ),
                )
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))

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
                assert page.locator("h1.mdl-v2-kicker").count() == 1
                assert page.locator("h1").count() == 1

                home = page.locator("a.mdl-v2-app-chrome__home")
                summary = page.locator("[data-mdl-engineering] > summary")
                engineering = page.locator("[data-mdl-engineering]")
                assert home.count() == 1
                assert summary.count() == 1
                assert engineering.evaluate("el => el.open") is False

                # Logical tab order: home link → engineering summary (only interactive controls).
                home.focus()
                assert home.evaluate("el => document.activeElement === el") is True
                page.keyboard.press("Tab")
                assert summary.evaluate("el => document.activeElement === el") is True

                # Visible focus indicator for keyboard focus (outline not none).
                focus_style = summary.evaluate(
                    """el => {
                      el.focus();
                      const s = getComputedStyle(el);
                      return {
                        outlineStyle: s.outlineStyle,
                        outlineWidth: s.outlineWidth,
                        outlineColor: s.outlineColor,
                      };
                    }"""
                )
                # :focus-visible may require keyboard modality; Tab already established it.
                page.keyboard.press("Shift+Tab")
                page.keyboard.press("Tab")
                focus_style = summary.evaluate(
                    """el => {
                      const s = getComputedStyle(el);
                      return {
                        outlineStyle: s.outlineStyle,
                        outlineWidth: s.outlineWidth,
                        outlineColor: s.outlineColor,
                      };
                    }"""
                )
                assert focus_style["outlineStyle"] != "none"
                assert focus_style["outlineWidth"] not in ("0px", "0")

                # Native Enter toggles disclosure; body becomes focusable only when open.
                page.keyboard.press("Enter")
                assert engineering.evaluate("el => el.open") is True
                body_focusable_when_open = page.evaluate(
                    """() => {
                      const body = document.getElementById('mdl-v2-engineering-body');
                      if (!body) return false;
                      const probe = document.createElement('a');
                      probe.href = '#';
                      probe.textContent = 'probe';
                      body.prepend(probe);
                      const tabbable = probe.tabIndex >= 0 && probe.offsetParent !== null;
                      probe.remove();
                      return tabbable;
                    }"""
                )
                assert body_focusable_when_open is True

                page.keyboard.press("Escape")
                assert engineering.evaluate("el => el.open") is False
                assert summary.evaluate("el => document.activeElement === el") is True

                # Closed drawer: descendants are not keyboard-reachable via Tab.
                hidden_not_focusable = page.evaluate(
                    """() => {
                      const details = document.querySelector('[data-mdl-engineering]');
                      const body = document.getElementById('mdl-v2-engineering-body');
                      if (!details || !body || details.open) return false;
                      const probe = document.createElement('a');
                      probe.href = '#';
                      probe.textContent = 'probe';
                      body.prepend(probe);
                      // In closed <details>, HTML5 removes the content from sequential focus.
                      const focused = (() => { probe.focus(); return document.activeElement === probe; })();
                      probe.remove();
                      return focused === false;
                    }"""
                )
                assert hidden_not_focusable is True

                # No keyboard trap into closed drawer body.
                page.keyboard.press("Tab")
                inside_closed_body = page.evaluate(
                    """() => {
                      const body = document.getElementById('mdl-v2-engineering-body');
                      return body && body.contains(document.activeElement);
                    }"""
                )
                assert inside_closed_body is False

                overflow = page.evaluate(
                    "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
                )
                assert overflow is False

                # Focus-visible screenshot (summary focused).
                summary.focus()
                page.keyboard.press("Shift+Tab")
                page.keyboard.press("Tab")
                shot_path = EVIDENCE_DIR / shot_name
                page.screenshot(path=str(shot_path), full_page=False)

                keyboard_notes[shot_name] = {
                    "viewport": [width, height],
                    "channel": channel,
                    "focus_outline": focus_style,
                    "tab_order": ["a.mdl-v2-app-chrome__home", "details > summary"],
                    "escape_restores_focus": True,
                    "hidden_content_not_focusable": True,
                    "no_horizontal_overflow": True,
                }
                ctx.close()
        finally:
            browser.close()

    assert console_errors == [], console_errors
    assert page_errors == [], page_errors

    (EVIDENCE_DIR / "console.log").write_text(
        json.dumps(
            {"console_errors": console_errors, "page_errors": page_errors},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (EVIDENCE_DIR / "keyboard_focus_review.txt").write_text(
        json.dumps(keyboard_notes, indent=2) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "a11y_chrome.json").write_text(
        json.dumps(keyboard_notes, indent=2) + "\n", encoding="utf-8"
    )
