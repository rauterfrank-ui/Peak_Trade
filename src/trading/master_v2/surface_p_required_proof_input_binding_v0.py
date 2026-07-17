"""
Surface P required proof-input binding v0.

Owner-bound evaluation for the Full Canonical Parity Proof Bundle Assembler
required proof input on surface P.

Canonical registry semantics (do not mix with activation):
- registry_parity_status / promoted parity_surface_assessments_v0 parity_status
  is PASS when offline 4-way parity + semantic bindings + evidence refs are
  satisfied AND the runtime bridge remains BOUND_NOT_ACTIVATED (activation
  pending by policy).
- PARTIAL is only the unpromoted base assessment when proof input is not
  satisfied.
- Runtime activation pending is tracked separately as
  surface_p_overall_status=PARTIAL_RUNTIME_ACTIVATION_PENDING on the semantic
  contract owner; it must not be confused with registry PARTIAL.

Does not activate runtime, grant order authority, or unlock live/orders.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal, Mapping, Tuple

SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_LAYER_VERSION = "v0"
SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_OWNER = (
    "trading.master_v2.surface_p_required_proof_input_binding_v0"
)
BINDING_SLICE_ID = "SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_V0"
PACKAGE_MARKER = "SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_V0=true"

SURFACE_P_PROOF_INPUT_ID = "backtest_offline_replay_runtime_decision_parity"
SURFACE_P_SURFACE_ID = "P"
SURFACE_P_PROOF_INPUT_LABEL = (
    "Backtest / Offline Replay / Runtime decision parity proof eligibility evidence"
)

REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P = "MISSING_REQUIRED_PROOF_INPUT_SURFACE_P"
REASON_OFFLINE_FOUR_WAY_INCOMPLETE = "OFFLINE_FOUR_WAY_PARITY_INCOMPLETE"
REASON_SEMANTIC_BINDING_INCOMPLETE = "SEMANTIC_BINDING_CONFIRMATION_INCOMPLETE"
REASON_OFFLINE_PARITY_NOT_COMPLETE = "SURFACE_P_OFFLINE_PARITY_NOT_COMPLETE"
REASON_RUNTIME_BRIDGE_NOT_BOUND_NOT_ACTIVATED = "RUNTIME_BRIDGE_NOT_BOUND_NOT_ACTIVATED"
REASON_OWNER_EVIDENCE_REFS_MISSING = "OWNER_EVIDENCE_REFS_MISSING"

SurfacePProofInputBindingStatus = Literal["VERIFIED", "MISSING_REQUIRED_PROOF_INPUT_SURFACE_P"]

CANONICAL_OWNER_FILES: Tuple[str, ...] = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "src/trading/master_v2/surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
    "src/trading/master_v2/surface_p_semantic_parity_gap_assessment_v0.py",
    "src/trading/master_v2/surface_p_required_proof_input_binding_v0.py",
)


@dataclass(frozen=True)
class SurfacePRequiredProofInputBindingResultV0:
    proof_input_id: str
    surface_id: str
    label: str
    owner: str
    binding_status: SurfacePProofInputBindingStatus
    satisfied: bool
    registry_parity_status: str
    offline_four_way_fixtures_complete: bool
    semantic_binding_confirmations_complete: bool
    surface_p_offline_parity_complete: bool
    runtime_bridge_bound_not_activated: bool
    owner_evidence_refs_present: bool
    evidence_ref_count: int
    present_evidence_ref_count: int
    missing_evidence_refs: Tuple[str, ...]
    detail: str
    fail_closed_reasons: Tuple[str, ...]
    full_canonical_chain_wired: bool
    backtest_runtime_decision_parity_pass: bool
    system_economic_evidence_admissible: bool
    runtime_rewire_admissible: bool
    claim_promotion_allowed: bool
    no_runtime_authority_confirmed: bool
    no_economic_claim_confirmed: bool


def _count_present_evidence_refs(
    repo_root: Path, evidence_refs: Tuple[str, ...]
) -> tuple[int, tuple[str, ...]]:
    present_count = 0
    missing: list[str] = []
    for ref in evidence_refs:
        if (repo_root / ref).is_file():
            present_count += 1
        else:
            missing.append(ref)
    return present_count, tuple(missing)


def evaluate_surface_p_required_proof_input_binding_v0(
    repo_root: Path,
) -> SurfacePRequiredProofInputBindingResultV0:
    """Evaluate Surface P required proof-input binding; never grants runtime authority."""
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        _parity_surface_assessments_base_v0,
    )
    from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
        evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
    )
    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0,
        derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0,
    )
    from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
        evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
        surface_p_offline_parity_complete_runtime_activation_pending_v0,
    )

    fail_reasons: list[str] = []
    surface_p = next(
        item for item in _parity_surface_assessments_base_v0() if item.surface_id == "P"
    )
    bar_assessment = evaluate_surface_p_full_bar_sequence_four_way_parity_v0()
    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0(
        offline_four_way_fixtures_complete=bar_assessment.fixtures_complete,
    )
    confirmations = derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0()
    missing_bindings = tuple(
        key
        for key in REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0
        if not confirmations.get(key, False)
    )
    present_ref_count, missing_refs = _count_present_evidence_refs(
        repo_root, surface_p.evidence_refs
    )

    offline_complete = bar_assessment.fixtures_complete
    if not offline_complete:
        fail_reasons.append(REASON_OFFLINE_FOUR_WAY_INCOMPLETE)

    semantic_bindings_complete = not missing_bindings
    if missing_bindings:
        fail_reasons.append(REASON_SEMANTIC_BINDING_INCOMPLETE)

    offline_parity_complete = semantic.surface_p_offline_parity_status == "COMPLETE"
    if not offline_parity_complete:
        fail_reasons.append(REASON_OFFLINE_PARITY_NOT_COMPLETE)

    runtime_bridge_bound_not_activated = (
        semantic.surface_p_runtime_bridge_binding_status == "BOUND_NOT_ACTIVATED"
        and semantic.surface_p_runtime_activation_status == "NOT_ACTIVATED_POLICY_BLOCKED"
    )
    if not runtime_bridge_bound_not_activated:
        fail_reasons.append(REASON_RUNTIME_BRIDGE_NOT_BOUND_NOT_ACTIVATED)

    owner_evidence_refs_present = present_ref_count > 0 and not missing_refs
    if not owner_evidence_refs_present:
        fail_reasons.append(REASON_OWNER_EVIDENCE_REFS_MISSING)

    activation_pending = surface_p_offline_parity_complete_runtime_activation_pending_v0(semantic)
    satisfied = (
        offline_complete
        and semantic_bindings_complete
        and offline_parity_complete
        and runtime_bridge_bound_not_activated
        and activation_pending
        and owner_evidence_refs_present
    )
    if not satisfied:
        fail_reasons.append(REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P)

    detail_parts: list[str] = []
    if not offline_complete:
        detail_parts.append("offline_four_way_fixtures_incomplete")
    if not semantic_bindings_complete:
        detail_parts.append("semantic_binding_confirmations_incomplete")
    if not offline_parity_complete:
        detail_parts.append("surface_p_offline_parity_incomplete")
    if not runtime_bridge_bound_not_activated:
        detail_parts.append("runtime_bridge_not_bound_not_activated")
    if not activation_pending:
        detail_parts.append("offline_complete_runtime_activation_not_pending")
    if not owner_evidence_refs_present:
        detail_parts.append("owner_evidence_refs_missing")

    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        build_surface_p_final_flags_evidence_input_v0,
        evaluate_surface_p_final_flags_fail_closed_contract_v0,
        resolve_canonical_parity_source_manifest_verify_rc_v0,
    )

    final_flags = evaluate_surface_p_final_flags_fail_closed_contract_v0(
        build_surface_p_final_flags_evidence_input_v0(
            source_manifest_verify_rc=resolve_canonical_parity_source_manifest_verify_rc_v0(),
            surface_p_parity_suite_confirmed=satisfied,
            runtime_bridge_binding_status=semantic.surface_p_runtime_bridge_binding_status,
        )
    )

    return SurfacePRequiredProofInputBindingResultV0(
        proof_input_id=SURFACE_P_PROOF_INPUT_ID,
        surface_id=SURFACE_P_SURFACE_ID,
        label=SURFACE_P_PROOF_INPUT_LABEL,
        owner=SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_OWNER,
        binding_status="VERIFIED" if satisfied else "MISSING_REQUIRED_PROOF_INPUT_SURFACE_P",
        satisfied=satisfied,
        registry_parity_status="PASS" if satisfied else surface_p.parity_status,
        offline_four_way_fixtures_complete=offline_complete,
        semantic_binding_confirmations_complete=semantic_bindings_complete,
        surface_p_offline_parity_complete=offline_parity_complete,
        runtime_bridge_bound_not_activated=runtime_bridge_bound_not_activated,
        owner_evidence_refs_present=owner_evidence_refs_present,
        evidence_ref_count=len(surface_p.evidence_refs),
        present_evidence_ref_count=present_ref_count,
        missing_evidence_refs=missing_refs,
        detail="verified" if satisfied else "; ".join(detail_parts),
        fail_closed_reasons=tuple(dict.fromkeys(fail_reasons)),
        full_canonical_chain_wired=final_flags.full_canonical_chain_wired,
        backtest_runtime_decision_parity_pass=final_flags.backtest_runtime_decision_parity_pass,
        system_economic_evidence_admissible=final_flags.system_economic_evidence_admissible,
        runtime_rewire_admissible=False,
        claim_promotion_allowed=False,
        no_runtime_authority_confirmed=True,
        no_economic_claim_confirmed=True,
    )


def surface_p_required_proof_input_binding_to_dict_v0(
    result: SurfacePRequiredProofInputBindingResultV0,
) -> Mapping[str, object]:
    return {
        "binding_version": SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_LAYER_VERSION,
        "binding_owner": SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_OWNER,
        "binding_slice_id": BINDING_SLICE_ID,
        "proof_input_id": result.proof_input_id,
        "surface_id": result.surface_id,
        "label": result.label,
        "owner": result.owner,
        "binding_status": result.binding_status,
        "satisfied": result.satisfied,
        "registry_parity_status": result.registry_parity_status,
        "offline_four_way_fixtures_complete": result.offline_four_way_fixtures_complete,
        "semantic_binding_confirmations_complete": result.semantic_binding_confirmations_complete,
        "surface_p_offline_parity_complete": result.surface_p_offline_parity_complete,
        "runtime_bridge_bound_not_activated": result.runtime_bridge_bound_not_activated,
        "owner_evidence_refs_present": result.owner_evidence_refs_present,
        "evidence_ref_count": result.evidence_ref_count,
        "present_evidence_ref_count": result.present_evidence_ref_count,
        "missing_evidence_refs": list(result.missing_evidence_refs),
        "detail": result.detail,
        "fail_closed_reasons": list(result.fail_closed_reasons),
        "full_canonical_chain_wired": result.full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": result.backtest_runtime_decision_parity_pass,
        "system_economic_evidence_admissible": result.system_economic_evidence_admissible,
        "runtime_rewire_admissible": result.runtime_rewire_admissible,
        "claim_promotion_allowed": result.claim_promotion_allowed,
        "no_runtime_authority_confirmed": result.no_runtime_authority_confirmed,
        "no_economic_claim_confirmed": result.no_economic_claim_confirmed,
        "canonical_owner_files": list(CANONICAL_OWNER_FILES),
    }


def binding_result_field_names_v0() -> Tuple[str, ...]:
    return tuple(field.name for field in fields(SurfacePRequiredProofInputBindingResultV0))
