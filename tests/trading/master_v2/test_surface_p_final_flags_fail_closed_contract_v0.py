"""Surface P final flags fail-closed contract tests (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    ALLOWED_SLICE_CHANGED_PATH_PREFIXES,
    render_parity_gap_matrix_json_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.legacy_runtime_entrypoint_guard_v0 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
)
from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
    CONTRACT_NAME,
    CONTRACT_SLICE_ID,
    DIRECT_TRUE_FLAG_ASSIGNMENT,
    PACKAGE_MARKER,
    PROMOTION_SLICE_ID,
    REASON_ELIGIBILITY_HEAD_STALE,
    REASON_ELIGIBILITY_MANIFEST_UNVERIFIED,
    REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0,
    SurfacePFinalFlagsEvidenceInputV0,
    build_surface_p_final_flags_evidence_from_eligibility_gate_v0,
    current_head_default_final_flags_evidence_input_v0,
    derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0,
    evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0,
    evaluate_surface_p_final_flags_fail_closed_contract_v0,
    evaluate_surface_p_final_flags_manifest_verified_promotion_v0,
    reject_direct_true_flag_assignment_v0,
    surface_p_final_flags_evidence_input_field_names_v0,
    verify_evidence_dir_manifest_sha256_v0,
)

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
DEFAULT_SOURCE_CLOSEOUT = (
    ARCHIVE_ROOT
    / "research/pr5133_merge_closeout_full_canonical_parity_pass_eligibility_gate_v0_20260712T224903Z"
)
DEFAULT_ELIGIBILITY_EVIDENCE = (
    ARCHIVE_ROOT / "planning/full_canonical_parity_pass_eligibility_gate_v0_20260712T222708Z"
)

REPO_ROOT = Path(__file__).resolve().parents[3]

_FINAL_FLAG_FIELD_NAMES = frozenset(
    {
        "full_canonical_chain_wired",
        "backtest_runtime_decision_parity_pass",
        "system_economic_evidence_admissible",
    }
)

_SLICE_SOURCE_PATHS = tuple(
    REPO_ROOT / p
    for p in ALLOWED_SLICE_CHANGED_PATH_PREFIXES
    if p.endswith(".py") and "surface_p_final_flags_fail_closed_contract" in p
)


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def _all_confirmed_evidence(
    *,
    manifest_rc: int = 0,
    runtime_bridge_binding_status: str = "ACTIVATED",
) -> SurfacePFinalFlagsEvidenceInputV0:
    return SurfacePFinalFlagsEvidenceInputV0(
        source_manifest_verify_rc=manifest_rc,
        targeted_semantic_binding_confirmations={
            key: True for key in REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0
        },
        surface_p_parity_suite_confirmed=True,
        runtime_bridge_binding_status=runtime_bridge_binding_status,  # type: ignore[arg-type]
    )


def test_contract_constants_v0() -> None:
    assert CONTRACT_NAME == "SurfacePFinalFlagsFailClosedContractV0"
    assert CONTRACT_SLICE_ID == "SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_V0"
    assert PACKAGE_MARKER == "SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_V0=true"
    assert DIRECT_TRUE_FLAG_ASSIGNMENT is False


def test_evidence_input_has_no_direct_final_flag_fields_v0() -> None:
    assert _FINAL_FLAG_FIELD_NAMES.isdisjoint(surface_p_final_flags_evidence_input_field_names_v0())


def test_missing_evidence_all_final_success_flags_false_v0() -> None:
    result = evaluate_surface_p_final_flags_fail_closed_contract_v0(
        SurfacePFinalFlagsEvidenceInputV0(
            source_manifest_verify_rc=-1,
            targeted_semantic_binding_confirmations={},
            surface_p_parity_suite_confirmed=False,
            runtime_bridge_binding_status="BOUND_NOT_ACTIVATED",
        )
    )
    assert result.full_canonical_chain_wired is False
    assert result.backtest_runtime_decision_parity_pass is False
    assert result.system_economic_evidence_admissible is False
    assert result.direct_true_flag_assignment is False


def test_manifest_verify_nonzero_all_final_success_flags_false_v0() -> None:
    result = evaluate_surface_p_final_flags_fail_closed_contract_v0(
        _all_confirmed_evidence(manifest_rc=1)
    )
    assert result.full_canonical_chain_wired is False
    assert result.backtest_runtime_decision_parity_pass is False
    assert result.system_economic_evidence_admissible is False
    assert any("source_manifest_verify_rc" in reason for reason in result.fail_closed_reasons)


def test_incomplete_semantic_binding_full_canonical_chain_wired_false_v0() -> None:
    confirmations = {key: True for key in REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0}
    confirmations["promotion_gate_boundary"] = False
    result = evaluate_surface_p_final_flags_fail_closed_contract_v0(
        SurfacePFinalFlagsEvidenceInputV0(
            source_manifest_verify_rc=0,
            targeted_semantic_binding_confirmations=confirmations,
            surface_p_parity_suite_confirmed=True,
            runtime_bridge_binding_status="ACTIVATED",
        )
    )
    assert result.full_canonical_chain_wired is False
    assert result.system_economic_evidence_admissible is False
    assert any(
        reason.startswith("missing_semantic_binding_confirmation:")
        for reason in result.fail_closed_reasons
    )


def test_missing_surface_p_parity_confirmation_backtest_parity_false_v0() -> None:
    result = evaluate_surface_p_final_flags_fail_closed_contract_v0(
        SurfacePFinalFlagsEvidenceInputV0(
            source_manifest_verify_rc=0,
            targeted_semantic_binding_confirmations={
                key: True for key in REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0
            },
            surface_p_parity_suite_confirmed=False,
            runtime_bridge_binding_status="ACTIVATED",
        )
    )
    assert result.backtest_runtime_decision_parity_pass is False
    assert result.system_economic_evidence_admissible is False
    assert "surface_p_parity_suite_not_targeted_test_confirmed" in result.fail_closed_reasons


def test_runtime_bridge_bound_not_activated_offline_parity_true_economic_false_v0() -> None:
    result = evaluate_surface_p_final_flags_fail_closed_contract_v0(
        _all_confirmed_evidence(runtime_bridge_binding_status="BOUND_NOT_ACTIVATED")
    )
    assert result.full_canonical_chain_wired is True
    assert result.backtest_runtime_decision_parity_pass is True
    assert result.system_economic_evidence_admissible is False
    assert result.runtime_bridge_bound is True
    assert result.runtime_bridge_activated is False
    assert "runtime_bridge_not_activated_for_economic_admissibility" in result.fail_closed_reasons


def test_direct_true_flag_assignment_rejected_fail_closed_v0() -> None:
    rejected, violations = reject_direct_true_flag_assignment_v0(
        full_canonical_chain_wired=True,
        backtest_runtime_decision_parity_pass=True,
    )
    assert rejected is False
    assert violations

    result = evaluate_surface_p_final_flags_fail_closed_contract_v0(
        _all_confirmed_evidence(),
        attempted_direct_true_flags={"full_canonical_chain_wired": True},
    )
    assert result.full_canonical_chain_wired is False
    assert result.direct_true_flag_assignment is False
    assert any("direct_true_flag_assignment:" in reason for reason in result.fail_closed_reasons)


def test_only_complete_manifest_verified_evidence_can_derive_true_flags_v0() -> None:
    result = evaluate_surface_p_final_flags_fail_closed_contract_v0(_all_confirmed_evidence())
    assert result.full_canonical_chain_wired is True
    assert result.backtest_runtime_decision_parity_pass is True
    assert result.system_economic_evidence_admissible is True
    assert result.direct_true_flag_assignment is False
    assert result.fail_closed_reasons == ()


def test_current_head_derives_offline_parity_flags_without_runtime_activation_v0() -> None:
    result = evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0()
    evidence = current_head_default_final_flags_evidence_input_v0()
    assert evidence.source_manifest_verify_rc == 0
    assert evidence.runtime_bridge_binding_status == "BOUND_NOT_ACTIVATED"
    assert result.full_canonical_chain_wired is True
    assert result.backtest_runtime_decision_parity_pass is True
    assert result.system_economic_evidence_admissible is False
    assert result.runtime_bridge_bound is True
    assert result.runtime_bridge_activated is False
    assert result.direct_true_flag_assignment is False
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "BOUND_NOT_ACTIVATED"


def test_current_head_default_manifest_verified_v0() -> None:
    evidence = current_head_default_final_flags_evidence_input_v0()
    assert evidence.source_manifest_verify_rc == 0
    assert evidence.runtime_bridge_binding_status == "BOUND_NOT_ACTIVATED"


def test_gap_assessment_semantic_bindings_derived_from_targeted_pass_surfaces_v0() -> None:
    confirmations = derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0()
    assert all(confirmations[key] for key in REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0)


def test_parity_gap_matrix_json_uses_derived_final_flags_v0() -> None:
    import json

    payload = json.loads(render_parity_gap_matrix_json_v0())
    final_flags = payload["final_flags"]
    summary = payload["summary"]
    assert summary["full_canonical_chain_wired"] == final_flags["full_canonical_chain_wired"]
    assert (
        summary["backtest_runtime_decision_parity_pass"]
        == final_flags["backtest_runtime_decision_parity_pass"]
    )
    assert (
        summary["system_economic_evidence_admissible"]
        == final_flags["system_economic_evidence_admissible"]
    )
    assert final_flags["direct_true_flag_assignment"] is False
    assert summary["full_canonical_chain_wired"] is True
    assert summary["backtest_runtime_decision_parity_pass"] is True
    assert summary["system_economic_evidence_admissible"] is False


def test_slice_sources_have_no_forbidden_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "src.execution",
            "src.live",
            "src.runtime",
            "src.scheduler",
            "credentials",
            "secrets",
        }
    )
    for path in _SLICE_SOURCE_PATHS:
        assert _scan_forbidden_imports(path, forbidden) == []


def test_slice_changed_paths_allowed_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(
        [p.replace(REPO_ROOT.as_posix() + "/", "") for p in map(str, _SLICE_SOURCE_PATHS)]
    )
    assert ok, violations


def test_promotion_slice_constant_v0() -> None:
    assert PROMOTION_SLICE_ID == "SURFACE_P_FINAL_FLAGS_MANIFEST_VERIFIED_PROMOTION_V0"


def test_manifest_verified_promotion_passes_with_source_closeout_and_eligibility_v0() -> None:
    if not DEFAULT_SOURCE_CLOSEOUT.is_dir() or not DEFAULT_ELIGIBILITY_EVIDENCE.is_dir():
        return
    promotion = evaluate_surface_p_final_flags_manifest_verified_promotion_v0(
        eligibility_evidence_dir=DEFAULT_ELIGIBILITY_EVIDENCE,
        closeout_evidence_dir=DEFAULT_SOURCE_CLOSEOUT,
        repo_root=REPO_ROOT,
    )
    assert promotion.transitive_manifest_verify_rc == 0
    assert promotion.eligibility_head_binding_ok is True
    assert promotion.promoted is True
    assert promotion.after_flags.full_canonical_chain_wired is True
    assert promotion.after_flags.backtest_runtime_decision_parity_pass is True
    assert promotion.after_flags.system_economic_evidence_admissible is False
    assert promotion.before_flags.full_canonical_chain_wired is False


def test_manifest_tamper_blocks_promotion_v0(tmp_path: Path) -> None:
    eligibility = tmp_path / "eligibility"
    closeout = tmp_path / "closeout"
    eligibility.mkdir()
    closeout.mkdir()
    (eligibility / "eligibility_gate_result.json").write_text(
        '{"assessment_verdict":"PASS_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0","full_canonical_parity_pass_eligible":true,"current_head":"deadbeef","runtime_bridge_boundary_status":"BOUND_NOT_ACTIVATED"}',
        encoding="utf-8",
    )
    (closeout / "final_report.txt").write_text("VERDICT=PASS\n", encoding="utf-8")
    promotion = evaluate_surface_p_final_flags_manifest_verified_promotion_v0(
        eligibility_evidence_dir=eligibility,
        closeout_evidence_dir=closeout,
        repo_root=REPO_ROOT,
        current_head="deadbeef",
    )
    assert promotion.promoted is False
    assert promotion.promotion_blocker in {
        REASON_ELIGIBILITY_MANIFEST_UNVERIFIED,
        REASON_ELIGIBILITY_HEAD_STALE,
    }


def test_stale_eligibility_head_blocks_promotion_v0(tmp_path: Path) -> None:
    from scripts.research.full_canonical_parity_pass_eligibility_gate_v0 import write_manifest

    eligibility = tmp_path / "eligibility"
    closeout = tmp_path / "closeout"
    proof = tmp_path / "proof"
    for directory in (eligibility, closeout, proof):
        directory.mkdir()
    stale_head = "0" * 40
    (eligibility / "eligibility_gate_result.json").write_text(
        (
            '{"assessment_verdict":"PASS_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0",'
            '"full_canonical_parity_pass_eligible":true,'
            f'"current_head":"{stale_head}",'
            '"runtime_bridge_boundary_status":"BOUND_NOT_ACTIVATED"}'
        ),
        encoding="utf-8",
    )
    (eligibility / "eligibility_gate_inputs.json").write_text(
        f'{{"proof_bundle_dir":"{proof}"}}',
        encoding="utf-8",
    )
    (eligibility / "current_head_proof_binding.json").write_text(
        (f'{{"manifest_verified_full_parity_proof_bundle":true,"proof_bundle_dir":"{proof}"}}'),
        encoding="utf-8",
    )
    (proof / "proof_bundle.json").write_text(
        '{"full_parity_proof_bundle_status":"PROVEN_MANIFEST_VERIFIED"}',
        encoding="utf-8",
    )
    (closeout / "final_report.txt").write_text("VERDICT=PASS\n", encoding="utf-8")
    assert write_manifest(eligibility) == 0
    assert write_manifest(closeout) == 0
    assert write_manifest(proof) == 0
    promotion = evaluate_surface_p_final_flags_manifest_verified_promotion_v0(
        eligibility_evidence_dir=eligibility,
        closeout_evidence_dir=closeout,
        repo_root=REPO_ROOT,
    )
    assert promotion.promoted is False
    assert promotion.promotion_blocker == REASON_ELIGIBILITY_HEAD_STALE


def test_promotion_materialization_is_deterministic_v0() -> None:
    if not DEFAULT_SOURCE_CLOSEOUT.is_dir() or not DEFAULT_ELIGIBILITY_EVIDENCE.is_dir():
        return
    first = evaluate_surface_p_final_flags_manifest_verified_promotion_v0(
        eligibility_evidence_dir=DEFAULT_ELIGIBILITY_EVIDENCE,
        closeout_evidence_dir=DEFAULT_SOURCE_CLOSEOUT,
        repo_root=REPO_ROOT,
    )
    second = evaluate_surface_p_final_flags_manifest_verified_promotion_v0(
        eligibility_evidence_dir=DEFAULT_ELIGIBILITY_EVIDENCE,
        closeout_evidence_dir=DEFAULT_SOURCE_CLOSEOUT,
        repo_root=REPO_ROOT,
    )
    assert first.promoted == second.promoted
    assert first.after_flags == second.after_flags
