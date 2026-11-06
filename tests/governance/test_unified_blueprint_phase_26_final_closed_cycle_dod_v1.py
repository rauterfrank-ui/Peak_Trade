"""Governance proof for Unified Blueprint Phase 26 final closed-cycle DoD."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_phase_26_final_closed_cycle_dod_v1 import (
    INTEGRATION_CONFIG,
    MATRIX_CONFIG,
    REQUIREMENT_IDS,
    WORKPACKAGE_ID,
    Phase26ClosedCycleVerdict,
    build_phase_26_integration_summary_v1,
    compute_phase_26_closed_cycle_verdict_v1,
    count_matrix_statuses,
    load_closed_cycle_dod_matrix_v1,
    prove_unified_blueprint_phase_26_final_closed_cycle_dod_v1,
    validate_matrix_structure,
    validate_phase_26_authority_invariants,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_phase_26_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_phase_26_final_closed_cycle_dod_v1(repo_root=REPO_ROOT)


def test_closure_matrix_all_proven_current() -> None:
    matrix = load_closed_cycle_dod_matrix_v1(repo_root=REPO_ROOT)
    assert not validate_matrix_structure(matrix)
    counts = count_matrix_statuses(matrix)
    assert counts["PROVEN_CURRENT"] == len(REQUIREMENT_IDS)
    assert (
        compute_phase_26_closed_cycle_verdict_v1(matrix)
        == Phase26ClosedCycleVerdict.PROVEN_COMPLETE
    )


def test_phase_26_config_matches_matrix_verdict() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_phase_26_authority_invariants(doc)
    matrix = load_closed_cycle_dod_matrix_v1(repo_root=REPO_ROOT)
    assert (
        doc["final_closed_cycle_dod_verdict"]
        == compute_phase_26_closed_cycle_verdict_v1(matrix).value
    )
    assert doc["closed_cycle_proof"]["final_closed_cycle_dod_proven"] is True


def test_phase_26_summary_reproof() -> None:
    summary = build_phase_26_integration_summary_v1(repo_root=REPO_ROOT)
    assert summary["phase_26_closure_status"] == "PROVEN_COMPLETE"
    assert summary["authority_pins_proven"] is True
    assert all(summary["phase_16_25_reproof"].values())
    assert json.loads((REPO_ROOT / MATRIX_CONFIG).read_text(encoding="utf-8"))["requirements"]
