"""S4 tests: single-lane C4 tagged-union composition contract."""

from __future__ import annotations

import pytest

from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionDirectionState,
    CompositionSelectedSide,
    CompositionStatus,
    DoublePlaySingleLaneCompositionInputV1,
    DualCandidateConstructionErrorV1,
    PositionManagementContext,
    SingleLaneCandidateKindV1,
    SingleLaneLongCandidateV1,
    build_single_lane_composition_candidate_v1,
    compute_composition_input_digest,
    evaluate_double_play_composition_matrix_v1,
)
from trading.master_v2.survival_assessment_v1 import SurvivalAssessmentStatus

from tests.trading.master_v2.test_double_play_composition_matrix_v1 import (
    _CONTEXT_REF,
    _EPOCH,
    _INSTRUMENT,
    _composition_policy,
    _side_bundle,
)


def _single_lane_input(candidate, **overrides):
    base = {
        "instrument_id": _INSTRUMENT,
        "trading_epoch": _EPOCH,
        "context_reference": _CONTEXT_REF,
        "candidate": candidate,
        "previous_direction_state": overrides.pop(
            "previous_direction_state",
            CompositionDirectionState.NEUTRAL,
        ),
        "position_management_context": PositionManagementContext.FLAT,
        "last_evaluated_trading_epoch": _EPOCH - 1,
        "input_complete": True,
        "input_digest": "",
        "explicit_blocked_reasons": (),
        "scope_chop_policy_active": False,
        "policy_version": _composition_policy().policy_version,
    }
    base.update(overrides)
    inp = DoublePlaySingleLaneCompositionInputV1(**base)
    return type(inp)(**{**base, "input_digest": compute_composition_input_digest(inp)})


def test_s4_no_direction_is_genuine_absence() -> None:
    candidate = build_single_lane_composition_candidate_v1()
    assert candidate.kind is SingleLaneCandidateKindV1.NO_DIRECTION
    inp = _single_lane_input(candidate)
    result = evaluate_double_play_composition_matrix_v1(inp, _composition_policy())
    assert result.composition_status is CompositionStatus.NO_ACTION
    assert result.selected_side is CompositionSelectedSide.NONE
    assert result.bull_assessment_ref is None
    assert result.bear_assessment_ref is None
    assert result.bull_survival_ref is None
    assert result.bear_survival_ref is None
    assert result.bull_suitability_ref is None
    assert result.bear_suitability_ref is None
    assert "observe" not in result.reason_codes
    assert "blocked" not in result.reason_codes
    assert "invalid" not in result.reason_codes
    assert "no_directional_candidate" in result.reason_codes


def test_s4_dual_candidate_construction_fails_closed() -> None:
    bull_a, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear_a, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    with pytest.raises(DualCandidateConstructionErrorV1, match="DUAL_CANDIDATE"):
        build_single_lane_composition_candidate_v1(
            long_assessment=bull_a,
            long_survival=bull_s,
            long_suitability=bull_u,
            short_assessment=bear_a,
            short_survival=bear_s,
            short_suitability=bear_u,
        )


def test_s4_bull_cannot_admit_short() -> None:
    bear_a, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    with pytest.raises(DualCandidateConstructionErrorV1, match="BULL_CANNOT_ADMIT_SHORT"):
        SingleLaneLongCandidateV1(
            kind=SingleLaneCandidateKindV1.LONG_CANDIDATE,
            directional_assessment=bear_a,
            survival_result=bear_s,
            suitability_result=bear_u,
        )


def test_s4_bear_cannot_admit_long() -> None:
    bull_a, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    with pytest.raises(DualCandidateConstructionErrorV1, match="BEAR_CANNOT_ADMIT_LONG"):
        build_single_lane_composition_candidate_v1(
            short_assessment=bull_a,
            short_survival=bull_s,
            short_suitability=bull_u,
        )


def test_s4_long_candidate_selects_long() -> None:
    bull_a, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    candidate = build_single_lane_composition_candidate_v1(
        long_assessment=bull_a,
        long_survival=bull_s,
        long_suitability=bull_u,
    )
    result = evaluate_double_play_composition_matrix_v1(
        _single_lane_input(candidate),
        _composition_policy(),
    )
    assert result.composition_status is CompositionStatus.LONG_SELECTED
    assert result.selected_side is CompositionSelectedSide.LONG
    assert result.bull_assessment_ref is not None
    assert result.bear_assessment_ref is None
    assert result.conflict_status.value != "both_sides_confirmed"


def test_s4_short_candidate_selects_short() -> None:
    bear_a, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    candidate = build_single_lane_composition_candidate_v1(
        short_assessment=bear_a,
        short_survival=bear_s,
        short_suitability=bear_u,
    )
    result = evaluate_double_play_composition_matrix_v1(
        _single_lane_input(candidate),
        _composition_policy(),
    )
    assert result.composition_status is CompositionStatus.SHORT_SELECTED
    assert result.selected_side is CompositionSelectedSide.SHORT
    assert result.bear_assessment_ref is not None
    assert result.bull_assessment_ref is None


def test_s4_survival_still_gates_selected_lane() -> None:
    bull_a, bull_s, bull_u = _side_bundle(
        DirectionalAssessmentSide.LONG,
        survival_status=SurvivalAssessmentStatus.FAIL,
    )
    result = evaluate_double_play_composition_matrix_v1(
        _single_lane_input(
            build_single_lane_composition_candidate_v1(
                long_assessment=bull_a,
                long_survival=bull_s,
                long_suitability=bull_u,
            )
        ),
        _composition_policy(),
    )
    assert result.composition_status is CompositionStatus.BLOCKED
    assert result.selected_side is CompositionSelectedSide.NONE
    assert "bull_confirmed_survival_not_pass" in result.reason_codes


def test_s4_scope_chop_remains_on_no_direction() -> None:
    result = evaluate_double_play_composition_matrix_v1(
        _single_lane_input(
            build_single_lane_composition_candidate_v1(),
            scope_chop_policy_active=True,
        ),
        _composition_policy(),
    )
    assert result.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    assert result.selected_side is CompositionSelectedSide.NONE
    assert "scope_chop_policy_projection" in result.reason_codes
    assert "both_sides_confirmed" not in result.reason_codes


def test_s4_both_sides_confirmed_unreachable_on_typed_path() -> None:
    bull_a, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    result = evaluate_double_play_composition_matrix_v1(
        _single_lane_input(
            build_single_lane_composition_candidate_v1(
                long_assessment=bull_a,
                long_survival=bull_s,
                long_suitability=bull_u,
            )
        ),
        _composition_policy(),
    )
    assert result.conflict_status.value != "both_sides_confirmed"
    assert result.composition_status is not CompositionStatus.CHOP_GUARD_BLOCK


def test_s4_observe_candidate_does_not_select() -> None:
    bull_a, bull_s, bull_u = _side_bundle(
        DirectionalAssessmentSide.LONG,
        assessment_status=DirectionalAssessmentStatus.CANDIDATE,
    )
    result = evaluate_double_play_composition_matrix_v1(
        _single_lane_input(
            build_single_lane_composition_candidate_v1(
                long_assessment=bull_a,
                long_survival=bull_s,
                long_suitability=bull_u,
            )
        ),
        _composition_policy(),
    )
    assert result.composition_status is CompositionStatus.OBSERVE
    assert result.selected_side is CompositionSelectedSide.NONE
    assert result.bear_assessment_ref is None
