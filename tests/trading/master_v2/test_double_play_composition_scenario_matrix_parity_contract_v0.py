"""Parity contract: scenario adapter vs canonical double_play_composition_matrix_v1."""

from __future__ import annotations

from dataclasses import replace

from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionInput,
    DoublePlayCompositionStatus,
    RequestedSide,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionConflictStatus,
    CompositionSelectedSide,
    CompositionStatus,
    PositionManagementContext,
    compute_composition_input_digest,
)
from trading.master_v2.double_play_composition_scenario_matrix_adapter_v0 import (
    CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER,
    DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER,
    build_scenario_matrix_composition_input_v0,
    compose_double_play_scenario_via_canonical_matrix_v0,
    evaluate_scenario_matrix_composition_v0,
    legacy_and_matrix_composition_parity_aligned_v0,
)
from trading.master_v2.double_play_state import SideState, TransitionDecision
from trading.master_v2.double_play_suitability import (
    SuitabilityProjectionDecision,
    project_strategy_suitability,
)
from trading.master_v2.double_play_survival import evaluate_survival_envelope
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    SYNTHETIC_FUTURES_INSTRUMENT,
    _survival_envelope,
    _suitability_input,
)

_INSTRUMENT = SYNTHETIC_FUTURES_INSTRUMENT
_EPOCH = 44
_CONTEXT = "scenario-matrix-parity-v0"


def _transition() -> TransitionDecision:
    return TransitionDecision(
        allowed=True,
        reason_code="TEST",
        live_authorization_granted=False,
    )


def _survival_ok():
    return evaluate_survival_envelope(_survival_envelope())


def _suitability_both_pools() -> SuitabilityProjectionDecision:
    return project_strategy_suitability(_suitability_input())


def _suitability_neutral_observe() -> SuitabilityProjectionDecision:
    base = _suitability_both_pools()
    proj = replace(base.projection, eligible_for_neutral_pool=True)
    return replace(
        base,
        projection=proj,
        can_enter_neutral_pool=True,
    )


def _legacy_input(
    *,
    side: SideState,
    requested: RequestedSide,
    suitability: SuitabilityProjectionDecision | None = None,
) -> DoublePlayCompositionInput:
    return DoublePlayCompositionInput(
        transition=_transition(),
        resulting_side_state=side,
        survival=_survival_ok(),
        suitability=suitability or _suitability_both_pools(),
        requested_side=requested,
    )


def _adapter_decision(
    *,
    side: SideState,
    requested: RequestedSide,
    suitability: SuitabilityProjectionDecision | None = None,
):
    return compose_double_play_scenario_via_canonical_matrix_v0(
        _legacy_input(side=side, requested=requested, suitability=suitability),
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )


def test_adapter_owner_points_at_canonical_matrix_v0() -> None:
    assert CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER.endswith("double_play_composition_matrix_v1")
    assert DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER.endswith(
        "double_play_composition_scenario_matrix_adapter_v0"
    )


def test_1_bull_confirmed_bear_blocked_long_selected_v0() -> None:
    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        side_st=SideState.LONG_ACTIVE,
        survival=_survival_ok(),
        suitability=_suitability_both_pools(),
    )
    matrix_result = evaluate_scenario_matrix_composition_v0(matrix_input)
    adapter = _adapter_decision(
        side=SideState.LONG_ACTIVE,
        requested=RequestedSide.LONG_BULL,
    )

    assert matrix_result.composition_status is CompositionStatus.LONG_SELECTED
    assert adapter.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    assert legacy_and_matrix_composition_parity_aligned_v0(adapter, matrix_result)


def test_2_bear_confirmed_bull_blocked_short_selected_v0() -> None:
    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        side_st=SideState.SHORT_ACTIVE,
        survival=_survival_ok(),
        suitability=_suitability_both_pools(),
    )
    matrix_result = evaluate_scenario_matrix_composition_v0(matrix_input)
    adapter = _adapter_decision(
        side=SideState.SHORT_ACTIVE,
        requested=RequestedSide.SHORT_BEAR,
    )

    assert matrix_result.composition_status is CompositionStatus.SHORT_SELECTED
    assert adapter.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    assert legacy_and_matrix_composition_parity_aligned_v0(adapter, matrix_result)


def test_3_both_confirmed_chop_guard_block_v0() -> None:
    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        side_st=SideState.CHOP_GUARD_BLOCK,
        survival=_survival_ok(),
        suitability=_suitability_both_pools(),
    )
    matrix_result = evaluate_scenario_matrix_composition_v0(matrix_input)
    adapter = _adapter_decision(
        side=SideState.CHOP_GUARD_BLOCK,
        requested=RequestedSide.NEUTRAL_OBSERVE,
    )

    assert matrix_result.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    assert matrix_result.conflict_status is CompositionConflictStatus.BOTH_SIDES_CONFIRMED
    assert "no_new_entry" in matrix_result.reason_codes
    assert adapter.status is DoublePlayCompositionStatus.CHOP_GUARD


def test_4_both_blocked_observe_no_action_v0() -> None:
    suitability = _suitability_neutral_observe()
    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        side_st=SideState.NEUTRAL_OBSERVE,
        survival=_survival_ok(),
        suitability=suitability,
    )
    matrix_result = evaluate_scenario_matrix_composition_v0(matrix_input)
    adapter = _adapter_decision(
        side=SideState.NEUTRAL_OBSERVE,
        requested=RequestedSide.NEUTRAL_OBSERVE,
        suitability=suitability,
    )

    assert matrix_result.composition_status in (
        CompositionStatus.OBSERVE,
        CompositionStatus.NO_ACTION,
    )
    assert matrix_result.selected_side is CompositionSelectedSide.NONE
    assert adapter.status is DoublePlayCompositionStatus.OBSERVE_ONLY


def test_5_existing_position_reversal_preparation_not_overridden_v0() -> None:
    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        side_st=SideState.LONG_ACTIVE,
        survival=_survival_ok(),
        suitability=_suitability_both_pools(),
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
    )
    matrix_input = replace(
        matrix_input,
        input_digest=compute_composition_input_digest(matrix_input),
    )
    matrix_result = evaluate_scenario_matrix_composition_v0(matrix_input)

    assert matrix_result.composition_status is CompositionStatus.REVERSAL_PREPARATION
    assert "existing_long_position" in matrix_result.reason_codes
    assert "reversal_preparation" in matrix_result.reason_codes


def test_scenario_replay_default_still_passes_v0() -> None:
    from trading.master_v2.offline_double_play_scenario_replay_v0 import (
        OfflineDoublePlayScenarioReplayInputV0,
        build_default_bull_bear_bull_scenario_ticks,
        run_offline_double_play_scenario_replay_v0,
    )

    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision="parity-contract-v0",
            allow_test_scope_event_injection=True,
        )
    )
    assert result.replay_pass, result.fail_reasons
