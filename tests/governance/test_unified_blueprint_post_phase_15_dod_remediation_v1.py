"""Governance proof for Post–Phase 15 Unified Blueprint DoD remediation."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_post_phase_15_dod_remediation_v1 import (
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    build_remediation_summary_v1,
    prove_data_substrate_bounded_closure_v1,
    prove_failure_memory_bounded_closure_v1,
    prove_parameter_lineage_bounded_closure_v1,
    prove_unified_blueprint_post_phase_15_dod_remediation_v1,
)
from src.governance.unified_blueprint_phase_15_final_dod_v1 import (
    compute_unified_blueprint_dod_verdict_v1,
    load_final_dod_matrix_v1,
    UnifiedBlueprintDodVerdict,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_post_phase_15_remediation_proof_passes() -> None:
    assert prove_unified_blueprint_post_phase_15_dod_remediation_v1(repo_root=REPO_ROOT)


def test_bounded_family_closure_proofs() -> None:
    assert prove_data_substrate_bounded_closure_v1(repo_root=REPO_ROOT)
    assert prove_failure_memory_bounded_closure_v1(repo_root=REPO_ROOT)
    assert prove_parameter_lineage_bounded_closure_v1(repo_root=REPO_ROOT)


def test_remediation_preserves_runtime_apply_out_of_scope() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    out = doc["runtime_apply_out_of_scope"]
    assert out["authorized_promotion_implies_runtime_apply"] is False
    assert out["runtime_apply_authority_owner_ratified"] is False
    assert out["owner_decision_required_for_runtime_apply"] is True
    inv = doc["authority_invariants"]
    assert inv["runtime_apply_started"] is False
    assert inv["m11_started"] is False


def test_remediation_yields_13_of_13_proven_matrix() -> None:
    matrix = load_final_dod_matrix_v1(repo_root=REPO_ROOT)
    verdict = compute_unified_blueprint_dod_verdict_v1(matrix)
    assert verdict == UnifiedBlueprintDodVerdict.PROVEN_COMPLETE


def test_remediation_summary_records_family_proofs() -> None:
    summary = build_remediation_summary_v1(repo_root=REPO_ROOT)
    proofs = summary["family_closure_proofs"]
    assert proofs["data_substrate"] is True
    assert proofs["failure_memory"] is True
    assert proofs["parameter_lineage"] is True
