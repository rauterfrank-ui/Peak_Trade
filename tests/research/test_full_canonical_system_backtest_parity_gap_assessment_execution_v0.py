from __future__ import annotations

import json
from pathlib import Path


def _artifact() -> dict:
    return json.loads(
        Path(
            "docs/research/full_canonical_system_backtest_parity_gap_assessment_execution_v0.json"
        ).read_text(encoding="utf-8")
    )


def test_full_canonical_gap_assessment_execution_is_authority_neutral() -> None:
    payload = _artifact()

    assert payload["authority_effect"] == "NONE"
    assert payload["execution_effect"] == "NONE"
    assert payload["adapter_actions_allowed"] is False
    assert payload["secret_material_allowed"] is False
    assert payload["production_execution_authorized"] is False
    assert payload["execution_path_change_admissible"] is False
    assert payload["system_economic_evidence_admissible"] is False


def test_full_canonical_gap_assessment_surfaces_are_complete_and_assessed() -> None:
    payload = _artifact()
    surfaces = payload["surfaces"]

    assert payload["verdict"] == (
        "PASS_FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_EXECUTION_READ_ONLY_V0"
    )
    assert payload["full_canonical_chain_wired_status"] == "ASSESSED_NOT_ASSERTED"
    assert payload["backtest_execution_decision_parity_status"] == "ASSESSED_NOT_ASSERTED"
    assert payload["summary"]["total_surfaces"] == 14
    assert len(surfaces) == 14
    assert all(surface["required_status"] == "ASSESSED" for surface in surfaces)
    assert all(surface["classification"] for surface in surfaces)
    assert all("reuse_first_integration_scope" in surface for surface in surfaces)


def test_full_canonical_gap_assessment_blocks_runtime_adjacent_stages() -> None:
    payload = _artifact()
    blocked = set(payload["blocked_steps"])

    assert "EXECUTION_PATH_CHANGE" in blocked
    assert "ZERO_EFFECT_EXECUTION_EVIDENCE" in blocked
    assert "SIMULATION_STAGE_SHADOW_EQUIVALENT" in blocked
    assert "SIMULATION_STAGE_PAPER_EQUIVALENT" in blocked
    assert "SIMULATION_STAGE_TEST_ENVIRONMENT" in blocked
    assert "PRODUCTION_EXECUTION" in blocked
    assert "ADAPTER_ACTION_DISPATCH" in blocked
    assert "SYSTEM_ECONOMIC_EVIDENCE_CLAIM" in blocked
