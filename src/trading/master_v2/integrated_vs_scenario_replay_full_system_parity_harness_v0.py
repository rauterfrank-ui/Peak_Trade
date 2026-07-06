# src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py
"""
Offline harness: compare Integrated Offline Trading Logic Replay vs Scenario Replay
composition semantics through the canonical ``double_play_composition_matrix_v1`` owner.

No runtime authority, no economic evaluation, no trading semantic extension.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Tuple

from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from trading.master_v2.double_play_composition import RequestedSide
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionStatus,
    DoublePlayCompositionResultV1,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    CANONICAL_ORDER_INTENT_OWNER,
    ORDER_INTENT_EFFECT_BOUND_OFFLINE,
    ORDER_INTENT_EFFECT_NONE,
    CanonicalOrderIntentOfflineReplayBindingResultV0,
    canonical_order_intent_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    KILLSWITCH_FENCING_OWNER,
    RUNTIME_ELIGIBILITY_OWNER,
    SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE,
    SAFETY_BOUNDARY_EFFECT_NONE,
    SAFETY_KERNEL_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    SafetyKernelOfflineReplayBindingResultV0,
    safety_kernel_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 import (
    ENTRY_EXIT_POLICY_OWNER as RECONCILIATION_ENTRY_EXIT_POLICY_OWNER,
    RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE,
    RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_NONE,
    RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    RUNTIME_STATE_RECONCILIATION_OWNER,
    ReconciliationUnknownOutcomeOfflineReplayBindingResultV0,
    reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CANONICAL_CAPITAL_RISK_SIZING_OWNER,
    CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    RISK_SIZING_EFFECT_BOUND_OFFLINE,
    RISK_SIZING_EFFECT_NONE,
    CapitalRiskSizingOfflineReplayBindingResultV0,
    capital_risk_sizing_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.double_play_composition_scenario_matrix_adapter_v0 import (
    CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER,
    DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER,
    _legacy_side_to_assessment_statuses,
    build_scenario_matrix_composition_input_v0,
    evaluate_scenario_matrix_composition_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import EntryExitPolicyDecisionV0
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
    DOUBLE_PLAY_ENTRY_EXIT_SCENARIO_BINDING_ADAPTER_OWNER,
    ScenarioEntryExitPolicyContextV0,
    evaluate_scenario_entry_exit_policy_v0,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    IntegratedOfflineReplayResultV1,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioReplayResultV0,
    OfflineDoublePlayScenarioReplayTickRecordV0,
)

INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_HARNESS_LAYER_VERSION = "v0"
INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_HARNESS_OWNER = (
    "trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0"
)

ALLOWED_SLICE_CHANGED_PATH_PREFIXES: Tuple[str, ...] = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "scripts/ops/run_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
)

FORBIDDEN_CHANGED_PATH_PREFIXES: Tuple[str, ...] = (
    "src/execution/",
    "src/live/",
    "src/runtime/",
    "src/scheduler/",
    "src/governance/",
    "src/risk/",
    "credentials",
    "secrets",
)


@dataclass(frozen=True)
class ParityDecisionEnvelopeV0:
    decision_outcome: str
    previous_side_state: Optional[str]
    next_side_state: Optional[str]
    composition_status: str
    composition_result_id: str
    entry_or_exit_policy_ref: str
    reason_codes: Tuple[str, ...]
    decision_precedence_trace: Tuple[str, ...]
    execution_eligible: bool
    adapter_compatible: bool
    quantity_status: str
    authority_effect: str
    runtime_effect: str
    quantity_provenance_ref: str = ""
    risk_sizing_ref: str = ""
    risk_sizing_effect: str = RISK_SIZING_EFFECT_NONE
    order_intent_ref: str = ""
    order_intent_effect: str = ORDER_INTENT_EFFECT_NONE
    safety_boundary_ref: str = ""
    safety_boundary_effect: str = SAFETY_BOUNDARY_EFFECT_NONE
    reconciliation_unknown_outcome_ref: str = ""
    reconciliation_unknown_outcome_effect: str = RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_NONE
    conflict_status: Optional[str] = None
    selected_side: Optional[str] = None


@dataclass(frozen=True)
class ParityCaseV0:
    case_id: str
    side_state: SideState
    expected_composition_status: CompositionStatus
    requested_side: RequestedSide = RequestedSide.NEUTRAL_OBSERVE


def evaluate_scenario_matrix_for_side_state_v0(
    *,
    side_state: SideState,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    suitability_neutral_observe: bool = False,
) -> DoublePlayCompositionResultV1:
    from dataclasses import replace

    from trading.master_v2.double_play_suitability import project_strategy_suitability
    from trading.master_v2.double_play_survival import evaluate_survival_envelope
    from trading.master_v2.offline_double_play_scenario_replay_v0 import (
        _suitability_input,
        _survival_envelope,
    )

    survival = evaluate_survival_envelope(_survival_envelope())
    suitability = project_strategy_suitability(_suitability_input())
    if suitability_neutral_observe:
        proj = replace(suitability.projection, eligible_for_neutral_pool=True)
        suitability = replace(suitability, projection=proj, can_enter_neutral_pool=True)

    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        side_st=side_state,
        survival=survival,
        suitability=suitability,
    )
    return evaluate_scenario_matrix_composition_v0(matrix_input)


def extract_integrated_parity_envelope_v0(
    result: IntegratedOfflineReplayResultV1,
) -> ParityDecisionEnvelopeV0:
    evidence = result.evidence
    intermediate = result.intermediate
    composition_status = "blocked"
    composition_result_id = ""
    reason_codes: Tuple[str, ...] = tuple(evidence.reason_codes)
    conflict_status: Optional[str] = None
    selected_side: Optional[str] = None
    previous_side_state: Optional[str] = None
    next_side_state: Optional[str] = None

    if intermediate is not None:
        comp = intermediate.composition_result
        composition_status = comp.composition_status.value
        composition_result_id = comp.composition_id
        reason_codes = tuple(comp.reason_codes)
        conflict_status = comp.conflict_status.value
        selected_side = comp.selected_side.value
        previous_side_state = intermediate.state_switch.previous_side_state
        next_side_state = intermediate.state_switch.next_side_state

    return ParityDecisionEnvelopeV0(
        decision_outcome=evidence.decision_outcome,
        previous_side_state=previous_side_state,
        next_side_state=next_side_state,
        composition_status=composition_status,
        composition_result_id=composition_result_id,
        entry_or_exit_policy_ref=evidence.entry_or_exit_policy_ref,
        reason_codes=reason_codes,
        decision_precedence_trace=tuple(evidence.decision_precedence_trace),
        execution_eligible=evidence.execution_eligible,
        adapter_compatible=evidence.adapter_compatible,
        quantity_status=evidence.quantity_status,
        quantity_provenance_ref=evidence.quantity_provenance_ref,
        risk_sizing_ref=evidence.risk_sizing_ref,
        risk_sizing_effect=evidence.risk_sizing_effect,
        order_intent_ref=evidence.order_intent_ref,
        order_intent_effect=evidence.order_intent_effect,
        safety_boundary_ref=evidence.safety_boundary_ref,
        safety_boundary_effect=evidence.safety_boundary_effect,
        reconciliation_unknown_outcome_ref=evidence.reconciliation_unknown_outcome_ref,
        reconciliation_unknown_outcome_effect=evidence.reconciliation_unknown_outcome_effect,
        authority_effect=evidence.authority_effect,
        runtime_effect=evidence.runtime_effect,
        conflict_status=conflict_status,
        selected_side=selected_side,
    )


def extract_scenario_matrix_parity_envelope_v0(
    matrix_result: DoublePlayCompositionResultV1,
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome="not_bound_offline_matrix_only",
        previous_side_state=None,
        next_side_state=None,
        composition_status=matrix_result.composition_status.value,
        composition_result_id=matrix_result.composition_id,
        entry_or_exit_policy_ref="",
        reason_codes=tuple(matrix_result.reason_codes),
        decision_precedence_trace=(),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status="NOT_BOUND",
        authority_effect="NONE",
        runtime_effect="NONE",
        conflict_status=matrix_result.conflict_status.value,
        selected_side=matrix_result.selected_side.value,
    )


def extract_entry_exit_policy_parity_envelope_v0(
    decision: EntryExitPolicyDecisionV0,
    *,
    previous_side_state: Optional[str] = None,
    next_side_state: Optional[str] = None,
    composition_status: str = "",
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome=decision.decision_outcome.value,
        previous_side_state=previous_side_state,
        next_side_state=next_side_state,
        composition_status=composition_status,
        composition_result_id=decision.composition_result_ref,
        entry_or_exit_policy_ref=decision.policy_decision_id,
        reason_codes=tuple(decision.reason_codes),
        decision_precedence_trace=tuple(decision.decision_precedence_trace),
        execution_eligible=decision.execution_eligible,
        adapter_compatible=decision.adapter_compatible,
        quantity_status=decision.quantity_status,
        authority_effect=decision.authority_effect,
        runtime_effect=decision.runtime_effect,
        selected_side=decision.selected_side.value,
    )


def extract_capital_risk_sizing_parity_envelope_v0(
    binding: CapitalRiskSizingOfflineReplayBindingResultV0,
    *,
    decision_outcome: str = "",
    composition_result_id: str = "",
) -> ParityDecisionEnvelopeV0:
    ev = binding.evidence
    return ParityDecisionEnvelopeV0(
        decision_outcome=decision_outcome or ev.decision_outcome,
        previous_side_state=None,
        next_side_state=None,
        composition_status="",
        composition_result_id=composition_result_id,
        entry_or_exit_policy_ref=ev.entry_or_exit_policy_ref,
        reason_codes=tuple(ev.reason_codes),
        decision_precedence_trace=tuple(ev.decision_precedence_trace),
        execution_eligible=ev.execution_eligible,
        adapter_compatible=ev.adapter_compatible,
        quantity_status=binding.quantity_status,
        quantity_provenance_ref=binding.quantity_provenance_ref,
        risk_sizing_ref=binding.risk_sizing_ref,
        risk_sizing_effect=binding.risk_sizing_effect,
        order_intent_ref=ev.order_intent_ref,
        order_intent_effect=ev.order_intent_effect,
        authority_effect=ev.authority_effect,
        runtime_effect=ev.runtime_effect,
    )


def extract_scenario_replay_tick_capital_risk_sizing_envelope_v0(
    tick: OfflineDoublePlayScenarioReplayTickRecordV0,
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome=tick.entry_exit_decision_outcome,
        previous_side_state=tick.prior_side_state.value,
        next_side_state=tick.side_state.value,
        composition_status=tick.composition_status,
        composition_result_id=tick.composition_result_id,
        entry_or_exit_policy_ref=tick.entry_exit_policy_ref,
        reason_codes=tuple(tick.sizing_reason_codes),
        decision_precedence_trace=tuple(tick.entry_exit_decision_precedence_trace),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status=tick.quantity_status,
        quantity_provenance_ref=tick.quantity_provenance_ref,
        risk_sizing_ref=tick.capital_risk_sizing_ref,
        risk_sizing_effect=tick.risk_sizing_effect,
        order_intent_ref=tick.canonical_order_intent_ref,
        order_intent_effect=tick.order_intent_effect,
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def extract_scenario_replay_tick_parity_envelope_v0(
    tick: OfflineDoublePlayScenarioReplayTickRecordV0,
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome=tick.entry_exit_decision_outcome,
        previous_side_state=tick.prior_side_state.value,
        next_side_state=tick.side_state.value,
        composition_status=tick.composition_status,
        composition_result_id=tick.composition_result_id,
        entry_or_exit_policy_ref=tick.entry_exit_policy_ref,
        reason_codes=tuple(tick.entry_exit_reason_codes),
        decision_precedence_trace=tuple(tick.entry_exit_decision_precedence_trace),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status="NOT_BOUND",
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def integrated_assessments_match_scenario_side_state_v0(
    *,
    side_state: SideState,
    bull_status: DirectionalAssessmentStatus,
    bear_status: DirectionalAssessmentStatus,
) -> bool:
    expected_bull, expected_bear = _legacy_side_to_assessment_statuses(side_state)
    return bull_status is expected_bull and bear_status is expected_bear


def composition_matrix_results_aligned_v0(
    integrated: DoublePlayCompositionResultV1,
    scenario: DoublePlayCompositionResultV1,
) -> bool:
    return (
        integrated.composition_status is scenario.composition_status
        and integrated.conflict_status is scenario.conflict_status
        and integrated.selected_side is scenario.selected_side
        and set(integrated.reason_codes) == set(scenario.reason_codes)
    )


def assert_non_authority_boundary_v0(envelope: ParityDecisionEnvelopeV0) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.quantity_status == "NOT_BOUND"
    assert envelope.risk_sizing_effect == RISK_SIZING_EFFECT_NONE
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"


def assert_capital_risk_sizing_non_authority_boundary_v0(
    envelope: ParityDecisionEnvelopeV0,
) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    if envelope.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE:
        assert envelope.risk_sizing_ref
    assert envelope.risk_sizing_effect in {
        RISK_SIZING_EFFECT_NONE,
        RISK_SIZING_EFFECT_BOUND_OFFLINE,
    }


def assert_canonical_order_intent_non_authority_boundary_v0(
    envelope: ParityDecisionEnvelopeV0,
) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    if envelope.order_intent_effect == ORDER_INTENT_EFFECT_BOUND_OFFLINE:
        assert envelope.order_intent_ref
    assert envelope.order_intent_effect in {
        ORDER_INTENT_EFFECT_NONE,
        ORDER_INTENT_EFFECT_BOUND_OFFLINE,
    }


def assert_safety_kernel_non_authority_boundary_v0(
    envelope: ParityDecisionEnvelopeV0,
) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    if envelope.safety_boundary_effect == SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE:
        assert envelope.safety_boundary_ref
    assert envelope.safety_boundary_effect in {
        SAFETY_BOUNDARY_EFFECT_NONE,
        SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE,
    }


def assert_reconciliation_unknown_outcome_non_authority_boundary_v0(
    envelope: ParityDecisionEnvelopeV0,
) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    if (
        envelope.reconciliation_unknown_outcome_effect
        == RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
    ):
        assert envelope.reconciliation_unknown_outcome_ref
    assert envelope.reconciliation_unknown_outcome_effect in {
        RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_NONE,
        RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE,
    }


def extract_canonical_order_intent_parity_envelope_v0(
    binding: CanonicalOrderIntentOfflineReplayBindingResultV0,
    *,
    decision_outcome: str = "",
    composition_result_id: str = "",
) -> ParityDecisionEnvelopeV0:
    ev = binding.evidence
    return ParityDecisionEnvelopeV0(
        decision_outcome=decision_outcome or ev.decision_outcome,
        previous_side_state=None,
        next_side_state=None,
        composition_status="",
        composition_result_id=composition_result_id,
        entry_or_exit_policy_ref=ev.entry_or_exit_policy_ref,
        reason_codes=tuple(ev.reason_codes),
        decision_precedence_trace=tuple(ev.decision_precedence_trace),
        execution_eligible=ev.execution_eligible,
        adapter_compatible=ev.adapter_compatible,
        quantity_status=ev.quantity_status,
        quantity_provenance_ref=ev.quantity_provenance_ref,
        risk_sizing_ref=ev.risk_sizing_ref,
        risk_sizing_effect=ev.risk_sizing_effect,
        order_intent_ref=binding.order_intent_ref,
        order_intent_effect=binding.order_intent_effect,
        authority_effect=ev.authority_effect,
        runtime_effect=ev.runtime_effect,
    )


def extract_scenario_replay_tick_canonical_order_intent_envelope_v0(
    tick: OfflineDoublePlayScenarioReplayTickRecordV0,
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome=tick.entry_exit_decision_outcome,
        previous_side_state=tick.prior_side_state.value,
        next_side_state=tick.side_state.value,
        composition_status=tick.composition_status,
        composition_result_id=tick.composition_result_id,
        entry_or_exit_policy_ref=tick.entry_exit_policy_ref,
        reason_codes=tuple(tick.sizing_reason_codes),
        decision_precedence_trace=tuple(tick.entry_exit_decision_precedence_trace),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status=tick.quantity_status,
        quantity_provenance_ref=tick.quantity_provenance_ref,
        risk_sizing_ref=tick.capital_risk_sizing_ref,
        risk_sizing_effect=tick.risk_sizing_effect,
        order_intent_ref=tick.canonical_order_intent_ref,
        order_intent_effect=tick.order_intent_effect,
        safety_boundary_ref=tick.safety_boundary_ref,
        safety_boundary_effect=tick.safety_boundary_effect,
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def extract_safety_kernel_parity_envelope_v0(
    binding: SafetyKernelOfflineReplayBindingResultV0,
    *,
    decision_outcome: str = "",
    composition_result_id: str = "",
) -> ParityDecisionEnvelopeV0:
    ev = binding.evidence
    return ParityDecisionEnvelopeV0(
        decision_outcome=decision_outcome or ev.decision_outcome,
        previous_side_state=None,
        next_side_state=None,
        composition_status="",
        composition_result_id=composition_result_id,
        entry_or_exit_policy_ref=ev.entry_or_exit_policy_ref,
        reason_codes=tuple(ev.reason_codes),
        decision_precedence_trace=tuple(ev.decision_precedence_trace),
        execution_eligible=ev.execution_eligible,
        adapter_compatible=ev.adapter_compatible,
        quantity_status=ev.quantity_status,
        quantity_provenance_ref=ev.quantity_provenance_ref,
        risk_sizing_ref=ev.risk_sizing_ref,
        risk_sizing_effect=ev.risk_sizing_effect,
        order_intent_ref=ev.order_intent_ref,
        order_intent_effect=ev.order_intent_effect,
        safety_boundary_ref=binding.safety_boundary_ref,
        safety_boundary_effect=binding.safety_boundary_effect,
        authority_effect=ev.authority_effect,
        runtime_effect=ev.runtime_effect,
    )


def extract_scenario_replay_tick_safety_kernel_envelope_v0(
    tick: OfflineDoublePlayScenarioReplayTickRecordV0,
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome=tick.entry_exit_decision_outcome,
        previous_side_state=tick.prior_side_state.value,
        next_side_state=tick.side_state.value,
        composition_status=tick.composition_status,
        composition_result_id=tick.composition_result_id,
        entry_or_exit_policy_ref=tick.entry_exit_policy_ref,
        reason_codes=tuple(tick.entry_exit_reason_codes),
        decision_precedence_trace=tuple(tick.entry_exit_decision_precedence_trace),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status=tick.quantity_status,
        quantity_provenance_ref=tick.quantity_provenance_ref,
        risk_sizing_ref=tick.capital_risk_sizing_ref,
        risk_sizing_effect=tick.risk_sizing_effect,
        order_intent_ref=tick.canonical_order_intent_ref,
        order_intent_effect=tick.order_intent_effect,
        safety_boundary_ref=tick.safety_boundary_ref,
        safety_boundary_effect=tick.safety_boundary_effect,
        reconciliation_unknown_outcome_ref=tick.reconciliation_unknown_outcome_ref,
        reconciliation_unknown_outcome_effect=tick.reconciliation_unknown_outcome_effect,
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def extract_reconciliation_unknown_outcome_parity_envelope_v0(
    binding: ReconciliationUnknownOutcomeOfflineReplayBindingResultV0,
    *,
    decision_outcome: str = "",
    composition_result_id: str = "",
) -> ParityDecisionEnvelopeV0:
    ev = binding.evidence
    return ParityDecisionEnvelopeV0(
        decision_outcome=decision_outcome or ev.decision_outcome,
        previous_side_state=None,
        next_side_state=None,
        composition_status="",
        composition_result_id=composition_result_id,
        entry_or_exit_policy_ref=ev.entry_or_exit_policy_ref,
        reason_codes=tuple(ev.reason_codes),
        decision_precedence_trace=tuple(ev.decision_precedence_trace),
        execution_eligible=ev.execution_eligible,
        adapter_compatible=ev.adapter_compatible,
        quantity_status=ev.quantity_status,
        quantity_provenance_ref=ev.quantity_provenance_ref,
        risk_sizing_ref=ev.risk_sizing_ref,
        risk_sizing_effect=ev.risk_sizing_effect,
        order_intent_ref=ev.order_intent_ref,
        order_intent_effect=ev.order_intent_effect,
        safety_boundary_ref=ev.safety_boundary_ref,
        safety_boundary_effect=ev.safety_boundary_effect,
        reconciliation_unknown_outcome_ref=binding.reconciliation_unknown_outcome_ref,
        reconciliation_unknown_outcome_effect=binding.reconciliation_unknown_outcome_effect,
        authority_effect=ev.authority_effect,
        runtime_effect=ev.runtime_effect,
    )


def extract_scenario_replay_tick_reconciliation_unknown_outcome_envelope_v0(
    tick: OfflineDoublePlayScenarioReplayTickRecordV0,
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome=tick.entry_exit_decision_outcome,
        previous_side_state=tick.prior_side_state.value,
        next_side_state=tick.side_state.value,
        composition_status=tick.composition_status,
        composition_result_id=tick.composition_result_id,
        entry_or_exit_policy_ref=tick.entry_exit_policy_ref,
        reason_codes=tuple(tick.entry_exit_reason_codes),
        decision_precedence_trace=tuple(tick.entry_exit_decision_precedence_trace),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status=tick.quantity_status,
        quantity_provenance_ref=tick.quantity_provenance_ref,
        risk_sizing_ref=tick.capital_risk_sizing_ref,
        risk_sizing_effect=tick.risk_sizing_effect,
        order_intent_ref=tick.canonical_order_intent_ref,
        order_intent_effect=tick.order_intent_effect,
        safety_boundary_ref=tick.safety_boundary_ref,
        safety_boundary_effect=tick.safety_boundary_effect,
        reconciliation_unknown_outcome_ref=tick.reconciliation_unknown_outcome_ref,
        reconciliation_unknown_outcome_effect=tick.reconciliation_unknown_outcome_effect,
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def assert_scenario_replay_zero_order_boundary_v0(
    result: OfflineDoublePlayScenarioReplayResultV0,
) -> None:
    assert result.summary.orders_total == 0
    assert result.summary.cancels_total == 0
    assert result.summary.fills_total == 0
    assert result.summary.positions_opened_total == 0
    for tick in result.tick_records:
        assert tick.orders == 0
        assert tick.cancels == 0
        assert tick.fills == 0
        assert tick.positions_opened == 0


def legacy_composition_status_for_matrix_v0(status: CompositionStatus) -> str:
    mapping = {
        CompositionStatus.LONG_SELECTED: "eligible_model_only",
        CompositionStatus.SHORT_SELECTED: "eligible_model_only",
        CompositionStatus.CHOP_GUARD_BLOCK: "chop_guard",
        CompositionStatus.OBSERVE: "observe_only",
        CompositionStatus.NO_ACTION: "observe_only",
        CompositionStatus.BLOCKED: "blocked",
        CompositionStatus.REVERSAL_PREPARATION: "eligible_model_only",
    }
    return mapping.get(status, status.value)


def entry_exit_parity_envelopes_aligned_v0(
    integrated: ParityDecisionEnvelopeV0,
    scenario: ParityDecisionEnvelopeV0,
) -> bool:
    if integrated.decision_outcome != scenario.decision_outcome:
        return False
    if integrated.decision_precedence_trace != scenario.decision_precedence_trace:
        return False
    if set(integrated.reason_codes) != set(scenario.reason_codes):
        return False
    if integrated.previous_side_state != scenario.previous_side_state:
        return False
    if integrated.next_side_state != scenario.next_side_state:
        return False
    return True


def evaluate_scenario_entry_exit_for_fixture_v0(
    *,
    side_state: SideState,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    policy_context: ScenarioEntryExitPolicyContextV0 | None = None,
    matrix_result: DoublePlayCompositionResultV1 | None = None,
) -> EntryExitPolicyDecisionV0:
    matrix = matrix_result or evaluate_scenario_matrix_for_side_state_v0(
        side_state=side_state,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
    )
    return evaluate_scenario_entry_exit_policy_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        composition_result=matrix,
        side_state=side_state,
        policy_context=policy_context,
    )


def canonical_owner_refs_v0() -> Mapping[str, str]:
    return {
        "integrated_offline_replay": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
        "scenario_replay": OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
        "scenario_matrix_adapter": DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER,
        "double_play_composition_matrix": CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER,
        "entry_exit_policy": CANONICAL_ENTRY_EXIT_POLICY_OWNER,
        "entry_exit_scenario_binding_adapter": (
            DOUBLE_PLAY_ENTRY_EXIT_SCENARIO_BINDING_ADAPTER_OWNER
        ),
        "capital_risk_sizing": CANONICAL_CAPITAL_RISK_SIZING_OWNER,
        "capital_risk_sizing_offline_replay_binding_adapter": (
            CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
        ),
        "canonical_order_intent": CANONICAL_ORDER_INTENT_OWNER,
        "canonical_order_intent_offline_replay_binding_adapter": (
            CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
        ),
        "runtime_eligibility": RUNTIME_ELIGIBILITY_OWNER,
        "killswitch_fencing": KILLSWITCH_FENCING_OWNER,
        "safety_kernel_offline_replay_binding_adapter": (
            SAFETY_KERNEL_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
        ),
        "reconciliation_unknown_outcome_offline_replay_binding_adapter": (
            RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
        ),
        "runtime_state_reconciliation": RUNTIME_STATE_RECONCILIATION_OWNER,
        "reconciliation_entry_exit_policy": RECONCILIATION_ENTRY_EXIT_POLICY_OWNER,
        "parity_harness": INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_HARNESS_OWNER,
    }


def default_parity_cases_v0() -> Tuple[ParityCaseV0, ...]:
    return (
        ParityCaseV0("long_bull", SideState.LONG_ACTIVE, CompositionStatus.LONG_SELECTED),
        ParityCaseV0("short_bear", SideState.SHORT_ACTIVE, CompositionStatus.SHORT_SELECTED),
        ParityCaseV0(
            "both_confirmed_chop_guard",
            SideState.CHOP_GUARD_BLOCK,
            CompositionStatus.CHOP_GUARD_BLOCK,
        ),
        ParityCaseV0(
            "neutral_observe_no_action",
            SideState.NEUTRAL_OBSERVE,
            CompositionStatus.OBSERVE,
        ),
        ParityCaseV0(
            "reversal_preparation_boundary",
            SideState.LONG_ACTIVE,
            CompositionStatus.REVERSAL_PREPARATION,
        ),
    )


def evaluate_reversal_preparation_matrix_v0(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
) -> DoublePlayCompositionResultV1:
    from dataclasses import replace

    from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
    from trading.master_v2.double_play_composition_matrix_v1 import (
        PositionManagementContext,
        compute_composition_input_digest,
    )
    from trading.master_v2.double_play_suitability import project_strategy_suitability
    from trading.master_v2.double_play_survival import evaluate_survival_envelope
    from trading.master_v2.offline_double_play_scenario_replay_v0 import (
        _suitability_input,
        _survival_envelope,
    )

    survival = evaluate_survival_envelope(_survival_envelope())
    suitability = project_strategy_suitability(_suitability_input())
    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        side_st=SideState.LONG_ACTIVE,
        survival=survival,
        suitability=suitability,
    )
    bull_observe = replace(
        matrix_input.bull_directional_assessment,
        status=DirectionalAssessmentStatus.OBSERVE,
    )
    bear_confirmed = replace(
        matrix_input.bear_directional_assessment,
        status=DirectionalAssessmentStatus.CONFIRMED,
    )
    matrix_input = replace(
        matrix_input,
        bull_directional_assessment=bull_observe,
        bear_directional_assessment=bear_confirmed,
        position_management_context=PositionManagementContext.LONG_POSITION,
        input_digest="",
    )
    matrix_input = replace(
        matrix_input,
        input_digest=compute_composition_input_digest(matrix_input),
    )
    return evaluate_scenario_matrix_composition_v0(matrix_input)


def scan_changed_paths_for_forbidden_runtime_v0(
    changed_paths: Sequence[str],
) -> Tuple[bool, Tuple[str, ...]]:
    violations: list[str] = []
    for path in changed_paths:
        normalized = path.replace("\\", "/")
        if any(normalized.startswith(prefix) for prefix in FORBIDDEN_CHANGED_PATH_PREFIXES):
            if normalized not in ALLOWED_SLICE_CHANGED_PATH_PREFIXES:
                violations.append(normalized)
    return (len(violations) == 0, tuple(violations))
