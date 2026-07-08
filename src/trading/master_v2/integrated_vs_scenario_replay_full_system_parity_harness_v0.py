# src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py
"""
Offline harness: compare Integrated Offline Trading Logic Replay vs Scenario Replay
composition semantics through the canonical ``double_play_composition_matrix_v1`` owner.

No runtime authority, no economic evaluation, no trading semantic extension.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Literal, Mapping, Optional, Sequence, Tuple

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
    SafetyKernelOfflineReplayContextV0,
    bind_safety_kernel_offline_replay_evidence_v0,
    safety_kernel_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 import (
    ENTRY_EXIT_POLICY_OWNER as RECONCILIATION_ENTRY_EXIT_POLICY_OWNER,
    RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE,
    RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_NONE,
    RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    RUNTIME_STATE_RECONCILIATION_OWNER,
    ReconciliationUnknownOutcomeOfflineReplayBindingResultV0,
    ReconciliationUnknownOutcomeOfflineReplayContextV0,
    bind_reconciliation_unknown_outcome_offline_replay_evidence_v0,
    reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE,
    KILLSWITCH_BOUNDARY_EFFECT_NONE,
    KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    KillSwitchBoundaryMode,
    KillSwitchBoundaryOfflineReplayBindingResultV0,
    KillSwitchBoundaryOfflineReplayContextV0,
    bind_killswitch_boundary_offline_replay_evidence_v0,
    killswitch_boundary_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.promotion_gate_boundary_backtest_state_file_binding_adapter_v0 import (
    PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.promotion_gate_boundary_offline_replay_binding_adapter_v0 import (
    PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE,
    PROMOTION_GATE_BOUNDARY_EFFECT_NONE,
    PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    PROMOTION_GATE_CANONICAL_OWNER,
    PromotionGateBoundaryOfflineReplayBindingResultV0,
    PromotionGateBoundaryOfflineReplayContextV0,
    bind_promotion_gate_boundary_offline_replay_evidence_v0,
    promotion_gate_boundary_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.ai_observability_boundary_offline_replay_binding_adapter_v0 import (
    AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE,
    AI_OBSERVABILITY_BOUNDARY_EFFECT_NONE,
    AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    AiObservabilityBoundaryOfflineReplayBindingResultV0,
    AiObservabilityBoundaryOfflineReplayContextV0,
    ai_observability_boundary_binding_non_authority_boundary_ok_v0,
    bind_ai_observability_boundary_offline_replay_evidence_v0,
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
    build_scenario_matrix_composition_input_v0,
    evaluate_scenario_matrix_composition_v0,
)
from trading.master_v2.survival_suitability_scenario_binding_adapter_v0 import (
    ScenarioSurvivalSuitabilityOverridesV0,
    SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER,
    legacy_side_to_assessment_statuses_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    EntryExitPolicyDecisionV0,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
)
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    ScenarioEntryExitPolicyContextV0,
    default_scenario_entry_exit_policy_context_v0,
)
from trading.master_v2.bull_bear_state_switch_scenario_binding_adapter_v0 import (
    BULL_BEAR_STATE_SWITCH_SCENARIO_BINDING_ADAPTER_OWNER,
    CANONICAL_STATE_SWITCH_OWNER,
    STATE_SWITCH_EFFECT_BOUND_OFFLINE,
    STATE_SWITCH_EFFECT_NONE,
    ScenarioStateSwitchBindingResultV0,
    ScenarioStateSwitchContextV0,
    evaluate_scenario_state_switch_v0,
    state_switch_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (
    CANONICAL_SCOPE_EVENT_GENERATOR_OWNER,
    SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER,
    SCOPE_EVENT_EFFECT_BOUND_OFFLINE,
    ScenarioScopeEventBindingResultV0,
    ScenarioScopeEventContextV0,
    evaluate_scenario_scope_event_v0,
    scope_event_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.reversal_preparation_scenario_binding_adapter_v0 import (
    REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER,
    REVERSAL_PREPARATION_EFFECT_BOUND_OFFLINE,
    evaluate_scenario_reversal_preparation_entry_exit_v0,
    is_reversal_preparation_composition_v0,
    reversal_preparation_binding_non_authority_boundary_ok_v0,
    reversal_preparation_decision_is_reduce_only_preparation_v0,
)
from trading.master_v2.flat_before_opposite_side_scenario_binding_adapter_v0 import (
    FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER,
    evaluate_scenario_flat_before_opposite_side_entry_exit_v0,
    flat_before_opposite_side_binding_non_authority_boundary_ok_v0,
    flat_before_opposite_side_blocks_opposite_entry_v0,
    merge_flat_before_opposite_side_policy_context_v0,
)
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
    DOUBLE_PLAY_ENTRY_EXIT_SCENARIO_BINDING_ADAPTER_OWNER,
    ScenarioEntryExitPolicyContextV0,
    entry_exit_decision_non_authority_boundary_ok_v0,
    evaluate_scenario_entry_exit_policy_v0,
)
from trading.master_v2.double_play_state import (
    ActiveSide,
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    IntegratedOfflineReplayResultV1,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioReplayResultV0,
    OfflineDoublePlayScenarioReplayTickRecordV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)

INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_HARNESS_LAYER_VERSION = "v0"
INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_HARNESS_OWNER = (
    "trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0"
)

FOUR_WAY_PARITY_REWIRE_SLICE_ID = "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0"
SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_SLICE_ID = (
    "SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_V0"
)
SURFACE_P_BOUNDARY_PATH_BAR_SEQUENCE_4_WAY_PARITY_EXTENSION_SLICE_ID = (
    "SURFACE_P_BOUNDARY_PATH_BAR_SEQUENCE_4_WAY_PARITY_EXTENSION_V0"
)
SURFACE_P_CORE_BAR_SEQUENCE_FIXTURE_COUNT = 8
SURFACE_P_BOUNDARY_PATH_FIXTURE_COUNT = 5
SURFACE_P_BAR_SEQUENCE_FIXTURE_COUNT = (
    SURFACE_P_CORE_BAR_SEQUENCE_FIXTURE_COUNT + SURFACE_P_BOUNDARY_PATH_FIXTURE_COUNT
)
RUNTIME_REFERENCE_INTEGRATION_STATUS_V0 = "BOUND_NOT_ACTIVATED"
SurfacePBarSequencePathKind = Literal[
    "entry_path",
    "hold_position_management_path",
    "adverse_exit_path",
    "reversal_preparation_exit_path",
    "flat_before_opposite_side_path",
    "capital_risk_sizing_path",
    "canonical_order_intent_path",
    "blocked_no_action_path",
    "safety_kernel_boundary_path",
    "killswitch_boundary_path",
    "reconciliation_unknown_outcome_boundary_path",
    "promotion_gate_boundary_path",
    "ai_observability_boundary_path",
]
SURFACE_P_BOUNDARY_PATH_KINDS: Tuple[SurfacePBarSequencePathKind, ...] = (
    "safety_kernel_boundary_path",
    "killswitch_boundary_path",
    "reconciliation_unknown_outcome_boundary_path",
    "promotion_gate_boundary_path",
    "ai_observability_boundary_path",
)
BACKTEST_PARITY_WIRING_OWNER = "backtest.mv2_research_wiring_v1"
RUNTIME_BRIDGE_REFERENCE_OWNER = "trading.master_v2.canonical_core_runtime_integration_bridge_v0"

ALLOWED_SLICE_CHANGED_PATH_PREFIXES: Tuple[str, ...] = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "scripts/ops/run_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "scripts/ops/run_integrated_vs_scenario_replay_full_system_4_way_parity_rewire_v0.py",
    "scripts/ops/run_surface_p_full_bar_sequence_4_way_parity_completion_v0.py",
    "scripts/ops/run_surface_p_boundary_path_bar_sequence_4_way_parity_extension_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_boundary_path_bar_sequence_4_way_parity_extension_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
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
    killswitch_boundary_ref: str = ""
    killswitch_boundary_effect: str = KILLSWITCH_BOUNDARY_EFFECT_NONE
    promotion_gate_boundary_ref: str = ""
    promotion_gate_boundary_effect: str = PROMOTION_GATE_BOUNDARY_EFFECT_NONE
    ai_observability_boundary_ref: str = ""
    ai_observability_boundary_effect: str = AI_OBSERVABILITY_BOUNDARY_EFFECT_NONE
    state_switch_ref: str = ""
    state_switch_effect: str = STATE_SWITCH_EFFECT_NONE
    scope_event_ref: str = ""
    scope_event_effect: str = ""
    transition_reason_code: str = ""
    conflict_status: Optional[str] = None
    selected_side: Optional[str] = None


@dataclass(frozen=True)
class ParityCaseV0:
    case_id: str
    side_state: SideState
    expected_composition_status: CompositionStatus
    requested_side: RequestedSide = RequestedSide.NEUTRAL_OBSERVE


@dataclass(frozen=True)
class FullSystemFourWayParityAssessmentV0:
    integrated_lane_bound: bool
    scenario_lane_bound: bool
    backtest_lane_bound: bool
    runtime_reference_lane_bound: bool
    integrated_scenario_composition_aligned: bool
    backtest_non_authority_confirmed: bool
    runtime_reference_non_authority_confirmed: bool
    four_way_parity_rewire_bound: bool
    fail_closed_reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class SurfacePBarSequenceFixtureV0:
    fixture_id: str
    path_kind: SurfacePBarSequencePathKind
    backtest_bar_index: int
    scenario_side_state: SideState
    instrument_id: str
    trading_epoch: int
    context_reference: str


@dataclass(frozen=True)
class SurfacePBarSequenceFixtureAssessmentV0:
    fixture_id: str
    path_kind: SurfacePBarSequencePathKind
    integrated_lane_bound: bool
    scenario_lane_bound: bool
    backtest_lane_bound: bool
    runtime_reference_lane_bound: bool
    integrated_scenario_evidence_aligned: bool
    backtest_non_authority_confirmed: bool
    runtime_reference_non_authority_confirmed: bool
    four_way_fixture_parity_bound: bool
    fail_closed_reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class SurfacePFullBarSequenceParityAssessmentV0:
    fixture_assessments: Tuple[SurfacePBarSequenceFixtureAssessmentV0, ...]
    fixtures_complete: bool
    runtime_bridge_status: str
    core_fixtures_complete: bool = False
    boundary_path_fixtures_complete: bool = False
    boundary_fixtures_added: Tuple[str, ...] = ()
    fail_closed_reasons: Tuple[str, ...] = ()


def evaluate_scenario_matrix_for_side_state_v0(
    *,
    side_state: SideState,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    suitability_neutral_observe: bool = False,
    survival_suitability_overrides: ScenarioSurvivalSuitabilityOverridesV0 | None = None,
) -> DoublePlayCompositionResultV1:
    del suitability_neutral_observe  # canonical path; legacy neutral pool not authority
    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        side_st=side_state,
        survival_suitability_overrides=survival_suitability_overrides,
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
        killswitch_boundary_ref=evidence.killswitch_boundary_ref,
        killswitch_boundary_effect=evidence.killswitch_boundary_effect,
        state_switch_ref=(
            intermediate.state_switch.state_switch_id if intermediate is not None else ""
        ),
        state_switch_effect=(
            STATE_SWITCH_EFFECT_BOUND_OFFLINE
            if intermediate is not None
            else STATE_SWITCH_EFFECT_NONE
        ),
        transition_reason_code=(
            intermediate.state_switch.transition_reason_code if intermediate is not None else ""
        ),
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


def extract_state_switch_parity_envelope_v0(
    binding: ScenarioStateSwitchBindingResultV0,
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome="not_bound_offline_state_switch_only",
        previous_side_state=binding.side_state_before.value,
        next_side_state=binding.side_state_after.value,
        composition_status="not_bound_offline_state_switch_only",
        composition_result_id="",
        entry_or_exit_policy_ref="",
        reason_codes=(binding.transition.reason_code,),
        decision_precedence_trace=(),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status="NOT_BOUND",
        state_switch_ref=binding.state_switch_ref,
        state_switch_effect=binding.state_switch_effect,
        transition_reason_code=binding.transition.reason_code,
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def extract_scenario_replay_tick_state_switch_envelope_v0(
    tick: OfflineDoublePlayScenarioReplayTickRecordV0,
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome="not_bound_offline_state_switch_only",
        previous_side_state=tick.prior_side_state.value,
        next_side_state=tick.side_state.value,
        composition_status=tick.composition_status,
        composition_result_id=tick.composition_result_id,
        entry_or_exit_policy_ref=tick.entry_exit_policy_ref,
        reason_codes=(tick.transition_reason_code,),
        decision_precedence_trace=(),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status="NOT_BOUND",
        state_switch_ref=tick.state_switch_ref,
        state_switch_effect=tick.state_switch_effect,
        transition_reason_code=tick.transition_reason_code,
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def assert_state_switch_non_authority_boundary_v0(envelope: ParityDecisionEnvelopeV0) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    if envelope.state_switch_effect == STATE_SWITCH_EFFECT_BOUND_OFFLINE:
        assert envelope.state_switch_ref


_DEFAULT_SCENARIO_STATE_SWITCH_ENVELOPE = RuntimeEnvelope(
    static=StaticHardLimits(min_band_width=1.0, max_band_width=100.0),
    live_authorization=False,
)
_DEFAULT_SCENARIO_STATE_SWITCH_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.02,
)
_EMPTY_SCENARIO_SCOPE_STATE = RuntimeScopeState(
    anchor_price=0.0,
    current_downscope_boundary=0.0,
    current_upscope_boundary=0.0,
    current_hysteresis_band=0.0,
    last_switch_tick=-1,
    switches_in_window=0,
    window_start_tick=0,
    chop_latched=False,
    now_tick=0,
)


def evaluate_scenario_state_switch_for_fixture_v0(
    *,
    side_state: SideState,
    scope_event: ScopeEvent,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    scope_state: RuntimeScopeState | None = None,
    rules: DynamicScopeRules | None = None,
    now_tick: int | None = None,
) -> ScenarioStateSwitchBindingResultV0:
    tick = now_tick if now_tick is not None else trading_epoch
    return evaluate_scenario_state_switch_v0(
        ScenarioStateSwitchContextV0(
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
            context_reference=context_reference,
            side_state=side_state,
            scope_event=scope_event,
            scope_state=scope_state or _EMPTY_SCENARIO_SCOPE_STATE,
            rules=rules or _DEFAULT_SCENARIO_STATE_SWITCH_RULES,
            envelope=_DEFAULT_SCENARIO_STATE_SWITCH_ENVELOPE,
            now_tick=tick,
            scope_event_id=f"{context_reference}-scope-{scope_event.value}",
        )
    )


_DEFAULT_SCENARIO_SCOPE_EVENT_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.02,
)
_DEFAULT_SCENARIO_SCOPE_RUNTIME = RuntimeScopeState(
    anchor_price=100.0,
    current_hysteresis_band=4.0,
)


def _default_scenario_scope_confirmation_state_v0():
    from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeConfirmationStateV1

    return ScopeConfirmationStateV1(
        candidate_kind=None,
        candidate_count=0,
        last_evaluated_trading_epoch=0,
    )


def extract_scope_event_parity_envelope_v0(
    binding: ScenarioScopeEventBindingResultV0,
) -> ParityDecisionEnvelopeV0:
    evidence = binding.scope_event_evidence
    adverse = binding.scope_adverse_exit_signal
    return ParityDecisionEnvelopeV0(
        decision_outcome="not_bound_offline_scope_event_only",
        previous_side_state=None,
        next_side_state=None,
        composition_status="not_bound_offline_scope_event_only",
        composition_result_id="",
        entry_or_exit_policy_ref="",
        reason_codes=(evidence.event_type.value, adverse.reason_code),
        decision_precedence_trace=(),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status="NOT_BOUND",
        scope_event_ref=binding.scope_event_ref,
        scope_event_effect=binding.scope_event_effect,
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def assert_scope_event_non_authority_boundary_v0(envelope: ParityDecisionEnvelopeV0) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    if envelope.scope_event_effect == SCOPE_EVENT_EFFECT_BOUND_OFFLINE:
        assert envelope.scope_event_ref


def evaluate_scenario_scope_event_for_fixture_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 48,
    context_reference: str = "scope-adverse-narrow-rewire-v0",
    current_price: float = 96.0,
    adverse_exit_distance: float = 2.0,
) -> ScenarioScopeEventBindingResultV0:
    return evaluate_scenario_scope_event_v0(
        ScenarioScopeEventContextV0(
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
            context_reference=context_reference,
            current_price=current_price,
            scope_state=_DEFAULT_SCENARIO_SCOPE_RUNTIME,
            rules=_DEFAULT_SCENARIO_SCOPE_EVENT_RULES,
            active_side=ActiveSide.LONG,
            confirmation_state=_default_scenario_scope_confirmation_state_v0(),
            up_distance=2.0,
            adverse_exit_distance=adverse_exit_distance,
            reversal_distance=4.0,
        )
    )


def extract_reversal_preparation_parity_envelope_v0(
    decision: EntryExitPolicyDecisionV0,
    *,
    reversal_preparation_ref: str = "",
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome=decision.decision_outcome.value,
        previous_side_state=None,
        next_side_state=None,
        composition_status=CompositionStatus.REVERSAL_PREPARATION.value,
        composition_result_id=reversal_preparation_ref,
        entry_or_exit_policy_ref=decision.policy_decision_id or "",
        reason_codes=tuple(decision.reason_codes),
        decision_precedence_trace=tuple(decision.decision_precedence_trace),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status="NOT_BOUND",
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def assert_reversal_preparation_non_authority_boundary_v0(
    envelope: ParityDecisionEnvelopeV0,
) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    assert envelope.composition_status == CompositionStatus.REVERSAL_PREPARATION.value


def evaluate_scenario_reversal_preparation_for_fixture_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 48,
    context_reference: str = "reversal-prep-narrow-rewire-v0",
) -> EntryExitPolicyDecisionV0:
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
    )
    if not is_reversal_preparation_composition_v0(matrix):
        raise ValueError("fixture matrix must be reversal preparation composition")
    return evaluate_scenario_reversal_preparation_entry_exit_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=default_scenario_entry_exit_policy_context_v0(),
    )


def extract_adverse_scope_exit_reversal_preparation_parity_envelope_v0(
    scope_binding: ScenarioScopeEventBindingResultV0,
    decision: EntryExitPolicyDecisionV0,
) -> ParityDecisionEnvelopeV0:
    scope_env = extract_scope_event_parity_envelope_v0(scope_binding)
    return ParityDecisionEnvelopeV0(
        decision_outcome=decision.decision_outcome.value,
        previous_side_state=None,
        next_side_state=None,
        composition_status=CompositionStatus.REVERSAL_PREPARATION.value,
        composition_result_id="",
        entry_or_exit_policy_ref=decision.policy_decision_id or "",
        reason_codes=tuple(decision.reason_codes) + scope_env.reason_codes,
        decision_precedence_trace=tuple(decision.decision_precedence_trace),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status="NOT_BOUND",
        scope_event_ref=scope_binding.scope_event_ref,
        scope_event_effect=scope_binding.scope_event_effect,
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def assert_adverse_scope_exit_reversal_preparation_non_authority_boundary_v0(
    envelope: ParityDecisionEnvelopeV0,
) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    assert envelope.scope_event_ref
    assert envelope.entry_or_exit_policy_ref
    assert envelope.composition_status == CompositionStatus.REVERSAL_PREPARATION.value


def evaluate_scenario_adverse_scope_exit_reversal_preparation_for_fixture_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 48,
    context_reference: str = "adverse-scope-exit-reversal-prep-narrow-rewire-v0",
) -> tuple[ScenarioScopeEventBindingResultV0, EntryExitPolicyDecisionV0]:
    scope_binding = evaluate_scenario_scope_event_for_fixture_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=f"{context_reference}-scope",
    )
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=f"{context_reference}-reversal",
    )
    if not is_reversal_preparation_composition_v0(matrix):
        raise ValueError("fixture matrix must be reversal preparation composition")
    policy_ctx = replace(
        default_scenario_entry_exit_policy_context_v0(),
        scope_adverse_exit_signal=scope_binding.scope_adverse_exit_signal,
    )
    decision = evaluate_scenario_reversal_preparation_entry_exit_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=f"{context_reference}-reversal",
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=policy_ctx,
    )
    if not scope_binding.scope_adverse_exit_signal.triggered:
        raise ValueError("adverse scope fixture must trigger scope adverse exit signal")
    if not reversal_preparation_binding_non_authority_boundary_ok_v0(decision):
        raise ValueError("reversal preparation binding violated non-authority boundary")
    return scope_binding, decision


def extract_flat_before_opposite_side_parity_envelope_v0(
    decision: EntryExitPolicyDecisionV0,
    *,
    composition_status: str,
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome=decision.decision_outcome.value,
        previous_side_state=None,
        next_side_state=None,
        composition_status=composition_status,
        composition_result_id="",
        entry_or_exit_policy_ref=decision.policy_decision_id or "",
        reason_codes=tuple(decision.reason_codes),
        decision_precedence_trace=tuple(decision.decision_precedence_trace),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status="NOT_BOUND",
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def assert_flat_before_opposite_side_non_authority_boundary_v0(
    envelope: ParityDecisionEnvelopeV0,
) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    assert envelope.entry_or_exit_policy_ref


def evaluate_scenario_flat_before_opposite_side_for_fixture_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 54,
    context_reference: str = "flat-before-opposite-narrow-rewire-v0",
) -> EntryExitPolicyDecisionV0:
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.SHORT_ARMED,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
    )
    if matrix.composition_status is not CompositionStatus.SHORT_SELECTED:
        raise ValueError("fixture matrix must be SHORT_SELECTED for opposite-side block")
    decision = evaluate_scenario_flat_before_opposite_side_entry_exit_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=default_scenario_entry_exit_policy_context_v0(),
    )
    if not flat_before_opposite_side_blocks_opposite_entry_v0(decision):
        raise ValueError("fixture must block opposite entry while position not flat")
    if not flat_before_opposite_side_binding_non_authority_boundary_ok_v0(decision):
        raise ValueError("flat-before-opposite-side binding violated non-authority boundary")
    return decision


def extract_entry_position_exit_policy_parity_envelope_v0(
    decision: EntryExitPolicyDecisionV0,
    *,
    composition_status: str,
    previous_side_state: Optional[str] = None,
    next_side_state: Optional[str] = None,
) -> ParityDecisionEnvelopeV0:
    return extract_entry_exit_policy_parity_envelope_v0(
        decision,
        previous_side_state=previous_side_state,
        next_side_state=next_side_state,
        composition_status=composition_status,
    )


def assert_entry_position_exit_policy_non_authority_boundary_v0(
    envelope: ParityDecisionEnvelopeV0,
) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    assert envelope.entry_or_exit_policy_ref
    assert envelope.decision_precedence_trace


def evaluate_scenario_entry_position_exit_policy_for_fixture_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 55,
    context_reference: str = "entry-position-exit-policy-narrow-rewire-v0",
) -> EntryExitPolicyDecisionV0:
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.SHORT_ARMED,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
    )
    if matrix.composition_status is not CompositionStatus.SHORT_SELECTED:
        raise ValueError("fixture matrix must be SHORT_SELECTED for opposite-entry block")
    scope_binding = evaluate_scenario_scope_event_for_fixture_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=f"{context_reference}-scope",
    )
    merged_ctx = merge_flat_before_opposite_side_policy_context_v0(
        side_state=SideState.LONG_ACTIVE,
        policy_context=replace(
            default_scenario_entry_exit_policy_context_v0(),
            scope_adverse_exit_signal=scope_binding.scope_adverse_exit_signal,
        ),
    )
    decision = evaluate_scenario_entry_exit_policy_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        composition_result=matrix,
        side_state=SideState.SHORT_ARMED,
        policy_context=merged_ctx,
    )
    if decision.decision_outcome in (DecisionOutcome.ENTER_LONG, DecisionOutcome.ENTER_SHORT):
        raise ValueError("entry position exit fixture must block opposite entry while long open")
    if decision.position_flip_allowed:
        raise ValueError("entry position exit fixture must keep position_flip_allowed false")
    if not entry_exit_decision_non_authority_boundary_ok_v0(decision):
        raise ValueError("entry position exit binding violated non-authority boundary")
    if not scope_binding.scope_adverse_exit_signal.triggered:
        raise ValueError("entry position exit fixture requires adverse scope handoff signal")
    return decision


def integrated_assessments_match_scenario_side_state_v0(
    *,
    side_state: SideState,
    bull_status: DirectionalAssessmentStatus,
    bear_status: DirectionalAssessmentStatus,
) -> bool:
    expected_bull, expected_bear = legacy_side_to_assessment_statuses_v0(side_state)
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


def assert_promotion_gate_boundary_non_authority_boundary_v0(
    envelope: ParityDecisionEnvelopeV0,
) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    if envelope.promotion_gate_boundary_effect == PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE:
        assert envelope.promotion_gate_boundary_ref
    assert envelope.promotion_gate_boundary_effect in {
        PROMOTION_GATE_BOUNDARY_EFFECT_NONE,
        PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE,
    }


def assert_killswitch_boundary_non_authority_boundary_v0(
    envelope: ParityDecisionEnvelopeV0,
) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"
    if envelope.killswitch_boundary_effect == KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE:
        assert envelope.killswitch_boundary_ref
    assert envelope.killswitch_boundary_effect in {
        KILLSWITCH_BOUNDARY_EFFECT_NONE,
        KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE,
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
        killswitch_boundary_ref=tick.killswitch_boundary_ref,
        killswitch_boundary_effect=tick.killswitch_boundary_effect,
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def extract_killswitch_boundary_parity_envelope_v0(
    binding: KillSwitchBoundaryOfflineReplayBindingResultV0,
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
        reconciliation_unknown_outcome_ref=ev.reconciliation_unknown_outcome_ref,
        reconciliation_unknown_outcome_effect=ev.reconciliation_unknown_outcome_effect,
        killswitch_boundary_ref=binding.killswitch_boundary_ref,
        killswitch_boundary_effect=binding.killswitch_boundary_effect,
        authority_effect=ev.authority_effect,
        runtime_effect=ev.runtime_effect,
    )


def extract_scenario_replay_tick_killswitch_boundary_envelope_v0(
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
        killswitch_boundary_ref=tick.killswitch_boundary_ref,
        killswitch_boundary_effect=tick.killswitch_boundary_effect,
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


def extract_promotion_gate_boundary_parity_envelope_v0(
    binding: PromotionGateBoundaryOfflineReplayBindingResultV0,
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
        reconciliation_unknown_outcome_ref=ev.reconciliation_unknown_outcome_ref,
        reconciliation_unknown_outcome_effect=ev.reconciliation_unknown_outcome_effect,
        killswitch_boundary_ref=ev.killswitch_boundary_ref,
        killswitch_boundary_effect=ev.killswitch_boundary_effect,
        promotion_gate_boundary_ref=binding.promotion_gate_boundary_ref,
        promotion_gate_boundary_effect=binding.promotion_gate_boundary_effect,
        authority_effect=ev.authority_effect,
        runtime_effect=ev.runtime_effect,
    )


def extract_ai_observability_boundary_parity_envelope_v0(
    binding: AiObservabilityBoundaryOfflineReplayBindingResultV0,
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
        reconciliation_unknown_outcome_ref=ev.reconciliation_unknown_outcome_ref,
        reconciliation_unknown_outcome_effect=ev.reconciliation_unknown_outcome_effect,
        killswitch_boundary_ref=ev.killswitch_boundary_ref,
        killswitch_boundary_effect=ev.killswitch_boundary_effect,
        promotion_gate_boundary_ref="",
        promotion_gate_boundary_effect=PROMOTION_GATE_BOUNDARY_EFFECT_NONE,
        ai_observability_boundary_ref=binding.ai_observability_boundary_ref,
        ai_observability_boundary_effect=binding.ai_observability_boundary_effect,
        authority_effect=ev.authority_effect,
        runtime_effect=ev.runtime_effect,
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
        "killswitch_boundary_offline_replay_binding_adapter": (
            KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
        ),
        "state_switch": CANONICAL_STATE_SWITCH_OWNER,
        "bull_bear_state_switch_scenario_binding_adapter": (
            BULL_BEAR_STATE_SWITCH_SCENARIO_BINDING_ADAPTER_OWNER
        ),
        "scope_event_generator": CANONICAL_SCOPE_EVENT_GENERATOR_OWNER,
        "scope_event_generator_scenario_binding_adapter": (
            SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER
        ),
        "reversal_preparation_scenario_binding_adapter": (
            REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER
        ),
        "flat_before_opposite_side_scenario_binding_adapter": (
            FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER
        ),
        "survival_suitability_scenario_binding_adapter": (
            SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER
        ),
        "runtime_state_reconciliation": RUNTIME_STATE_RECONCILIATION_OWNER,
        "reconciliation_entry_exit_policy": RECONCILIATION_ENTRY_EXIT_POLICY_OWNER,
        "promotion_economic_gate": PROMOTION_GATE_CANONICAL_OWNER,
        "promotion_gate_boundary_offline_replay_binding_adapter": (
            PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
        ),
        "promotion_gate_boundary_backtest_state_file_binding_adapter": (
            PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER
        ),
        "backtest_parity_wiring": BACKTEST_PARITY_WIRING_OWNER,
        "runtime_bridge_reference": RUNTIME_BRIDGE_REFERENCE_OWNER,
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

    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        side_st=SideState.LONG_ACTIVE,
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


def extract_backtest_evidence_parity_envelope_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
) -> ParityDecisionEnvelopeV0:
    from trading.master_v2.canonical_trading_decision_evidence_v1 import (
        CanonicalTradingDecisionEvidenceV1,
    )

    if not isinstance(evidence, CanonicalTradingDecisionEvidenceV1):
        raise TypeError("evidence must be CanonicalTradingDecisionEvidenceV1")
    return ParityDecisionEnvelopeV0(
        decision_outcome=evidence.decision_outcome,
        previous_side_state=evidence.previous_direction_state or None,
        next_side_state=evidence.next_direction_state or None,
        composition_status="",
        composition_result_id=evidence.composition_result_ref,
        entry_or_exit_policy_ref=evidence.entry_or_exit_policy_ref,
        reason_codes=tuple(evidence.reason_codes),
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
        killswitch_boundary_ref=evidence.killswitch_boundary_ref,
        killswitch_boundary_effect=evidence.killswitch_boundary_effect,
        authority_effect=evidence.authority_effect,
        runtime_effect=evidence.runtime_effect,
        selected_side=evidence.selected_side or None,
    )


def extract_runtime_reference_parity_envelope_v0() -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome="runtime_reference_not_activated",
        previous_side_state=None,
        next_side_state=None,
        composition_status="runtime_reference_only",
        composition_result_id="runtime_bridge_reference_v0",
        entry_or_exit_policy_ref=RUNTIME_BRIDGE_REFERENCE_OWNER,
        reason_codes=("BOUND_NOT_ACTIVATED", "NO_RUNTIME_AUTHORITY"),
        decision_precedence_trace=("runtime_reference_lane_v0",),
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status="NOT_BOUND",
        authority_effect="NONE",
        runtime_effect="NONE",
        transition_reason_code=RUNTIME_REFERENCE_INTEGRATION_STATUS_V0,
    )


def assert_runtime_reference_lane_v0(envelope: ParityDecisionEnvelopeV0) -> None:
    assert envelope.transition_reason_code == RUNTIME_REFERENCE_INTEGRATION_STATUS_V0
    assert envelope.decision_outcome == "runtime_reference_not_activated"
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"


def assert_backtest_lane_non_authority_boundary_v0(envelope: ParityDecisionEnvelopeV0) -> None:
    assert not envelope.execution_eligible
    assert not envelope.adapter_compatible
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"


def _default_mv2_research_cfg_v0() -> Mapping[str, object]:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_params": {
                "fast_window": 2,
                "slow_window": 3,
            },
        },
    }


def _synthetic_mv2_research_bars_v0(*, bar_count: int = 13) -> "pd.DataFrame":
    import pandas as pd

    idx = pd.date_range("2026-06-01", periods=bar_count, freq="1h", tz="UTC")
    close = [100.0 + float(i) for i in range(bar_count)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1m" for _ in close],
        },
        index=idx,
    )


def bind_backtest_bar_four_way_parity_lane_v0() -> ParityDecisionEnvelopeV0 | None:
    from src.backtest.mv2_research_wiring_v1 import (
        MV2_REQUIRED_INSTRUMENT_ID,
        run_mv2_research_backtest_wiring_v1,
    )

    result = run_mv2_research_backtest_wiring_v1(
        bars=_synthetic_mv2_research_bars_v0(),
        strategy_id="ma_crossover",
        cfg=_default_mv2_research_cfg_v0(),
        instrument_id=MV2_REQUIRED_INSTRUMENT_ID,
    )
    if not result.bar_outcomes:
        return None
    for bar_outcome in result.bar_outcomes:
        envelope = extract_backtest_evidence_parity_envelope_v0(bar_outcome.evidence)
        assert_backtest_lane_non_authority_boundary_v0(envelope)
        return envelope
    return None


def evaluate_surface_p_four_way_parity_v0(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    integrated_envelope: ParityDecisionEnvelopeV0 | None = None,
) -> FullSystemFourWayParityAssessmentV0:
    fail_reasons: list[str] = []

    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.CHOP_GUARD_BLOCK,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
    )
    scenario_env = extract_scenario_matrix_parity_envelope_v0(matrix)
    scenario_lane_bound = matrix.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    if scenario_lane_bound:
        assert_non_authority_boundary_v0(scenario_env)
    else:
        fail_reasons.append("scenario_lane_unbound")

    integrated_lane_bound = integrated_envelope is not None
    integrated_scenario_aligned = False
    if integrated_envelope is not None:
        try:
            assert_non_authority_boundary_v0(integrated_envelope)
            integrated_scenario_aligned = (
                integrated_envelope.composition_status == scenario_env.composition_status
            )
        except AssertionError:
            integrated_lane_bound = False
            fail_reasons.append("integrated_lane_invalid")
    else:
        fail_reasons.append("integrated_lane_unbound")
    if integrated_lane_bound and not integrated_scenario_aligned:
        fail_reasons.append("integrated_scenario_composition_not_aligned")

    backtest_env = bind_backtest_bar_four_way_parity_lane_v0()
    backtest_lane_bound = backtest_env is not None
    backtest_non_authority = backtest_lane_bound
    if not backtest_lane_bound:
        fail_reasons.append("backtest_lane_unbound")

    runtime_env = extract_runtime_reference_parity_envelope_v0()
    runtime_reference_lane_bound = True
    runtime_reference_non_authority = True
    try:
        assert_runtime_reference_lane_v0(runtime_env)
    except AssertionError:
        runtime_reference_lane_bound = False
        runtime_reference_non_authority = False
        fail_reasons.append("runtime_reference_lane_invalid")

    four_way_bound = (
        integrated_lane_bound
        and scenario_lane_bound
        and backtest_lane_bound
        and runtime_reference_lane_bound
        and integrated_scenario_aligned
        and backtest_non_authority
        and runtime_reference_non_authority
    )
    return FullSystemFourWayParityAssessmentV0(
        integrated_lane_bound=integrated_lane_bound,
        scenario_lane_bound=scenario_lane_bound,
        backtest_lane_bound=backtest_lane_bound,
        runtime_reference_lane_bound=runtime_reference_lane_bound,
        integrated_scenario_composition_aligned=integrated_scenario_aligned,
        backtest_non_authority_confirmed=backtest_non_authority,
        runtime_reference_non_authority_confirmed=runtime_reference_non_authority,
        four_way_parity_rewire_bound=four_way_bound,
        fail_closed_reasons=tuple(fail_reasons),
    )


_SURFACE_P_INTEGRATED_INSTRUMENT = "inst-eth-usdt-perp"
_SURFACE_P_REPLAY_ID = "surface-p-bar-sequence-integrated-replay-v0"
_SURFACE_P_CONFIG_DIGEST = "c" * 64
_SURFACE_P_IMPL_DIGEST = "d" * 64


def surface_p_core_bar_sequence_fixtures_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 44,
    context_reference: str = "surface-p-bar-sequence-4way-parity-v0",
) -> Tuple[SurfacePBarSequenceFixtureV0, ...]:
    return (
        SurfacePBarSequenceFixtureV0(
            "entry_long_path",
            "entry_path",
            0,
            SideState.LONG_ARMED,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "hold_position_management",
            "hold_position_management_path",
            1,
            SideState.LONG_ACTIVE,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "adverse_scope_exit",
            "adverse_exit_path",
            2,
            SideState.LONG_ACTIVE,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "reversal_preparation_exit",
            "reversal_preparation_exit_path",
            3,
            SideState.LONG_ACTIVE,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "flat_before_opposite_side",
            "flat_before_opposite_side_path",
            4,
            SideState.SHORT_ARMED,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "capital_risk_sizing",
            "capital_risk_sizing_path",
            5,
            SideState.LONG_ARMED,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "canonical_order_intent",
            "canonical_order_intent_path",
            6,
            SideState.LONG_ARMED,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "blocked_no_action",
            "blocked_no_action_path",
            7,
            SideState.CHOP_GUARD_BLOCK,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
    )


def surface_p_boundary_path_fixtures_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 44,
    context_reference: str = "surface-p-boundary-path-4way-parity-v0",
) -> Tuple[SurfacePBarSequenceFixtureV0, ...]:
    return (
        SurfacePBarSequenceFixtureV0(
            "safety_kernel_boundary",
            "safety_kernel_boundary_path",
            8,
            SideState.LONG_ACTIVE,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "killswitch_boundary",
            "killswitch_boundary_path",
            9,
            SideState.KILL_ALL,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "reconciliation_unknown_outcome_boundary",
            "reconciliation_unknown_outcome_boundary_path",
            10,
            SideState.LONG_ACTIVE,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "promotion_gate_boundary",
            "promotion_gate_boundary_path",
            11,
            SideState.LONG_ARMED,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
        SurfacePBarSequenceFixtureV0(
            "ai_observability_boundary",
            "ai_observability_boundary_path",
            12,
            SideState.LONG_ACTIVE,
            instrument_id,
            trading_epoch,
            context_reference,
        ),
    )


def surface_p_bar_sequence_fixtures_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 44,
    context_reference: str = "surface-p-bar-sequence-4way-parity-v0",
) -> Tuple[SurfacePBarSequenceFixtureV0, ...]:
    return surface_p_core_bar_sequence_fixtures_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
    ) + surface_p_boundary_path_fixtures_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference="surface-p-boundary-path-4way-parity-v0",
    )


def parity_decision_evidence_core_fields_aligned_v0(
    left: ParityDecisionEnvelopeV0,
    right: ParityDecisionEnvelopeV0,
    *,
    require_risk_sizing: bool = False,
    require_order_intent: bool = False,
) -> bool:
    if left.decision_outcome != right.decision_outcome:
        return False
    if left.decision_precedence_trace != right.decision_precedence_trace:
        return False
    if set(left.reason_codes) != set(right.reason_codes):
        return False
    if left.authority_effect != right.authority_effect:
        return False
    if left.runtime_effect != right.runtime_effect:
        return False
    if require_risk_sizing and left.risk_sizing_effect != right.risk_sizing_effect:
        return False
    if require_order_intent and left.order_intent_effect != right.order_intent_effect:
        return False
    return True


def run_backtest_bar_sequence_envelopes_v0() -> Tuple[ParityDecisionEnvelopeV0, ...]:
    from src.backtest.mv2_research_wiring_v1 import (
        MV2_REQUIRED_INSTRUMENT_ID,
        run_mv2_research_backtest_wiring_v1,
    )

    result = run_mv2_research_backtest_wiring_v1(
        bars=_synthetic_mv2_research_bars_v0(),
        strategy_id="ma_crossover",
        cfg=_default_mv2_research_cfg_v0(),
        instrument_id=MV2_REQUIRED_INSTRUMENT_ID,
    )
    envelopes: list[ParityDecisionEnvelopeV0] = []
    for bar_outcome in result.bar_outcomes:
        envelope = extract_backtest_evidence_parity_envelope_v0(bar_outcome.evidence)
        assert_backtest_lane_non_authority_boundary_v0(envelope)
        envelopes.append(envelope)
    return tuple(envelopes)


def bind_backtest_bar_parity_lane_at_index_v0(
    bar_index: int,
) -> ParityDecisionEnvelopeV0 | None:
    envelopes = run_backtest_bar_sequence_envelopes_v0()
    if bar_index < 0 or bar_index >= len(envelopes):
        return None
    return envelopes[bar_index]


def _surface_p_integrated_replay_overrides_v0(
    fixture: SurfacePBarSequenceFixtureV0,
) -> Mapping[str, object]:
    from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
    from trading.master_v2.double_play_composition_matrix_v1 import PositionManagementContext

    base: dict[str, object] = {
        "price_path": (3500.0, 3570.0),
        "side_state": fixture.scenario_side_state,
        "direction_state": EntryExitDirectionState.LONG_ARMED,
    }
    if fixture.path_kind == "entry_path":
        base.update(
            {
                "side_state": SideState.LONG_ARMED,
                "direction_state": EntryExitDirectionState.LONG_ARMED,
                "price_path": (3500.0, 3570.0),
            }
        )
    elif fixture.path_kind == "hold_position_management_path":
        base.update(
            {
                "side_state": SideState.LONG_ACTIVE,
                "direction_state": EntryExitDirectionState.LONG_ACTIVE,
                "position_state": PositionState.OPEN_FULL,
                "existing_position_side": ExistingPositionSide.LONG,
                "venue_flat": False,
                "position_management_context": PositionManagementContext.LONG_POSITION,
            }
        )
    elif fixture.path_kind == "adverse_exit_path":
        base.update(
            {
                "side_state": SideState.LONG_ACTIVE,
                "direction_state": EntryExitDirectionState.LONG_ACTIVE,
                "position_state": PositionState.OPEN_FULL,
                "existing_position_side": ExistingPositionSide.LONG,
                "venue_flat": False,
                "scope_adverse_exit_signal": PolicySignalV0(
                    triggered=True,
                    reason_code="adverse_scope",
                ),
            }
        )
    elif fixture.path_kind == "reversal_preparation_exit_path":
        base.update(
            {
                "side_state": SideState.LONG_ACTIVE,
                "direction_state": EntryExitDirectionState.LONG_ACTIVE,
                "position_state": PositionState.OPEN_FULL,
                "existing_position_side": ExistingPositionSide.LONG,
                "venue_flat": False,
                "price_path": (3500.0, 3400.0),
                "scope_direction_state": ScopeDirectionState.SHORT,
            }
        )
    elif fixture.path_kind == "flat_before_opposite_side_path":
        base.update(
            {
                "side_state": SideState.SHORT_ARMED,
                "direction_state": EntryExitDirectionState.SHORT_ARMED,
                "position_state": PositionState.OPEN_FULL,
                "existing_position_side": ExistingPositionSide.LONG,
                "venue_flat": False,
                "scope_direction_state": ScopeDirectionState.SHORT,
                "price_path": (3500.0, 3400.0),
            }
        )
    elif fixture.path_kind in ("capital_risk_sizing_path", "canonical_order_intent_path"):
        base.update(
            {
                "side_state": SideState.LONG_ARMED,
                "direction_state": EntryExitDirectionState.LONG_ARMED,
                "price_path": (3500.0, 3570.0),
            }
        )
    elif fixture.path_kind == "blocked_no_action_path":
        base.update(
            {
                "side_state": SideState.CHOP_GUARD_BLOCK,
                "direction_state": EntryExitDirectionState.NEUTRAL,
                "price_path": (3500.0, 3600.0),
            }
        )
    return base


def build_surface_p_integrated_replay_result_v0(
    fixture: SurfacePBarSequenceFixtureV0,
) -> IntegratedOfflineReplayResultV1 | None:
    from trading.master_v2.canonical_market_context_v1 import (
        BarFinalityStatus,
        CanonicalMarketContextBindingStateV1,
        CanonicalMarketContextV1,
        ClockTrustStatus,
        DataIntegrityStatus,
        FEATURE_CONTRACT_VERSION,
        WarmupStatus,
        with_computed_input_digest,
    )
    from trading.master_v2.canonical_scope_initialization_v1 import (
        CanonicalScopeInitializationPolicyV1,
        ScopeInitializationPrerequisitesV1,
        ScopeReinitializationGuardV1,
        SCOPE_INITIALIZATION_POLICY_VERSION,
    )
    from trading.master_v2.deterministic_scope_event_generator_v1 import (
        SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ScopeConfirmationStateV1,
        ScopeCooldownStateV1,
        ScopeDirectionState,
        ScopeEventGeneratorPolicyV1,
    )
    from trading.master_v2.directional_assessment_v1 import (
        DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
        DirectionalAssessmentPolicyV1,
        DirectionalAssessmentSide,
        DirectionalConfirmationStateV1,
    )
    from trading.master_v2.double_play_composition_matrix_v1 import (
        DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
        BothCandidateOutcome,
        BothInvalidOutcome,
        CompositionDirectionState,
        DoublePlayCompositionPolicyV1,
        PositionManagementContext,
    )
    from trading.master_v2.double_play_entry_exit_policy_v0 import (
        ENTRY_EXIT_POLICY_VERSION,
        DoublePlayEntryExitPolicyV0,
        ReconciliationState,
        SafetyMode,
        TradingGate,
    )
    from trading.master_v2.double_play_futures_input import FuturesMarketType
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        IntegratedOfflineReplayInputV1,
        IntegratedOfflineReplayPoliciesV1,
    )
    from trading.master_v2.suitability_binding_v1 import (
        SUITABILITY_RANKING_POLICY_VERSION,
        SuitabilityBindingStatus,
        SuitabilityRankingPolicyV1,
        SuitabilityRegimeStatus,
        SuitabilityStrategyEntryV1,
        SuitabilityStrategyRegistryV1,
    )
    from trading.master_v2.survival_assessment_v1 import (
        SURVIVAL_ASSESSMENT_POLICY_VERSION,
        SurvivalAssessmentPolicyV1,
    )

    overrides = dict(_surface_p_integrated_replay_overrides_v0(fixture))
    price_path = tuple(overrides.pop("price_path", (3500.0, 3570.0)))  # type: ignore[arg-type]
    ctx = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id=f"ctx-surface-p-{fixture.fixture_id}",
            instrument_id=_SURFACE_P_INTEGRATED_INSTRUMENT,
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=fixture.trading_epoch,
            market_event_time="2026-06-30T12:00:00+00:00",
            decision_time="2026-06-30T12:00:01+00:00",
            bar_interval="1m",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=float(price_path[-1]),
            index_price=float(price_path[-1]) - 0.5,
            best_bid=float(price_path[-1]) - 0.2,
            best_ask=float(price_path[-1]) + 0.2,
            spread=0.4,
            volume=1_250_000.0,
            open_interest=85_000_000.0,
            funding_rate=0.00012,
            volatility_estimate=0.38,
            trend_feature_set={"slope": 0.02, "strength": 0.71},
            momentum_feature_set={"rsi": 55.0, "roc": 0.015},
            liquidity_feature_set={"depth_score": 0.88},
            market_structure_feature_set={"range_ratio": 0.42},
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=WarmupStatus.WARMUP_COMPLETE,
            feature_contract_version=FEATURE_CONTRACT_VERSION,
            input_digest="",
        )
    )
    replay_input = IntegratedOfflineReplayInputV1(
        replay_id=_SURFACE_P_REPLAY_ID,
        instrument_id=_SURFACE_P_INTEGRATED_INSTRUMENT,
        trading_epoch=fixture.trading_epoch,
        canonical_market_context=ctx,
        market_context_binding_state=CanonicalMarketContextBindingStateV1(),
        scope_prerequisites=ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        scope_reinitialization_guard=ScopeReinitializationGuardV1(),
        existing_scope=None,
        scope_direction_state=overrides.get("scope_direction_state", ScopeDirectionState.LONG),
        scope_confirmation_state=ScopeConfirmationStateV1(
            candidate_kind=None,
            candidate_count=1,
            last_evaluated_trading_epoch=fixture.trading_epoch - 1,
        ),
        scope_cooldown_state=ScopeCooldownStateV1(
            active=False,
            remaining_epochs=0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        up_distance=200.0,
        adverse_exit_distance=80.0,
        reversal_distance=120.0,
        confirmation_epochs=2,
        current_price=float(price_path[-1]),
        price_path=price_path,
        directional_confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=1,
            last_evaluated_trading_epoch=fixture.trading_epoch - 1,
            last_signal_strength=0.02,
        ),
        strategy_registry=SuitabilityStrategyRegistryV1(
            entries=(
                SuitabilityStrategyEntryV1(
                    strategy_id="strat-momentum-v1",
                    supported_regime_ids=("trending",),
                    supported_sides=(
                        DirectionalAssessmentSide.LONG,
                        DirectionalAssessmentSide.SHORT,
                    ),
                    priority_rank=10,
                    disabled=False,
                    confidence_score=0.75,
                ),
            )
        ),
        regime_id="trending",
        regime_status=SuitabilityRegimeStatus.KNOWN,
        previous_composition_direction_state=CompositionDirectionState.NEUTRAL,
        position_management_context=overrides.get(
            "position_management_context",
            PositionManagementContext.FLAT,
        ),
        last_evaluated_trading_epoch=fixture.trading_epoch - 1,
        side_state=overrides.get("side_state", SideState.LONG_ARMED),
        direction_state=overrides.get("direction_state", EntryExitDirectionState.LONG_ARMED),
        position_state=overrides.get("position_state", PositionState.FLAT_RECONCILED),
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        safety_mode=SafetyMode.NORMAL,
        existing_position_side=overrides.get(
            "existing_position_side",
            ExistingPositionSide.NONE,
        ),
        venue_flat=overrides.get("venue_flat", True),
        cooldown_pass=True,
        scope_adverse_exit_signal=overrides.get(
            "scope_adverse_exit_signal",
            PolicySignalV0(triggered=False),
        ),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        safety_exit_signal=PolicySignalV0(triggered=False),
        policies=IntegratedOfflineReplayPoliciesV1(
            scope_initialization=CanonicalScopeInitializationPolicyV1(
                min_scope_band=50.0,
                max_scope_band=500.0,
                policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
            ),
            scope_event_generator=ScopeEventGeneratorPolicyV1(
                hard_max_scope_distance=1000.0,
                hard_max_adverse_distance=500.0,
                hard_max_reversal_distance=800.0,
                policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
            ),
            directional=DirectionalAssessmentPolicyV1(
                observe_signal_threshold=0.001,
                candidate_signal_threshold=0.005,
                confirmation_signal_threshold=0.01,
                confirmation_epochs=2,
                validity_epochs=3,
                policy_version=DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
            ),
            survival=SurvivalAssessmentPolicyV1(
                min_net_edge=0.001,
                min_volatility_survival_ratio=0.5,
                min_sequence_survival_ratio=0.5,
                min_drawdown_survival_ratio=0.5,
                min_liquidation_buffer_ratio=0.1,
                validity_epochs=3,
                policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
            ),
            suitability=SuitabilityRankingPolicyV1(
                validity_epochs=3,
                no_match_status=SuitabilityBindingStatus.FAIL,
                policy_version=SUITABILITY_RANKING_POLICY_VERSION,
            ),
            composition=DoublePlayCompositionPolicyV1(
                validity_epochs=3,
                both_candidate_outcome=BothCandidateOutcome.OBSERVE,
                both_invalid_outcome=BothInvalidOutcome.BLOCKED,
                policy_version=DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
            ),
            entry_exit=DoublePlayEntryExitPolicyV0(policy_version=ENTRY_EXIT_POLICY_VERSION),
        ),
        component_versions={
            "integrated_offline_trading_logic_replay": (
                INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION
            ),
        },
        policy_versions={
            "scope_initialization": SCOPE_INITIALIZATION_POLICY_VERSION,
            "scope_event_generator": SCOPE_EVENT_GENERATOR_POLICY_VERSION,
            "directional": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
            "survival": SURVIVAL_ASSESSMENT_POLICY_VERSION,
            "suitability": SUITABILITY_RANKING_POLICY_VERSION,
            "composition": DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
            "entry_exit": ENTRY_EXIT_POLICY_VERSION,
        },
        config_digest=_SURFACE_P_CONFIG_DIGEST,
        implementation_digest=_SURFACE_P_IMPL_DIGEST,
        input_digest=hashlib.sha256(f"surface-p-fixture-{fixture.fixture_id}".encode()).hexdigest(),
        expected_component_contracts={
            "integrated_offline_trading_logic_replay": (
                INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION
            ),
        },
        context_reference=fixture.context_reference,
        now_tick=0,
    )
    result = run_integrated_offline_trading_logic_replay_v1(replay_input)
    if not result.replay_pass:
        return None
    return result


def build_surface_p_fixture_scenario_envelope_v0(
    fixture: SurfacePBarSequenceFixtureV0,
) -> ParityDecisionEnvelopeV0 | None:
    if fixture.path_kind in SURFACE_P_BOUNDARY_PATH_KINDS:
        return _build_surface_p_boundary_path_envelope_v0(fixture)
    if fixture.path_kind == "reversal_preparation_exit_path":
        matrix = evaluate_reversal_preparation_matrix_v0(
            instrument_id=fixture.instrument_id,
            trading_epoch=fixture.trading_epoch,
            context_reference=fixture.context_reference,
        )
        decision = evaluate_scenario_entry_exit_for_fixture_v0(
            side_state=SideState.SHORT_ARMED,
            instrument_id=fixture.instrument_id,
            trading_epoch=fixture.trading_epoch,
            context_reference=fixture.context_reference,
            policy_context=ScenarioEntryExitPolicyContextV0(
                position_state=PositionState.OPEN_FULL,
                existing_position_side=ExistingPositionSide.LONG,
                venue_flat=False,
            ),
            matrix_result=matrix,
        )
        return extract_entry_exit_policy_parity_envelope_v0(
            decision,
            composition_status=matrix.composition_status.value,
        )
    if fixture.path_kind == "flat_before_opposite_side_path":
        matrix = evaluate_scenario_matrix_for_side_state_v0(
            side_state=SideState.SHORT_ACTIVE,
            instrument_id=fixture.instrument_id,
            trading_epoch=fixture.trading_epoch,
            context_reference=fixture.context_reference,
        )
        decision = evaluate_scenario_entry_exit_for_fixture_v0(
            side_state=SideState.SHORT_ARMED,
            instrument_id=fixture.instrument_id,
            trading_epoch=fixture.trading_epoch,
            context_reference=fixture.context_reference,
            policy_context=ScenarioEntryExitPolicyContextV0(
                position_state=PositionState.OPEN_FULL,
                existing_position_side=ExistingPositionSide.LONG,
                venue_flat=False,
            ),
            matrix_result=matrix,
        )
        return extract_entry_exit_policy_parity_envelope_v0(
            decision,
            composition_status=matrix.composition_status.value,
        )
    if fixture.path_kind in ("capital_risk_sizing_path", "canonical_order_intent_path"):
        replay = run_offline_double_play_scenario_replay_v0(
            OfflineDoublePlayScenarioReplayInputV0(
                selected_future_id=fixture.instrument_id,
                ticks=build_default_bull_bear_bull_scenario_ticks(),
                source_revision=f"surface-p-{fixture.fixture_id}",
            )
        )
        if not replay.replay_pass:
            return None
        tick = _surface_p_scenario_replay_tick_for_fixture_v0(fixture)
        if tick is None:
            return None
        if fixture.path_kind == "capital_risk_sizing_path":
            return extract_scenario_replay_tick_capital_risk_sizing_envelope_v0(tick)
        from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
            evaluate_scenario_canonical_order_intent_v0,
        )
        from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
            build_scenario_tick_decision_evidence_v0,
            evaluate_scenario_capital_risk_sizing_v0,
        )

        evidence = build_scenario_tick_decision_evidence_v0(
            decision_id=tick.entry_exit_policy_ref,
            replay_id=f"{fixture.context_reference}-replay",
            instrument_id=fixture.instrument_id,
            trading_epoch=fixture.trading_epoch,
            composition_result_id=tick.composition_result_id,
            entry_exit_policy_ref=tick.entry_exit_policy_ref,
            selected_side="long",
            decision_outcome=tick.entry_exit_decision_outcome,
            reason_codes=tick.entry_exit_reason_codes,
            decision_precedence_trace=tick.entry_exit_decision_precedence_trace,
            config_digest=_SURFACE_P_CONFIG_DIGEST,
            implementation_digest=_SURFACE_P_IMPL_DIGEST,
        )
        sizing_binding = evaluate_scenario_capital_risk_sizing_v0(evidence)
        intent_binding = evaluate_scenario_canonical_order_intent_v0(
            sizing_binding.evidence,
            sizing_decision=sizing_binding.sizing_decision,
        )
        return extract_canonical_order_intent_parity_envelope_v0(intent_binding)
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=fixture.scenario_side_state,
        instrument_id=fixture.instrument_id,
        trading_epoch=fixture.trading_epoch,
        context_reference=fixture.context_reference,
    )
    policy_context = default_scenario_entry_exit_policy_context_v0()
    if fixture.path_kind == "adverse_exit_path":
        policy_context = ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.LONG,
            venue_flat=False,
            scope_adverse_exit_signal=PolicySignalV0(
                triggered=True,
                reason_code="adverse_scope",
            ),
        )
    elif fixture.path_kind == "hold_position_management_path":
        policy_context = ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.LONG,
            venue_flat=False,
        )
    decision = evaluate_scenario_entry_exit_for_fixture_v0(
        side_state=fixture.scenario_side_state,
        instrument_id=fixture.instrument_id,
        trading_epoch=fixture.trading_epoch,
        context_reference=fixture.context_reference,
        policy_context=policy_context,
        matrix_result=matrix,
    )
    return extract_entry_exit_policy_parity_envelope_v0(
        decision,
        composition_status=matrix.composition_status.value,
    )


def _surface_p_scenario_replay_tick_for_fixture_v0(
    fixture: SurfacePBarSequenceFixtureV0,
) -> OfflineDoublePlayScenarioReplayTickRecordV0 | None:
    replay = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=fixture.instrument_id,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision=f"surface-p-{fixture.fixture_id}",
        )
    )
    if not replay.replay_pass:
        return None
    if fixture.path_kind == "capital_risk_sizing_path":
        for tick in replay.tick_records:
            if tick.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE:
                return tick
        return None
    if fixture.path_kind == "canonical_order_intent_path":
        for tick in replay.tick_records:
            if tick.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE:
                return tick
        return None
    if fixture.path_kind == "entry_path":
        for tick in replay.tick_records:
            if tick.entry_exit_decision_outcome == DecisionOutcome.ENTER_LONG.value:
                return tick
        return None
    if fixture.path_kind == "hold_position_management_path":
        for tick in replay.tick_records:
            if tick.entry_exit_decision_outcome == DecisionOutcome.HOLD.value:
                return tick
        return None
    if fixture.path_kind == "adverse_exit_path":
        for tick in replay.tick_records:
            if tick.entry_exit_decision_outcome in (
                DecisionOutcome.EXIT.value,
                DecisionOutcome.REDUCE.value,
            ):
                return tick
        return None
    if fixture.path_kind == "blocked_no_action_path":
        for tick in replay.tick_records:
            if tick.entry_exit_decision_outcome in (
                DecisionOutcome.OBSERVE.value,
                DecisionOutcome.BLOCKED.value,
                DecisionOutcome.NO_ACTION.value,
            ):
                return tick
        return None
    return replay.tick_records[0] if replay.tick_records else None


def _surface_p_boundary_base_evidence_v0(
    fixture: SurfacePBarSequenceFixtureV0,
) -> "CanonicalTradingDecisionEvidenceV1 | None":
    from trading.master_v2.canonical_trading_decision_evidence_v1 import (
        CanonicalTradingDecisionEvidenceV1,
    )
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        build_scenario_tick_decision_evidence_v0,
    )

    hold_fixture = SurfacePBarSequenceFixtureV0(
        f"{fixture.fixture_id}-hold-base",
        "hold_position_management_path",
        min(fixture.backtest_bar_index, 1),
        SideState.LONG_ACTIVE,
        fixture.instrument_id,
        fixture.trading_epoch,
        fixture.context_reference,
    )
    tick = _surface_p_scenario_replay_tick_for_fixture_v0(hold_fixture)
    if tick is None:
        return None
    return build_scenario_tick_decision_evidence_v0(
        decision_id=tick.entry_exit_policy_ref,
        replay_id=f"{fixture.context_reference}-replay",
        instrument_id=fixture.instrument_id,
        trading_epoch=fixture.trading_epoch,
        composition_result_id=tick.composition_result_id,
        entry_exit_policy_ref=tick.entry_exit_policy_ref,
        selected_side="long",
        decision_outcome=tick.entry_exit_decision_outcome,
        reason_codes=tick.entry_exit_reason_codes,
        decision_precedence_trace=tick.entry_exit_decision_precedence_trace,
        config_digest=_SURFACE_P_CONFIG_DIGEST,
        implementation_digest=_SURFACE_P_IMPL_DIGEST,
    )


def _backtest_bar_evidence_at_index_v0(
    bar_index: int,
) -> "CanonicalTradingDecisionEvidenceV1 | None":
    from src.backtest.mv2_research_wiring_v1 import (
        MV2_REQUIRED_INSTRUMENT_ID,
        run_mv2_research_backtest_wiring_v1,
    )

    result = run_mv2_research_backtest_wiring_v1(
        bars=_synthetic_mv2_research_bars_v0(bar_count=SURFACE_P_BAR_SEQUENCE_FIXTURE_COUNT),
        strategy_id="ma_crossover",
        cfg=_default_mv2_research_cfg_v0(),
        instrument_id=MV2_REQUIRED_INSTRUMENT_ID,
    )
    if bar_index < 0 or bar_index >= len(result.bar_outcomes):
        return None
    return result.bar_outcomes[bar_index].evidence


def _surface_p_promotion_gate_context_v0() -> PromotionGateBoundaryOfflineReplayContextV0:
    from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1
    from src.governance.promotion_loop import promotion_economic_gate_v1 as gate

    return PromotionGateBoundaryOfflineReplayContextV0(
        strategy_id="mv2_offline_research",
        strategy_version="v1",
        candidate_id="surface-p-boundary-promotion-blocked",
        economic_viability_evidence_ref="evidence://surface-p/boundary/promotion-blocked",
        economic_validity_status=gate.FAIL_STATUS,
        robustness_status=gate.FAIL_STATUS,
        data_admissibility_status=gate.PASS_STATUS,
        evidence_admissibility_status=gate.PASS_STATUS,
        policy_threshold_status=gate.PASS_STATUS,
        walk_forward_status=gate.FAIL_STATUS,
        out_of_sample_status=gate.FAIL_STATUS,
        monte_carlo_status=gate.FAIL_STATUS,
        stress_status=gate.FAIL_STATUS,
        parameter_sensitivity_status=gate.PASS_STATUS,
        reproducibility_status=gate.PASS_STATUS,
        digest_binding_status=gate.PASS_STATUS,
        manifest_binding_status=gate.PASS_STATUS,
        safety_policy_status=gate.PASS_STATUS,
        futures_only=True,
        bitcoin_direction_allowed=False,
        config_digest=_SURFACE_P_CONFIG_DIGEST,
        implementation_digest=_SURFACE_P_IMPL_DIGEST,
        policy_digest=canonical_economic_validity_policy_v1().policy_digest(),
        evidence_manifest_digest="e" * 64,
        economic_validity_proven=False,
        profitability_claim_allowed=False,
        promotion_basis_confidence_only=True,
        manifest_verify_only=True,
    )


def _apply_surface_p_boundary_binding_v0(
    fixture: SurfacePBarSequenceFixtureV0,
    evidence: "CanonicalTradingDecisionEvidenceV1",
) -> ParityDecisionEnvelopeV0 | None:
    path_kind = fixture.path_kind
    if path_kind == "safety_kernel_boundary_path":
        from trading.master_v2.double_play_entry_exit_policy_v0 import (
            ReconciliationState,
            SafetyMode,
            TradingGate,
        )

        binding = bind_safety_kernel_offline_replay_evidence_v0(
            evidence,
            context=SafetyKernelOfflineReplayContextV0(
                safety_exit_signal=PolicySignalV0(
                    triggered=True,
                    reason_code="hard_risk_exit",
                ),
                safety_mode=SafetyMode.EXIT_ONLY,
                position_state=PositionState.OPEN_FULL,
                trading_gate=TradingGate.EXIT_ONLY,
                reconciliation_state=ReconciliationState.RECONCILED,
            ),
        )
        if not safety_kernel_binding_non_authority_boundary_ok_v0(binding):
            return None
        envelope = extract_safety_kernel_parity_envelope_v0(
            binding,
            decision_outcome=DecisionOutcome.REDUCE.value,
        )
        assert_safety_kernel_non_authority_boundary_v0(envelope)
        return envelope
    if path_kind == "killswitch_boundary_path":
        from trading.master_v2.double_play_entry_exit_policy_v0 import (
            ReconciliationState,
            SafetyMode,
            TradingGate,
        )

        binding = bind_killswitch_boundary_offline_replay_evidence_v0(
            evidence,
            context=KillSwitchBoundaryOfflineReplayContextV0(
                boundary_mode=KillSwitchBoundaryMode.BLOCK_NEW,
                killswitch_active=True,
                side_state=SideState.KILL_ALL,
                safety_mode=SafetyMode.BLOCKED,
                trading_gate=TradingGate.BLOCKED,
                reconciliation_state=ReconciliationState.RECONCILED,
            ),
        )
        if not killswitch_boundary_binding_non_authority_boundary_ok_v0(binding):
            return None
        envelope = extract_killswitch_boundary_parity_envelope_v0(
            binding,
            decision_outcome=DecisionOutcome.BLOCKED.value,
        )
        assert_killswitch_boundary_non_authority_boundary_v0(envelope)
        return envelope
    if path_kind == "reconciliation_unknown_outcome_boundary_path":
        from trading.master_v2.double_play_entry_exit_policy_v0 import (
            ReconciliationState,
        )

        binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
            evidence,
            context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
                position_state=PositionState.OPEN_FULL,
                reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED,
                venue_flat=False,
                existing_position_side=ExistingPositionSide.LONG,
                order_snapshot_unresolved=True,
            ),
        )
        if not reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0(binding):
            return None
        envelope = extract_reconciliation_unknown_outcome_parity_envelope_v0(
            binding,
            decision_outcome=DecisionOutcome.OBSERVE.value,
        )
        assert_reconciliation_unknown_outcome_non_authority_boundary_v0(envelope)
        return envelope
    if path_kind == "promotion_gate_boundary_path":
        binding = bind_promotion_gate_boundary_offline_replay_evidence_v0(
            evidence,
            context=_surface_p_promotion_gate_context_v0(),
        )
        if not promotion_gate_boundary_binding_non_authority_boundary_ok_v0(binding):
            return None
        envelope = extract_promotion_gate_boundary_parity_envelope_v0(
            binding,
            decision_outcome=DecisionOutcome.OBSERVE.value,
        )
        assert not envelope.execution_eligible
        assert envelope.authority_effect == "NONE"
        return envelope
    if path_kind == "ai_observability_boundary_path":
        binding = bind_ai_observability_boundary_offline_replay_evidence_v0(evidence)
        if not ai_observability_boundary_binding_non_authority_boundary_ok_v0(binding):
            return None
        envelope = extract_ai_observability_boundary_parity_envelope_v0(
            binding,
            decision_outcome=evidence.decision_outcome,
        )
        assert envelope.authority_effect == "NONE"
        assert envelope.runtime_effect == "NONE"
        return envelope
    return None


def _build_surface_p_boundary_path_envelope_v0(
    fixture: SurfacePBarSequenceFixtureV0,
) -> ParityDecisionEnvelopeV0 | None:
    evidence = _surface_p_boundary_base_evidence_v0(fixture)
    if evidence is None:
        return None
    return _apply_surface_p_boundary_binding_v0(fixture, evidence)


def _build_surface_p_boundary_backtest_envelope_v0(
    fixture: SurfacePBarSequenceFixtureV0,
) -> ParityDecisionEnvelopeV0 | None:
    evidence = _backtest_bar_evidence_at_index_v0(fixture.backtest_bar_index)
    if evidence is None:
        return None
    return _apply_surface_p_boundary_binding_v0(fixture, evidence)


def _surface_p_boundary_effects_aligned_v0(
    left: ParityDecisionEnvelopeV0,
    right: ParityDecisionEnvelopeV0,
    *,
    path_kind: SurfacePBarSequencePathKind,
) -> bool:
    if path_kind == "safety_kernel_boundary_path":
        return (
            left.safety_boundary_effect
            == right.safety_boundary_effect
            == (SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE)
        )
    if path_kind == "killswitch_boundary_path":
        return (
            left.killswitch_boundary_effect
            == right.killswitch_boundary_effect
            == (KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE)
        )
    if path_kind == "reconciliation_unknown_outcome_boundary_path":
        return (
            left.reconciliation_unknown_outcome_effect
            == right.reconciliation_unknown_outcome_effect
            == RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
        )
    if path_kind == "promotion_gate_boundary_path":
        return (
            left.promotion_gate_boundary_effect
            == right.promotion_gate_boundary_effect
            == (PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE)
        )
    if path_kind == "ai_observability_boundary_path":
        return (
            left.ai_observability_boundary_effect
            == right.ai_observability_boundary_effect
            == AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE
        )
    return False


def surface_p_fixture_lane_semantics_ok_v0(
    fixture: SurfacePBarSequenceFixtureV0,
    envelope: ParityDecisionEnvelopeV0 | None,
    *,
    lane: Literal["integrated", "scenario", "backtest", "runtime_reference"],
) -> bool:
    if envelope is None:
        return False
    if lane == "runtime_reference":
        return (
            envelope.transition_reason_code == RUNTIME_REFERENCE_INTEGRATION_STATUS_V0
            and envelope.authority_effect == "NONE"
            and not envelope.execution_eligible
        )
    if lane == "backtest":
        return (
            envelope.authority_effect == "NONE"
            and envelope.runtime_effect == "NONE"
            and not envelope.execution_eligible
        )
    path_kind = fixture.path_kind
    if path_kind == "entry_path":
        if lane == "scenario":
            return envelope.decision_outcome in (
                DecisionOutcome.ENTER_LONG.value,
                DecisionOutcome.ENTER_SHORT.value,
            )
        return bool(envelope.entry_or_exit_policy_ref) and envelope.authority_effect == "NONE"
    if path_kind == "hold_position_management_path":
        if lane == "scenario":
            return envelope.decision_outcome == DecisionOutcome.HOLD.value
        return bool(envelope.entry_or_exit_policy_ref) and envelope.authority_effect == "NONE"
    if path_kind == "adverse_exit_path":
        return envelope.decision_outcome in (
            DecisionOutcome.EXIT.value,
            DecisionOutcome.REDUCE.value,
        )
    if path_kind == "reversal_preparation_exit_path":
        return envelope.decision_outcome != DecisionOutcome.ENTER_SHORT.value
    if path_kind == "flat_before_opposite_side_path":
        return envelope.decision_outcome != DecisionOutcome.ENTER_SHORT.value
    if path_kind == "capital_risk_sizing_path":
        return envelope.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE
    if path_kind == "canonical_order_intent_path":
        return envelope.order_intent_effect == ORDER_INTENT_EFFECT_BOUND_OFFLINE
    if path_kind == "blocked_no_action_path":
        return envelope.decision_outcome in (
            DecisionOutcome.OBSERVE.value,
            DecisionOutcome.BLOCKED.value,
            DecisionOutcome.NO_ACTION.value,
        ) and envelope.decision_outcome not in (
            DecisionOutcome.ENTER_LONG.value,
            DecisionOutcome.ENTER_SHORT.value,
        )
    if path_kind == "safety_kernel_boundary_path":
        return (
            envelope.safety_boundary_effect == SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE
            and envelope.authority_effect == "NONE"
            and not envelope.execution_eligible
            and envelope.decision_outcome
            in (
                DecisionOutcome.REDUCE.value,
                DecisionOutcome.EXIT.value,
                DecisionOutcome.BLOCKED.value,
            )
        )
    if path_kind == "killswitch_boundary_path":
        return (
            envelope.killswitch_boundary_effect == KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE
            and envelope.authority_effect == "NONE"
            and not envelope.execution_eligible
            and envelope.decision_outcome
            in (
                DecisionOutcome.BLOCKED.value,
                DecisionOutcome.REDUCE.value,
                DecisionOutcome.EXIT.value,
                DecisionOutcome.CANCEL_PENDING.value,
            )
        )
    if path_kind == "reconciliation_unknown_outcome_boundary_path":
        return (
            envelope.reconciliation_unknown_outcome_effect
            == RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
            and envelope.authority_effect == "NONE"
            and not envelope.execution_eligible
        )
    if path_kind == "promotion_gate_boundary_path":
        return (
            envelope.promotion_gate_boundary_effect == PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE
            and envelope.authority_effect == "NONE"
            and not envelope.execution_eligible
            and not envelope.adapter_compatible
        )
    if path_kind == "ai_observability_boundary_path":
        return (
            envelope.ai_observability_boundary_effect
            == AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE
            and envelope.authority_effect == "NONE"
            and envelope.runtime_effect == "NONE"
            and not envelope.execution_eligible
            and bool(envelope.reason_codes)
            and bool(envelope.decision_precedence_trace)
        )
    return False


def _build_surface_p_adapter_integrated_envelope_v0(
    fixture: SurfacePBarSequenceFixtureV0,
) -> ParityDecisionEnvelopeV0 | None:
    from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
        evaluate_scenario_canonical_order_intent_v0,
    )
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        bind_capital_risk_sizing_offline_replay_evidence_v0,
        build_scenario_tick_decision_evidence_v0,
        evaluate_scenario_capital_risk_sizing_v0,
    )

    tick = _surface_p_scenario_replay_tick_for_fixture_v0(fixture)
    if tick is None:
        return None
    evidence = build_scenario_tick_decision_evidence_v0(
        decision_id=tick.entry_exit_policy_ref,
        replay_id=f"{fixture.context_reference}-replay",
        instrument_id=fixture.instrument_id,
        trading_epoch=fixture.trading_epoch,
        composition_result_id=tick.composition_result_id,
        entry_exit_policy_ref=tick.entry_exit_policy_ref,
        selected_side=tick.side_state.value.replace("_active", "").replace("_armed", ""),
        decision_outcome=tick.entry_exit_decision_outcome,
        reason_codes=tick.entry_exit_reason_codes,
        decision_precedence_trace=tick.entry_exit_decision_precedence_trace,
        config_digest=_SURFACE_P_CONFIG_DIGEST,
        implementation_digest=_SURFACE_P_IMPL_DIGEST,
    )
    if fixture.path_kind == "capital_risk_sizing_path":
        binding = bind_capital_risk_sizing_offline_replay_evidence_v0(evidence)
        return extract_capital_risk_sizing_parity_envelope_v0(binding)
    if fixture.path_kind == "canonical_order_intent_path":
        sizing_binding = evaluate_scenario_capital_risk_sizing_v0(evidence)
        intent_binding = evaluate_scenario_canonical_order_intent_v0(
            sizing_binding.evidence,
            sizing_decision=sizing_binding.sizing_decision,
        )
        return extract_canonical_order_intent_parity_envelope_v0(intent_binding)
    return None


def build_surface_p_fixture_integrated_envelope_v0(
    fixture: SurfacePBarSequenceFixtureV0,
) -> ParityDecisionEnvelopeV0 | None:
    if fixture.path_kind in SURFACE_P_BOUNDARY_PATH_KINDS:
        return _build_surface_p_boundary_path_envelope_v0(fixture)
    if fixture.path_kind in ("capital_risk_sizing_path", "canonical_order_intent_path"):
        envelope = _build_surface_p_adapter_integrated_envelope_v0(fixture)
        if envelope is None:
            return None
        if fixture.path_kind == "capital_risk_sizing_path":
            assert_capital_risk_sizing_non_authority_boundary_v0(envelope)
        else:
            assert_canonical_order_intent_non_authority_boundary_v0(envelope)
        return envelope
    result = build_surface_p_integrated_replay_result_v0(fixture)
    if result is None:
        return None
    envelope = extract_integrated_parity_envelope_v0(result)
    assert_non_authority_boundary_v0(envelope)
    return envelope


def evaluate_surface_p_bar_sequence_fixture_four_way_parity_v0(
    fixture: SurfacePBarSequenceFixtureV0,
) -> SurfacePBarSequenceFixtureAssessmentV0:
    fail_reasons: list[str] = []

    integrated_env = build_surface_p_fixture_integrated_envelope_v0(fixture)
    integrated_lane_bound = integrated_env is not None
    if not integrated_lane_bound:
        fail_reasons.append("integrated_lane_unbound")

    scenario_env = build_surface_p_fixture_scenario_envelope_v0(fixture)
    scenario_lane_bound = scenario_env is not None
    if not scenario_lane_bound:
        fail_reasons.append("scenario_lane_unbound")

    integrated_scenario_aligned = False
    if integrated_env is not None and scenario_env is not None:
        integrated_sem = surface_p_fixture_lane_semantics_ok_v0(
            fixture,
            integrated_env,
            lane="integrated",
        )
        scenario_sem = surface_p_fixture_lane_semantics_ok_v0(
            fixture,
            scenario_env,
            lane="scenario",
        )
        if fixture.path_kind in ("capital_risk_sizing_path", "canonical_order_intent_path"):
            integrated_scenario_aligned = (
                integrated_sem
                and scenario_sem
                and integrated_env.risk_sizing_effect == scenario_env.risk_sizing_effect
                and integrated_env.order_intent_effect == scenario_env.order_intent_effect
            )
        elif fixture.path_kind in SURFACE_P_BOUNDARY_PATH_KINDS:
            integrated_scenario_aligned = (
                integrated_sem
                and scenario_sem
                and _surface_p_boundary_effects_aligned_v0(
                    integrated_env,
                    scenario_env,
                    path_kind=fixture.path_kind,
                )
            )
        else:
            integrated_scenario_aligned = integrated_sem and scenario_sem
    if integrated_lane_bound and scenario_lane_bound and not integrated_scenario_aligned:
        fail_reasons.append("integrated_scenario_evidence_not_aligned")

    if fixture.path_kind in SURFACE_P_BOUNDARY_PATH_KINDS:
        backtest_env = _build_surface_p_boundary_backtest_envelope_v0(fixture)
    else:
        backtest_env = bind_backtest_bar_parity_lane_at_index_v0(fixture.backtest_bar_index)
    backtest_lane_bound = backtest_env is not None
    backtest_non_authority = False
    if backtest_lane_bound and backtest_env is not None:
        backtest_non_authority = surface_p_fixture_lane_semantics_ok_v0(
            fixture,
            backtest_env,
            lane="backtest",
        )
    if not backtest_lane_bound:
        fail_reasons.append("backtest_lane_unbound")
    elif not backtest_non_authority:
        fail_reasons.append("backtest_lane_semantics_invalid")

    runtime_env = extract_runtime_reference_parity_envelope_v0()
    runtime_reference_lane_bound = True
    runtime_reference_non_authority = True
    try:
        assert_runtime_reference_lane_v0(runtime_env)
    except AssertionError:
        runtime_reference_lane_bound = False
        runtime_reference_non_authority = False
        fail_reasons.append("runtime_reference_lane_invalid")

    four_way_bound = (
        integrated_lane_bound
        and scenario_lane_bound
        and backtest_lane_bound
        and runtime_reference_lane_bound
        and integrated_scenario_aligned
        and backtest_non_authority
        and runtime_reference_non_authority
    )
    return SurfacePBarSequenceFixtureAssessmentV0(
        fixture_id=fixture.fixture_id,
        path_kind=fixture.path_kind,
        integrated_lane_bound=integrated_lane_bound,
        scenario_lane_bound=scenario_lane_bound,
        backtest_lane_bound=backtest_lane_bound,
        runtime_reference_lane_bound=runtime_reference_lane_bound,
        integrated_scenario_evidence_aligned=integrated_scenario_aligned,
        backtest_non_authority_confirmed=backtest_non_authority,
        runtime_reference_non_authority_confirmed=runtime_reference_non_authority,
        four_way_fixture_parity_bound=four_way_bound,
        fail_closed_reasons=tuple(fail_reasons),
    )


def evaluate_surface_p_full_bar_sequence_four_way_parity_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 44,
    context_reference: str = "surface-p-bar-sequence-4way-parity-v0",
) -> SurfacePFullBarSequenceParityAssessmentV0:
    assessments = tuple(
        evaluate_surface_p_bar_sequence_fixture_four_way_parity_v0(fixture)
        for fixture in surface_p_bar_sequence_fixtures_v0(
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
            context_reference=context_reference,
        )
    )
    core_assessments = assessments[:SURFACE_P_CORE_BAR_SEQUENCE_FIXTURE_COUNT]
    boundary_assessments = assessments[SURFACE_P_CORE_BAR_SEQUENCE_FIXTURE_COUNT:]
    fail_reasons: list[str] = []
    fixtures_complete = all(item.four_way_fixture_parity_bound for item in assessments)
    core_fixtures_complete = all(item.four_way_fixture_parity_bound for item in core_assessments)
    boundary_path_fixtures_complete = all(
        item.four_way_fixture_parity_bound for item in boundary_assessments
    )
    if not fixtures_complete:
        for item in assessments:
            if not item.four_way_fixture_parity_bound:
                fail_reasons.append(
                    f"{item.fixture_id}:{'|'.join(item.fail_closed_reasons) or 'unbound'}"
                )
    return SurfacePFullBarSequenceParityAssessmentV0(
        fixture_assessments=assessments,
        fixtures_complete=fixtures_complete,
        runtime_bridge_status=RUNTIME_REFERENCE_INTEGRATION_STATUS_V0,
        core_fixtures_complete=core_fixtures_complete,
        boundary_path_fixtures_complete=boundary_path_fixtures_complete,
        boundary_fixtures_added=tuple(item.fixture_id for item in boundary_assessments),
        fail_closed_reasons=tuple(fail_reasons),
    )


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
