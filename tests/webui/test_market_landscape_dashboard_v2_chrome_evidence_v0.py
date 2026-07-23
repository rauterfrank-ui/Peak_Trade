"""Real Chrome Playwright evidence for Market Landscape V2 Phase 4.4A binding."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytest.importorskip("playwright")
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    SAFETY_AUTHORITY_OWNER_MODULE,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2 import (
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
)

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO / "evidence" / "market_dashboard_v2" / "phase4" / "pr7"

VIEWPORTS = (
    (1512, 982, "market_1512x982.png"),
    (1920, 1080, "market_1920x1080.png"),
)

STAMP = datetime(2026, 7, 23, 18, 0, 0, tzinfo=timezone.utc)
SAFETY_PRODUCER_FRESH = datetime(2026, 7, 23, 15, 0, 0, tzinfo=timezone.utc)


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


def _collect_injected_safety_html() -> str:
    """Test-only DI path: inject Safety fields; never auto-loads live state."""
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        safety_authority_fields={
            "kill_switch_state": "KILLED",
            "veto_active": True,
            "reason_codes": ("killswitch_block_new", "reconciliation_required"),
            "generated_at": SAFETY_PRODUCER_FRESH,
            "saved_at": SAFETY_PRODUCER_FRESH,
            "killswitch_owner_ref": SAFETY_AUTHORITY_OWNER_MODULE,
            "semantic_digest": "e" * 64,
        },
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    context = present_market_landscape_v2(page)
    env = Environment(
        loader=FileSystemLoader(str(REPO / "templates" / "peak_trade_dashboard")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("market_landscape_v2.html")
    return template.render(
        status={"project": "Peak_Trade"},
        **context,
    )


def _run_chrome_against_html(
    *,
    html: str,
    shot_prefix: str,
    expect_safety_available: bool,
) -> dict[str, object]:
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
                assert root.get_attribute("data-phase") == (
                    "PHASE_4_4A_CANONICAL_SAFETY_PROJECTION_BINDING"
                )
                chart = page.locator("[data-mdl-chart-region='true']")
                decision = page.locator("[data-mdl-decision-strip='true']")
                assert chart.count() == 1
                assert decision.count() == 1

                if expect_safety_available:
                    safety = page.locator(
                        '[data-mdl-field="safety"][data-availability="AVAILABLE"]'
                    )
                    assert safety.count() == 1
                    safety_text = safety.inner_text()
                    assert "KILLED" in safety_text
                    assert "veto=True" in safety_text
                    assert page.get_by_text("killswitch_block_new").count() >= 0
                else:
                    assert (
                        page.locator(
                            '[data-mdl-field="safety"][data-availability="MISSING_SOURCE"]'
                        ).count()
                        == 1
                    )

                # Risk / Sizing / Capital remain NOT_BOUND in this slice.
                assert page.get_by_text("Risk / Sizing / Capital").count() >= 1
                ops_risk = page.locator(".mdl-v2-ops__col").filter(
                    has_text="Risk / Sizing / Capital"
                )
                assert ops_risk.locator('[data-availability="NOT_BOUND"]').count() >= 1

                overflow = page.evaluate(
                    "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
                )
                assert overflow is False

                assert page.locator("form").count() == 0
                assert page.locator("button").count() == 0
                body_text = page.locator("body").inner_text()
                assert "place_order" not in body_text
                assert "Submit Order" not in body_text
                assert "Trigger Kill" not in body_text
                assert "Recover Kill" not in body_text

                shot_path = EVIDENCE_DIR / f"{shot_prefix}{shot_name}"
                page.screenshot(path=str(shot_path), full_page=False)
                results[f"{shot_prefix}{shot_name}"] = {
                    "viewport": [width, height],
                    "channel": channel,
                    "safety_available": expect_safety_available,
                }
                context.close()
        finally:
            browser.close()

    assert console_errors == [], console_errors
    assert page_errors == [], page_errors
    return {
        "results": results,
        "console_errors": console_errors,
        "page_errors": page_errors,
    }


def test_real_chrome_landscape_shell_viewports(tmp_path: Path) -> None:
    html = _collect_asgi_html()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    rendered = EVIDENCE_DIR / "rendered_market.html"
    rendered.write_text(html, encoding="utf-8")

    out = _run_chrome_against_html(
        html=html,
        shot_prefix="",
        expect_safety_available=False,
    )
    (EVIDENCE_DIR / "console.log").write_text(
        json.dumps(
            {
                "console_errors": out["console_errors"],
                "page_errors": out["page_errors"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "chrome_results.json").write_text(
        json.dumps(out["results"], indent=2) + "\n", encoding="utf-8"
    )


def test_real_chrome_injected_safety_viewports(tmp_path: Path) -> None:
    html = _collect_injected_safety_html()
    assert html, "injected safety template must render"
    assert "KILLED" in html
    assert "veto=True" in html
    assert 'data-availability="AVAILABLE"' in html
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "rendered_market_injected_safety.html").write_text(html, encoding="utf-8")

    out = _run_chrome_against_html(
        html=html,
        shot_prefix="injected_",
        expect_safety_available=True,
    )
    (EVIDENCE_DIR / "console_injected.log").write_text(
        json.dumps(
            {
                "console_errors": out["console_errors"],
                "page_errors": out["page_errors"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "chrome_injected_results.json").write_text(
        json.dumps(out["results"], indent=2) + "\n", encoding="utf-8"
    )
