"""Decision-strip Blockers + Confidence operator-information fidelity (consumer-only)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    LANDSCAPE_PHASE43B_MAX_AGE_SECONDS,
)
from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
    project_double_play_snapshot_v1,
)
from src.webui.market_dashboard_landscape_v2.decision_double_play_observability_v1 import (
    CONFIDENCE_FIELD_STATE,
    build_decision_strip_blockers_presentation_v1,
    build_decision_strip_confidence_presentation_v1,
)
from src.webui.market_dashboard_landscape_v2.landscape_observability_common_v1 import (
    OPTIONAL_FIELD_ABSENT_DISPLAY,
)
from src.webui.market_dashboard_landscape_v2.unavailable import unavailable_double_play

STAMP = datetime(2026, 9, 21, 9, 0, 0, tzinfo=timezone.utc)
PRODUCER = datetime(2026, 9, 21, 8, 0, 0, tzinfo=timezone.utc)


def _dp(**kwargs: object):
    defaults = {
        "overall_status": "display_ready",
        "panel_summaries": (
            {
                "name": "composition",
                "status": "display_ready",
                "summary": "Composition panel fact",
                "blockers": (),
            },
        ),
        "blockers": ("DP_BLOCK_A", "DP_BLOCK_B"),
        "generated_at": PRODUCER,
        "effective_at": PRODUCER,
        "source_reference": "presentation://dp_test",
        "availability": Availability.AVAILABLE,
        "max_age_seconds": LANDSCAPE_PHASE43B_MAX_AGE_SECONDS,
        "is_stale": False,
        "display_only": True,
        "live_authorization": False,
    }
    defaults.update(kwargs)
    return project_double_play_snapshot_v1(**defaults)  # type: ignore[arg-type]


def test_blockers_from_double_play_only_when_available() -> None:
    view = build_decision_strip_blockers_presentation_v1(_dp())
    assert view["render"] is True
    assert view["source_slot"] == "double_play"
    assert view["availability"] == "AVAILABLE"
    assert view["display"] == "DP_BLOCK_A, DP_BLOCK_B"
    assert "reason" not in view["display"].lower()


def test_blockers_empty_when_available_is_not_available_token() -> None:
    view = build_decision_strip_blockers_presentation_v1(_dp(blockers=()))
    assert view["display"] == OPTIONAL_FIELD_ABSENT_DISPLAY
    assert view["codes"] == []


def test_blockers_missing_source_is_availability_only() -> None:
    snap = unavailable_double_play(
        availability=Availability.MISSING_SOURCE,
        generated_at=STAMP,
        reason="CANONICAL_DOUBLE_PLAY_DISPLAY_NOT_PERSISTED_FOR_DASHBOARD",
    )
    view = build_decision_strip_blockers_presentation_v1(snap)
    assert view["display"] == "MISSING_SOURCE"
    assert "CANONICAL_DOUBLE_PLAY" not in view["display"]
    assert view["codes"] == []


def test_confidence_suppressed_no_placeholder() -> None:
    view = build_decision_strip_confidence_presentation_v1()
    assert view["render"] is False
    assert view["field_state"] == CONFIDENCE_FIELD_STATE
    assert view["display"] == ""


def test_presenter_and_ssr_bind_blockers_and_hide_confidence() -> None:
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides={"double_play": _dp()},
    )
    ctx = present_market_landscape_v2(page)
    blockers = ctx["decision_double_play_observability"]["decision_strip_blockers"]
    confidence = ctx["decision_double_play_observability"]["decision_strip_confidence"]
    assert blockers["display"] == "DP_BLOCK_A, DP_BLOCK_B"
    assert confidence["render"] is False

    html = TestClient(create_app()).get("/market").text
    assert 'data-mdl-field="blockers"' in html
    assert 'data-mdl-confidence-render="false"' in html
    assert 'data-mdl-confidence-field-state="NOT_AVAILABLE_NO_CANONICAL_FIELD"' in html
    assert 'data-mdl-field="confidence"' not in html
    # Default host without DP injection remains fail-closed availability, not blank.
    blockers_chunk = html.split('data-mdl-field="blockers"', 1)[1].split("</dd>", 1)[0]
    text = blockers_chunk.split(">", 1)[1].strip()
    assert text
    assert text not in {"", "None", "null", "undefined"}
    assert "CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD" not in text


def test_no_decision_reason_codes_copied_into_blockers_on_default_route() -> None:
    html = TestClient(create_app()).get("/market").text
    decision = html.split('data-mdl-region="CANONICAL_DECISION_STRIP"', 1)[1].split(
        'data-mdl-region="DECISION_DOUBLE_PLAY_OBSERVABILITY"', 1
    )[0]
    blockers_dd = decision.split('data-mdl-field="blockers"', 1)[1].split("</dd>", 1)[0]
    assert "CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD" not in blockers_dd
    assert "MISSING_SOURCE ·" not in blockers_dd
