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
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE,
    KILLSWITCH_BOUNDARY_EFFECT_NONE,
    KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    KillSwitchBoundaryOfflineReplayBindingResultV0,
    killswitch_boundary_binding_non_authority_boundary_ok_v0,
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
from trading.master_v2.double_play_entry_exit_policy_v0 import EntryExitPolicyDecisionV0
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
    reversal_preparation_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.flat_before_opposite_side_scenario_binding_adapter_v0 import (
    FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
    DOUBLE_PLAY_ENTRY_EXIT_SCENARIO_BINDING_ADAPTER_OWNER,
    ScenarioEntryExitPolicyContextV0,
    evaluate_scenario_entry_exit_policy_v0,
)
from trading.master_v2.double_play_state import (
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

FOUR_WAY_PARITY_REWIRE_SLICE_ID = "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0"
RUNTIME_REFERENCE_INTEGRATION_STATUS_V0 = "BOUND_NOT_ACTIVATED"
BACKTEST_PARITY_WIRING_OWNER = "backtest.mv2_research_wiring_v1"
RUNTIME_BRIDGE_REFERENCE_OWNER = "trading.master_v2.canonical_core_runtime_integration_bridge_v0"

ALLOWED_SLICE_CHANGED_PATH_PREFIXES: Tuple[str, ...] = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "scripts/ops/run_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "scripts/ops/run_integrated_vs_scenario_replay_full_system_4_way_parity_rewire_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
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
    state_switch_ref: str = ""
    state_switch_effect: str = STATE_SWITCH_EFFECT_NONE
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


def _synthetic_mv2_research_bars_v0(*, bar_count: int = 12) -> "pd.DataFrame":
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
