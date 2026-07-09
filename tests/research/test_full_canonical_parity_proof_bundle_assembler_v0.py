from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

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
    DEFAULT_PR5027_CLOSEOUT_EVIDENCE,
    DEFAULT_PR5028_CLOSEOUT_EVIDENCE,
    DEFAULT_PR5028_ELIGIBILITY_EVIDENCE,
    REASON_GAP_ASSESSMENT_NOT_ALL_PASS,
    REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P,
    REASON_SOURCE_EVIDENCE_MISSING,
    REQUIRED_PROOF_INPUT_SPECS,
    SLICE_CHANGED_FILES,
    build_required_proof_inputs_matrix,
    build_surface_coverage_matrix,
    collect_source_evidence_refs,
    evaluate_proof_bundle,
    scan_assembler_forbidden_positive_claims,
    verify_manifest,
    write_manifest,
)

REPO_ROOT = Path.cwd()


@pytest.fixture(scope="module")
def module_proof_bundle() -> dict[str, Any]:
    return evaluate_proof_bundle(REPO_ROOT)


def _repo_head(repo_root: Path) -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root)).decode().strip()
    )


def _write_verified_evidence_dir(
    evidence_dir: Path,
    *,
    post_merge_head: str,
    extra_files: dict[str, str] | None = None,
) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "final_report.txt").write_text(
        "\n".join(
            [
                f"POST_MERGE_HEAD={post_merge_head}",
                f"POST_MERGE_ORIGIN_MAIN={post_merge_head}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "git_context.txt").write_text(
        f"HEAD={post_merge_head}\nORIGIN_MAIN={post_merge_head}\n",
        encoding="utf-8",
    )
    if extra_files:
        for name, content in extra_files.items():
            (evidence_dir / name).write_text(content, encoding="utf-8")
    assert write_manifest(evidence_dir) == 0


def _build_verified_source_evidence_fixture(
    tmp_path: Path,
    repo_root: Path,
    *,
    origin_main: str | None = None,
) -> tuple[Path, Path, Path, Path, str]:
    if origin_main is None:
        origin_main = _repo_head(repo_root)
    pr5020 = tmp_path / "pr5020_closeout"
    pr5027 = tmp_path / "pr5027_closeout"
    pr5028 = tmp_path / "pr5028_closeout"
    eligibility = tmp_path / "pr5028_eligibility"
    _write_verified_evidence_dir(pr5020, post_merge_head=origin_main)
    _write_verified_evidence_dir(pr5027, post_merge_head=origin_main)
    _write_verified_evidence_dir(
        pr5028,
        post_merge_head=origin_main,
        extra_files={
            "final_report.txt": (
                "\n".join(
                    [
                        f"POST_MERGE_HEAD={origin_main}",
                        f"POST_MERGE_ORIGIN_MAIN={origin_main}",
                        f"SOURCE_EVIDENCE_DIR={eligibility}",
                        "SOURCE_MANIFEST_VERIFY_RC=0",
                        "SOURCE_EVIDENCE_REFERENCED=true",
                    ]
                )
                + "\n"
            ),
        },
    )
    _write_verified_evidence_dir(eligibility, post_merge_head=origin_main)
    return pr5020, pr5027, pr5028, eligibility, origin_main


def test_proof_bundle_schema_and_fail_closed_status(module_proof_bundle: dict[str, Any]) -> None:
    bundle = module_proof_bundle
    assert bundle["schema"] == ASSEMBLER_SCHEMA
    assert bundle["assembler_id"] == ASSEMBLER_ID
    assert bundle["full_parity_proof_bundle_status"] == "NOT_PROVEN_FAIL_CLOSED"
    assert bundle["chain_surface_binding_complete"] is True
    assert bundle["next_unbound_node"] == "NONE"
    assert bundle["boundary_chain_status"] == "FAIL_CLOSED_DOCUMENTED"
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
    assert bundle["required_proof_input_count"] == 16
    assert bundle["satisfied_proof_input_count"] == 16
    assert bundle["required_proof_inputs_complete"] is True
    assert bundle["missing_proof_input_ids"] == []
    assert bundle["no_runtime_authority_confirmed"] is True
    assert bundle["no_economic_claim_confirmed"] is True


def test_required_proof_inputs_matrix_accounts_for_all_sixteen_surfaces() -> None:
    matrix = build_required_proof_inputs_matrix(REPO_ROOT)
    assert matrix["required_proof_input_count"] == 16
    assert len(matrix["proof_inputs"]) == 16
    assert [spec.proof_input_id for spec in REQUIRED_PROOF_INPUT_SPECS] == [
        item["proof_input_id"] for item in matrix["proof_inputs"]
    ]
    surface_p = next(item for item in matrix["proof_inputs"] if item["surface_id"] == "P")
    assert surface_p["status"] == "VERIFIED"
    assert surface_p["binding_status"] == "VERIFIED"
    assert surface_p["parity_status"] == "PARTIAL"
    assert surface_p["registry_parity_status"] == "PARTIAL"
    assert surface_p["satisfied"] is True


def test_proof_bundle_reports_gap_assessment_blocker_when_proof_inputs_complete(
    tmp_path: Path,
) -> None:
    repo_root = Path.cwd()
    pr5020, pr5027, pr5028, eligibility, origin_main = _build_verified_source_evidence_fixture(
        tmp_path,
        repo_root,
        origin_main="1fecc0566ccc5d0b9ffd7e0cc9d485f88a63729b",
    )
    bundle = evaluate_proof_bundle(
        repo_root,
        pr5020_closeout_dir=pr5020,
        pr5027_closeout_dir=pr5027,
        pr5028_closeout_dir=pr5028,
        pr5028_eligibility_dir=eligibility,
        current_origin_main=origin_main,
    )
    assert bundle["required_proof_inputs_complete"] is True
    assert bundle["satisfied_proof_input_count"] == 16
    assert bundle["next_blocker"] == REASON_GAP_ASSESSMENT_NOT_ALL_PASS
    assert REASON_GAP_ASSESSMENT_NOT_ALL_PASS in bundle["reason_codes"]
    assert bundle["gap_assessment_all_pass"] is False
    assert bundle["source_evidence_all_manifests_verified"] is True
    assert bundle["source_evidence_missing"] == []


def test_proof_bundle_reports_missing_surface_p_proof_input_when_binding_unsatisfied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    pr5020, pr5027, pr5028, eligibility, origin_main = _build_verified_source_evidence_fixture(
        tmp_path,
        repo_root,
        origin_main="1fecc0566ccc5d0b9ffd7e0cc9d485f88a63729b",
    )

    def _unsatisfied_binding(_repo_root: Path):
        from trading.master_v2.surface_p_required_proof_input_binding_v0 import (
            SurfacePRequiredProofInputBindingResultV0,
        )

        return SurfacePRequiredProofInputBindingResultV0(
            proof_input_id="backtest_offline_replay_runtime_decision_parity",
            surface_id="P",
            label="Backtest / Offline Replay / Runtime decision parity proof eligibility evidence",
            owner="trading.master_v2.surface_p_required_proof_input_binding_v0",
            binding_status="MISSING_REQUIRED_PROOF_INPUT_SURFACE_P",
            satisfied=False,
            registry_parity_status="PARTIAL",
            offline_four_way_fixtures_complete=False,
            semantic_binding_confirmations_complete=False,
            surface_p_offline_parity_complete=False,
            runtime_bridge_bound_not_activated=False,
            owner_evidence_refs_present=False,
            evidence_ref_count=0,
            present_evidence_ref_count=0,
            missing_evidence_refs=("missing/evidence.py",),
            detail="offline_four_way_fixtures_incomplete",
            fail_closed_reasons=(REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P,),
            full_canonical_chain_wired=False,
            backtest_runtime_decision_parity_pass=False,
            system_economic_evidence_admissible=False,
            runtime_rewire_admissible=False,
            claim_promotion_allowed=False,
            no_runtime_authority_confirmed=True,
            no_economic_claim_confirmed=True,
        )

    monkeypatch.setattr(
        "trading.master_v2.surface_p_required_proof_input_binding_v0.evaluate_surface_p_required_proof_input_binding_v0",
        _unsatisfied_binding,
    )
    bundle = evaluate_proof_bundle(
        repo_root,
        pr5020_closeout_dir=pr5020,
        pr5027_closeout_dir=pr5027,
        pr5028_closeout_dir=pr5028,
        pr5028_eligibility_dir=eligibility,
        current_origin_main=origin_main,
    )
    assert bundle["required_proof_inputs_complete"] is False
    assert bundle["next_blocker"] == REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P
    assert REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P in bundle["reason_codes"]


def test_proof_bundle_reports_missing_source_evidence_without_local_archive(
    module_proof_bundle: dict[str, Any],
) -> None:
    closeout_5020 = Path(
        os.environ.get("PEAK_TRADE_PR5020_CLOSEOUT_EVIDENCE", DEFAULT_PR5020_CLOSEOUT_EVIDENCE)
    )
    if closeout_5020.is_dir():
        return
    bundle = module_proof_bundle
    assert bundle["next_blocker"] == REASON_SOURCE_EVIDENCE_MISSING
    assert REASON_SOURCE_EVIDENCE_MISSING in bundle["reason_codes"]
    assert bundle["source_evidence_missing"]


def test_proof_bundle_verifies_source_evidence_manifests_when_available(
    module_proof_bundle: dict[str, Any],
) -> None:
    bundle = module_proof_bundle
    assert bundle["source_evidence_count"] == 4
    closeout_5020 = Path(
        os.environ.get("PEAK_TRADE_PR5020_CLOSEOUT_EVIDENCE", DEFAULT_PR5020_CLOSEOUT_EVIDENCE)
    )
    closeout_5027 = Path(
        os.environ.get("PEAK_TRADE_PR5027_CLOSEOUT_EVIDENCE", DEFAULT_PR5027_CLOSEOUT_EVIDENCE)
    )
    closeout_5028 = Path(
        os.environ.get("PEAK_TRADE_PR5028_CLOSEOUT_EVIDENCE", DEFAULT_PR5028_CLOSEOUT_EVIDENCE)
    )
    eligibility_5028 = Path(
        os.environ.get(
            "PEAK_TRADE_PR5028_ELIGIBILITY_EVIDENCE", DEFAULT_PR5028_ELIGIBILITY_EVIDENCE
        )
    )
    if all(
        path.is_dir() for path in (closeout_5020, closeout_5027, closeout_5028, eligibility_5028)
    ):
        assert bundle["source_evidence_all_manifests_verified"] is True
        assert bundle["source_evidence_missing"] == []
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
        pr5027_closeout_dir=tmp_path / "b",
        pr5028_closeout_dir=tmp_path / "c",
        pr5028_eligibility_dir=tmp_path / "d",
        current_origin_main="deadbeef",
        repo_root=Path.cwd(),
    )
    assert len(refs) == 4
    assert all(not ref.present for ref in refs)
    assert all(not ref.manifest_verified for ref in refs)


def test_forbidden_positive_claims_scan_allows_context_protected_literals() -> None:
    violations = scan_assembler_forbidden_positive_claims(Path.cwd(), list(SLICE_CHANGED_FILES))
    assert violations == []


def test_proof_bundle_does_not_promote_positive_claims(
    module_proof_bundle: dict[str, Any],
) -> None:
    bundle = module_proof_bundle
    assert bundle["full_canonical_chain_wired"] is False
    assert bundle["backtest_runtime_decision_parity_pass"] is False
    assert bundle["claim_promotion_allowed"] is False
    assert bundle["system_economic_evidence_admissible"] is False
    assert bundle["runtime_rewire_admissible"] is False
