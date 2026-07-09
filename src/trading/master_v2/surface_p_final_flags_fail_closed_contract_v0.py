"""
Surface P final flags fail-closed contract v0.

Derives FULL_CANONICAL_CHAIN_WIRED, BACKTEST_RUNTIME_DECISION_PARITY_PASS, and
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE fail-closed from manifest-verified evidence
and targeted parity confirmation. No runtime activation, no direct true assignment.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Literal, Mapping, Tuple

SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_LAYER_VERSION = "v0"
SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_OWNER = (
    "trading.master_v2.surface_p_final_flags_fail_closed_contract_v0"
)
CONTRACT_NAME = "SurfacePFinalFlagsFailClosedContractV0"
CONTRACT_SLICE_ID = "SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_V0"
PACKAGE_MARKER = "SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_V0=true"
DIRECT_TRUE_FLAG_ASSIGNMENT = False

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
    direct_true_flag_assignment: bool
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

    if evidence.runtime_bridge_binding_status == "BOUND_NOT_ACTIVATED":
        fail_reasons.append("runtime_bridge_bound_not_activated")
    elif evidence.runtime_bridge_binding_status == "UNBOUND":
        fail_reasons.append("runtime_bridge_unbound")

    manifest_ok = _manifest_verified_v0(evidence.source_manifest_verify_rc)
    full_canonical_chain_wired = manifest_ok and semantic_ok
    backtest_runtime_decision_parity_pass = (
        manifest_ok and evidence.surface_p_parity_suite_confirmed
    )
    system_economic_evidence_admissible = (
        full_canonical_chain_wired
        and backtest_runtime_decision_parity_pass
        and evidence.runtime_bridge_binding_status == "ACTIVATED"
    )

    if fail_reasons:
        full_canonical_chain_wired = False
        backtest_runtime_decision_parity_pass = False
        system_economic_evidence_admissible = False

    return SurfacePFinalFlagsResultV0(
        full_canonical_chain_wired=full_canonical_chain_wired,
        backtest_runtime_decision_parity_pass=backtest_runtime_decision_parity_pass,
        system_economic_evidence_admissible=system_economic_evidence_admissible,
        direct_true_flag_assignment=False,
        fail_closed_reasons=tuple(fail_reasons),
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
        bar_assessment.fixtures_complete
        and semantic.surface_p_offline_parity_status == "COMPLETE"
        and semantic.surface_p_overall_status == "PASS"
    )


def current_head_default_final_flags_evidence_input_v0() -> SurfacePFinalFlagsEvidenceInputV0:
    """Reuse-first snapshot: manifest unverified and runtime bridge policy-blocked."""
    from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
        evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
    )

    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    return SurfacePFinalFlagsEvidenceInputV0(
        source_manifest_verify_rc=-1,
        targeted_semantic_binding_confirmations=derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0(),
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
        "direct_true_flag_assignment": result.direct_true_flag_assignment,
        "fail_closed_reasons": list(result.fail_closed_reasons),
    }


def surface_p_final_flags_evidence_input_field_names_v0() -> Tuple[str, ...]:
    return tuple(field.name for field in fields(SurfacePFinalFlagsEvidenceInputV0))
