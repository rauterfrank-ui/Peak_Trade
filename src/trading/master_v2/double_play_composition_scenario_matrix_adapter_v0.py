# src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py
"""
Scenario replay adapter: routes Double Play composition through the canonical
``double_play_composition_matrix_v1`` owner while preserving the legacy
``DoublePlayCompositionDecision`` envelope for scenario replay consumers.

No runtime authority, no semantic extension — wiring-only parity slice.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional, Tuple

from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
    DirectionalAssessmentV1,
    ScopeEventRefV1,
)
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionBlockReason,
    DoublePlayCompositionDecision,
    DoublePlayCompositionInput,
    DoublePlayCompositionStatus,
    RequestedSide,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    BothCandidateOutcome,
    BothInvalidOutcome,
    CompositionStatus,
    CompositionDirectionState,
    DoublePlayCompositionInputV1,
    DoublePlayCompositionPolicyV1,
    DoublePlayCompositionResultV1,
    PositionManagementContext,
    compute_composition_input_digest,
    evaluate_double_play_composition_matrix_v1,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.double_play_suitability import (
    SuitabilityClass,
    SuitabilityProjectionDecision,
)
from trading.master_v2.double_play_survival import (
    SurvivalEnvelopeDecision,
    SurvivalEnvelopeStatus,
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

DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_LAYER_VERSION = "v0"
DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER = (
    "trading.master_v2.double_play_composition_scenario_matrix_adapter_v0"
)
CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER = "trading.master_v2.double_play_composition_matrix_v1"

_STUB_DIGEST = "a" * 64
_DEFAULT_POLICY = DoublePlayCompositionPolicyV1(
    validity_epochs=3,
    both_candidate_outcome=BothCandidateOutcome.OBSERVE,
    both_invalid_outcome=BothInvalidOutcome.BLOCKED,
    policy_version=DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
)


def _apply_legacy_pre_matrix_gates(
    inp: DoublePlayCompositionInput,
) -> Optional[DoublePlayCompositionDecision]:
    tr = inp.transition
    side_st = inp.resulting_side_state
    surv = inp.survival
    suit = inp.suitability
    proj = suit.projection
    req = inp.requested_side
    rat = inp.capital_slot_ratchet_decision
    rel = inp.capital_slot_release_decision

    if (
        tr.live_authorization_granted
        or suit.live_authorization
        or proj.live_authorization
        or surv.live_authorization
        or (rat is not None and rat.live_authorization)
        or (rel is not None and rel.live_authorization)
    ):
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.LIVE_NOT_AUTHORIZED,),
            reason="Live authorization must not be asserted on sub-decisions; fail closed.",
            live_authorization=False,
        )

    if side_st == SideState.KILL_ALL:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.KILL_ALL,
            block_reasons=(DoublePlayCompositionBlockReason.STATE_KILL_ALL,),
            reason="State is KILL_ALL; no new activation.",
            live_authorization=False,
        )

    if side_st == SideState.CHOP_GUARD_BLOCK:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.CHOP_GUARD,
            block_reasons=(DoublePlayCompositionBlockReason.STATE_CHOP_GUARD,),
            reason="Chop guard blocks new activation.",
            live_authorization=False,
        )

    if surv.status == SurvivalEnvelopeStatus.BLOCKED or not surv.pre_authorization_eligible:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.SURVIVAL_BLOCKED,),
            reason="Survival envelope blocks composition.",
            live_authorization=False,
        )

    sc = proj.suitability_class
    if sc == SuitabilityClass.UNKNOWN_SUITABILITY:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.SUITABILITY_UNKNOWN,),
            reason="Suitability unknown; fail closed.",
            live_authorization=False,
        )

    if sc == SuitabilityClass.DISABLED_FOR_CANDIDATE:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.SUITABILITY_DISABLED,),
            reason="Suitability disabled for candidate.",
            live_authorization=False,
        )

    if req == RequestedSide.LONG_BULL and not suit.can_enter_long_bull_pool:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
            reason="Requested Long/Bull but suitability does not allow long/bull pool.",
            live_authorization=False,
        )

    if req == RequestedSide.SHORT_BEAR and not suit.can_enter_short_bear_pool:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
            reason="Requested Short/Bear but suitability does not allow short/bear pool.",
            live_authorization=False,
        )

    if req == RequestedSide.NEUTRAL_OBSERVE and not suit.can_enter_neutral_pool:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
            reason="Requested neutral observe but suitability does not allow neutral pool.",
            live_authorization=False,
        )

    if (
        req in (RequestedSide.LONG_BULL, RequestedSide.SHORT_BEAR)
        and side_st == SideState.NEUTRAL_OBSERVE
    ):
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.STATE_NOT_ACTIVE_OR_ARMED,),
            reason="Directional request while state is neutral observe; not active/armed.",
            live_authorization=False,
        )

    if req == RequestedSide.NEUTRAL_OBSERVE and side_st == SideState.NEUTRAL_OBSERVE:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.OBSERVE_ONLY,
            block_reasons=(),
            reason="Neutral observe path; model-level observe only.",
            live_authorization=False,
        )

    return None


def _apply_legacy_capital_slot_overlay(
    inp: DoublePlayCompositionInput,
    *,
    matrix_status: CompositionStatus,
) -> DoublePlayCompositionDecision:
    req = inp.requested_side
    rat = inp.capital_slot_ratchet_decision
    rel = inp.capital_slot_release_decision

    if rel is not None and rel.released:
        if req in (RequestedSide.LONG_BULL, RequestedSide.SHORT_BEAR):
            return DoublePlayCompositionDecision(
                status=DoublePlayCompositionStatus.BLOCKED,
                block_reasons=(DoublePlayCompositionBlockReason.CAPITAL_SLOT_RELEASED,),
                reason=(
                    "Capital slot released (inactivity or opportunity cost); "
                    "no directional model eligibility."
                ),
                live_authorization=False,
            )
        if req == RequestedSide.NEUTRAL_OBSERVE:
            return DoublePlayCompositionDecision(
                status=DoublePlayCompositionStatus.OBSERVE_ONLY,
                block_reasons=(),
                reason="Capital slot released; neutral observe only (model-level).",
                live_authorization=False,
            )

    if rat is not None and rat.block_reasons:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.CAPITAL_SLOT_RATCHET_BLOCKED,),
            reason="Capital slot ratchet pre-authorization blocked.",
            live_authorization=False,
        )

    if matrix_status is CompositionStatus.CHOP_GUARD_BLOCK:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.CHOP_GUARD,
            block_reasons=(DoublePlayCompositionBlockReason.STATE_CHOP_GUARD,),
            reason="Canonical matrix chop guard blocks new activation.",
            live_authorization=False,
        )

    if matrix_status in (CompositionStatus.OBSERVE, CompositionStatus.NO_ACTION):
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.OBSERVE_ONLY,
            block_reasons=(),
            reason="Canonical matrix observe-only coordination.",
            live_authorization=False,
        )

    if matrix_status is CompositionStatus.BLOCKED:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
            reason="Canonical matrix blocked coordination.",
            live_authorization=False,
        )

    if matrix_status in (CompositionStatus.LONG_SELECTED, CompositionStatus.SHORT_SELECTED):
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
            block_reasons=(),
            reason="All pure gates pass; model-only eligibility (not trading permission).",
            live_authorization=False,
        )

    if matrix_status is CompositionStatus.REVERSAL_PREPARATION:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
            block_reasons=(),
            reason="Reversal preparation; model-only eligibility (not trading permission).",
            live_authorization=False,
        )

    return DoublePlayCompositionDecision(
        status=DoublePlayCompositionStatus.BLOCKED,
        block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
        reason=f"Unhandled canonical matrix status: {matrix_status.value}",
        live_authorization=False,
    )


def _legacy_side_to_assessment_statuses(
    side_st: SideState,
) -> Tuple[DirectionalAssessmentStatus, DirectionalAssessmentStatus]:
    if side_st == SideState.CHOP_GUARD_BLOCK:
        return (
            DirectionalAssessmentStatus.CONFIRMED,
            DirectionalAssessmentStatus.CONFIRMED,
        )
    if side_st in (SideState.LONG_ACTIVE, SideState.LONG_ARMED):
        return (
            DirectionalAssessmentStatus.CONFIRMED,
            DirectionalAssessmentStatus.OBSERVE,
        )
    if side_st in (SideState.SHORT_ACTIVE, SideState.SHORT_ARMED):
        return (
            DirectionalAssessmentStatus.OBSERVE,
            DirectionalAssessmentStatus.CONFIRMED,
        )
    if side_st == SideState.LONG_BLOCKED:
        return (
            DirectionalAssessmentStatus.BLOCKED,
            DirectionalAssessmentStatus.OBSERVE,
        )
    if side_st == SideState.SHORT_BLOCKED:
        return (
            DirectionalAssessmentStatus.OBSERVE,
            DirectionalAssessmentStatus.BLOCKED,
        )
    if side_st == SideState.SWITCH_LONG_TO_SHORT_PENDING:
        return (
            DirectionalAssessmentStatus.OBSERVE,
            DirectionalAssessmentStatus.CANDIDATE,
        )
    if side_st == SideState.SWITCH_SHORT_TO_LONG_PENDING:
        return (
            DirectionalAssessmentStatus.CANDIDATE,
            DirectionalAssessmentStatus.OBSERVE,
        )
    return (
        DirectionalAssessmentStatus.OBSERVE,
        DirectionalAssessmentStatus.OBSERVE,
    )


def _position_management_context(side_st: SideState) -> PositionManagementContext:
    if side_st in (SideState.LONG_ACTIVE, SideState.LONG_ARMED, SideState.LONG_BLOCKED):
        return PositionManagementContext.LONG_POSITION
    if side_st in (SideState.SHORT_ACTIVE, SideState.SHORT_ARMED, SideState.SHORT_BLOCKED):
        return PositionManagementContext.SHORT_POSITION
    return PositionManagementContext.FLAT


def _previous_direction_state(side_st: SideState) -> CompositionDirectionState:
    if side_st in (SideState.LONG_ACTIVE, SideState.LONG_ARMED, SideState.LONG_BLOCKED):
        return CompositionDirectionState.LONG
    if side_st in (SideState.SHORT_ACTIVE, SideState.SHORT_ARMED, SideState.SHORT_BLOCKED):
        return CompositionDirectionState.SHORT
    return CompositionDirectionState.NEUTRAL


def _stub_directional_assessment(
    *,
    side: DirectionalAssessmentSide,
    status: DirectionalAssessmentStatus,
    instrument_id: str,
    trading_epoch: int,
) -> DirectionalAssessmentV1:
    side_label = "long" if side is DirectionalAssessmentSide.LONG else "short"
    return DirectionalAssessmentV1(
        assessment_id=f"scenario-{side_label}-{trading_epoch}",
        side=side,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        status=status,
        signal_strength=0.02 if status is DirectionalAssessmentStatus.CONFIRMED else 0.0,
        confidence=0.9 if status is DirectionalAssessmentStatus.CONFIRMED else 0.1,
        feature_refs=("scenario-replay-v0",),
        scope_event_ref=ScopeEventRefV1(
            scope_event_id=f"scope-{instrument_id}-{trading_epoch}",
            semantic_digest=_STUB_DIGEST,
            event_type="noop",
            trading_epoch=trading_epoch - 1,
        ),
        survival_preconditions=("scenario_replay_ref_only",),
        hard_block_reasons=(),
        reason_codes=(f"scenario_{side_label}_{status.value}",),
        valid_until_epoch=trading_epoch + 3,
        semantic_digest=_STUB_DIGEST,
    )


def _survival_policy() -> SurvivalAssessmentPolicyV1:
    return SurvivalAssessmentPolicyV1(
        min_net_edge=0.001,
        min_volatility_survival_ratio=0.5,
        min_sequence_survival_ratio=0.5,
        min_drawdown_survival_ratio=0.5,
        min_liquidation_buffer_ratio=0.1,
        validity_epochs=3,
        policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
    )


def _scenario_survival_for(
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


def _strategy_entry(side: DirectionalAssessmentSide) -> SuitabilityStrategyEntryV1:
    return SuitabilityStrategyEntryV1(
        strategy_id="scenario-replay-v0",
        supported_regime_ids=("trending",),
        supported_sides=(side,),
        priority_rank=10,
        disabled=False,
        confidence_score=0.75,
    )


def _scenario_suitability_for(
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


def build_scenario_matrix_composition_input_v0(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    side_st: SideState,
    survival: SurvivalEnvelopeDecision,
    suitability: SuitabilityProjectionDecision,
) -> DoublePlayCompositionInputV1:
    bull_status, bear_status = _legacy_side_to_assessment_statuses(side_st)
    bull = _stub_directional_assessment(
        side=DirectionalAssessmentSide.LONG,
        status=bull_status,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
    )
    bear = _stub_directional_assessment(
        side=DirectionalAssessmentSide.SHORT,
        status=bear_status,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
    )

    survival_status = (
        SurvivalAssessmentStatus.PASS
        if survival.status is SurvivalEnvelopeStatus.OK and survival.pre_authorization_eligible
        else SurvivalAssessmentStatus.FAIL
    )
    bull_survival = _scenario_survival_for(bull, status=survival_status)
    bear_survival = _scenario_survival_for(bear, status=survival_status)

    bull_suit_status = (
        SuitabilityBindingStatus.PASS
        if suitability.can_enter_long_bull_pool
        else SuitabilityBindingStatus.BLOCKED
    )
    bear_suit_status = (
        SuitabilityBindingStatus.PASS
        if suitability.can_enter_short_bear_pool
        else SuitabilityBindingStatus.BLOCKED
    )
    bull_suit = _scenario_suitability_for(bull, bull_survival, status=bull_suit_status)
    bear_suit = _scenario_suitability_for(bear, bear_survival, status=bear_suit_status)

    raw = DoublePlayCompositionInputV1(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_survival,
        bear_survival_result=bear_survival,
        bull_suitability_result=bull_suit,
        bear_suitability_result=bear_suit,
        previous_direction_state=_previous_direction_state(side_st),
        position_management_context=_position_management_context(side_st),
        last_evaluated_trading_epoch=trading_epoch - 1,
        input_complete=True,
        input_digest="",
        explicit_blocked_reasons=(),
        policy_version=DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    )
    return replace(raw, input_digest=compute_composition_input_digest(raw))


def evaluate_scenario_matrix_composition_v0(
    matrix_input: DoublePlayCompositionInputV1,
    *,
    policy: DoublePlayCompositionPolicyV1 | None = None,
) -> DoublePlayCompositionResultV1:
    return evaluate_double_play_composition_matrix_v1(
        matrix_input,
        policy or _DEFAULT_POLICY,
    )


def compose_double_play_scenario_via_canonical_matrix_v0(
    inp: DoublePlayCompositionInput,
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    policy: DoublePlayCompositionPolicyV1 | None = None,
) -> DoublePlayCompositionDecision:
    pre = _apply_legacy_pre_matrix_gates(inp)
    if pre is not None:
        return pre

    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        side_st=inp.resulting_side_state,
        survival=inp.survival,
        suitability=inp.suitability,
    )
    matrix_result = evaluate_scenario_matrix_composition_v0(matrix_input, policy=policy)
    return _apply_legacy_capital_slot_overlay(
        inp,
        matrix_status=matrix_result.composition_status,
    )


def legacy_and_matrix_composition_parity_aligned_v0(
    legacy: DoublePlayCompositionDecision,
    matrix_result: DoublePlayCompositionResultV1,
) -> bool:
    status_map = {
        CompositionStatus.LONG_SELECTED: DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
        CompositionStatus.SHORT_SELECTED: DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
        CompositionStatus.CHOP_GUARD_BLOCK: DoublePlayCompositionStatus.CHOP_GUARD,
        CompositionStatus.OBSERVE: DoublePlayCompositionStatus.OBSERVE_ONLY,
        CompositionStatus.NO_ACTION: DoublePlayCompositionStatus.OBSERVE_ONLY,
        CompositionStatus.BLOCKED: DoublePlayCompositionStatus.BLOCKED,
        CompositionStatus.REVERSAL_PREPARATION: DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
    }
    expected = status_map.get(matrix_result.composition_status)
    if expected is None:
        return False
    return legacy.status is expected
