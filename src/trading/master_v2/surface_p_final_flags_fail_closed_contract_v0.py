"""
Surface P final flags fail-closed contract v0.

Derives FULL_CANONICAL_CHAIN_WIRED, BACKTEST_RUNTIME_DECISION_PARITY_PASS, and
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE fail-closed from manifest-verified evidence
and targeted parity confirmation. No runtime activation, no direct true assignment.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal, Mapping, Tuple

DEFAULT_CANONICAL_PARITY_SOURCE_EVIDENCE_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_system_backtest_parity_gap_assessment_and_rewire_scope_continuation_v0_"
    "20260710T034813Z"
)

SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_LAYER_VERSION = "v0"
SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_OWNER = (
    "trading.master_v2.surface_p_final_flags_fail_closed_contract_v0"
)
CONTRACT_NAME = "SurfacePFinalFlagsFailClosedContractV0"
CONTRACT_SLICE_ID = "SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_V0"
PROMOTION_SLICE_ID = "SURFACE_P_FINAL_FLAGS_MANIFEST_VERIFIED_PROMOTION_V0"
PACKAGE_MARKER = "SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_V0=true"
DIRECT_TRUE_FLAG_ASSIGNMENT = False
ELIGIBILITY_PASS_VERDICTS = frozenset(
    {
        "PASS_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0",
    }
)
REASON_ELIGIBILITY_MANIFEST_UNVERIFIED = "ELIGIBILITY_SOURCE_MANIFEST_NOT_VERIFIED"
REASON_ELIGIBILITY_NOT_PASS = "ELIGIBILITY_GATE_NOT_PASS"
REASON_ELIGIBILITY_HEAD_STALE = "ELIGIBILITY_EVIDENCE_HEAD_STALE"
REASON_PROOF_BUNDLE_MANIFEST_UNVERIFIED = "PROOF_BUNDLE_MANIFEST_NOT_VERIFIED"
REASON_CLOSEOUT_MANIFEST_UNVERIFIED = "MERGE_CLOSEOUT_MANIFEST_NOT_VERIFIED"

REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0: Tuple[str, ...] = (
    "bull_bear_state_switch_backtest_parity",
    "scope_exit_reversal_backtest_parity",
    "capital_risk_sizing_backtest_parity",
    "safety_killswitch_backtest_boundary",
    "reconciliation_unknown_outcome_backtest_boundary",
    "promotion_gate_boundary",
    "ai_observability_feedback_boundary",
)

_SURFACE_IDS_BY_SEMANTIC_BINDING_V0: dict[str, Tuple[str, ...]] = {
    "bull_bear_state_switch_backtest_parity": ("A",),
    "scope_exit_reversal_backtest_parity": ("B", "C"),
    "capital_risk_sizing_backtest_parity": ("H",),
    "safety_killswitch_backtest_boundary": ("J", "K"),
    "reconciliation_unknown_outcome_backtest_boundary": ("L",),
    "promotion_gate_boundary": ("M",),
    "ai_observability_feedback_boundary": ("N", "O"),
}

_FINAL_FLAG_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "full_canonical_chain_wired",
        "backtest_runtime_decision_parity_pass",
        "system_economic_evidence_admissible",
    }
)


@dataclass(frozen=True)
class SurfacePFinalFlagsEvidenceInputV0:
    source_manifest_verify_rc: int
    targeted_semantic_binding_confirmations: Mapping[str, bool]
    surface_p_parity_suite_confirmed: bool
    runtime_bridge_binding_status: Literal["BOUND_NOT_ACTIVATED", "ACTIVATED", "UNBOUND"]


@dataclass(frozen=True)
class SurfacePFinalFlagsResultV0:
    full_canonical_chain_wired: bool
    backtest_runtime_decision_parity_pass: bool
    system_economic_evidence_admissible: bool
    runtime_bridge_bound: bool
    runtime_bridge_activated: bool
    direct_true_flag_assignment: bool
    fail_closed_reasons: Tuple[str, ...]


@dataclass(frozen=True)
class SurfacePFinalFlagsPromotionResultV0:
    promoted: bool
    promotion_blocker: str
    eligibility_evidence_dir: str
    closeout_evidence_dir: str
    proof_bundle_dir: str
    eligibility_head: str
    current_head: str
    eligibility_head_binding_ok: bool
    source_manifest_verify_rc: int
    transitive_manifest_verify_rc: int
    before_flags: SurfacePFinalFlagsResultV0
    after_flags: SurfacePFinalFlagsResultV0
    fail_closed_reasons: Tuple[str, ...]


def reject_direct_true_flag_assignment_v0(**kwargs: object) -> Tuple[bool, Tuple[str, ...]]:
    """Reject any attempt to inject final success flags directly into evaluation."""
    violations = tuple(
        f"direct_true_flag_assignment:{name}={kwargs[name]!r}"
        for name in _FINAL_FLAG_FIELD_NAMES
        if name in kwargs and kwargs[name] is True
    )
    return (not violations, violations)


def _manifest_verified_v0(source_manifest_verify_rc: int) -> bool:
    return source_manifest_verify_rc == 0


def _semantic_bindings_confirmed_v0(
    confirmations: Mapping[str, bool],
) -> Tuple[bool, Tuple[str, ...]]:
    missing = tuple(
        key
        for key in REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0
        if not confirmations.get(key, False)
    )
    return (not missing, missing)


def evaluate_surface_p_final_flags_fail_closed_contract_v0(
    evidence: SurfacePFinalFlagsEvidenceInputV0,
    *,
    attempted_direct_true_flags: Mapping[str, bool] | None = None,
) -> SurfacePFinalFlagsResultV0:
    """Derive final Surface-P flags fail-closed; never grants runtime authority."""
    fail_reasons: list[str] = []

    if attempted_direct_true_flags:
        rejected, violations = reject_direct_true_flag_assignment_v0(**attempted_direct_true_flags)
        if not rejected:
            fail_reasons.extend(violations)

    if not _manifest_verified_v0(evidence.source_manifest_verify_rc):
        fail_reasons.append(f"source_manifest_verify_rc!={evidence.source_manifest_verify_rc}")

    semantic_ok, missing_bindings = _semantic_bindings_confirmed_v0(
        evidence.targeted_semantic_binding_confirmations
    )
    if not semantic_ok:
        for binding in missing_bindings:
            fail_reasons.append(f"missing_semantic_binding_confirmation:{binding}")

    if not evidence.surface_p_parity_suite_confirmed:
        fail_reasons.append("surface_p_parity_suite_not_targeted_test_confirmed")

    runtime_bridge_bound = evidence.runtime_bridge_binding_status in (
        "BOUND_NOT_ACTIVATED",
        "ACTIVATED",
    )
    runtime_bridge_activated = evidence.runtime_bridge_binding_status == "ACTIVATED"

    if evidence.runtime_bridge_binding_status == "UNBOUND":
        fail_reasons.append("runtime_bridge_unbound")
    elif not runtime_bridge_bound:
        fail_reasons.append("runtime_bridge_not_bound")

    manifest_ok = _manifest_verified_v0(evidence.source_manifest_verify_rc)
    offline_parity_ok = manifest_ok and semantic_ok and evidence.surface_p_parity_suite_confirmed

    full_canonical_chain_wired = offline_parity_ok and runtime_bridge_bound
    backtest_runtime_decision_parity_pass = offline_parity_ok and runtime_bridge_bound

    system_economic_evidence_admissible = offline_parity_ok and runtime_bridge_activated
    if offline_parity_ok and not runtime_bridge_activated:
        fail_reasons.append("runtime_bridge_not_activated_for_economic_admissibility")

    if not offline_parity_ok:
        full_canonical_chain_wired = False
        backtest_runtime_decision_parity_pass = False
        system_economic_evidence_admissible = False
    elif any(reason.startswith("direct_true_flag_assignment:") for reason in fail_reasons):
        full_canonical_chain_wired = False
        backtest_runtime_decision_parity_pass = False
        system_economic_evidence_admissible = False

    return SurfacePFinalFlagsResultV0(
        full_canonical_chain_wired=full_canonical_chain_wired,
        backtest_runtime_decision_parity_pass=backtest_runtime_decision_parity_pass,
        system_economic_evidence_admissible=system_economic_evidence_admissible,
        runtime_bridge_bound=runtime_bridge_bound,
        runtime_bridge_activated=runtime_bridge_activated,
        direct_true_flag_assignment=False,
        fail_closed_reasons=tuple(dict.fromkeys(fail_reasons)),
    )


def derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0() -> dict[str, bool]:
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        _parity_surface_assessments_base_v0,
    )

    status_by_surface = {
        item.surface_id: item.parity_status == "PASS"
        for item in _parity_surface_assessments_base_v0()
    }
    return {
        binding: all(status_by_surface.get(surface_id, False) for surface_id in surface_ids)
        for binding, surface_ids in _SURFACE_IDS_BY_SEMANTIC_BINDING_V0.items()
    }


def derive_surface_p_parity_suite_confirmed_from_targeted_tests_v0() -> bool:
    from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
        evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
    )
    from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
        evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
    )

    bar_assessment = evaluate_surface_p_full_bar_sequence_four_way_parity_v0()
    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0(
        offline_four_way_fixtures_complete=bar_assessment.fixtures_complete,
    )
    return (
        bar_assessment.fixtures_complete and semantic.surface_p_offline_parity_status == "COMPLETE"
    )


def resolve_canonical_parity_source_manifest_verify_rc_v0(
    evidence_dir: Path | None = None,
) -> int:
    """Verify canonical parity continuation evidence manifest when present."""
    directory = evidence_dir or DEFAULT_CANONICAL_PARITY_SOURCE_EVIDENCE_DIR
    return verify_evidence_dir_manifest_sha256_v0(directory)


def verify_evidence_dir_manifest_sha256_v0(directory: Path) -> int:
    manifest = directory / "MANIFEST.sha256"
    if not directory.is_dir() or not manifest.is_file():
        return -1
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode


def _repo_head_v0(repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def is_head_ancestor_or_equal_v0(
    recorded_head: str,
    current_head: str,
    *,
    repo_root: Path,
) -> bool:
    if not recorded_head or not current_head:
        return False
    if recorded_head == current_head:
        return True
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", recorded_head, current_head],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _load_json_object_v0(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_eligibility_gate_promotion_context_v0(
    *,
    eligibility_evidence_dir: Path,
    closeout_evidence_dir: Path,
    current_head: str,
    repo_root: Path,
) -> tuple[bool, str, dict[str, object]]:
    blockers: list[str] = []
    eligibility_manifest_rc = verify_evidence_dir_manifest_sha256_v0(eligibility_evidence_dir)
    closeout_manifest_rc = verify_evidence_dir_manifest_sha256_v0(closeout_evidence_dir)
    if eligibility_manifest_rc != 0:
        blockers.append(REASON_ELIGIBILITY_MANIFEST_UNVERIFIED)
    if closeout_manifest_rc != 0:
        blockers.append(REASON_CLOSEOUT_MANIFEST_UNVERIFIED)

    gate_result_path = eligibility_evidence_dir / "eligibility_gate_result.json"
    gate_inputs_path = eligibility_evidence_dir / "eligibility_gate_inputs.json"
    proof_binding_path = eligibility_evidence_dir / "current_head_proof_binding.json"
    if not gate_result_path.is_file():
        blockers.append(REASON_ELIGIBILITY_NOT_PASS)
        gate_result: dict[str, object] = {}
        gate_inputs: dict[str, object] = {}
        proof_binding: dict[str, object] = {}
    else:
        gate_result = _load_json_object_v0(gate_result_path)
        gate_inputs = _load_json_object_v0(gate_inputs_path) if gate_inputs_path.is_file() else {}
        proof_binding = (
            _load_json_object_v0(proof_binding_path) if proof_binding_path.is_file() else {}
        )

    assessment_verdict = str(gate_result.get("assessment_verdict", ""))
    if assessment_verdict not in ELIGIBILITY_PASS_VERDICTS:
        blockers.append(REASON_ELIGIBILITY_NOT_PASS)
    if not bool(gate_result.get("full_canonical_parity_pass_eligible", False)):
        blockers.append(REASON_ELIGIBILITY_NOT_PASS)

    eligibility_head = str(gate_result.get("current_head", gate_inputs.get("current_head", "")))
    head_binding_ok = is_head_ancestor_or_equal_v0(
        eligibility_head, current_head, repo_root=repo_root
    )
    if not head_binding_ok:
        blockers.append(REASON_ELIGIBILITY_HEAD_STALE)

    proof_bundle_dir = Path(
        str(proof_binding.get("proof_bundle_dir") or gate_inputs.get("proof_bundle_dir") or "")
    )
    proof_bundle_manifest_rc = (
        verify_evidence_dir_manifest_sha256_v0(proof_bundle_dir)
        if proof_bundle_dir.is_dir()
        else -1
    )
    if proof_bundle_manifest_rc != 0:
        blockers.append(REASON_PROOF_BUNDLE_MANIFEST_UNVERIFIED)
    if not bool(proof_binding.get("manifest_verified_full_parity_proof_bundle", False)):
        blockers.append(REASON_PROOF_BUNDLE_MANIFEST_UNVERIFIED)

    transitive_manifest_rc = 0
    for rc in (eligibility_manifest_rc, closeout_manifest_rc, proof_bundle_manifest_rc):
        if rc != 0:
            transitive_manifest_rc = rc
            break

    context = {
        "eligibility_manifest_rc": eligibility_manifest_rc,
        "closeout_manifest_rc": closeout_manifest_rc,
        "proof_bundle_manifest_rc": proof_bundle_manifest_rc,
        "transitive_manifest_verify_rc": transitive_manifest_rc,
        "eligibility_head": eligibility_head,
        "current_head": current_head,
        "eligibility_head_binding_ok": head_binding_ok,
        "proof_bundle_dir": str(proof_bundle_dir),
        "assessment_verdict": assessment_verdict,
        "runtime_bridge_boundary_status": str(
            gate_result.get("runtime_bridge_boundary_status", "BOUND_NOT_ACTIVATED")
        ),
    }
    if blockers:
        return False, blockers[0], context
    return True, "NONE", context


def build_surface_p_final_flags_evidence_from_eligibility_gate_v0(
    *,
    eligibility_evidence_dir: Path,
    closeout_evidence_dir: Path,
    current_head: str,
    repo_root: Path,
) -> tuple[SurfacePFinalFlagsEvidenceInputV0 | None, str, dict[str, object]]:
    ok, blocker, context = validate_eligibility_gate_promotion_context_v0(
        eligibility_evidence_dir=eligibility_evidence_dir,
        closeout_evidence_dir=closeout_evidence_dir,
        current_head=current_head,
        repo_root=repo_root,
    )
    if not ok:
        return None, blocker, context

    runtime_status = context["runtime_bridge_boundary_status"]
    if runtime_status not in {"BOUND_NOT_ACTIVATED", "ACTIVATED", "UNBOUND"}:
        runtime_status = "BOUND_NOT_ACTIVATED"
    evidence = build_surface_p_final_flags_evidence_input_v0(
        source_manifest_verify_rc=0,
        surface_p_parity_suite_confirmed=derive_surface_p_parity_suite_confirmed_from_targeted_tests_v0(),
        runtime_bridge_binding_status=runtime_status,  # type: ignore[arg-type]
    )
    return evidence, "NONE", context


def evaluate_surface_p_final_flags_manifest_verified_promotion_v0(
    *,
    eligibility_evidence_dir: Path,
    closeout_evidence_dir: Path,
    repo_root: Path | None = None,
    current_head: str | None = None,
) -> SurfacePFinalFlagsPromotionResultV0:
    repo = repo_root or Path.cwd()
    head = current_head or _repo_head_v0(repo)
    before_flags = evaluate_surface_p_final_flags_fail_closed_contract_v0(
        SurfacePFinalFlagsEvidenceInputV0(
            source_manifest_verify_rc=-1,
            targeted_semantic_binding_confirmations={},
            surface_p_parity_suite_confirmed=False,
            runtime_bridge_binding_status="BOUND_NOT_ACTIVATED",
        )
    )
    evidence, blocker, context = build_surface_p_final_flags_evidence_from_eligibility_gate_v0(
        eligibility_evidence_dir=eligibility_evidence_dir,
        closeout_evidence_dir=closeout_evidence_dir,
        current_head=head,
        repo_root=repo,
    )
    if evidence is None:
        after_flags = before_flags
        return SurfacePFinalFlagsPromotionResultV0(
            promoted=False,
            promotion_blocker=blocker,
            eligibility_evidence_dir=str(eligibility_evidence_dir),
            closeout_evidence_dir=str(closeout_evidence_dir),
            proof_bundle_dir=str(context.get("proof_bundle_dir", "")),
            eligibility_head=str(context.get("eligibility_head", "")),
            current_head=head,
            eligibility_head_binding_ok=bool(context.get("eligibility_head_binding_ok", False)),
            source_manifest_verify_rc=int(context.get("eligibility_manifest_rc", -1)),
            transitive_manifest_verify_rc=int(context.get("transitive_manifest_verify_rc", -1)),
            before_flags=before_flags,
            after_flags=after_flags,
            fail_closed_reasons=(blocker,),
        )

    after_flags = evaluate_surface_p_final_flags_fail_closed_contract_v0(evidence)
    promoted = (
        after_flags.full_canonical_chain_wired
        and after_flags.backtest_runtime_decision_parity_pass
        and not after_flags.system_economic_evidence_admissible
        and not after_flags.direct_true_flag_assignment
    )
    return SurfacePFinalFlagsPromotionResultV0(
        promoted=promoted,
        promotion_blocker="NONE" if promoted else "PROMOTION_CONTRACT_NOT_SATISFIED",
        eligibility_evidence_dir=str(eligibility_evidence_dir),
        closeout_evidence_dir=str(closeout_evidence_dir),
        proof_bundle_dir=str(context.get("proof_bundle_dir", "")),
        eligibility_head=str(context.get("eligibility_head", "")),
        current_head=head,
        eligibility_head_binding_ok=bool(context.get("eligibility_head_binding_ok", False)),
        source_manifest_verify_rc=0,
        transitive_manifest_verify_rc=0,
        before_flags=before_flags,
        after_flags=after_flags,
        fail_closed_reasons=after_flags.fail_closed_reasons,
    )


def build_surface_p_final_flags_evidence_input_v0(
    *,
    source_manifest_verify_rc: int,
    surface_p_parity_suite_confirmed: bool,
    runtime_bridge_binding_status: Literal["BOUND_NOT_ACTIVATED", "ACTIVATED", "UNBOUND"],
) -> SurfacePFinalFlagsEvidenceInputV0:
    return SurfacePFinalFlagsEvidenceInputV0(
        source_manifest_verify_rc=source_manifest_verify_rc,
        targeted_semantic_binding_confirmations=(
            derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0()
        ),
        surface_p_parity_suite_confirmed=surface_p_parity_suite_confirmed,
        runtime_bridge_binding_status=runtime_bridge_binding_status,
    )


def current_head_default_final_flags_evidence_input_v0() -> SurfacePFinalFlagsEvidenceInputV0:
    """Reuse-first snapshot from manifest-verified parity evidence when available."""
    from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
        evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
    )

    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    return build_surface_p_final_flags_evidence_input_v0(
        source_manifest_verify_rc=resolve_canonical_parity_source_manifest_verify_rc_v0(),
        surface_p_parity_suite_confirmed=derive_surface_p_parity_suite_confirmed_from_targeted_tests_v0(),
        runtime_bridge_binding_status=semantic.surface_p_runtime_bridge_binding_status,
    )


def evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0() -> (
    SurfacePFinalFlagsResultV0
):
    return evaluate_surface_p_final_flags_fail_closed_contract_v0(
        current_head_default_final_flags_evidence_input_v0()
    )


def surface_p_final_flags_result_to_dict_v0(
    result: SurfacePFinalFlagsResultV0,
) -> Mapping[str, object]:
    return {
        "full_canonical_chain_wired": result.full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": result.backtest_runtime_decision_parity_pass,
        "system_economic_evidence_admissible": result.system_economic_evidence_admissible,
        "runtime_bridge_bound": result.runtime_bridge_bound,
        "runtime_bridge_activated": result.runtime_bridge_activated,
        "direct_true_flag_assignment": result.direct_true_flag_assignment,
        "fail_closed_reasons": list(result.fail_closed_reasons),
    }


def surface_p_final_flags_evidence_input_field_names_v0() -> Tuple[str, ...]:
    return tuple(field.name for field in fields(SurfacePFinalFlagsEvidenceInputV0))
