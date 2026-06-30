# src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py
"""
Integrated Offline Trading Logic Replay v1: pure orchestrator for STEP 29B–29H chain.

Orchestrates canonical component owners without duplicating component logic.
No I/O, runtime, orders, adapter, quantity, or authority effects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from typing import Mapping, Optional, Tuple

from trading.master_v2.canonical_market_context_v1 import (
    CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
    CanonicalMarketContextBindingOutcome,
    CanonicalMarketContextBindingStateV1,
    CanonicalMarketContextV1,
    bind_canonical_market_context_event,
    with_computed_input_digest,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
    CanonicalScopeInitializationPolicyV1,
    CanonicalScopeInitializationResultV1,
    CanonicalScopeSnapshotV1,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    initialize_canonical_scope,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
    CanonicalTradingDecisionEvidenceV1,
    derive_decision_id,
    with_computed_evidence_semantic_digest,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
    CanonicalScopeEventType,
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventEvidenceV1,
    ScopeEventGeneratorInputV1,
    ScopeEventGeneratorPolicyV1,
    generate_deterministic_scope_event,
    with_computed_scope_event_digest,
)
from trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_LAYER_VERSION,
    DirectionalAssessmentInputV1,
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentSide,
    DirectionalAssessmentV1,
    DirectionalConfirmationStateV1,
    ScopeEventRefV1,
    evaluate_directional_assessment_v1,
    mirror_price_path_for_short,
    with_computed_directional_assessment_digest,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    DOUBLE_PLAY_COMPOSITION_MATRIX_LAYER_VERSION,
    CompositionDirectionState,
    CompositionSelectedSide,
    DoublePlayCompositionInputV1,
    DoublePlayCompositionPolicyV1,
    DoublePlayCompositionResultV1,
    PositionManagementContext,
    compute_composition_input_digest,
    evaluate_double_play_composition_matrix_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    ENTRY_EXIT_POLICY_LAYER_VERSION,
    DecisionOutcome,
    DoublePlayEntryExitPolicyInputV0,
    DoublePlayEntryExitPolicyV0,
    EntryExitDirectionState,
    EntryExitPolicyDecisionV0,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
    compute_entry_exit_policy_input_digest,
    evaluate_double_play_entry_exit_policy_v0,
)
from trading.master_v2.double_play_state import (
    DOUBLE_PLAY_STATE_LAYER_VERSION,
    ActiveSide,
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    TransitionDecision,
    transition_state,
)
from trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_BINDING_LAYER_VERSION,
    SuitabilityBindingInputV1,
    SuitabilityRankingPolicyV1,
    SuitabilityRegimeStatus,
    SuitabilityResultV1,
    SuitabilityStrategyRegistryV1,
    evaluate_suitability_binding_v1,
)
from trading.master_v2.survival_assessment_v1 import (
    SURVIVAL_ASSESSMENT_LAYER_VERSION,
    SurvivalAssessmentInputV1,
    SurvivalAssessmentPolicyV1,
    SurvivalCostInputsV1,
    SurvivalMetricInputsV1,
    SurvivalResultV1,
    evaluate_survival_assessment_v1,
)

INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION = "v1"
INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1"
)

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})

_DEFAULT_STATIC_LIMITS = StaticHardLimits(
    max_notional=1.0,
    max_leverage=1.0,
    max_switches_per_window=100,
    min_band_width=1.0,
    max_band_width=100.0,
)
_DEFAULT_RUNTIME_ENVELOPE = RuntimeEnvelope(static=_DEFAULT_STATIC_LIMITS, live_authorization=False)
_DEFAULT_SCOPE_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.02,
)
_EMPTY_SCOPE_STATE = RuntimeScopeState(
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


@dataclass(frozen=True)
class IntegratedOfflineReplayPoliciesV1:
    scope_initialization: CanonicalScopeInitializationPolicyV1
    scope_event_generator: ScopeEventGeneratorPolicyV1
    directional: DirectionalAssessmentPolicyV1
    survival: SurvivalAssessmentPolicyV1
    suitability: SuitabilityRankingPolicyV1
    composition: DoublePlayCompositionPolicyV1
    entry_exit: DoublePlayEntryExitPolicyV0


@dataclass(frozen=True)
class IntegratedOfflineReplayInputV1:
    replay_id: str
    instrument_id: str
    trading_epoch: int
    canonical_market_context: CanonicalMarketContextV1
    market_context_binding_state: CanonicalMarketContextBindingStateV1
    scope_prerequisites: ScopeInitializationPrerequisitesV1
    scope_reinitialization_guard: ScopeReinitializationGuardV1
    existing_scope: Optional[CanonicalScopeSnapshotV1]
    scope_direction_state: ScopeDirectionState
    scope_confirmation_state: ScopeConfirmationStateV1
    scope_cooldown_state: ScopeCooldownStateV1
    up_distance: float
    adverse_exit_distance: float
    reversal_distance: float
    confirmation_epochs: int
    current_price: float
    price_path: Tuple[float, ...]
    directional_confirmation_state: DirectionalConfirmationStateV1
    strategy_registry: SuitabilityStrategyRegistryV1
    regime_id: str
    regime_status: SuitabilityRegimeStatus
    previous_composition_direction_state: CompositionDirectionState
    position_management_context: PositionManagementContext
    last_evaluated_trading_epoch: int
    side_state: SideState
    direction_state: EntryExitDirectionState
    position_state: PositionState
    reconciliation_state: ReconciliationState
    trading_gate: TradingGate
    safety_mode: SafetyMode
    existing_position_side: ExistingPositionSide
    venue_flat: bool
    cooldown_pass: bool
    scope_adverse_exit_signal: PolicySignalV0
    profit_protection_signal: PolicySignalV0
    time_exit_signal: PolicySignalV0
    strategy_invalidation_signal: PolicySignalV0
    hard_risk_reduction_signal: PolicySignalV0
    safety_exit_signal: PolicySignalV0
    policies: IntegratedOfflineReplayPoliciesV1
    component_versions: Mapping[str, str]
    policy_versions: Mapping[str, str]
    config_digest: str
    implementation_digest: str
    input_digest: str
    expected_component_contracts: Mapping[str, str]
    context_reference: str
    now_tick: int = 0


@dataclass(frozen=True)
class StateSwitchEvidenceV1:
    state_switch_id: str
    instrument_id: str
    trading_epoch: int
    previous_side_state: str
    next_side_state: str
    scope_event_type: str
    transition_allowed: bool
    transition_reason_code: str
    semantic_digest: str


@dataclass(frozen=True)
class IntegratedOfflineReplayIntermediateV1:
    market_context: CanonicalMarketContextV1
    scope_initialization: CanonicalScopeInitializationResultV1
    scope_event: ScopeEventEvidenceV1
    bull_assessment: DirectionalAssessmentV1
    bear_assessment: DirectionalAssessmentV1
    bull_survival: SurvivalResultV1
    bear_survival: SurvivalResultV1
    bull_suitability: SuitabilityResultV1
    bear_suitability: SuitabilityResultV1
    composition_result: DoublePlayCompositionResultV1
    entry_exit_decision: EntryExitPolicyDecisionV0
    state_switch: StateSwitchEvidenceV1
    current_scope: CanonicalScopeSnapshotV1
    next_scope_ref: str


@dataclass(frozen=True)
class IntegratedOfflineReplayResultV1:
    replay_pass: bool
    fail_reasons: Tuple[str, ...]
    evidence: CanonicalTradingDecisionEvidenceV1
    intermediate: Optional[IntegratedOfflineReplayIntermediateV1] = None


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _instrument_allowed(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return not any(token in lowered for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def _canonical_scope_event_to_scope_event(event_type: CanonicalScopeEventType) -> ScopeEvent:
    mapping = {
        CanonicalScopeEventType.NOOP: ScopeEvent.NOOP,
        CanonicalScopeEventType.UPSCOPE_CANDIDATE: ScopeEvent.UPSCOPE_CANDIDATE,
        CanonicalScopeEventType.UPSCOPE_CONFIRMED: ScopeEvent.UPSCOPE_CONFIRMED,
        CanonicalScopeEventType.DOWNSCOPE_CANDIDATE: ScopeEvent.DOWNSCOPE_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED: ScopeEvent.DOWNSCOPE_CONFIRMED,
        CanonicalScopeEventType.CHOP_DETECTED: ScopeEvent.CHOP_DETECTED,
    }
    if event_type in mapping:
        return mapping[event_type]
    return ScopeEvent.SCOPE_UNKNOWN


def _side_state_to_entry_exit_direction(side: SideState) -> EntryExitDirectionState:
    table = {
        SideState.NEUTRAL_OBSERVE: EntryExitDirectionState.NEUTRAL,
        SideState.LONG_ARMED: EntryExitDirectionState.LONG_ARMED,
        SideState.LONG_ACTIVE: EntryExitDirectionState.LONG_ACTIVE,
        SideState.LONG_BLOCKED: EntryExitDirectionState.NEUTRAL,
        SideState.SHORT_ARMED: EntryExitDirectionState.SHORT_ARMED,
        SideState.SHORT_ACTIVE: EntryExitDirectionState.SHORT_ACTIVE,
        SideState.SHORT_BLOCKED: EntryExitDirectionState.NEUTRAL,
        SideState.SWITCH_LONG_TO_SHORT_PENDING: EntryExitDirectionState.SHORT_ARMED,
        SideState.SWITCH_SHORT_TO_LONG_PENDING: EntryExitDirectionState.LONG_ARMED,
        SideState.CHOP_GUARD_BLOCK: EntryExitDirectionState.NEUTRAL,
        SideState.KILL_ALL: EntryExitDirectionState.NEUTRAL,
    }
    return table.get(side, EntryExitDirectionState.NEUTRAL)


def _scope_event_ref_from_evidence(evidence: ScopeEventEvidenceV1) -> ScopeEventRefV1:
    return ScopeEventRefV1(
        scope_event_id=evidence.scope_event_id,
        semantic_digest=evidence.semantic_digest,
        event_type=evidence.event_type.value,
        trading_epoch=evidence.trading_epoch,
    )


def _compute_state_switch_digest(
    *,
    state_switch_id: str,
    instrument_id: str,
    trading_epoch: int,
    previous_side_state: str,
    next_side_state: str,
    scope_event_type: str,
    transition_allowed: bool,
    transition_reason_code: str,
) -> str:
    payload = {
        "instrument_id": instrument_id,
        "next_side_state": next_side_state,
        "previous_side_state": previous_side_state,
        "scope_event_type": scope_event_type,
        "state_switch_id": state_switch_id,
        "trading_epoch": trading_epoch,
        "transition_allowed": transition_allowed,
        "transition_reason_code": transition_reason_code,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _derive_state_switch_id(instrument_id: str, trading_epoch: int, scope_event_id: str) -> str:
    material = f"{instrument_id}|{trading_epoch}|{scope_event_id}"
    return f"state-switch-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _default_component_versions() -> dict[str, str]:
    return {
        "canonical_market_context": CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
        "canonical_scope_initialization": CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
        "deterministic_scope_event_generator": DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
        "directional_assessment": DIRECTIONAL_ASSESSMENT_LAYER_VERSION,
        "survival_assessment": SURVIVAL_ASSESSMENT_LAYER_VERSION,
        "suitability_binding": SUITABILITY_BINDING_LAYER_VERSION,
        "double_play_composition_matrix": DOUBLE_PLAY_COMPOSITION_MATRIX_LAYER_VERSION,
        "double_play_entry_exit_policy": ENTRY_EXIT_POLICY_LAYER_VERSION,
        "double_play_state": DOUBLE_PLAY_STATE_LAYER_VERSION,
        "integrated_offline_trading_logic_replay": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        "canonical_trading_decision_evidence": CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
    }


def _validate_contract_versions(inp: IntegratedOfflineReplayInputV1) -> Tuple[str, ...]:
    errors: list[str] = []
    expected = dict(inp.expected_component_contracts) if inp.expected_component_contracts else {}
    actual = (
        dict(inp.component_versions) if inp.component_versions else _default_component_versions()
    )
    for key, expected_version in sorted(expected.items()):
        actual_version = actual.get(key)
        if actual_version != expected_version:
            errors.append(f"component_version_mismatch:{key}:{actual_version}!={expected_version}")
    for key, expected_version in sorted(inp.policy_versions.items()):
        policy_attr = {
            "scope_initialization": inp.policies.scope_initialization.policy_version,
            "scope_event_generator": inp.policies.scope_event_generator.policy_version,
            "directional": inp.policies.directional.policy_version,
            "survival": inp.policies.survival.policy_version,
            "suitability": inp.policies.suitability.policy_version,
            "composition": inp.policies.composition.policy_version,
            "entry_exit": inp.policies.entry_exit.policy_version,
        }.get(key)
        if policy_attr is not None and policy_attr != expected_version:
            errors.append(f"policy_version_mismatch:{key}:{policy_attr}!={expected_version}")
    return tuple(errors)


def _blocked_evidence(
    inp: IntegratedOfflineReplayInputV1,
    *,
    fail_reasons: Tuple[str, ...],
    decision_outcome: str = "blocked",
) -> CanonicalTradingDecisionEvidenceV1:
    input_digest = (
        inp.input_digest
        if _valid_sha256_hex(inp.input_digest)
        else hashlib.sha256(
            json.dumps(
                {"replay_id": inp.replay_id, "trading_epoch": inp.trading_epoch},
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
    )
    decision_id = derive_decision_id(
        replay_id=inp.replay_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        input_digest=input_digest,
    )
    evidence = CanonicalTradingDecisionEvidenceV1(
        decision_id=decision_id,
        replay_id=inp.replay_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        market_context_ref="",
        scope_initialization_ref="",
        scope_event_ref="",
        bull_assessment_ref="",
        bear_assessment_ref="",
        state_switch_ref="",
        bull_survival_ref="",
        bear_survival_ref="",
        bull_suitability_ref="",
        bear_suitability_ref="",
        composition_result_ref="",
        entry_exit_policy_ref="",
        current_scope_ref="",
        next_scope_ref="",
        previous_direction_state=inp.direction_state.value,
        next_direction_state=inp.direction_state.value,
        selected_side=CompositionSelectedSide.NONE.value,
        selected_strategy_ref="",
        decision_outcome=decision_outcome,
        entry_or_exit_policy_ref="",
        reason_codes=tuple(sorted(fail_reasons)),
        decision_precedence_trace=(),
        component_versions=dict(inp.component_versions)
        if inp.component_versions
        else _default_component_versions(),
        policy_versions=dict(inp.policy_versions),
        config_digest=inp.config_digest,
        implementation_digest=inp.implementation_digest,
        input_digest=input_digest,
        semantic_digest="",
    )
    return with_computed_evidence_semantic_digest(evidence)


def _directional_input_for_side(
    inp: IntegratedOfflineReplayInputV1,
    side: DirectionalAssessmentSide,
    scope_event_ref: ScopeEventRefV1,
) -> DirectionalAssessmentInputV1:
    anchor = float(inp.canonical_market_context.mark_price)
    long_path = inp.price_path
    price_path = (
        long_path
        if side is DirectionalAssessmentSide.LONG
        else mirror_price_path_for_short(long_path, anchor)
    )
    return DirectionalAssessmentInputV1(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        side=side,
        price_path=price_path,
        reference_price=anchor,
        feature_refs=("feat-momentum-v1",),
        scope_event_ref=scope_event_ref,
        survival_preconditions=("survival_precondition_ref_only",),
        confirmation_state=inp.directional_confirmation_state,
        data_integrity_status=inp.canonical_market_context.data_integrity_status,
        clock_trust_status=inp.canonical_market_context.clock_trust_status,
        bar_finality_status=inp.canonical_market_context.bar_finality_status,
        trusted_data=inp.canonical_market_context.data_integrity_status.value == "trusted",
        input_complete=True,
        explicit_hard_block_reasons=(),
        policy_version=inp.policies.directional.policy_version,
    )


def _survival_input_for_assessment(
    inp: IntegratedOfflineReplayInputV1,
    assessment: DirectionalAssessmentV1,
) -> SurvivalAssessmentInputV1:
    return SurvivalAssessmentInputV1(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        side=assessment.side,
        directional_assessment=assessment,
        cost_inputs=SurvivalCostInputsV1(
            entry_fee=0.0005,
            expected_entry_slippage=0.0002,
            exit_fee=0.0005,
            expected_exit_slippage=0.0002,
            expected_funding_cost=0.0001,
            expected_gross_edge=0.02,
            funding_cost_required=True,
        ),
        metric_inputs=SurvivalMetricInputsV1(
            data_completeness_complete=True,
            volatility_survival_ratio=0.8,
            sequence_survival_ratio=0.8,
            drawdown_survival_ratio=0.8,
            liquidation_buffer_ratio=0.2,
        ),
        last_evaluated_trading_epoch=inp.last_evaluated_trading_epoch,
        input_complete=True,
        explicit_hard_fail_reasons=(),
        explicit_blocked_reasons=(),
        policy_version=inp.policies.survival.policy_version,
    )


def _suitability_input_for_assessment(
    inp: IntegratedOfflineReplayInputV1,
    assessment: DirectionalAssessmentV1,
    survival: SurvivalResultV1,
) -> SuitabilityBindingInputV1:
    return SuitabilityBindingInputV1(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        side=assessment.side,
        directional_assessment=assessment,
        survival_result=survival,
        regime_id=inp.regime_id,
        regime_status=inp.regime_status,
        strategy_registry=inp.strategy_registry,
        last_evaluated_trading_epoch=inp.last_evaluated_trading_epoch,
        input_complete=True,
        explicit_hard_block_reasons=(),
        explicit_blocked_reasons=(),
        ranking_policy_version=inp.policies.suitability.policy_version,
    )


def run_integrated_offline_trading_logic_replay_v1(
    inp: IntegratedOfflineReplayInputV1,
) -> IntegratedOfflineReplayResultV1:
    """Execute the canonical STEP 29B–29H offline replay chain fail-closed."""
    fail_reasons: list[str] = []

    if not _instrument_allowed(inp.instrument_id):
        fail_reasons.append("instrument_kind_forbidden")
    if inp.instrument_id != inp.canonical_market_context.instrument_id:
        fail_reasons.append("instrument_mismatch")
    if inp.trading_epoch != inp.canonical_market_context.trading_epoch:
        fail_reasons.append("trading_epoch_mismatch")
    if inp.input_digest and not _valid_sha256_hex(inp.input_digest):
        fail_reasons.append("input_digest_invalid")

    contract_errors = _validate_contract_versions(inp)
    fail_reasons.extend(contract_errors)

    if fail_reasons:
        evidence = _blocked_evidence(inp, fail_reasons=tuple(fail_reasons))
        return IntegratedOfflineReplayResultV1(
            replay_pass=False,
            fail_reasons=tuple(fail_reasons),
            evidence=evidence,
        )

    context = (
        inp.canonical_market_context
        if inp.canonical_market_context.input_digest
        else with_computed_input_digest(inp.canonical_market_context)
    )

    binding = bind_canonical_market_context_event(
        context,
        inp.market_context_binding_state,
    )
    if binding.eligibility.binding_outcome is CanonicalMarketContextBindingOutcome.BLOCKED:
        reasons = tuple(r.value for r in binding.eligibility.block_reasons)
        evidence = _blocked_evidence(
            inp,
            fail_reasons=reasons or ("market_context_blocked",),
            decision_outcome="blocked",
        )
        return IntegratedOfflineReplayResultV1(
            False, reasons or ("market_context_blocked",), evidence
        )

    if not binding.context:
        evidence = _blocked_evidence(inp, fail_reasons=("missing_market_context_output",))
        return IntegratedOfflineReplayResultV1(False, ("missing_market_context_output",), evidence)

    bound_context = binding.context

    scope_init = initialize_canonical_scope(
        bound_context,
        inp.policies.scope_initialization,
        inp.scope_prerequisites,
        existing_scope=inp.existing_scope,
        reinitialization_guard=inp.scope_reinitialization_guard,
    )
    if scope_init.scope is None:
        reasons = tuple(r.value for r in scope_init.block_reasons) or (
            "scope_initialization_blocked",
        )
        decision_outcome = "observe" if any("warmup" in r for r in reasons) else "blocked"
        evidence = _blocked_evidence(inp, fail_reasons=reasons, decision_outcome=decision_outcome)
        return IntegratedOfflineReplayResultV1(False, reasons, evidence)

    current_scope = scope_init.scope

    scope_event_inp = ScopeEventGeneratorInputV1(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        market_context_id=bound_context.context_id,
        market_context_digest=bound_context.input_digest,
        current_scope=current_scope,
        current_direction_state=inp.scope_direction_state,
        reference_price=float(bound_context.mark_price),
        current_price=float(inp.current_price),
        trailing_anchor=float(current_scope.trailing_anchor),
        up_distance=float(inp.up_distance),
        adverse_exit_distance=float(inp.adverse_exit_distance),
        reversal_distance=float(inp.reversal_distance),
        confirmation_epochs=int(inp.confirmation_epochs),
        confirmation_state=inp.scope_confirmation_state,
        cooldown_state=inp.scope_cooldown_state,
        cooldown_remaining_epochs=int(inp.scope_cooldown_state.remaining_epochs),
        data_integrity_status=bound_context.data_integrity_status,
        clock_trust_status=bound_context.clock_trust_status,
        bar_finality_status=bound_context.bar_finality_status,
        policy_version=inp.policies.scope_event_generator.policy_version,
    )
    scope_event = with_computed_scope_event_digest(
        generate_deterministic_scope_event(scope_event_inp, inp.policies.scope_event_generator)
    )

    scope_event_ref = _scope_event_ref_from_evidence(scope_event)
    bull_inp = _directional_input_for_side(inp, DirectionalAssessmentSide.LONG, scope_event_ref)
    bear_inp = _directional_input_for_side(inp, DirectionalAssessmentSide.SHORT, scope_event_ref)
    bull_assessment = with_computed_directional_assessment_digest(
        evaluate_directional_assessment_v1(bull_inp, inp.policies.directional)
    )
    bear_assessment = with_computed_directional_assessment_digest(
        evaluate_directional_assessment_v1(bear_inp, inp.policies.directional)
    )

    bull_survival = evaluate_survival_assessment_v1(
        _survival_input_for_assessment(inp, bull_assessment),
        inp.policies.survival,
    )
    bear_survival = evaluate_survival_assessment_v1(
        _survival_input_for_assessment(inp, bear_assessment),
        inp.policies.survival,
    )
    bull_suitability = evaluate_suitability_binding_v1(
        _suitability_input_for_assessment(inp, bull_assessment, bull_survival),
        inp.policies.suitability,
    )
    bear_suitability = evaluate_suitability_binding_v1(
        _suitability_input_for_assessment(inp, bear_assessment, bear_survival),
        inp.policies.suitability,
    )

    composition_inp = DoublePlayCompositionInputV1(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        context_reference=inp.context_reference,
        bull_directional_assessment=bull_assessment,
        bear_directional_assessment=bear_assessment,
        bull_survival_result=bull_survival,
        bear_survival_result=bear_survival,
        bull_suitability_result=bull_suitability,
        bear_suitability_result=bear_suitability,
        previous_direction_state=inp.previous_composition_direction_state,
        position_management_context=inp.position_management_context,
        last_evaluated_trading_epoch=inp.last_evaluated_trading_epoch,
        input_complete=True,
        input_digest="",
        explicit_blocked_reasons=(),
        policy_version=inp.policies.composition.policy_version,
    )
    composition_inp = replace(
        composition_inp,
        input_digest=compute_composition_input_digest(composition_inp),
    )
    composition_result = evaluate_double_play_composition_matrix_v1(
        composition_inp,
        inp.policies.composition,
    )

    mapped_event = _canonical_scope_event_to_scope_event(scope_event.event_type)
    next_side_state, _, transition = transition_state(
        side_state=inp.side_state,
        event=mapped_event,
        scope_state=_EMPTY_SCOPE_STATE,
        rules=_DEFAULT_SCOPE_RULES,
        envelope=_DEFAULT_RUNTIME_ENVELOPE,
        now_tick=inp.now_tick,
    )
    state_switch_id = _derive_state_switch_id(
        inp.instrument_id, inp.trading_epoch, scope_event.scope_event_id
    )
    switch_digest = _compute_state_switch_digest(
        state_switch_id=state_switch_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        previous_side_state=inp.side_state.value,
        next_side_state=next_side_state.value,
        scope_event_type=scope_event.event_type.value,
        transition_allowed=transition.allowed,
        transition_reason_code=transition.reason_code,
    )
    state_switch = StateSwitchEvidenceV1(
        state_switch_id=state_switch_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        previous_side_state=inp.side_state.value,
        next_side_state=next_side_state.value,
        scope_event_type=scope_event.event_type.value,
        transition_allowed=transition.allowed,
        transition_reason_code=transition.reason_code,
        semantic_digest=switch_digest,
    )

    effective_direction = _side_state_to_entry_exit_direction(next_side_state)
    entry_exit_inp = DoublePlayEntryExitPolicyInputV0(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        context_reference=inp.context_reference,
        composition_result=composition_result,
        direction_state=effective_direction,
        position_state=inp.position_state,
        reconciliation_state=inp.reconciliation_state,
        trading_gate=inp.trading_gate,
        safety_mode=inp.safety_mode,
        data_integrity_state=bound_context.data_integrity_status,
        clock_trust_status=bound_context.clock_trust_status,
        clock_trust_valid=bound_context.clock_trust_status.value == "trusted",
        cooldown_pass=inp.cooldown_pass,
        existing_position_side=inp.existing_position_side,
        venue_flat=inp.venue_flat,
        scope_adverse_exit_signal=inp.scope_adverse_exit_signal,
        profit_protection_signal=inp.profit_protection_signal,
        time_exit_signal=inp.time_exit_signal,
        strategy_invalidation_signal=inp.strategy_invalidation_signal,
        hard_risk_reduction_signal=inp.hard_risk_reduction_signal,
        safety_exit_signal=inp.safety_exit_signal,
        input_complete=True,
        input_digest="",
        explicit_blocked_reasons=(),
        policy_version=inp.policies.entry_exit.policy_version,
    )
    entry_exit_inp = replace(
        entry_exit_inp,
        input_digest=compute_entry_exit_policy_input_digest(entry_exit_inp),
    )
    entry_exit_decision = evaluate_double_play_entry_exit_policy_v0(
        entry_exit_inp,
        inp.policies.entry_exit,
    )

    next_scope_ref = current_scope.scope_id
    if scope_event.next_scope_effective_epoch is not None:
        next_scope_ref = f"{current_scope.scope_id}-next-{scope_event.next_scope_effective_epoch}"

    selected_strategy_ref = ""
    if composition_result.selected_side is CompositionSelectedSide.LONG:
        selected_strategy_ref = bull_suitability.selected_strategy_id or ""
    elif composition_result.selected_side is CompositionSelectedSide.SHORT:
        selected_strategy_ref = bear_suitability.selected_strategy_id or ""

    input_digest = (
        inp.input_digest
        or hashlib.sha256(
            json.dumps(
                {
                    "config_digest": inp.config_digest,
                    "implementation_digest": inp.implementation_digest,
                    "replay_id": inp.replay_id,
                    "trading_epoch": inp.trading_epoch,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
    )

    decision_id = derive_decision_id(
        replay_id=inp.replay_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        input_digest=input_digest,
    )

    evidence = CanonicalTradingDecisionEvidenceV1(
        decision_id=decision_id,
        replay_id=inp.replay_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        market_context_ref=bound_context.context_id,
        scope_initialization_ref=current_scope.scope_id,
        scope_event_ref=scope_event.scope_event_id,
        bull_assessment_ref=bull_assessment.assessment_id,
        bear_assessment_ref=bear_assessment.assessment_id,
        state_switch_ref=state_switch.state_switch_id,
        bull_survival_ref=bull_survival.survival_id,
        bear_survival_ref=bear_survival.survival_id,
        bull_suitability_ref=bull_suitability.suitability_id,
        bear_suitability_ref=bear_suitability.suitability_id,
        composition_result_ref=composition_result.composition_id,
        entry_exit_policy_ref=entry_exit_decision.policy_decision_id,
        current_scope_ref=current_scope.scope_id,
        next_scope_ref=next_scope_ref,
        previous_direction_state=inp.direction_state.value,
        next_direction_state=effective_direction.value,
        selected_side=composition_result.selected_side.value,
        selected_strategy_ref=selected_strategy_ref,
        decision_outcome=entry_exit_decision.decision_outcome.value,
        entry_or_exit_policy_ref=entry_exit_decision.policy_decision_id,
        reason_codes=entry_exit_decision.reason_codes,
        decision_precedence_trace=entry_exit_decision.decision_precedence_trace,
        component_versions=dict(inp.component_versions)
        if inp.component_versions
        else _default_component_versions(),
        policy_versions=dict(inp.policy_versions),
        config_digest=inp.config_digest,
        implementation_digest=inp.implementation_digest,
        input_digest=input_digest,
        semantic_digest="",
    )
    evidence = with_computed_evidence_semantic_digest(evidence)

    intermediate = IntegratedOfflineReplayIntermediateV1(
        market_context=bound_context,
        scope_initialization=scope_init,
        scope_event=scope_event,
        bull_assessment=bull_assessment,
        bear_assessment=bear_assessment,
        bull_survival=bull_survival,
        bear_survival=bear_survival,
        bull_suitability=bull_suitability,
        bear_suitability=bear_suitability,
        composition_result=composition_result,
        entry_exit_decision=entry_exit_decision,
        state_switch=state_switch,
        current_scope=current_scope,
        next_scope_ref=next_scope_ref,
    )

    boundary_ok = (
        not entry_exit_decision.execution_eligible
        and not entry_exit_decision.adapter_compatible
        and entry_exit_decision.quantity_status == "NOT_BOUND"
        and entry_exit_decision.authority_effect == "NONE"
        and entry_exit_decision.runtime_effect == "NONE"
        and entry_exit_decision.order_effect == "NONE"
        and entry_exit_decision.risk_sizing_effect == "NONE"
        and not evidence.execution_eligible
        and not evidence.adapter_compatible
    )
    replay_pass = boundary_ok
    if not boundary_ok:
        fail_reasons.append("runtime_order_boundary_violation")

    return IntegratedOfflineReplayResultV1(
        replay_pass=replay_pass,
        fail_reasons=tuple(fail_reasons),
        evidence=evidence,
        intermediate=intermediate,
    )
