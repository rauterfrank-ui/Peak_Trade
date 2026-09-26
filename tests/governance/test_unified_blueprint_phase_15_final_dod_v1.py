"""Governance proof for Unified Blueprint Phase 15 final DoD adjudication."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_phase_15_final_dod_v1 import (
    DOD_FAMILY_IDS,
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    UnifiedBlueprintDodVerdict,
    build_phase_15_integration_summary_v1,
    compute_unified_blueprint_dod_verdict_v1,
    count_classifications,
    load_final_dod_matrix_v1,
    prove_global_negative_authority_invariants_v1,
    prove_unified_blueprint_phase_15_final_dod_v1,
    validate_phase_15_authority_invariants,
    validate_phase_15_runtime,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_phase_15_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_phase_15_final_dod_v1(repo_root=REPO_ROOT)


def test_phase_15_authority_invariants_and_runtime() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_phase_15_authority_invariants(doc)
    assert not validate_phase_15_runtime(REPO_ROOT, doc)


def test_matrix_covers_all_dod_families_with_truthful_verdict() -> None:
    matrix = load_final_dod_matrix_v1(repo_root=REPO_ROOT)
    counts = count_classifications(matrix)
    assert len(DOD_FAMILY_IDS) == 13
    assert sum(counts.values()) == 13
    verdict = compute_unified_blueprint_dod_verdict_v1(matrix)
    assert verdict == UnifiedBlueprintDodVerdict.PARTIAL
    assert counts["PARTIAL"] >= 1
    assert counts["PROVEN"] >= 1
    assert _doc()["unified_blueprint_dod_verdict"] == verdict.value


def test_partial_families_are_data_substrate_parameter_lineage_failure_memory() -> None:
    matrix = load_final_dod_matrix_v1(repo_root=REPO_ROOT)
    by_id = {row["dod_family"]: row for row in matrix["dod_families"]}
    assert by_id["DATA_SUBSTRATE"]["classification"] == "PARTIAL"
    assert by_id["PARAMETER_LINEAGE"]["classification"] == "PARTIAL"
    assert by_id["FAILURE_MEMORY"]["classification"] == "PARTIAL"


def test_global_negative_authority_invariants() -> None:
    assert prove_global_negative_authority_invariants_v1(repo_root=REPO_ROOT)
    inv = _doc()["global_negative_authority_invariants"]
    assert inv["authorized_promotion_implies_runtime_apply"] is False
    assert inv["optimization_promotion_authority"] == "NONE"
    assert inv["attribution_authority"] == "NONE"


def test_phase_15_summary_records_m11_outside_default() -> None:
    summary = build_phase_15_integration_summary_v1(repo_root=REPO_ROOT)
    assert summary["phase_15_final_dod_adjudication_status"] == "PROVEN_COMPLETE"
    assert summary["unified_blueprint_dod_verdict"] == "PARTIAL"
    assert summary["cross_phase_0_14_reproof"]["all_pass"] is True
    assert summary["m11_outside_default_completion"] is True
