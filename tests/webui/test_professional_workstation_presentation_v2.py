"""Professional workstation V2 presentation composition (P2; presentation-only)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.webui.app import create_app


def test_market_route_exposes_workstation_composition_markers() -> None:
    response = TestClient(create_app()).get("/market")
    assert response.status_code == 200
    html = response.text
    assert 'data-mdl-composition="professional_workstation_v2"' in html
    assert "mdl-v2--workstation-v2" in html
    assert 'data-mdl-rail-stack="decision-panel"' in html
    assert 'data-mdl-field="strip_live_mark"' in html
    assert 'data-mdl-field="strip_decision"' in html


def test_required_landscape_regions_remain_present() -> None:
    response = TestClient(create_app()).get("/market")
    html = response.text
    for region in (
        "GLOBAL_SYSTEM_STRIP",
        "UNIVERSE_RANK_RAIL",
        "PRIMARY_MARKET_WORKSPACE",
        "SYSTEM_CONTEXT_RAIL",
        "CANONICAL_DECISION_STRIP",
        "SECONDARY_STATUS_REGION",
        "DECISION_DOUBLE_PLAY_OBSERVABILITY",
        "GOVERNANCE_DIAGNOSTICS_REGION",
        "EVENT_DECISION_TIMELINE",
        "ENGINEERING_DRAWER",
    ):
        assert f'data-mdl-region="{region}"' in html, region
