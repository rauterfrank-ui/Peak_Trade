from __future__ import annotations

import os
from pathlib import Path

from scripts.research.full_canonical_parity_pass_eligibility_gate_v0 import (
    DEFAULT_PR5027_CLOSEOUT_EVIDENCE,
    GATE_ID,
    GATE_SCHEMA,
    NEXT_STEP_AFTER_NOT_ELIGIBLE,
    REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING,
    SLICE_CHANGED_FILES,
    build_eligibility_gate,
    scan_gate_forbidden_positive_claims,
)


def test_eligibility_gate_schema_and_fail_closed_status() -> None:
    gate = build_eligibility_gate(Path.cwd())
    assert gate["schema"] == GATE_SCHEMA
    assert gate["gate_id"] == GATE_ID
    assert gate["assessment_verdict"] == "PASS_ASSESSMENT_FAIL_CLOSED"
    assert gate["boundary_chain_status"] == "FAIL_CLOSED_DOCUMENTED"
    assert gate["trace_next_unbound_node"] == "NONE"
    assert gate["chain_surface_binding_complete"] is True
    assert gate["next_unbound_node"] == "NONE"
    assert gate["gap_records_count"] == 0
    assert gate["runtime_bridge_boundary_status"] == "BOUND_NOT_ACTIVATED"
    assert gate["parity_pass_claim_deferred"] is True
    assert gate["full_canonical_chain_wired"] is False
    assert gate["backtest_runtime_decision_parity_pass"] is False
    assert gate["system_economic_evidence_admissible"] is False
    assert gate["runtime_rewire_admissible"] is False
    assert gate["parity_pass_eligibility_status"] == "NOT_ELIGIBLE_FAIL_CLOSED"
    assert gate["claim_promotion_allowed"] is False
    assert gate["primary_blocker"] == REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING
    assert gate["next_gap_or_next_step"] == NEXT_STEP_AFTER_NOT_ELIGIBLE
    assert gate["next_blocker"] == REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING
    assert gate["no_runtime_authority_confirmed"] is True
    assert gate["no_economic_claim_confirmed"] is True


def test_eligibility_gate_reports_manifest_proof_as_first_blocker() -> None:
    gate = build_eligibility_gate(Path.cwd())
    failed = [
        item for item in gate["eligibility_criteria"] if item["required"] and not item["satisfied"]
    ]
    assert failed
    assert failed[0]["criterion_id"] == "manifest_verified_full_parity_proof_bundle"
    assert (
        REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING
        in gate["evidence_admissibility_reason_codes"]
    )


def test_eligibility_gate_verifies_pr5027_closeout_manifest_when_reference_available() -> None:
    gate = build_eligibility_gate(Path.cwd())
    closeout_dir = Path(
        os.environ.get("PEAK_TRADE_PR5027_CLOSEOUT_EVIDENCE", DEFAULT_PR5027_CLOSEOUT_EVIDENCE)
    )
    if closeout_dir.is_dir():
        assert gate["source_pr5027_closeout_manifest_verified"] is True
        assert gate["source_pr5027_closeout_reference_status"] == "VERIFIED"
        assert "merge_closeout_pr5027" in gate["source_pr5027_closeout_dir"]
    else:
        assert gate["source_pr5027_closeout_manifest_verified"] is False
        assert gate["source_pr5027_closeout_reference_status"] == "NOT_AVAILABLE_OFFLINE_REFERENCE"


def test_eligibility_gate_does_not_promote_positive_claims() -> None:
    gate = build_eligibility_gate(Path.cwd())
    assert gate["full_canonical_chain_wired"] is False
    assert gate["backtest_runtime_decision_parity_pass"] is False
    assert gate["claim_promotion_allowed"] is False


def test_eligibility_gate_binds_required_proof_inputs_from_closure_assessment() -> None:
    gate = build_eligibility_gate(Path.cwd())
    assert gate["required_proof_input_count"] == 16
    assert gate["satisfied_proof_input_count"] == 16
    assert gate["required_proof_inputs_complete"] is True
    assert gate["missing_proof_input_ids"] == []
    criterion = next(
        item
        for item in gate["eligibility_criteria"]
        if item["criterion_id"] == "required_proof_inputs_complete"
    )
    assert criterion["satisfied"] is True


def test_forbidden_positive_claims_scan_allows_context_protected_literals() -> None:
    violations = scan_gate_forbidden_positive_claims(Path.cwd(), list(SLICE_CHANGED_FILES))
    assert violations == []
