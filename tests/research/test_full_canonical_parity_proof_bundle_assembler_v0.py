from __future__ import annotations

import os
from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    TRACE_PRIORITY,
    TRACE_REWIRE_BOUND_STATE,
)
from scripts.research.full_canonical_parity_pass_eligibility_gate_v0 import (
    DEFAULT_PR5020_CLOSEOUT_EVIDENCE,
    REASON_GAP_ASSESSMENT_NOT_ALL_PASS,
)
from scripts.research.full_canonical_parity_proof_bundle_assembler_v0 import (
    ASSEMBLER_ID,
    ASSEMBLER_SCHEMA,
    DEFAULT_PR5021_CLOSEOUT_EVIDENCE,
    DEFAULT_PR5021_ELIGIBILITY_EVIDENCE,
    REASON_SEMANTIC_PARITY_NOT_PROVEN,
    SLICE_CHANGED_FILES,
    build_surface_coverage_matrix,
    collect_source_evidence_refs,
    evaluate_proof_bundle,
    scan_assembler_forbidden_positive_claims,
    verify_manifest,
)


def test_proof_bundle_schema_and_fail_closed_status() -> None:
    bundle = evaluate_proof_bundle(Path.cwd())
    assert bundle["schema"] == ASSEMBLER_SCHEMA
    assert bundle["assembler_id"] == ASSEMBLER_ID
    assert bundle["full_parity_proof_bundle_status"] == "NOT_PROVEN_FAIL_CLOSED"
    assert bundle["chain_surface_binding_complete"] is True
    assert bundle["next_unbound_node"] == "NONE"
    assert bundle["parity_pass_claim_deferred"] is True
    assert bundle["full_canonical_chain_wired"] is False
    assert bundle["backtest_runtime_decision_parity_pass"] is False
    assert bundle["system_economic_evidence_admissible"] is False
    assert bundle["runtime_rewire_admissible"] is False
    assert bundle["claim_promotion_allowed"] is False
    assert bundle["surface_coverage_complete"] is True
    assert bundle["required_surface_count"] == 12
    assert bundle["covered_surface_count"] == 12
    assert bundle["missing_surfaces"] == []
    assert bundle["no_runtime_authority_confirmed"] is True
    assert bundle["no_economic_claim_confirmed"] is True


def test_proof_bundle_reports_gap_assessment_as_next_blocker() -> None:
    bundle = evaluate_proof_bundle(Path.cwd())
    assert bundle["next_blocker"] == REASON_GAP_ASSESSMENT_NOT_ALL_PASS
    assert REASON_GAP_ASSESSMENT_NOT_ALL_PASS in bundle["reason_codes"]
    assert REASON_SEMANTIC_PARITY_NOT_PROVEN in bundle["reason_codes"]
    assert bundle["gap_assessment_all_pass"] is False


def test_proof_bundle_verifies_source_evidence_manifests_when_available() -> None:
    bundle = evaluate_proof_bundle(Path.cwd())
    assert bundle["source_evidence_count"] == 3
    closeout_5020 = Path(
        os.environ.get("PEAK_TRADE_PR5020_CLOSEOUT_EVIDENCE", DEFAULT_PR5020_CLOSEOUT_EVIDENCE)
    )
    closeout_5021 = Path(
        os.environ.get("PEAK_TRADE_PR5021_CLOSEOUT_EVIDENCE", DEFAULT_PR5021_CLOSEOUT_EVIDENCE)
    )
    eligibility_5021 = Path(
        os.environ.get(
            "PEAK_TRADE_PR5021_ELIGIBILITY_EVIDENCE", DEFAULT_PR5021_ELIGIBILITY_EVIDENCE
        )
    )
    if all(path.is_dir() for path in (closeout_5020, closeout_5021, eligibility_5021)):
        assert bundle["source_evidence_all_manifests_verified"] is True
        assert bundle["source_evidence_missing"] == []
        assert bundle["stale_source_evidence_detected"] is False
        for ref in bundle["source_evidence_refs"]:
            assert ref["manifest_verified"] is True


def test_surface_coverage_matrix_covers_all_twelve_surfaces() -> None:
    from scripts.research.full_canonical_parity_closure_assessment_v0 import (
        build_closure_assessment,
    )

    coverage = build_surface_coverage_matrix(build_closure_assessment(Path.cwd()))
    assert coverage["required_surface_count"] == 12
    assert coverage["covered_surface_count"] == 12
    assert coverage["surface_coverage_complete"] is True
    assert coverage["missing_surfaces"] == []
    for surface in coverage["surfaces"]:
        assert surface["trace_state"] == TRACE_REWIRE_BOUND_STATE
        assert surface["meets_required_binding"] is True
    assert [surface["surface_id"] for surface in coverage["surfaces"]] == list(TRACE_PRIORITY)


def test_verify_manifest_returns_false_for_missing_directory(tmp_path: Path) -> None:
    ok, detail = verify_manifest(tmp_path / "missing")
    assert ok is False
    assert "missing" in detail


def test_collect_source_evidence_refs_detects_missing_directories(tmp_path: Path) -> None:
    refs = collect_source_evidence_refs(
        pr5020_closeout_dir=tmp_path / "a",
        pr5021_closeout_dir=tmp_path / "b",
        pr5021_eligibility_dir=tmp_path / "c",
        current_origin_main="deadbeef",
        repo_root=Path.cwd(),
    )
    assert len(refs) == 3
    assert all(not ref.present for ref in refs)
    assert all(not ref.manifest_verified for ref in refs)


def test_forbidden_positive_claims_scan_allows_context_protected_literals() -> None:
    violations = scan_assembler_forbidden_positive_claims(Path.cwd(), list(SLICE_CHANGED_FILES))
    assert violations == []


def test_proof_bundle_does_not_promote_positive_claims() -> None:
    bundle = evaluate_proof_bundle(Path.cwd())
    assert bundle["full_canonical_chain_wired"] is False
    assert bundle["backtest_runtime_decision_parity_pass"] is False
    assert bundle["claim_promotion_allowed"] is False
    assert bundle["system_economic_evidence_admissible"] is False
    assert bundle["runtime_rewire_admissible"] is False
