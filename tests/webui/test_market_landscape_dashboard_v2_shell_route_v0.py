"""Route / aggregate / presenter tests for Market Landscape V2 Phase 3 shell."""

from __future__ import annotations

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
    assert "PHASE_4_4A_CANONICAL_SAFETY_PROJECTION_BINDING" in html
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
    assert 'data-availability="MISSING_SOURCE"' in html
    assert "MISSING_SOURCE" in html
    # Safety strip value is MISSING_SOURCE without injection.
    assert ">MISSING_SOURCE</dd>" in html or "MISSING_SOURCE" in html
    assert "Risk / Sizing / Capital" in html
    assert "OPERATOR_SKELETON_APPROVAL" not in html
    assert "<button" not in html.lower()
    assert "Trigger Kill" not in html
    assert "Recover Kill" not in html


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
    assert ctx["chart"]["ohlcv"] is None
    assert ctx["decision"]["availability_label"] == "NOT_BOUND"
    assert ctx["global_strip"]["instrument"] == "NOT_BOUND"
    assert ctx["global_strip"]["safety_status"] == "NOT_BOUND"
    assert ctx["risk"]["availability"] == "NOT_BOUND"
    assert ctx["regime"]["availability"] == "NOT_BOUND"
    assert ctx["bull_bear"]["availability"] == "NOT_BOUND"
    assert ctx["switch"]["availability"] == "NOT_BOUND"
    # Must not invent HOLD/FLAT
    assert ctx["decision"]["fields"]["decision"] is None
    assert ctx["decision"]["fields"]["direction"] is None
    assert ctx["phase"] == "PHASE_4_4A_CANONICAL_SAFETY_PROJECTION_BINDING"


def test_shell_assets_exist() -> None:
    assert (REPO / "templates/peak_trade_dashboard/market_landscape_v2.html").is_file()
    assert (REPO / "static/css/market_dashboard_landscape_v2.css").is_file()
    assert (REPO / "static/js/market_dashboard_landscape_v2.js").is_file()
