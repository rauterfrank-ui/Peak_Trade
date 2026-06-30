# tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py
from __future__ import annotations

import ast
from dataclasses import fields, replace
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    DirectionalAssessmentInputV1,
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
    DirectionalAssessmentV1,
    DirectionalConfirmationStateV1,
    ScopeEventRefV1,
    evaluate_directional_assessment_v1,
    mirror_price_path_for_short,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    BothCandidateOutcome,
    BothInvalidOutcome,
    CompositionConflictStatus,
    CompositionDirectionState,
    CompositionSelectedSide,
    CompositionStatus,
    DoublePlayCompositionInputV1,
    DoublePlayCompositionPolicyV1,
    DoublePlayCompositionResultV1,
    PositionManagementContext,
    compute_composition_input_digest,
    evaluate_double_play_composition_matrix_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    ENTRY_EXIT_POLICY_LAYER_VERSION,
    ENTRY_EXIT_POLICY_VERSION,
    DecisionOutcome,
    DoublePlayEntryExitPolicyInputV0,
    DoublePlayEntryExitPolicyV0,
    EntryEligibility,
    EntryExitDirectionState,
    ExitClass,
    ExistingPositionSide,
    PolicyBlockedReason,
    PolicySignalV0,
    PositionManagementAction,
    PositionState,
    ReconciliationState,
    ReversalState,
    SafetyMode,
    TradingGate,
    compute_entry_exit_policy_input_digest,
    compute_entry_exit_policy_semantic_digest,
    evaluate_double_play_entry_exit_policy_v0,
)
from trading.master_v2.survival_assessment_v1 import (
    SURVIVAL_ASSESSMENT_POLICY_VERSION,
    SurvivalAssessmentInputV1,
    SurvivalAssessmentPolicyV1,
    SurvivalAssessmentStatus,
    SurvivalCostInputsV1,
    SurvivalMetricInputsV1,
    SurvivalResultV1,
    evaluate_survival_assessment_v1,
)
from trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_RANKING_POLICY_VERSION,
    SuitabilityBindingInputV1,
    SuitabilityBindingStatus,
    SuitabilityRankingPolicyV1,
    SuitabilityRegimeStatus,
    SuitabilityResultV1,
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
    evaluate_suitability_binding_v1,
    mirror_suitability_strategy_entry_for_short,
)

_INSTRUMENT = "inst-eth-usdt-perp"
_EPOCH = 44
_CONTEXT_REF = "trading-context-epoch-44"


def _scope_ref(**overrides: object) -> ScopeEventRefV1:
    base: dict = {
        "scope_event_id": "scope-event-inst-eth-usdt-perp-epoch43-upscope_candidate",
        "semantic_digest": "a" * 64,
        "event_type": "upscope_candidate",
        "trading_epoch": 43,
    }
    base.update(overrides)
    return ScopeEventRefV1(**base)


def _directional_policy(**overrides: object) -> DirectionalAssessmentPolicyV1:
    base: dict = {
        "observe_signal_threshold": 0.001,
        "candidate_signal_threshold": 0.005,
        "confirmation_signal_threshold": 0.01,
        "confirmation_epochs": 2,
        "validity_epochs": 3,
        "policy_version": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return DirectionalAssessmentPolicyV1(**base)


def _directional_input(
    side: DirectionalAssessmentSide, **overrides: object
) -> DirectionalAssessmentInputV1:
    anchor = 3500.0
    long_path = (anchor, anchor * 1.02)
    price_path = (
        long_path
        if side is DirectionalAssessmentSide.LONG
        else mirror_price_path_for_short(long_path, anchor)
    )
    base: dict = {
        "instrument_id": _INSTRUMENT,
        "trading_epoch": _EPOCH,
        "side": side,
        "price_path": price_path,
        "reference_price": anchor,
        "feature_refs": ("feat-momentum-v1",),
        "scope_event_ref": _scope_ref(),
        "survival_preconditions": ("survival_precondition_ref_only",),
        "confirmation_state": DirectionalConfirmationStateV1(
            candidate_count=1,
            last_evaluated_trading_epoch=_EPOCH - 1,
            last_signal_strength=0.02,
        ),
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "trusted_data": True,
        "input_complete": True,
        "explicit_hard_block_reasons": (),
        "policy_version": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return DirectionalAssessmentInputV1(**base)


def _confirmed_assessment(
    side: DirectionalAssessmentSide, **overrides: object
) -> DirectionalAssessmentV1:
    policy = overrides.pop("policy", _directional_policy())
    first = evaluate_directional_assessment_v1(
        _directional_input(
            side,
            trading_epoch=_EPOCH - 1,
            confirmation_state=DirectionalConfirmationStateV1(
                candidate_count=0,
                last_evaluated_trading_epoch=_EPOCH - 2,
                last_signal_strength=0.0,
            ),
            scope_event_ref=_scope_ref(trading_epoch=_EPOCH - 2),
            **{k: v for k, v in overrides.items() if k != "trading_epoch"},
        ),
        policy,
    )
    second = evaluate_directional_assessment_v1(
        _directional_input(
            side,
            trading_epoch=_EPOCH,
            confirmation_state=DirectionalConfirmationStateV1(
                candidate_count=1,
                last_evaluated_trading_epoch=_EPOCH - 1,
                last_signal_strength=first.signal_strength,
            ),
            scope_event_ref=_scope_ref(trading_epoch=_EPOCH - 1),
            **overrides,
        ),
        policy,
    )
    assert second.status is DirectionalAssessmentStatus.CONFIRMED
    return second


def _survival_policy(**overrides: object) -> SurvivalAssessmentPolicyV1:
    base: dict = {
        "min_net_edge": 0.001,
        "min_volatility_survival_ratio": 0.5,
        "min_sequence_survival_ratio": 0.5,
        "min_drawdown_survival_ratio": 0.5,
        "min_liquidation_buffer_ratio": 0.1,
        "validity_epochs": 3,
        "policy_version": SURVIVAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return SurvivalAssessmentPolicyV1(**base)


def _survival_for(
    assessment: DirectionalAssessmentV1,
    *,
    status: SurvivalAssessmentStatus = SurvivalAssessmentStatus.PASS,
) -> SurvivalResultV1:
    inp = SurvivalAssessmentInputV1(
        instrument_id=assessment.instrument_id,
        trading_epoch=assessment.trading_epoch,
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
        last_evaluated_trading_epoch=assessment.trading_epoch - 1,
        input_complete=True,
        explicit_hard_fail_reasons=(),
        explicit_blocked_reasons=(),
        policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
    )
    result = evaluate_survival_assessment_v1(inp, _survival_policy())
    if status is not SurvivalAssessmentStatus.PASS:
        return replace(result, status=status)
    return result


def _strategy_entry(
    side: DirectionalAssessmentSide, **overrides: object
) -> SuitabilityStrategyEntryV1:
    base: dict = {
        "strategy_id": "strat-momentum-v1",
        "supported_regime_ids": ("trending",),
        "supported_sides": (side,),
        "priority_rank": 10,
        "disabled": False,
        "confidence_score": 0.75,
    }
    base.update(overrides)
    return SuitabilityStrategyEntryV1(**base)


def _suitability_for(
    assessment: DirectionalAssessmentV1,
    survival: SurvivalResultV1,
    *,
    status: SuitabilityBindingStatus = SuitabilityBindingStatus.PASS,
) -> SuitabilityResultV1:
    entry = _strategy_entry(assessment.side)
    if assessment.side is DirectionalAssessmentSide.SHORT:
        entry = mirror_suitability_strategy_entry_for_short(
            _strategy_entry(DirectionalAssessmentSide.LONG)
        )
    inp = SuitabilityBindingInputV1(
        instrument_id=assessment.instrument_id,
        trading_epoch=assessment.trading_epoch,
        side=assessment.side,
        directional_assessment=assessment,
        survival_result=survival,
        regime_id="trending",
        regime_status=SuitabilityRegimeStatus.KNOWN,
        strategy_registry=SuitabilityStrategyRegistryV1(entries=(entry,)),
        last_evaluated_trading_epoch=assessment.trading_epoch - 1,
        input_complete=True,
        explicit_hard_block_reasons=(),
        explicit_blocked_reasons=(),
        ranking_policy_version=SUITABILITY_RANKING_POLICY_VERSION,
    )
    policy = SuitabilityRankingPolicyV1(
        validity_epochs=3,
        no_match_status=SuitabilityBindingStatus.FAIL,
        policy_version=SUITABILITY_RANKING_POLICY_VERSION,
    )
    result = evaluate_suitability_binding_v1(inp, policy)
    if status is not SuitabilityBindingStatus.PASS:
        return replace(result, status=status, selected_strategy_id=None)
    return result


def _side_bundle(
    side: DirectionalAssessmentSide,
    *,
    assessment_status: DirectionalAssessmentStatus | None = None,
    survival_status: SurvivalAssessmentStatus = SurvivalAssessmentStatus.PASS,
    suitability_status: SuitabilityBindingStatus = SuitabilityBindingStatus.PASS,
) -> tuple[DirectionalAssessmentV1, SurvivalResultV1, SuitabilityResultV1]:
    if assessment_status is DirectionalAssessmentStatus.CONFIRMED or assessment_status is None:
        assessment = _confirmed_assessment(side)
    else:
        assessment = replace(_confirmed_assessment(side), status=assessment_status)
    survival = _survival_for(assessment, status=survival_status)
    suitability = _suitability_for(assessment, survival, status=suitability_status)
    return assessment, survival, suitability


def _composition_input(**overrides: object) -> DoublePlayCompositionInputV1:
    bull_a, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear_a, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    bull_a = overrides.pop("bull_directional_assessment", bull_a)
    bear_a = overrides.pop("bear_directional_assessment", bear_a)
    bull_s = overrides.pop("bull_survival_result", bull_s)
    bear_s = overrides.pop("bear_survival_result", bear_s)
    bull_u = overrides.pop("bull_suitability_result", bull_u)
    bear_u = overrides.pop("bear_suitability_result", bear_u)
    base: dict = {
        "instrument_id": _INSTRUMENT,
        "trading_epoch": _EPOCH,
        "context_reference": _CONTEXT_REF,
        "bull_directional_assessment": bull_a,
        "bear_directional_assessment": bear_a,
        "bull_survival_result": bull_s,
        "bear_survival_result": bear_s,
        "bull_suitability_result": bull_u,
        "bear_suitability_result": bear_u,
        "previous_direction_state": CompositionDirectionState.NEUTRAL,
        "position_management_context": PositionManagementContext.FLAT,
        "last_evaluated_trading_epoch": _EPOCH - 1,
        "input_complete": True,
        "input_digest": "",
        "explicit_blocked_reasons": (),
        "policy_version": "double_play_composition_matrix_policy_v1",
    }
    base.update(overrides)
    inp = DoublePlayCompositionInputV1(**base)
    digest = compute_composition_input_digest(inp)
    return replace(inp, input_digest=digest)


def _composition_result(**kwargs: object) -> DoublePlayCompositionResultV1:
    inp = kwargs.pop("inp", _composition_input(**kwargs))
    policy = DoublePlayCompositionPolicyV1(
        validity_epochs=3,
        both_candidate_outcome=BothCandidateOutcome.OBSERVE,
        both_invalid_outcome=BothInvalidOutcome.BLOCKED,
        policy_version="double_play_composition_matrix_policy_v1",
    )
    return evaluate_double_play_composition_matrix_v1(inp, policy)


def _long_selected_composition() -> DoublePlayCompositionResultV1:
    bull, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear = replace(
        _confirmed_assessment(DirectionalAssessmentSide.SHORT),
        status=DirectionalAssessmentStatus.OBSERVE,
    )
    bear_s = _survival_for(bear)
    bear_u = _suitability_for(bear, bear_s)
    return _composition_result(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
    )


def _short_selected_composition() -> DoublePlayCompositionResultV1:
    bear, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    bull = replace(
        _confirmed_assessment(DirectionalAssessmentSide.LONG),
        status=DirectionalAssessmentStatus.OBSERVE,
    )
    bull_s = _survival_for(bull)
    bull_u = _suitability_for(bull, bull_s)
    return _composition_result(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
    )


def _policy_input(**overrides: object) -> DoublePlayEntryExitPolicyInputV0:
    comp = overrides.pop("composition_result", _long_selected_composition())
    base: dict = {
        "instrument_id": _INSTRUMENT,
        "trading_epoch": _EPOCH,
        "context_reference": _CONTEXT_REF,
        "composition_result": comp,
        "direction_state": EntryExitDirectionState.LONG_ARMED,
        "position_state": PositionState.FLAT_RECONCILED,
        "reconciliation_state": ReconciliationState.RECONCILED,
        "trading_gate": TradingGate.ENTRY_ALLOWED,
        "safety_mode": SafetyMode.NORMAL,
        "data_integrity_state": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "clock_trust_valid": True,
        "cooldown_pass": True,
        "existing_position_side": ExistingPositionSide.NONE,
        "venue_flat": True,
        "scope_adverse_exit_signal": PolicySignalV0(triggered=False),
        "profit_protection_signal": PolicySignalV0(triggered=False),
        "time_exit_signal": PolicySignalV0(triggered=False),
        "strategy_invalidation_signal": PolicySignalV0(triggered=False),
        "hard_risk_reduction_signal": PolicySignalV0(triggered=False),
        "safety_exit_signal": PolicySignalV0(triggered=False),
        "input_complete": True,
        "input_digest": "",
        "explicit_blocked_reasons": (),
        "policy_version": ENTRY_EXIT_POLICY_VERSION,
    }
    base.update(overrides)
    inp = DoublePlayEntryExitPolicyInputV0(**base)
    digest = compute_entry_exit_policy_input_digest(inp)
    return replace(inp, input_digest=digest)


def _evaluate(**kwargs: object):
    inp = kwargs.pop("inp", _policy_input(**kwargs))
    policy = kwargs.pop("policy", DoublePlayEntryExitPolicyV0())
    return evaluate_double_play_entry_exit_policy_v0(inp, policy)


def test_layer_version() -> None:
    assert ENTRY_EXIT_POLICY_LAYER_VERSION == "v0"


def test_contract_schema_complete() -> None:
    d = _evaluate()
    required = {
        "policy_decision_id",
        "instrument_id",
        "trading_epoch",
        "composition_result_ref",
        "decision_outcome",
        "entry_eligibility",
        "exit_class",
        "position_management_action",
        "reversal_state",
        "reduce_only",
        "position_flip_allowed",
        "quantity_status",
        "reason_codes",
        "decision_precedence_trace",
        "semantic_digest",
        "execution_eligible",
        "adapter_compatible",
        "authority_effect",
        "runtime_effect",
        "order_effect",
        "risk_sizing_effect",
    }
    assert required.issubset({f.name for f in fields(type(d))})


def test_1_flat_reconciled_long_admissible_enter_long() -> None:
    d = _evaluate(
        composition_result=_long_selected_composition(),
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    assert d.decision_outcome is DecisionOutcome.ENTER_LONG
    assert d.entry_eligibility is EntryEligibility.ELIGIBLE


def test_2_flat_reconciled_short_admissible_enter_short() -> None:
    d = _evaluate(
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )
    assert d.decision_outcome is DecisionOutcome.ENTER_SHORT
    assert d.entry_eligibility is EntryEligibility.ELIGIBLE


def test_3_survival_fail_blocks_entry() -> None:
    comp = replace(
        _long_selected_composition(),
        composition_status=CompositionStatus.LONG_SELECTED,
        selected_side=CompositionSelectedSide.LONG,
        bull_survival_ref=replace(
            _long_selected_composition().bull_survival_ref,
            status=SurvivalAssessmentStatus.FAIL,
        ),
    )
    d = _evaluate(composition_result=comp)
    assert d.decision_outcome is DecisionOutcome.BLOCKED
    assert "survival_not_pass" in d.reason_codes


def test_4_suitability_blocked_blocks_entry() -> None:
    comp = replace(
        _long_selected_composition(),
        composition_status=CompositionStatus.LONG_SELECTED,
        selected_side=CompositionSelectedSide.LONG,
        bull_suitability_ref=replace(
            _long_selected_composition().bull_suitability_ref,
            status=SuitabilityBindingStatus.FAIL,
        ),
    )
    d = _evaluate(composition_result=comp)
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_5_entry_signal_position_not_flat_no_new_entry() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL, existing_position_side=ExistingPositionSide.LONG
    )
    assert d.decision_outcome is not DecisionOutcome.ENTER_LONG


def test_6_reconciliation_not_reconciled_reconcile_only() -> None:
    d = _evaluate(reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED)
    assert d.decision_outcome is DecisionOutcome.RECONCILE_ONLY


def test_7_safety_mode_not_normal_blocks_entry() -> None:
    d = _evaluate(safety_mode=SafetyMode.BLOCKED)
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_8_data_integrity_untrusted_blocks() -> None:
    d = _evaluate(data_integrity_state=DataIntegrityStatus.UNTRUSTED)
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_9_clock_trust_invalid_blocks() -> None:
    d = _evaluate(clock_trust_valid=False, clock_trust_status=ClockTrustStatus.UNTRUSTED)
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_10_cooldown_fail_blocks() -> None:
    d = _evaluate(cooldown_pass=False)
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_11_existing_long_hold() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        composition_result=_long_selected_composition(),
    )
    assert d.decision_outcome is DecisionOutcome.HOLD
    assert d.position_management_action is PositionManagementAction.HOLD


def test_12_existing_short_hold() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.SHORT,
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )
    assert d.decision_outcome is DecisionOutcome.HOLD


def test_13_existing_long_adverse_scope_exit_reduce() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        scope_adverse_exit_signal=PolicySignalV0(triggered=True, reason_code="adverse_scope"),
    )
    assert d.decision_outcome is DecisionOutcome.REDUCE
    assert d.exit_class is ExitClass.ADVERSE_SCOPE_EXIT
    assert d.reduce_only is True
    assert d.position_flip_allowed is False


def test_14_existing_short_adverse_scope_mirrored() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.SHORT,
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
        scope_adverse_exit_signal=PolicySignalV0(triggered=True, reason_code="adverse_scope"),
    )
    assert d.decision_outcome is DecisionOutcome.REDUCE
    assert d.exit_class is ExitClass.ADVERSE_SCOPE_EXIT


def test_15_profit_protection_exit() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        profit_protection_signal=PolicySignalV0(triggered=True, reason_code="profit_lock"),
    )
    assert d.exit_class is ExitClass.PROFIT_PROTECTION_EXIT
    assert d.decision_outcome is DecisionOutcome.EXIT


def test_16_time_exit() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        time_exit_signal=PolicySignalV0(triggered=True, reason_code="time_limit"),
    )
    assert d.exit_class is ExitClass.TIME_EXIT
    assert d.decision_outcome is DecisionOutcome.EXIT


def test_17_strategy_invalidation_exit() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        strategy_invalidation_signal=PolicySignalV0(triggered=True, reason_code="invalidated"),
    )
    assert d.exit_class is ExitClass.STRATEGY_INVALIDATION_EXIT


def test_18_safety_exit_highest_priority() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        safety_exit_signal=PolicySignalV0(triggered=True, reason_code="safety"),
        scope_adverse_exit_signal=PolicySignalV0(triggered=True),
        profit_protection_signal=PolicySignalV0(triggered=True),
    )
    assert d.exit_class is ExitClass.SAFETY_EXIT
    assert d.decision_precedence_trace[0] == "safety_authority"


def test_19_hard_risk_reduction() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        hard_risk_reduction_signal=PolicySignalV0(triggered=True, reason_code="hard_risk"),
    )
    assert d.exit_class is ExitClass.HARD_RISK_EXIT
    assert d.decision_outcome is DecisionOutcome.REDUCE


def test_20_reconciliation_required() -> None:
    d = _evaluate(position_state=PositionState.RECONCILIATION_REQUIRED)
    assert d.decision_outcome is DecisionOutcome.RECONCILE_ONLY


def test_21_existing_long_short_selected_reversal_preparation() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )
    assert d.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT
    assert d.reversal_state is ReversalState.PREPARATION
    assert d.decision_outcome is not DecisionOutcome.ENTER_SHORT


def test_22_existing_short_long_selected_reversal_mirrored() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.SHORT,
        composition_result=_long_selected_composition(),
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    assert d.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT
    assert d.decision_outcome is not DecisionOutcome.ENTER_LONG


def test_23_reducing_partial_blocks_opposite_entry() -> None:
    d = _evaluate(
        position_state=PositionState.REDUCING_PARTIAL,
        existing_position_side=ExistingPositionSide.LONG,
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_24_exit_pending_blocks_opposite_entry() -> None:
    d = _evaluate(
        position_state=PositionState.EXIT_PENDING,
        existing_position_side=ExistingPositionSide.LONG,
        composition_result=_short_selected_composition(),
    )
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_25_submission_unknown_reconcile_only() -> None:
    d = _evaluate(position_state=PositionState.SUBMISSION_UNKNOWN)
    assert d.decision_outcome is DecisionOutcome.RECONCILE_ONLY
    assert d.reversal_state is ReversalState.BLOCKED


def test_26_venue_flat_not_reconciled_not_flat_reconciled() -> None:
    d = _evaluate(
        position_state=PositionState.RECONCILIATION_REQUIRED,
        venue_flat=True,
    )
    assert d.decision_outcome is DecisionOutcome.RECONCILE_ONLY


def test_27_both_sides_confirmed_chop_guard_no_new_entry() -> None:
    bull, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    comp = _composition_result(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
    )
    assert comp.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    d = _evaluate(composition_result=comp)
    assert d.decision_outcome is DecisionOutcome.OBSERVE
    assert d.decision_outcome is not DecisionOutcome.ENTER_LONG


def test_28_entry_and_exit_exit_wins() -> None:
    d = _evaluate(
        scope_adverse_exit_signal=PolicySignalV0(triggered=True, reason_code="adverse"),
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
    )
    assert d.decision_outcome in (DecisionOutcome.REDUCE, DecisionOutcome.EXIT)
    assert d.decision_outcome is not DecisionOutcome.ENTER_LONG


def test_29_multiple_exit_signals_stable_priority() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        scope_adverse_exit_signal=PolicySignalV0(triggered=True),
        profit_protection_signal=PolicySignalV0(triggered=True),
        time_exit_signal=PolicySignalV0(triggered=True),
    )
    assert d.exit_class is ExitClass.ADVERSE_SCOPE_EXIT


def test_30_missing_inputs_fail_closed() -> None:
    d = _evaluate(input_complete=False)
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_31_instrument_mismatch_blocked() -> None:
    comp = _long_selected_composition()
    d = _evaluate(composition_result=comp, instrument_id="other-instrument")
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_32_trading_epoch_mismatch_blocked() -> None:
    comp = _long_selected_composition()
    d = _evaluate(composition_result=comp, trading_epoch=_EPOCH + 1)
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_33_provenance_digest_mismatch_blocked() -> None:
    inp = _policy_input()
    bad = replace(inp, input_digest="b" * 64)
    d = evaluate_double_play_entry_exit_policy_v0(bad, DoublePlayEntryExitPolicyV0())
    assert d.decision_outcome is DecisionOutcome.BLOCKED
    assert PolicyBlockedReason.INPUT_DIGEST_MISMATCH.value in d.reason_codes


def test_34_long_short_symmetry() -> None:
    long_d = _evaluate(
        composition_result=_long_selected_composition(),
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    short_d = _evaluate(
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )
    assert long_d.decision_outcome is DecisionOutcome.ENTER_LONG
    assert short_d.decision_outcome is DecisionOutcome.ENTER_SHORT
    assert long_d.execution_eligible is False
    assert short_d.execution_eligible is False


def test_35_deterministic_replay_identical_digest() -> None:
    inp = _policy_input()
    d1 = evaluate_double_play_entry_exit_policy_v0(inp, DoublePlayEntryExitPolicyV0())
    d2 = evaluate_double_play_entry_exit_policy_v0(inp, DoublePlayEntryExitPolicyV0())
    assert d1.semantic_digest == d2.semantic_digest
    assert d1.reason_codes == d2.reason_codes
    assert d1.decision_precedence_trace == d2.decision_precedence_trace


def test_boundary_no_runtime_order_effects() -> None:
    d = _evaluate()
    assert d.execution_eligible is False
    assert d.adapter_compatible is False
    assert d.authority_effect == "NONE"
    assert d.runtime_effect == "NONE"
    assert d.order_effect == "NONE"
    assert d.risk_sizing_effect == "NONE"
    assert d.quantity_status == "NOT_BOUND"


def test_exit_invariant_reduce_only_no_flip() -> None:
    d = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        safety_exit_signal=PolicySignalV0(triggered=True),
    )
    assert d.reduce_only is True
    assert d.position_flip_allowed is False


def test_trading_gate_blocks_entry() -> None:
    d = _evaluate(trading_gate=TradingGate.BLOCKED)
    assert d.decision_outcome is DecisionOutcome.BLOCKED


def test_collection_order_invariance_mandatory_exits() -> None:
    signals_a = {
        "scope_adverse_exit_signal": PolicySignalV0(triggered=True),
        "profit_protection_signal": PolicySignalV0(triggered=True),
        "time_exit_signal": PolicySignalV0(triggered=True),
    }
    signals_b = {
        "time_exit_signal": PolicySignalV0(triggered=True),
        "profit_protection_signal": PolicySignalV0(triggered=True),
        "scope_adverse_exit_signal": PolicySignalV0(triggered=True),
    }
    base = dict(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
    )
    d_a = _evaluate(**base, **signals_a)
    d_b = _evaluate(**base, **signals_b)
    assert d_a.exit_class == d_b.exit_class
    assert d_a.semantic_digest == d_b.semantic_digest


def test_no_forbidden_imports_in_module() -> None:
    p = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "trading"
        / "master_v2"
        / "double_play_entry_exit_policy_v0.py"
    )
    tree = ast.parse(p.read_text(encoding="utf-8"))
    bad = {
        "requests",
        "urllib3",
        "ccxt",
        "httpx",
        "socket",
        "aiohttp",
        "execution",
        "scheduler",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                root = n.name.split(".")[0]
                assert root not in bad
        if isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in ("trading",):
                continue
            assert root not in bad


def test_semantic_digest_recomputable() -> None:
    d = _evaluate()
    assert d.semantic_digest == compute_entry_exit_policy_semantic_digest(d)
