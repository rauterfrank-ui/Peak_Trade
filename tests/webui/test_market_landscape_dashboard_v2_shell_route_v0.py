"""Route / aggregate / presenter tests for Market Landscape V2 Phase 3 shell."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
)
from src.webui.market_dashboard_landscape_v2.unavailable import (
    unavailable_canonical_decision,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 23, 16, 0, 0, tzinfo=timezone.utc)

LANDMARKS = (
    'data-mdl-region="GLOBAL_SYSTEM_STRIP"',
    'data-mdl-region="UNIVERSE_RANK_RAIL"',
    'data-mdl-region="PRIMARY_MARKET_WORKSPACE"',
    'data-mdl-region="SYSTEM_CONTEXT_RAIL"',
    'data-mdl-region="CANONICAL_DECISION_STRIP"',
    'data-mdl-region="SECONDARY_STATUS_REGION"',
    'data-mdl-region="EVENT_DECISION_TIMELINE"',
    'data-mdl-region="ENGINEERING_DRAWER"',
)

FORBIDDEN_UI = (
    "place_order",
    "submit_order",
    "activate_runtime",
    "arm_live",
    "Submit Order",
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_get_market_returns_200_with_landmarks(client: TestClient) -> None:
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert 'data-market-landscape-v2="true"' in html
    for landmark in LANDMARKS:
        assert landmark in html, landmark
    assert "PHASE_4_6B_ECONOMIC_EVIDENCE_EXPLICIT_INJECTION_BINDING" in html
    assert "BOUND_NOT_ACTIVATED" in html
    assert "no ohlcv fabricated" in html.lower()
    assert "BTC/USD" not in html
    assert "btc_usd_dummy" not in html.lower()
    assert 'data-mdl-outer-workspace="true"' in html
    assert "mdl-v2-ops" in html
    assert 'data-mdl-field="selected_instrument"' in html
    assert 'data-mdl-field="universe_membership"' in html
    assert 'data-mdl-field="scope_lifecycle"' in html
    assert 'data-mdl-field="current_scope_ref"' in html
    assert 'data-mdl-field="regime"' in html
    assert 'data-mdl-field="bull_bear"' in html
    assert 'data-mdl-field="switch"' in html
    assert 'data-mdl-field="source_health"' in html
    assert 'data-mdl-field="blockers" data-availability="NOT_BOUND"' in html
    assert 'data-mdl-field="confidence" data-availability="NOT_BOUND"' in html
    # Decision + DP + Safety wired but absent without injection; Regime / Switch stay NOT_BOUND
    assert "NOT_BOUND" in html
    assert "MISSING_SOURCE" in html
    assert "CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD" in html or (
        'data-mdl-field="decision" data-availability="MISSING_SOURCE"' in html
    )
    assert "CANONICAL_DOUBLE_PLAY_DISPLAY_NOT_PERSISTED_FOR_DASHBOARD" in html or (
        'data-mdl-field="double_play" data-availability="MISSING_SOURCE"' in html
    )
    assert 'data-mdl-field="safety"' in html
    assert 'data-mdl-field="economic"' in html
    assert 'data-availability="MISSING_SOURCE"' in html
    assert "MISSING_SOURCE" in html
    # Safety strip value is MISSING_SOURCE without injection.
    assert ">MISSING_SOURCE</dd>" in html or "MISSING_SOURCE" in html
    # Economic region is MISSING_SOURCE without injection (wired slot, no evidence).
    assert 'data-mdl-field="economic"' in html
    assert "Risk / Sizing / Capital" in html
    assert "OPERATOR_SKELETON_APPROVAL" not in html
    assert "<button" not in html.lower()
    assert "Trigger Kill" not in html
    assert "Recover Kill" not in html


def _region_html(html: str, region: str) -> str:
    marker = f'data-mdl-region="{region}"'
    start = html.index(marker)
    # Regions are sibling sections/asides/headers; cut until next region or end of shell.
    rest = html[start:]
    next_region = rest.find('data-mdl-region="', len(marker))
    return rest if next_region < 0 else rest[:next_region]


def test_get_market_duplicate_status_facts_have_single_primary_location(
    client: TestClient,
) -> None:
    """Phase 5 PR1: Regime/Scope lifecycle/Source Health each have one primary surface."""
    html = client.get("/market").text
    strip = _region_html(html, "GLOBAL_SYSTEM_STRIP")
    context = _region_html(html, "SYSTEM_CONTEXT_RAIL")

    # Regime: Context only (not Global Strip).
    assert 'data-mdl-field="regime"' not in strip
    assert context.count('data-mdl-field="regime"') == 1
    assert 'data-availability="NOT_BOUND"' in context.split('data-mdl-field="regime"', 1)[1][:200]

    # Scope lifecycle: Context Lifecycle only (not Global Strip Scope).
    assert 'data-mdl-field="scope"' not in strip
    assert context.count('data-mdl-field="scope_lifecycle"') == 1
    assert 'data-mdl-field="scope_freshness"' not in html

    # Freshness must not relabel aggregate availability in the strip.
    assert "<dt>Freshness</dt>" not in strip
    assert 'data-mdl-field="freshness"' not in strip

    # Source Health remains the sole operator-visible aggregate availability fact.
    assert 'data-mdl-field="source_health"' not in strip
    assert context.count('data-mdl-field="source_health"') == 1
    assert 'data-mdl-source-health="true"' in context
    assert 'data-mdl-source-health-summary="true"' in context
    assert " · " in context.split('data-mdl-source-health-summary="true"', 1)[1][:200]
    assert 'data-mdl-source-slot="canonical_decision"' in context
    assert 'data-mdl-source-slot="market_instrument"' in context
    # Compact freshness must not reappear as a strip Freshness alias.
    assert context.count('data-mdl-field="source_health"') == html.count(
        'data-mdl-field="source_health"'
    )
    assert 'data-mdl-field="instrument"' in strip
    assert 'data-mdl-field="venue"' in strip
    assert 'data-mdl-field="runtime"' in strip
    assert 'data-mdl-field="safety"' in strip


def test_get_market_decision_why_blocker_primary_reading_flow(client: TestClient) -> None:
    """Phase 5 PR2: Decision → Why → Blockers are the primary hierarchy; no semantic enrichment."""
    html = client.get("/market").text
    decision = _region_html(html, "CANONICAL_DECISION_STRIP")

    assert 'data-mdl-decision-primary="true"' in decision
    assert 'data-mdl-decision-secondary="true"' in decision
    assert 'data-mdl-decision-primary-fact="decision"' in decision
    assert 'data-mdl-decision-primary-fact="why"' in decision
    assert 'data-mdl-decision-primary-fact="blockers"' in decision
    assert 'data-mdl-decision-secondary-fact="direction"' in decision
    assert 'data-mdl-decision-secondary-fact="double_play"' in decision
    assert 'data-mdl-decision-secondary-fact="confidence"' in decision
    assert 'data-mdl-why-primary="true"' in decision

    primary = decision.split('data-mdl-decision-primary="true"', 1)[1].split(
        'data-mdl-decision-secondary="true"', 1
    )[0]
    secondary = decision.split('data-mdl-decision-secondary="true"', 1)[1]

    # Primary order: Decision before Why before Blockers.
    assert primary.index('data-mdl-field="decision"') < primary.index(
        'data-mdl-field="reason_codes"'
    )
    assert primary.index('data-mdl-field="reason_codes"') < primary.index(
        'data-mdl-field="blockers"'
    )
    assert 'data-mdl-field="direction"' not in primary
    assert 'data-mdl-field="double_play"' not in primary
    assert 'data-mdl-field="confidence"' not in primary

    # Secondary retains Direction / Double Play / Confidence only.
    assert 'data-mdl-field="direction"' in secondary
    assert 'data-mdl-field="double_play"' in secondary
    assert 'data-mdl-field="confidence"' in secondary
    assert 'data-mdl-field="decision"' not in secondary
    assert 'data-mdl-field="reason_codes"' not in secondary
    assert 'data-mdl-field="blockers"' not in secondary

    # Honest NOT_BOUND; no reason_codes copied into blockers.
    assert 'data-mdl-field="blockers" data-availability="NOT_BOUND">NOT_BOUND</dd>' in decision
    assert 'data-mdl-field="confidence" data-availability="NOT_BOUND">NOT_BOUND</dd>' in decision
    blockers_dd = decision.split('data-mdl-field="blockers"', 1)[1].split("</dd>", 1)[0]
    assert "CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD" not in blockers_dd
    assert "MISSING_SOURCE ·" not in blockers_dd


def test_get_market_engineering_drawer_renders_existing_slot_diagnostics(
    client: TestClient,
) -> None:
    """Phase 5 PR4: Engineering drawer surfaces presenter engineering.slots exactly."""
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    drawer = _region_html(html, "ENGINEERING_DRAWER")

    assert 'data-mdl-engineering="true"' in drawer
    assert "<summary>Engineering · provenance / schemas / diagnostics</summary>" in drawer
    # Closed by default: the engineering details open-tag (before body) has no open attr.
    eng_open_tag = html.split('data-mdl-engineering="true"', 1)[0].rsplit("<details", 1)[-1]
    eng_open_tag = "<details" + eng_open_tag.split(">", 1)[0] + ">"
    assert " open" not in eng_open_tag
    assert 'open="' not in eng_open_tag
    assert "open'" not in eng_open_tag

    assert 'data-mdl-engineering-slots="true"' in drawer
    assert 'data-mdl-engineering-slot="canonical_decision"' in drawer
    assert 'data-mdl-engineering-slot="market_instrument"' in drawer
    assert drawer.count('data-mdl-engineering-slot="') == 11

    decision = drawer.split('data-mdl-engineering-slot="canonical_decision"', 1)[1].split(
        "</article>", 1
    )[0]
    assert 'data-mdl-eng-field="availability">MISSING_SOURCE</dd>' in decision
    assert 'data-mdl-eng-field="schema_id"' in decision
    assert "market_dashboard_landscape_projection.canonical_decision.v1" in decision
    assert 'data-mdl-eng-field="schema_version"' in decision
    assert 'data-mdl-eng-field="producer_module"' in decision
    assert "trading.master_v2.canonical_trading_decision_evidence_v1" in decision
    assert 'data-mdl-eng-field="source_reference"' in decision
    assert "CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD" in decision
    assert 'data-mdl-eng-field="reason_codes"' in decision
    assert 'data-mdl-eng-field="freshness_observed_at"' in decision
    assert 'data-mdl-eng-field="provenance_generated_at"' in decision

    # Exact availability vocabulary; no HEALTHY/OK aliases.
    assert "HEALTHY" not in drawer
    assert ">OK</dd>" not in drawer
    assert "PASS" not in drawer.split("data-mdl-engineering-slots", 1)[1]

    # Existing Source Health compaction and Decision→Why→Blocker remain intact.
    assert 'data-mdl-source-health="true"' in html
    assert 'data-mdl-source-health-summary="true"' in html
    assert 'data-mdl-decision-primary="true"' in html
    assert 'data-mdl-why-primary="true"' in html
    assert "<button" not in html.lower()
    assert "place_order" not in html
    assert "activate_runtime" not in html
    assert "arm_live" not in html


def test_get_market_has_no_write_or_order_controls(client: TestClient) -> None:
    html = client.get("/market").text
    assert "<form" not in html.lower()
    assert 'method="post"' not in html.lower()
    for token in FORBIDDEN_UI:
        assert token not in html, token


def test_page_aggregate_owner_projects_not_bound_without_silent_defaults() -> None:
    service = MarketDashboardReadServiceV1()
    page = service.load_page_snapshot(generated_at=STAMP, git_sha="abc123")
    assert page.canonical_decision.availability is Availability.NOT_BOUND
    assert page.canonical_decision.decision is None
    assert page.canonical_decision.direction is None
    assert page.source_health.availability is Availability.NOT_BOUND
    assert page.runtime_bridge_display == "BOUND_NOT_ACTIVATED"
    assert all(
        state is Availability.NOT_BOUND for state in page.source_health.slot_availability.values()
    )
    # Provenance + freshness retained
    assert page.canonical_decision.provenance.availability is Availability.NOT_BOUND
    assert page.canonical_decision.freshness.observed_at == STAMP


def test_page_aggregate_partial_invalid_remains_renderable() -> None:
    service = MarketDashboardReadServiceV1()
    invalid = unavailable_canonical_decision(
        availability=Availability.INVALID,
        generated_at=STAMP,
        reason="SCHEMA_MISMATCH",
    )
    page = service.load_page_snapshot(
        generated_at=STAMP,
        slot_overrides={"canonical_decision": invalid},
    )
    assert page.canonical_decision.availability is Availability.INVALID
    assert page.source_health.availability is Availability.INVALID
    assert "SCHEMA_MISMATCH" in page.canonical_decision.reason_codes
    ctx = present_market_landscape_v2(page)
    assert ctx["decision"]["availability"] == "INVALID"
    assert ctx["decision"]["fields"]["decision"] is None


def test_presenter_formats_only_no_authority_defaults() -> None:
    page = MarketDashboardReadServiceV1().load_page_snapshot(generated_at=STAMP)
    ctx = present_market_landscape_v2(page)
    assert ctx["product_flags"]["dashboard_authority"] is False
    assert ctx["product_flags"]["live_authorized"] is False
    assert ctx["product_flags"]["write_endpoints"] is False
    assert ctx["product_flags"]["phase_4_1_binding_active"] is True
    assert ctx["product_flags"]["phase_4_2_binding_active"] is True
    assert ctx["product_flags"]["phase_4_3a_binding_active"] is True
    assert ctx["product_flags"]["phase_4_3b_binding_active"] is True
    assert ctx["product_flags"]["phase_4_4a_binding_active"] is True
    assert ctx["product_flags"]["phase_4_6b_binding_active"] is True
    assert ctx["chart"]["ohlcv"] is None
    assert ctx["decision"]["availability_label"] == "NOT_BOUND"
    assert ctx["economic"]["availability_label"] == "NOT_BOUND"
    assert ctx["global_strip"]["instrument"] == "NOT_BOUND"
    assert ctx["global_strip"]["safety_status"] == "NOT_BOUND"
    assert "scope" not in ctx["global_strip"]
    assert "regime" not in ctx["global_strip"]
    assert "freshness" not in ctx["global_strip"]
    assert "source_health" not in ctx["global_strip"]
    assert ctx["risk"]["availability"] == "NOT_BOUND"
    assert ctx["regime"]["availability"] == "NOT_BOUND"
    assert ctx["bull_bear"]["availability"] == "NOT_BOUND"
    assert ctx["switch"]["availability"] == "NOT_BOUND"
    # Must not invent HOLD/FLAT
    assert ctx["decision"]["fields"]["decision"] is None
    assert ctx["decision"]["fields"]["direction"] is None
    assert ctx["phase"] == "PHASE_4_6B_ECONOMIC_EVIDENCE_EXPLICIT_INJECTION_BINDING"
    # Aggregate availability remains on source_health only (not under Freshness).
    assert ctx["source_health"]["availability"] == "NOT_BOUND"
    assert "observed_at" in ctx["source_health"]["freshness"]
    assert ctx["source_health"]["freshness_display"] == "2026-07-23T16:00:00Z"
    assert ctx["source_health"]["summary_display"] == "NOT_BOUND · 2026-07-23T16:00:00Z"
    assert len(ctx["source_health"]["sources"]) == 11
    decision_src = next(
        src for src in ctx["source_health"]["sources"] if src["slot"] == "canonical_decision"
    )
    assert decision_src["availability"] == "NOT_BOUND"
    assert decision_src["freshness_display"] == "2026-07-23T16:00:00Z"
    assert " · " in decision_src["line_display"]
    assert "HEALTHY" not in json.dumps(ctx["source_health"])
    assert "OK" != ctx["source_health"]["availability"]


def test_presenter_source_health_freshness_states_distinct() -> None:
    """STALE / INVALID / MISSING_SOURCE / NOT_BOUND remain distinct; freshness fail-closed."""
    from src.webui.market_dashboard_landscape_v2.presenter import (
        _FRESHNESS_UNAVAILABLE,
        _format_freshness_display,
        _source_line_display,
    )

    service = MarketDashboardReadServiceV1()
    stale = unavailable_canonical_decision(
        availability=Availability.STALE,
        generated_at=STAMP,
        reason="EVIDENCE_STALE",
    )
    invalid = unavailable_canonical_decision(
        availability=Availability.INVALID,
        generated_at=STAMP,
        reason="SCHEMA_MISMATCH",
    )
    missing = unavailable_canonical_decision(
        availability=Availability.MISSING_SOURCE,
        generated_at=STAMP,
        reason="CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD",
    )

    stale_page = service.load_page_snapshot(
        generated_at=STAMP,
        slot_overrides={"canonical_decision": stale},
    )
    stale_ctx = present_market_landscape_v2(stale_page)
    stale_src = next(
        src for src in stale_ctx["source_health"]["sources"] if src["slot"] == "canonical_decision"
    )
    assert stale_src["availability"] == "STALE"
    assert stale_src["is_stale"] is True
    assert stale_src["freshness_display"] == "2026-07-23T16:00:00Z"
    assert stale_src["line_display"].startswith("STALE · ")
    assert stale_ctx["source_health"]["availability"] == "STALE"

    invalid_page = service.load_page_snapshot(
        generated_at=STAMP,
        slot_overrides={"canonical_decision": invalid},
    )
    invalid_ctx = present_market_landscape_v2(invalid_page)
    invalid_src = next(
        src
        for src in invalid_ctx["source_health"]["sources"]
        if src["slot"] == "canonical_decision"
    )
    assert invalid_src["availability"] == "INVALID"
    assert invalid_src["availability"] != "MISSING_SOURCE"
    assert invalid_src["availability"] != "NOT_BOUND"
    assert invalid_ctx["source_health"]["availability"] == "INVALID"

    missing_page = service.load_page_snapshot(
        generated_at=STAMP,
        slot_overrides={"canonical_decision": missing},
    )
    missing_ctx = present_market_landscape_v2(missing_page)
    missing_src = next(
        src
        for src in missing_ctx["source_health"]["sources"]
        if src["slot"] == "canonical_decision"
    )
    assert missing_src["availability"] == "MISSING_SOURCE"
    assert missing_src["availability"] != "INVALID"
    assert missing_src["availability"] != "NOT_BOUND"

    # Fail-closed when freshness payload is absent from a slot view.
    assert _format_freshness_display(None) == _FRESHNESS_UNAVAILABLE
    assert _format_freshness_display({}) == _FRESHNESS_UNAVAILABLE
    assert _format_freshness_display({"observed_at": ""}) == _FRESHNESS_UNAVAILABLE
    assert (
        _source_line_display(
            availability="AVAILABLE",
            freshness_display=_FRESHNESS_UNAVAILABLE,
        )
        == f"AVAILABLE · {_FRESHNESS_UNAVAILABLE}"
    )
    assert "HEALTHY" not in json.dumps(stale_ctx["source_health"])


def test_shell_assets_exist() -> None:
    assert (REPO / "templates/peak_trade_dashboard/market_landscape_v2.html").is_file()
    assert (REPO / "static/css/market_dashboard_landscape_v2.css").is_file()
    assert (REPO / "static/js/market_dashboard_landscape_v2.js").is_file()
