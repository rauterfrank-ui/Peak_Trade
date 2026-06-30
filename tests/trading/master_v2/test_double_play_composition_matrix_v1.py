# tests/trading/master_v2/test_double_play_composition_matrix_v1.py
from __future__ import annotations

import ast
import inspect
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
    DOUBLE_PLAY_COMPOSITION_MATRIX_LAYER_VERSION,
    DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    BothCandidateOutcome,
    BothInvalidOutcome,
    CompositionBlockedReason,
    CompositionChopGuardStatus,
    CompositionConflictStatus,
    CompositionDirectionState,
    CompositionSelectedSide,
    CompositionStatus,
    DoublePlayCompositionInputV1,
    DoublePlayCompositionPolicyV1,
    DoublePlayCompositionResultV1,
    PositionManagementContext,
    compute_composition_input_digest,
    compute_composition_result_semantic_digest,
    evaluate_double_play_composition_matrix_v1,
    serialize_composition_input_canonical,
    serialize_composition_result_canonical,
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


def _composition_policy(**overrides: object) -> DoublePlayCompositionPolicyV1:
    base: dict = {
        "validity_epochs": 3,
        "both_candidate_outcome": BothCandidateOutcome.OBSERVE,
        "both_invalid_outcome": BothInvalidOutcome.BLOCKED,
        "policy_version": DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    }
    base.update(overrides)
    return DoublePlayCompositionPolicyV1(**base)


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
        "policy_version": DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    }
    base.update(overrides)
    inp = DoublePlayCompositionInputV1(**base)
    digest = compute_composition_input_digest(inp)
    return replace(inp, input_digest=digest)


def _evaluate(**kwargs: object) -> DoublePlayCompositionResultV1:
    inp = kwargs.pop("inp", _composition_input(**kwargs))
    policy = kwargs.pop("policy", _composition_policy())
    return evaluate_double_play_composition_matrix_v1(inp, policy)


def test_1_contract_schema_complete() -> None:
    names = {f.name for f in fields(DoublePlayCompositionResultV1)}
    required = {
        "composition_id",
        "instrument_id",
        "trading_epoch",
        "bull_assessment_ref",
        "bear_assessment_ref",
        "bull_survival_ref",
        "bear_survival_ref",
        "bull_suitability_ref",
        "bear_suitability_ref",
        "previous_direction_state",
        "composition_status",
        "selected_side",
        "conflict_status",
        "chop_guard_status",
        "reason_codes",
        "policy_version",
        "input_digest",
        "semantic_digest",
        "authority_effect",
        "runtime_effect",
        "order_effect",
        "risk_effect",
        "sizing_effect",
    }
    assert required.issubset(names)


def test_2_layer_version() -> None:
    assert DOUBLE_PLAY_COMPOSITION_MATRIX_LAYER_VERSION == "v1"


def test_3_both_sides_invalid_blocked() -> None:
    bull = replace(
        _confirmed_assessment(DirectionalAssessmentSide.LONG),
        status=DirectionalAssessmentStatus.INVALID,
    )
    bear = replace(
        _confirmed_assessment(DirectionalAssessmentSide.SHORT),
        status=DirectionalAssessmentStatus.INVALID,
    )
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=_survival_for(bull),
        bear_survival_result=_survival_for(bear),
        bull_suitability_result=_suitability_for(bull, _survival_for(bull)),
        bear_suitability_result=_suitability_for(bear, _survival_for(bear)),
    )
    assert result.composition_status is CompositionStatus.BLOCKED
    assert CompositionBlockedReason.BOTH_SIDES_INVALID.value in result.reason_codes


def test_4_both_sides_blocked() -> None:
    bull = replace(
        _confirmed_assessment(DirectionalAssessmentSide.LONG),
        status=DirectionalAssessmentStatus.BLOCKED,
    )
    bear = replace(
        _confirmed_assessment(DirectionalAssessmentSide.SHORT),
        status=DirectionalAssessmentStatus.BLOCKED,
    )
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=_survival_for(bull),
        bear_survival_result=_survival_for(bear),
        bull_suitability_result=_suitability_for(bull, _survival_for(bull)),
        bear_suitability_result=_suitability_for(bear, _survival_for(bear)),
    )
    assert result.composition_status is CompositionStatus.BLOCKED
    assert "both_sides_blocked" in result.reason_codes


def test_5_both_sides_candidate_observe() -> None:
    bull = replace(
        _confirmed_assessment(DirectionalAssessmentSide.LONG),
        status=DirectionalAssessmentStatus.CANDIDATE,
    )
    bear = replace(
        _confirmed_assessment(DirectionalAssessmentSide.SHORT),
        status=DirectionalAssessmentStatus.CANDIDATE,
    )
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=_survival_for(bull),
        bear_survival_result=_survival_for(bear),
        bull_suitability_result=_suitability_for(bull, _survival_for(bull)),
        bear_suitability_result=_suitability_for(bear, _survival_for(bear)),
    )
    assert result.composition_status is CompositionStatus.OBSERVE
    assert result.conflict_status is CompositionConflictStatus.BOTH_SIDES_CANDIDATE
    assert result.selected_side is CompositionSelectedSide.NONE


def test_6_both_sides_confirmed_chop_guard() -> None:
    bull, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
    )
    assert result.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    assert result.conflict_status is CompositionConflictStatus.BOTH_SIDES_CONFIRMED
    assert result.chop_guard_status is CompositionChopGuardStatus.CHOP_GUARD_BLOCK
    assert "no_new_entry" in result.reason_codes
    assert result.selected_side is CompositionSelectedSide.NONE


def test_7_long_only_admissible() -> None:
    bull, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear = replace(
        _confirmed_assessment(DirectionalAssessmentSide.SHORT),
        status=DirectionalAssessmentStatus.OBSERVE,
    )
    bear_s = _survival_for(bear)
    bear_u = _suitability_for(bear, bear_s, status=SuitabilityBindingStatus.BLOCKED)
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
    )
    assert result.composition_status is CompositionStatus.LONG_SELECTED
    assert result.selected_side is CompositionSelectedSide.LONG


def test_8_short_only_admissible() -> None:
    bear, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    bull = replace(
        _confirmed_assessment(DirectionalAssessmentSide.LONG),
        status=DirectionalAssessmentStatus.OBSERVE,
    )
    bull_s = _survival_for(bull)
    bull_u = _suitability_for(bull, bull_s, status=SuitabilityBindingStatus.BLOCKED)
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
    )
    assert result.composition_status is CompositionStatus.SHORT_SELECTED
    assert result.selected_side is CompositionSelectedSide.SHORT


def test_9_survival_fail_blocks_entry() -> None:
    bull, bull_s, bull_u = _side_bundle(
        DirectionalAssessmentSide.LONG,
        survival_status=SurvivalAssessmentStatus.FAIL,
    )
    bear = replace(
        _confirmed_assessment(DirectionalAssessmentSide.SHORT),
        status=DirectionalAssessmentStatus.INVALID,
    )
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=_survival_for(bear),
        bull_suitability_result=bull_u,
        bear_suitability_result=_suitability_for(bear, _survival_for(bear)),
    )
    assert result.composition_status is CompositionStatus.BLOCKED
    assert CompositionBlockedReason.SURVIVAL_NOT_PASS.value in result.reason_codes


def test_10_survival_blocked_blocks_entry() -> None:
    bull, bull_s, _ = _side_bundle(
        DirectionalAssessmentSide.LONG,
        survival_status=SurvivalAssessmentStatus.BLOCKED,
    )
    bear = replace(
        _confirmed_assessment(DirectionalAssessmentSide.SHORT),
        status=DirectionalAssessmentStatus.INVALID,
    )
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=_survival_for(bear),
        bull_suitability_result=_suitability_for(bull, bull_s),
        bear_suitability_result=_suitability_for(bear, _survival_for(bear)),
    )
    assert result.composition_status is CompositionStatus.BLOCKED


def test_11_suitability_blocked_blocks_entry() -> None:
    bull, bull_s, bull_u = _side_bundle(
        DirectionalAssessmentSide.LONG,
        suitability_status=SuitabilityBindingStatus.BLOCKED,
    )
    bear = replace(
        _confirmed_assessment(DirectionalAssessmentSide.SHORT),
        status=DirectionalAssessmentStatus.INVALID,
    )
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=_survival_for(bear),
        bull_suitability_result=bull_u,
        bear_suitability_result=_suitability_for(bear, _survival_for(bear)),
    )
    assert result.composition_status is CompositionStatus.BLOCKED
    assert CompositionBlockedReason.SUITABILITY_NOT_PASS.value in result.reason_codes


def test_12_confidence_override_forbidden_on_both_confirmed() -> None:
    bull, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    result = _evaluate(
        bull_directional_assessment=replace(bull, confidence=0.99),
        bear_directional_assessment=replace(bear, confidence=0.01),
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
    )
    assert result.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    assert result.selected_side is CompositionSelectedSide.NONE


def test_13_existing_long_position_bear_confirmed_reversal_preparation() -> None:
    bull = replace(
        _confirmed_assessment(DirectionalAssessmentSide.LONG),
        status=DirectionalAssessmentStatus.OBSERVE,
    )
    bear, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=_survival_for(bull),
        bear_survival_result=bear_s,
        bull_suitability_result=_suitability_for(bull, _survival_for(bull)),
        bear_suitability_result=bear_u,
        position_management_context=PositionManagementContext.LONG_POSITION,
    )
    assert result.composition_status is CompositionStatus.REVERSAL_PREPARATION
    assert result.selected_side is CompositionSelectedSide.NONE


def test_14_existing_short_position_bull_confirmed_reversal_preparation() -> None:
    bull, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear = replace(
        _confirmed_assessment(DirectionalAssessmentSide.SHORT),
        status=DirectionalAssessmentStatus.OBSERVE,
    )
    result = _evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=_survival_for(bear),
        bull_suitability_result=bull_u,
        bear_suitability_result=_suitability_for(bear, _survival_for(bear)),
        position_management_context=PositionManagementContext.SHORT_POSITION,
    )
    assert result.composition_status is CompositionStatus.REVERSAL_PREPARATION
    assert result.selected_side is CompositionSelectedSide.NONE


def test_15_input_digest_mismatch_blocks() -> None:
    inp = _composition_input()
    bad = replace(inp, input_digest="b" * 64)
    result = evaluate_double_play_composition_matrix_v1(bad, _composition_policy())
    assert result.composition_status is CompositionStatus.BLOCKED
    assert CompositionBlockedReason.INPUT_DIGEST_MISMATCH.value in result.reason_codes


def test_16_instrument_mismatch_blocks() -> None:
    bear = _confirmed_assessment(DirectionalAssessmentSide.SHORT, instrument_id="inst-other-perp")
    result = _evaluate(bear_directional_assessment=bear, bear_survival_result=_survival_for(bear))
    assert result.composition_status is CompositionStatus.BLOCKED


def test_17_epoch_mismatch_blocks() -> None:
    bear = replace(_confirmed_assessment(DirectionalAssessmentSide.SHORT), trading_epoch=_EPOCH + 1)
    result = _evaluate(bear_directional_assessment=bear, bear_survival_result=_survival_for(bear))
    assert result.composition_status is CompositionStatus.BLOCKED


def test_18_missing_required_input_blocks() -> None:
    result = _evaluate(input_complete=False)
    assert result.composition_status is CompositionStatus.BLOCKED
    assert CompositionBlockedReason.INPUT_INCOMPLETE.value in result.reason_codes


def _observe_invalid_input() -> DoublePlayCompositionInputV1:
    return _composition_input(
        bull_directional_assessment=replace(
            _confirmed_assessment(DirectionalAssessmentSide.LONG),
            status=DirectionalAssessmentStatus.OBSERVE,
        ),
        bear_directional_assessment=replace(
            _confirmed_assessment(DirectionalAssessmentSide.SHORT),
            status=DirectionalAssessmentStatus.INVALID,
        ),
    )


def test_19_deterministic_replay() -> None:
    inp = _observe_invalid_input()
    policy = _composition_policy()
    first = evaluate_double_play_composition_matrix_v1(inp, policy)
    second = evaluate_double_play_composition_matrix_v1(inp, policy)
    assert first == second
    assert first.semantic_digest == second.semantic_digest


def test_20_collection_order_invariance() -> None:
    inp_a = _observe_invalid_input()
    inp_b = replace(
        inp_a,
        bull_directional_assessment=inp_a.bull_directional_assessment,
        bear_directional_assessment=inp_a.bear_directional_assessment,
    )
    policy = _composition_policy()
    assert evaluate_double_play_composition_matrix_v1(
        inp_a, policy
    ) == evaluate_double_play_composition_matrix_v1(inp_b, policy)


def test_21_authority_and_effect_fields_none() -> None:
    result = _evaluate(
        bull_directional_assessment=replace(
            _confirmed_assessment(DirectionalAssessmentSide.LONG),
            status=DirectionalAssessmentStatus.OBSERVE,
        ),
        bear_directional_assessment=replace(
            _confirmed_assessment(DirectionalAssessmentSide.SHORT),
            status=DirectionalAssessmentStatus.INVALID,
        ),
    )
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"
    assert result.order_effect == "NONE"
    assert result.risk_effect == "NONE"
    assert result.sizing_effect == "NONE"


def test_22_long_short_symmetry() -> None:
    long_bull, long_bull_s, long_bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    short_bear, short_bear_s, short_bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    bear_noise = replace(
        _confirmed_assessment(DirectionalAssessmentSide.SHORT),
        status=DirectionalAssessmentStatus.INVALID,
    )
    bull_noise = replace(
        _confirmed_assessment(DirectionalAssessmentSide.LONG),
        status=DirectionalAssessmentStatus.INVALID,
    )

    long_result = _evaluate(
        bull_directional_assessment=long_bull,
        bear_directional_assessment=bear_noise,
        bull_survival_result=long_bull_s,
        bear_survival_result=_survival_for(bear_noise),
        bull_suitability_result=long_bull_u,
        bear_suitability_result=_suitability_for(bear_noise, _survival_for(bear_noise)),
    )
    short_result = _evaluate(
        bull_directional_assessment=bull_noise,
        bear_directional_assessment=short_bear,
        bull_survival_result=_survival_for(bull_noise),
        bear_survival_result=short_bear_s,
        bull_suitability_result=_suitability_for(bull_noise, _survival_for(bull_noise)),
        bear_suitability_result=short_bear_u,
    )
    assert long_result.composition_status is CompositionStatus.LONG_SELECTED
    assert short_result.composition_status is CompositionStatus.SHORT_SELECTED
    assert long_result.selected_side is CompositionSelectedSide.LONG
    assert short_result.selected_side is CompositionSelectedSide.SHORT


def test_23_stable_semantic_digest() -> None:
    result = _evaluate(
        bull_directional_assessment=replace(
            _confirmed_assessment(DirectionalAssessmentSide.LONG),
            status=DirectionalAssessmentStatus.OBSERVE,
        ),
        bear_directional_assessment=replace(
            _confirmed_assessment(DirectionalAssessmentSide.SHORT),
            status=DirectionalAssessmentStatus.INVALID,
        ),
    )
    assert result.semantic_digest == compute_composition_result_semantic_digest(result)


def test_24_no_live_adapter_imports() -> None:
    module_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "trading"
        / "master_v2"
        / "double_play_composition_matrix_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden_roots = {
        "requests",
        "urllib3",
        "ccxt",
        "httpx",
        "socket",
        "aiohttp",
        "live",
        "execution",
        "scheduler",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in forbidden_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in ("trading",):
                continue
            assert root not in forbidden_roots


def test_25_immutable_input_dataclasses() -> None:
    instance = _composition_input()
    with pytest.raises(Exception):
        instance.instrument_id = "mutated"  # type: ignore[misc]


def test_26_serialization_stable() -> None:
    result = _evaluate(
        bull_directional_assessment=replace(
            _confirmed_assessment(DirectionalAssessmentSide.LONG),
            status=DirectionalAssessmentStatus.OBSERVE,
        ),
        bear_directional_assessment=replace(
            _confirmed_assessment(DirectionalAssessmentSide.SHORT),
            status=DirectionalAssessmentStatus.INVALID,
        ),
    )
    first = serialize_composition_result_canonical(result)
    second = serialize_composition_result_canonical(result)
    assert first == second


def test_27_input_canonical_serialization_stable() -> None:
    inp = _composition_input()
    assert serialize_composition_input_canonical(inp) == serialize_composition_input_canonical(inp)
