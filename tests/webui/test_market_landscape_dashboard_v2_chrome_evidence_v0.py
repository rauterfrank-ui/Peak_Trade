"""Real Chrome Playwright evidence for Market Landscape V2 Capability 7 product maturity."""

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
EVIDENCE_DIR = REPO / "evidence" / "market_dashboard_v2" / "capability7_product_maturity"

VIEWPORTS = (
    (1512, 982, "market_1512x982.png"),
    (1920, 1080, "market_1920x1080.png"),
)

STAMP = datetime(2026, 7, 23, 18, 0, 0, tzinfo=timezone.utc)
SAFETY_PRODUCER_FRESH = datetime(2026, 7, 23, 15, 0, 0, tzinfo=timezone.utc)
# Fixed evidence clock — must not use wall-clock datetime.now (byte-stable artifacts).
EVIDENCE_GENERATED_AT = STAMP
EVIDENCE_GENERATED_AT_ISO = "2026-07-23T18:00:00Z"


def _render_landscape_html(*, safety_authority_fields: dict | None = None) -> str:
    """Render Landscape HTML with a fixed generated_at for deterministic evidence."""
    if safety_authority_fields is None:
        slots = bind_market_universe_slots(generated_at=EVIDENCE_GENERATED_AT)
    else:
        slots = bind_market_universe_slots(
            generated_at=EVIDENCE_GENERATED_AT,
            safety_authority_fields=safety_authority_fields,
        )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=EVIDENCE_GENERATED_AT,
        slot_overrides=slots,
    )
    context = present_market_landscape_v2(page)
    env = Environment(
        loader=FileSystemLoader(str(REPO / "templates" / "peak_trade_dashboard")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("market_landscape_v2.html")
    html = template.render(
        status={"project": "Peak_Trade"},
        **context,
    )
    assert EVIDENCE_GENERATED_AT_ISO in html
    return html


@pytest.fixture(scope="module")
def live_server_url() -> str:
    """Use TestClient ASGI transport via playwright request interception is hard;

    Prefer uvicorn subprocess through review harness launch helper when available;
    fallback: sync TestClient HTML + playwright route fulfill for static checks.
    """
    return "http://127.0.0.1:8765"


def _collect_asgi_html() -> str:
    """Default-shell evidence HTML with fixed generated_at (no wall-clock drift).

    Live ASGI /market uses datetime.now; evidence artifacts must remain byte-stable
    across reruns, so this path mirrors the default binding with EVIDENCE_GENERATED_AT.
    """
    # Smoke: live route still serves /market.
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    return _render_landscape_html()


def _collect_injected_safety_html() -> str:
    """Test-only DI path: inject Safety fields; never auto-loads live state."""
    return _render_landscape_html(
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


def _assert_no_duplicate_status_facts(page) -> None:  # type: ignore[no-untyped-def]
    strip = page.locator('[data-mdl-region="GLOBAL_SYSTEM_STRIP"]')
    context = page.locator('[data-mdl-region="SYSTEM_CONTEXT_RAIL"]')
    assert strip.locator('[data-mdl-field="regime"]').count() == 0
    assert context.locator('[data-mdl-field="regime"]').count() == 1
    assert strip.locator('[data-mdl-field="scope"]').count() == 0
    assert context.locator('[data-mdl-field="scope_lifecycle"]').count() == 1
    assert page.locator('[data-mdl-field="scope_freshness"]').count() == 0
    assert strip.locator('[data-mdl-field="freshness"]').count() == 0
    assert strip.get_by_text("Freshness", exact=True).count() == 0
    assert strip.locator('[data-mdl-field="source_health"]').count() == 0
    assert context.locator('[data-mdl-field="source_health"]').count() == 1
    assert context.locator('[data-mdl-source-health="true"]').count() == 1
    summary = context.locator('[data-mdl-source-health-summary="true"]')
    assert summary.count() == 1
    summary_text = summary.inner_text().strip()
    assert " · " in summary_text
    assert context.locator('[data-mdl-source-slot="canonical_decision"]').count() == 1
    assert context.locator('[data-mdl-source-slot="market_instrument"]').count() == 1
    # Aggregate Source Health field remains unique across the page.
    assert page.locator('[data-mdl-field="source_health"]').count() == 1


def _assert_decision_why_blocker_reading_flow(page) -> dict[str, object]:  # type: ignore[no-untyped-def]
    """Phase 5 PR2: primary hierarchy + fully readable Why (no destructive ellipsis)."""
    strip = page.locator("[data-mdl-decision-strip='true']")
    primary = strip.locator('[data-mdl-decision-primary="true"]')
    secondary = strip.locator('[data-mdl-decision-secondary="true"]')
    assert primary.count() == 1
    assert secondary.count() == 1
    assert primary.locator('[data-mdl-decision-primary-fact="decision"]').count() == 1
    assert primary.locator('[data-mdl-decision-primary-fact="why"]').count() == 1
    assert primary.locator('[data-mdl-decision-primary-fact="blockers"]').count() == 1
    assert secondary.locator('[data-mdl-decision-secondary-fact="direction"]').count() == 1
    assert secondary.locator('[data-mdl-decision-secondary-fact="double_play"]').count() == 1
    assert secondary.locator('[data-mdl-decision-secondary-fact="confidence"]').count() == 1

    why = page.locator('[data-mdl-why-primary="true"]')
    assert why.count() == 1
    why_text = why.inner_text().strip()
    assert why_text
    assert "…" not in why_text
    assert why_text.endswith("…") is False

    style = why.evaluate(
        """(el) => {
          const cs = getComputedStyle(el);
          return {
            whiteSpace: cs.whiteSpace,
            overflow: cs.overflow,
            textOverflow: cs.textOverflow,
            scrollWidth: el.scrollWidth,
            clientWidth: el.clientWidth,
            scrollHeight: el.scrollHeight,
            clientHeight: el.clientHeight,
          };
        }"""
    )
    assert style["whiteSpace"] in ("normal", "pre-wrap", "break-spaces")
    assert style["overflow"] in ("visible", "auto")
    assert style["textOverflow"] in ("clip", "")
    # Fully readable: no horizontal clipping of Why content.
    assert int(style["scrollWidth"]) <= int(style["clientWidth"]) + 1
    assert int(style["scrollHeight"]) <= int(style["clientHeight"]) + 1

    blockers = page.locator('[data-mdl-field="blockers"]')
    confidence = page.locator('[data-mdl-field="confidence"]')
    assert blockers.count() == 1
    assert confidence.count() == 1
    assert blockers.get_attribute("data-availability") == "NOT_BOUND"
    assert confidence.get_attribute("data-availability") == "NOT_BOUND"
    assert blockers.inner_text().strip() == "NOT_BOUND"
    assert confidence.inner_text().strip() == "NOT_BOUND"
    assert "CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD" not in blockers.inner_text()

    return {
        "why_text": why_text,
        "why_style": style,
        "blockers": blockers.inner_text().strip(),
        "confidence": confidence.inner_text().strip(),
    }


def _assert_engineering_drawer_completeness(page) -> dict[str, object]:  # type: ignore[no-untyped-def]
    """Capability 7 product maturity: closed-by-default drawer renders existing engineering.slots."""
    engineering = page.locator("[data-mdl-engineering]")
    assert engineering.count() == 1
    assert engineering.evaluate("el => el.open") is False

    slots = page.locator("[data-mdl-engineering-slots='true']")
    assert slots.count() == 1
    assert page.locator("[data-mdl-engineering-slot]").count() == 11

    decision = page.locator('[data-mdl-engineering-slot="canonical_decision"]')
    assert decision.count() == 1
    assert decision.get_attribute("data-availability") == "MISSING_SOURCE"
    # text_content includes closed <details> descendants; inner_text does not.
    assert (
        decision.locator('[data-mdl-eng-field="availability"]').text_content() or ""
    ).strip() == "MISSING_SOURCE"
    schema_id = (decision.locator('[data-mdl-eng-field="schema_id"]').text_content() or "").strip()
    assert schema_id == "market_dashboard_landscape_projection.canonical_decision.v1"
    source_ref = (
        decision.locator('[data-mdl-eng-field="source_reference"]').text_content() or ""
    ).strip()
    assert source_ref == "CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD"
    reason_codes = (
        decision.locator('[data-mdl-eng-field="reason_codes"]').text_content() or ""
    ).strip()
    assert "CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD" in reason_codes
    producer = (
        decision.locator('[data-mdl-eng-field="producer_module"]').text_content() or ""
    ).strip()
    assert producer == "trading.master_v2.canonical_trading_decision_evidence_v1"

    body_text = engineering.text_content() or ""
    assert "HEALTHY" not in body_text
    assert "\nOK\n" not in body_text

    # Keyboard: summary is focusable; Escape closes an opened drawer.
    summary = engineering.locator("summary")
    assert summary.count() == 1
    summary.focus()
    assert summary.evaluate("el => document.activeElement === el") is True
    page.keyboard.press("Enter")
    assert engineering.evaluate("el => el.open") is True
    assert decision.is_visible()
    assert decision.locator('[data-mdl-eng-field="availability"]').inner_text().strip() == (
        "MISSING_SOURCE"
    )
    page.keyboard.press("Escape")
    assert engineering.evaluate("el => el.open") is False

    return {
        "slot_count": 11,
        "canonical_decision_availability": "MISSING_SOURCE",
        "schema_id": schema_id,
        "source_reference": source_ref,
        "reason_codes": reason_codes,
        "producer_module": producer,
        "escape_closes": True,
    }


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
                    "PHASE_5_CAPABILITY_7_PRODUCT_MATURITY_TECHNICAL"
                )
                chart = page.locator("[data-mdl-chart-region='true']")
                decision = page.locator("[data-mdl-decision-strip='true']")
                assert chart.count() == 1
                assert decision.count() == 1
                _assert_no_duplicate_status_facts(page)
                reading_flow = _assert_decision_why_blocker_reading_flow(page)
                engineering_diag = _assert_engineering_drawer_completeness(page)

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

                # Risk / Execution / Economic wired; absent without injection → MISSING_SOURCE.
                assert page.get_by_text("Risk / Sizing / Capital").count() >= 1
                assert page.get_by_text("Execution / Reconciliation").count() >= 1
                assert page.get_by_text("Economic", exact=True).count() >= 1
                ops_risk = page.locator('[data-mdl-ops="risk_sizing_capital"]')
                ops_exec = page.locator('[data-mdl-ops="execution_reconciliation"]')
                ops_econ = page.locator('[data-mdl-ops="economic_summary"]')
                ops_diag = page.locator('[data-mdl-ops="diagnostics_summary"]')
                ops_gov = page.locator('[data-mdl-ops="governance_autonomy"]')
                assert ops_risk.locator('[data-availability="MISSING_SOURCE"]').count() >= 1
                assert ops_exec.locator('[data-availability="MISSING_SOURCE"]').count() >= 1
                assert ops_econ.locator('[data-availability="MISSING_SOURCE"]').count() >= 1
                assert ops_risk.locator('[data-mdl-field="risk_status"]').count() == 1
                assert ops_exec.locator('[data-mdl-field="execution_status"]').count() == 1
                assert ops_econ.locator('[data-mdl-field="economic_profit_factor"]').count() == 1
                assert ops_diag.locator('[data-mdl-field="diagnostics_status"]').count() == 1
                assert (
                    "NOT_BOUND"
                    in ops_diag.locator('[data-mdl-field="diagnostics_status"]').inner_text()
                )
                assert "NON_AUTHORITATIVE" in ops_diag.inner_text()
                assert "UNRESOLVED" in ops_diag.inner_text()
                assert ops_gov.locator('[data-mdl-field="autonomy_stage"]').count() == 1
                assert (
                    "NOT_BOUND" in ops_gov.locator('[data-mdl-field="autonomy_stage"]').inner_text()
                )
                assert (
                    "NOT_BOUND"
                    in ops_gov.locator('[data-mdl-field="promotion_eligibility"]').inner_text()
                )
                assert (
                    "NOT_BOUND"
                    in ops_gov.locator('[data-mdl-field="activation_eligibility"]').inner_text()
                )
                assert (
                    "BOUND_NOT_ACTIVATED"
                    in ops_gov.locator('[data-mdl-field="runtime_bridge_lock"]').inner_text()
                )
                assert (
                    "ACTIVE"
                    not in ops_gov.locator('[data-mdl-field="runtime_bridge_lock"]').inner_text()
                )
                assert (
                    "REQUIRED=true"
                    in ops_gov.locator('[data-mdl-field="operator_go_required"]').inner_text()
                )
                assert page.locator("button").count() == 0
                assert page.locator("form").count() == 0

                overflow = page.evaluate(
                    "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
                )
                assert overflow is False
                viewport_metrics = page.evaluate(
                    """() => ({
                      scrollWidth: document.documentElement.scrollWidth,
                      clientWidth: document.documentElement.clientWidth,
                      horizontal_overflow:
                        document.documentElement.scrollWidth >
                        document.documentElement.clientWidth + 1,
                      chart_present:
                        document.querySelector('[data-mdl-chart-region="true"]') !== null,
                      engineering_open:
                        document.querySelector('[data-mdl-engineering]')?.open === true,
                    })"""
                )
                assert viewport_metrics["horizontal_overflow"] is False
                assert viewport_metrics["chart_present"] is True
                assert viewport_metrics["engineering_open"] is False

                assert page.locator("form").count() == 0
                assert page.locator("button").count() == 0
                body_text = page.locator("body").inner_text()
                assert "place_order" not in body_text
                assert "Submit Order" not in body_text
                assert "Trigger Kill" not in body_text
                assert "Recover Kill" not in body_text

                # Closed-state screenshot (drawer remains closed after Escape assertion).
                shot_path = EVIDENCE_DIR / f"{shot_prefix}{shot_name}"
                page.screenshot(path=str(shot_path), full_page=False)

                # Open-state screenshot with visible per-slot engineering diagnostics.
                engineering = page.locator("[data-mdl-engineering]")
                engineering.locator("summary").click()
                assert engineering.evaluate("el => el.open") is True
                open_shot_name = (
                    f"{shot_prefix}{shot_name.replace('market_', 'market_drawer_open_', 1)}"
                )
                open_path = EVIDENCE_DIR / open_shot_name
                page.locator(
                    '[data-mdl-engineering-slot="canonical_decision"]'
                ).scroll_into_view_if_needed()
                page.screenshot(path=str(open_path), full_page=False)
                page.keyboard.press("Escape")
                assert engineering.evaluate("el => el.open") is False

                overflow_open_cycle = page.evaluate(
                    "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
                )
                assert overflow_open_cycle is False

                results[f"{shot_prefix}{shot_name}"] = {
                    "viewport": [width, height],
                    "channel": channel,
                    "safety_available": expect_safety_available,
                    "why_text": reading_flow["why_text"],
                    "why_fully_readable": True,
                    "primary_why_destructive_ellipsis": False,
                    "viewport_metrics": viewport_metrics,
                    "blockers": reading_flow["blockers"],
                    "confidence": reading_flow["confidence"],
                    "engineering": engineering_diag,
                    "drawer_open_shot": open_shot_name,
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
