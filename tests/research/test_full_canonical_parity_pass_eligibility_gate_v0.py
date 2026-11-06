from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.research.full_canonical_parity_pass_eligibility_gate_v0 import (
    CLOSEOUT_RUNNER_SKIP_TESTS_CONTRACT_DEFECT,
    DEFAULT_PR5027_CLOSEOUT_EVIDENCE,
    GATE_ID,
    GATE_SCHEMA,
    NEXT_STEP_AFTER_ELIGIBLE,
    NEXT_STEP_AFTER_NOT_ELIGIBLE,
    REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING,
    REASON_PROOF_BUNDLE_HEAD_MISMATCH,
    REASON_PROOF_BUNDLE_MANIFEST_UNVERIFIED,
    SLICE_CHANGED_FILES,
    build_eligibility_gate,
    scan_gate_forbidden_positive_claims,
    verify_proof_bundle_binding,
    write_manifest,
    collect_evidence,
)

REPO_ROOT = Path.cwd()


def _repo_head(repo_root: Path) -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root)).decode().strip()
    )


def _write_verified_proof_bundle_dir(
    evidence_dir: Path,
    *,
    post_merge_head: str,
    bundle_status: str = "PROVEN_MANIFEST_VERIFIED",
) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "git_context.txt").write_text(
        f"HEAD={post_merge_head}\nORIGIN_MAIN={post_merge_head}\n",
        encoding="utf-8",
    )
    (evidence_dir / "proof_bundle.json").write_text(
        json.dumps({"full_parity_proof_bundle_status": bundle_status}) + "\n",
        encoding="utf-8",
    )
    assert write_manifest(evidence_dir) == 0


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


def test_eligibility_gate_passes_with_manifest_verified_current_head_proof_bundle(
    tmp_path: Path,
) -> None:
    head = _repo_head(REPO_ROOT)
    proof_bundle = tmp_path / "proof_bundle"
    _write_verified_proof_bundle_dir(proof_bundle, post_merge_head=head)
    gate = build_eligibility_gate(REPO_ROOT, proof_bundle_dir=proof_bundle, current_head=head)
    assert gate["full_canonical_parity_pass_eligible"] is True
    assert gate["assessment_verdict"] == "PASS_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0"
    assert gate["parity_pass_eligibility_status"] == "ELIGIBLE_FOR_SEPARATE_PARITY_PASS_EVIDENCE"
    assert gate["primary_blocker"] == "NONE"
    assert gate["next_gap_or_next_step"] == NEXT_STEP_AFTER_ELIGIBLE
    assert gate["full_canonical_chain_wired"] is False
    assert gate["backtest_runtime_decision_parity_pass"] is False
    assert gate["system_economic_evidence_admissible"] is False


def test_verify_proof_bundle_binding_fails_on_head_mismatch(tmp_path: Path) -> None:
    proof_bundle = tmp_path / "proof_bundle"
    _write_verified_proof_bundle_dir(proof_bundle, post_merge_head="deadbeef" * 5)
    binding = verify_proof_bundle_binding(proof_bundle, current_head=_repo_head(REPO_ROOT))
    assert binding["manifest_verified_full_parity_proof_bundle"] is False
    assert binding["proof_bundle_head_equals_current_head"] is False
    assert binding["blocker_code"] == REASON_PROOF_BUNDLE_HEAD_MISMATCH


def test_verify_proof_bundle_binding_fails_on_unverified_manifest(tmp_path: Path) -> None:
    proof_bundle = tmp_path / "proof_bundle"
    proof_bundle.mkdir(parents=True)
    (proof_bundle / "proof_bundle.json").write_text(
        json.dumps({"full_parity_proof_bundle_status": "PROVEN_MANIFEST_VERIFIED"}) + "\n",
        encoding="utf-8",
    )
    binding = verify_proof_bundle_binding(proof_bundle, current_head=_repo_head(REPO_ROOT))
    assert binding["manifest_verified"] is False
    assert binding["manifest_verify_rc"] == 1
    assert binding["blocker_code"] == REASON_PROOF_BUNDLE_MANIFEST_UNVERIFIED


def test_eligibility_gate_fails_closed_on_head_mismatch_proof_bundle(tmp_path: Path) -> None:
    proof_bundle = tmp_path / "proof_bundle"
    _write_verified_proof_bundle_dir(proof_bundle, post_merge_head="deadbeef" * 5)
    gate = build_eligibility_gate(
        REPO_ROOT,
        proof_bundle_dir=proof_bundle,
        current_head=_repo_head(REPO_ROOT),
    )
    assert gate["full_canonical_parity_pass_eligible"] is False
    assert gate["primary_blocker"] == REASON_PROOF_BUNDLE_HEAD_MISMATCH


def test_collect_evidence_skip_tests_requires_verified_proof_bundle_dir(tmp_path: Path) -> None:
    result = collect_evidence(
        REPO_ROOT,
        output_dir=tmp_path / "evidence",
        skip_tests=True,
        proof_bundle_dir=None,
    )
    assert result["verdict"] == CLOSEOUT_RUNNER_SKIP_TESTS_CONTRACT_DEFECT


def test_collect_evidence_skip_tests_does_not_invoke_pytest(tmp_path: Path, monkeypatch) -> None:
    head = _repo_head(REPO_ROOT)
    proof_bundle = tmp_path / "proof_bundle"
    _write_verified_proof_bundle_dir(proof_bundle, post_merge_head=head)
    pytest_invoked = False
    import scripts.research.full_canonical_parity_pass_eligibility_gate_v0 as gate_mod

    original_run = gate_mod._run

    def _guarded_run(cmd, **kwargs):
        nonlocal pytest_invoked
        if "pytest" in cmd:
            pytest_invoked = True
        return original_run(cmd, **kwargs)

    monkeypatch.setattr(gate_mod, "_run", _guarded_run)
    result = collect_evidence(
        REPO_ROOT,
        output_dir=tmp_path / "evidence",
        skip_tests=True,
        proof_bundle_dir=proof_bundle,
        source_gap_inventory_bundle=tmp_path / "missing_source",
    )
    assert pytest_invoked is False
    assert result["verdict"] == "PASS_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0"
