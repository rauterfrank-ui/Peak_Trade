"""Excluded Landscape V2 surfaces cleanup contracts (consumer-only)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import create_app

REPO = Path(__file__).resolve().parents[2]
ADJUDICATION = (
    REPO
    / "docs"
    / "ops"
    / "market_dashboard"
    / "MARKET_DASHBOARD_LANDSCAPE_V2_EXCLUDED_SURFACES_CLEANUP_ADJUDICATION_V1.md"
)
TEMPLATE = REPO / "templates" / "peak_trade_dashboard" / "market_landscape_v2.html"


def test_adjudication_artifact_present() -> None:
    text = ADJUDICATION.read_text(encoding="utf-8")
    assert "MARKET_DASHBOARD_LANDSCAPE_V2_EXCLUDED_SURFACES_CLEANUP_V1" in text
    assert "UNKNOWN_SET=" in text


def test_duplicate_timeline_note_removed_honest_region_remains() -> None:
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "multi_decision_timeline_status" not in html
    assert 'data-mdl-region="EVENT_DECISION_TIMELINE"' in html


def test_confidence_template_has_no_unreachable_render_branch() -> None:
    html = TEMPLATE.read_text(encoding="utf-8")
    assert 'data-mdl-field="confidence"' not in html
    assert (
        "{% if decision_double_play_observability.decision_strip_confidence.render %}" not in html
    )
    assert "data-mdl-confidence-render" in html


def test_ssr_excluded_surfaces_cleanup_invariants() -> None:
    page = TestClient(create_app()).get("/market").text
    assert 'data-mdl-field="multi_decision_timeline_status"' not in page
    assert 'data-mdl-region="EVENT_DECISION_TIMELINE"' in page
    assert 'data-mdl-confidence-render="false"' in page
    assert 'data-mdl-field="confidence"' not in page
    assert 'data-mdl-field="autonomy_stage"' in page
    assert 'data-mdl-ops="diagnostics_summary"' in page
