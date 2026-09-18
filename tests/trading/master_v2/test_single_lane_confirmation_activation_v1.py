"""S1/S2 tests: typed single-lane presence and activation lifecycle."""

from __future__ import annotations

import pytest

from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentStateV1,
    ConfirmationProgressReasonCodeV1,
    ConfirmationProgressStateV1,
    ConfirmationSideV1,
    evaluate_confirmation_progress_v1,
    ConfirmationProgressInputV1,
    ConfirmationAssessmentSignalV1,
    initial_confirmation_progress_state_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationCandidateV1,
    ObservationClassification,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.elementary_direction_v1 import (
    ElementaryDirectionReasonCodeV1,
    ElementaryDirectionStatusV1,
    ElementaryDirectionV1,
    evaluate_elementary_direction_from_observation_acceptance_v1,
    evaluate_elementary_direction_v1,
)
from trading.market_state.observation_identity_v1 import (
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
)
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    non_advancing_observation_acceptance_result_v1,
)
from trading.master_v2.single_lane_confirmation_activation_v1 import (
    InactiveLaneAuthorityErrorV1,
    SingleLaneLifecycleReasonV1,
    SingleLanePresenceKindV1,
    active_single_lane_presence_v1,
    apply_single_lane_confirmation_lifecycle_v1,
    inactive_single_lane_presence_v1,
    persist_single_lane_into_dual_carrier_v1,
    prior_presence_from_dual_carrier_v1,
    selected_lane_from_elementary_direction_v1,
)


def _key() -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id="ETH-USD-SWAP-CANON",
        venue_instrument_id="ETH-USD-SWAP",
    )


def _candidate(*, event_time: float, mark: float) -> ObservationCandidateV1:
    key = _key()
    return ObservationCandidateV1(
        venue=key.venue,
        canonical_instrument_id=key.canonical_instrument_id,
        venue_instrument_id=key.venue_instrument_id,
        venue_event_time=event_time,
        mark_price=mark,
    )


def _eval_c1(state, candidate):
    result = evaluate_distinct_market_observation_v1(state, candidate)
    if result.classification is ObservationClassification.DISTINCT:
        state = commit_observation_acceptance_v1(current_state=state, result=result)
    return result, state


def _lifecycle(*, prior, elementary, acceptor):
    return apply_single_lane_confirmation_lifecycle_v1(
        prior_presence=prior,
        elementary=elementary,
        observation_acceptance_result=acceptor,
        session_id="sess-od1",
        venue="okx_eea",
        instrument=_key(),
    )


def test_s1_bull_selects_long() -> None:
    result = evaluate_elementary_direction_v1(previous_mark=3000.0, current_mark=3001.0)
    assert result.direction is ElementaryDirectionV1.BULL
    assert selected_lane_from_elementary_direction_v1(result) is ConfirmationSideV1.LONG


def test_s1_bear_selects_short() -> None:
    result = evaluate_elementary_direction_v1(previous_mark=3000.0, current_mark=2999.0)
    assert result.direction is ElementaryDirectionV1.BEAR
    assert selected_lane_from_elementary_direction_v1(result) is ConfirmationSideV1.SHORT


def test_s1_neutral_selects_none() -> None:
    result = evaluate_elementary_direction_v1(previous_mark=3000.0, current_mark=3000.0)
    assert result.direction is ElementaryDirectionV1.NEUTRAL
    assert selected_lane_from_elementary_direction_v1(result) is None


def test_s1_inactive_cannot_expose_da_or_c2_authority() -> None:
    presence = inactive_single_lane_presence_v1()
    assert presence.kind is SingleLanePresenceKindV1.INACTIVE
    assert presence.selected_side is None
    assert presence.confirmation_progress is None
    with pytest.raises(InactiveLaneAuthorityErrorV1, match="INACTIVE_HAS_NO_C2_AUTHORITY"):
        presence.authoritative_confirmation_progress()
    with pytest.raises(ValueError, match="INACTIVE_MUST_BE_ABSENCE"):
        type(presence)(
            kind=SingleLanePresenceKindV1.INACTIVE,
            selected_side=ConfirmationSideV1.LONG,
            confirmation_progress=initial_confirmation_progress_state_v1(
                session_id="sess-od1",
                venue="okx_eea",
                instrument=_key(),
                side=ConfirmationSideV1.LONG,
            ),
        )


def test_s1_rejected_cannot_normalize_to_neutral() -> None:
    rejected = evaluate_elementary_direction_v1(previous_mark=None, current_mark=None)
    assert rejected.status is ElementaryDirectionStatusV1.REJECTED
    assert rejected.direction is None
    assert selected_lane_from_elementary_direction_v1(rejected) is None
    acceptor = non_advancing_observation_acceptance_result_v1(bound_instrument_key=_key())
    out = _lifecycle(
        prior=inactive_single_lane_presence_v1(),
        elementary=rejected,
        acceptor=acceptor,
    )
    assert out.identity_status is ElementaryDirectionStatusV1.REJECTED
    assert out.elementary_direction is None
    assert out.selected_side is None
    assert out.presence.kind is SingleLanePresenceKindV1.INACTIVE
    assert out.reason_code == SingleLaneLifecycleReasonV1.REJECTED_NO_LANE.value
    assert out.reason_code != ElementaryDirectionV1.NEUTRAL.value


def test_s2_neutral_to_neutral_no_lane_no_eval() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    second, _ = _eval_c1(c1, _candidate(event_time=1001.0, mark=10.0))
    elementary = evaluate_elementary_direction_from_observation_acceptance_v1(
        second, bound_instrument_key=_key(), current_mark=10.0
    )
    assert elementary.direction is ElementaryDirectionV1.NEUTRAL
    out = _lifecycle(
        prior=inactive_single_lane_presence_v1(),
        elementary=elementary,
        acceptor=second,
    )
    assert out.presence.kind is SingleLanePresenceKindV1.INACTIVE
    assert out.selected_side is None
    assert out.activated_new_sequence is False
    assert out.reason_code == SingleLaneLifecycleReasonV1.NEUTRAL_NO_LANE.value


def test_s2_neutral_to_bull_activates_long_at_c1_state_before() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    second, _ = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    elementary = evaluate_elementary_direction_from_observation_acceptance_v1(
        second, bound_instrument_key=_key(), current_mark=11.0
    )
    assert elementary.direction is ElementaryDirectionV1.BULL
    out = _lifecycle(
        prior=inactive_single_lane_presence_v1(),
        elementary=elementary,
        acceptor=second,
    )
    assert out.presence.kind is SingleLanePresenceKindV1.ACTIVE
    assert out.selected_side is ConfirmationSideV1.LONG
    assert out.activated_new_sequence is True
    prior = out.presence.authoritative_confirmation_progress()
    assert prior.side is ConfirmationSideV1.LONG
    assert (
        prior.latest_accepted_market_observation_epoch
        == second.state_before.market_observation_epoch
    )
    progressed = evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=prior,
            observation_acceptance_result=second,
            session_id="sess-od1",
            venue="okx_eea",
            instrument=_key(),
            side=ConfirmationSideV1.LONG,
            assessment_signal=ConfirmationAssessmentSignalV1.CONFIRMED,
            confirmation_threshold=2,
        )
    )
    assert progressed.fail_closed is False
    assert progressed.reason_code is not ConfirmationProgressReasonCodeV1.EPOCH_GAP
    assert (
        progressed.state_after.latest_accepted_market_observation_epoch
        == second.state_after.market_observation_epoch
    )
    assert progressed.confirmation_advanced is True
    assert progressed.state_after.distinct_confirmation_observation_count == 1


def test_s2_bull_to_bull_continues_canonical_c2() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    second, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    elementary_bull = evaluate_elementary_direction_from_observation_acceptance_v1(
        second, bound_instrument_key=_key(), current_mark=11.0
    )
    activated = _lifecycle(
        prior=inactive_single_lane_presence_v1(),
        elementary=elementary_bull,
        acceptor=second,
    )
    progressed = evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=activated.presence.authoritative_confirmation_progress(),
            observation_acceptance_result=second,
            session_id="sess-od1",
            venue="okx_eea",
            instrument=_key(),
            side=ConfirmationSideV1.LONG,
            assessment_signal=ConfirmationAssessmentSignalV1.CONFIRMED,
            confirmation_threshold=2,
        )
    )
    continued_presence = active_single_lane_presence_v1(
        selected_side=ConfirmationSideV1.LONG,
        confirmation_progress=progressed.state_after,
    )
    third, _ = _eval_c1(c1, _candidate(event_time=1002.0, mark=12.0))
    elementary_still_bull = evaluate_elementary_direction_from_observation_acceptance_v1(
        third, bound_instrument_key=_key(), current_mark=12.0
    )
    continued = _lifecycle(
        prior=continued_presence,
        elementary=elementary_still_bull,
        acceptor=third,
    )
    assert continued.activated_new_sequence is False
    assert continued.reason_code == SingleLaneLifecycleReasonV1.CONTINUE_SELECTED_LANE.value
    assert continued.presence.authoritative_confirmation_progress() is progressed.state_after


def test_s2_bull_to_neutral_discards_long() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    second, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    activated = _lifecycle(
        prior=inactive_single_lane_presence_v1(),
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            second, bound_instrument_key=_key(), current_mark=11.0
        ),
        acceptor=second,
    )
    confirmed = ConfirmationProgressStateV1(
        session_id="sess-od1",
        venue="okx_eea",
        instrument=_key(),
        side=ConfirmationSideV1.LONG,
        assessment_state=ConfirmationAssessmentStateV1.CONFIRMED,
        latest_accepted_market_observation_epoch=second.state_after.market_observation_epoch,
        candidate_started_at_epoch=second.state_after.market_observation_epoch,
        distinct_confirmation_observation_count=1,
        last_processed_acceptor_result_fingerprint="abc",
    )
    stale = active_single_lane_presence_v1(
        selected_side=ConfirmationSideV1.LONG,
        confirmation_progress=confirmed,
    )
    third, _ = _eval_c1(c1, _candidate(event_time=1002.0, mark=11.0))
    discarded = _lifecycle(
        prior=stale,
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            third, bound_instrument_key=_key(), current_mark=11.0
        ),
        acceptor=third,
    )
    assert discarded.presence.kind is SingleLanePresenceKindV1.INACTIVE
    assert discarded.discarded_prior_authority is True
    assert discarded.selected_side is None


def test_s2_bull_to_bear_discards_long_activates_new_short() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    second, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    third, _ = _eval_c1(c1, _candidate(event_time=1002.0, mark=9.0))
    stale_long = ConfirmationProgressStateV1(
        session_id="sess-od1",
        venue="okx_eea",
        instrument=_key(),
        side=ConfirmationSideV1.LONG,
        assessment_state=ConfirmationAssessmentStateV1.CONFIRMED,
        latest_accepted_market_observation_epoch=second.state_after.market_observation_epoch,
        candidate_started_at_epoch=second.state_after.market_observation_epoch,
        distinct_confirmation_observation_count=2,
        last_processed_acceptor_result_fingerprint="stale-long",
    )
    switched = _lifecycle(
        prior=active_single_lane_presence_v1(
            selected_side=ConfirmationSideV1.LONG,
            confirmation_progress=stale_long,
        ),
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            third, bound_instrument_key=_key(), current_mark=9.0
        ),
        acceptor=third,
    )
    assert switched.selected_side is ConfirmationSideV1.SHORT
    assert switched.discarded_prior_authority is True
    assert switched.activated_new_sequence is True
    new_short = switched.presence.authoritative_confirmation_progress()
    assert new_short.side is ConfirmationSideV1.SHORT
    assert new_short.assessment_state is ConfirmationAssessmentStateV1.OBSERVE
    assert new_short.distinct_confirmation_observation_count == 0
    assert new_short.last_processed_acceptor_result_fingerprint is None
    assert (
        new_short.latest_accepted_market_observation_epoch
        == third.state_before.market_observation_epoch
    )


def test_s2_bear_to_bear_continues_short() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=12.0))
    second, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    activated = _lifecycle(
        prior=inactive_single_lane_presence_v1(),
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            second, bound_instrument_key=_key(), current_mark=11.0
        ),
        acceptor=second,
    )
    assert activated.selected_side is ConfirmationSideV1.SHORT
    third, _ = _eval_c1(c1, _candidate(event_time=1002.0, mark=10.0))
    continued = _lifecycle(
        prior=activated.presence,
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            third, bound_instrument_key=_key(), current_mark=10.0
        ),
        acceptor=third,
    )
    assert continued.reason_code == SingleLaneLifecycleReasonV1.CONTINUE_SELECTED_LANE.value
    assert continued.selected_side is ConfirmationSideV1.SHORT


def test_s2_bear_to_neutral_discards_short() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=12.0))
    second, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    third, _ = _eval_c1(c1, _candidate(event_time=1002.0, mark=11.0))
    activated = _lifecycle(
        prior=inactive_single_lane_presence_v1(),
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            second, bound_instrument_key=_key(), current_mark=11.0
        ),
        acceptor=second,
    )
    discarded = _lifecycle(
        prior=activated.presence,
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            third, bound_instrument_key=_key(), current_mark=11.0
        ),
        acceptor=third,
    )
    assert discarded.presence.kind is SingleLanePresenceKindV1.INACTIVE
    assert discarded.discarded_prior_authority is True


def test_s2_bear_to_bull_discards_short_activates_new_long() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=12.0))
    second, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    third, _ = _eval_c1(c1, _candidate(event_time=1002.0, mark=13.0))
    activated = _lifecycle(
        prior=inactive_single_lane_presence_v1(),
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            second, bound_instrument_key=_key(), current_mark=11.0
        ),
        acceptor=second,
    )
    switched = _lifecycle(
        prior=activated.presence,
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            third, bound_instrument_key=_key(), current_mark=13.0
        ),
        acceptor=third,
    )
    assert switched.selected_side is ConfirmationSideV1.LONG
    assert switched.discarded_prior_authority is True
    assert switched.activated_new_sequence is True
    assert (
        switched.presence.authoritative_confirmation_progress().latest_accepted_market_observation_epoch
        == third.state_before.market_observation_epoch
    )


def test_s2_inactivity_then_reactivation_does_not_manufacture_epoch_gap() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    second, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    third, c1 = _eval_c1(c1, _candidate(event_time=1002.0, mark=11.0))
    fourth, _ = _eval_c1(c1, _candidate(event_time=1003.0, mark=12.0))
    bull = _lifecycle(
        prior=inactive_single_lane_presence_v1(),
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            second, bound_instrument_key=_key(), current_mark=11.0
        ),
        acceptor=second,
    )
    progressed = evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=bull.presence.authoritative_confirmation_progress(),
            observation_acceptance_result=second,
            session_id="sess-od1",
            venue="okx_eea",
            instrument=_key(),
            side=ConfirmationSideV1.LONG,
            assessment_signal=ConfirmationAssessmentSignalV1.CONFIRMED,
            confirmation_threshold=2,
        )
    )
    assert progressed.state_after.assessment_state is ConfirmationAssessmentStateV1.CANDIDATE
    after_neutral = _lifecycle(
        prior=active_single_lane_presence_v1(
            selected_side=ConfirmationSideV1.LONG,
            confirmation_progress=progressed.state_after,
        ),
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            third, bound_instrument_key=_key(), current_mark=11.0
        ),
        acceptor=third,
    )
    assert after_neutral.presence.kind is SingleLanePresenceKindV1.INACTIVE
    reactivated = _lifecycle(
        prior=after_neutral.presence,
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            fourth, bound_instrument_key=_key(), current_mark=12.0
        ),
        acceptor=fourth,
    )
    assert reactivated.activated_new_sequence is True
    assert reactivated.presence.authoritative_confirmation_progress().assessment_state is (
        ConfirmationAssessmentStateV1.OBSERVE
    )
    resumed = evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=reactivated.presence.authoritative_confirmation_progress(),
            observation_acceptance_result=fourth,
            session_id="sess-od1",
            venue="okx_eea",
            instrument=_key(),
            side=ConfirmationSideV1.LONG,
            assessment_signal=ConfirmationAssessmentSignalV1.CONFIRMED,
            confirmation_threshold=2,
        )
    )
    assert resumed.fail_closed is False
    assert resumed.reason_code is not ConfirmationProgressReasonCodeV1.EPOCH_GAP
    assert resumed.state_after.distinct_confirmation_observation_count == 1
    assert resumed.state_after.assessment_state is ConfirmationAssessmentStateV1.CANDIDATE


def test_s2_identity_change_without_distinct_produces_no_activation() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    second, _ = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    activated = _lifecycle(
        prior=inactive_single_lane_presence_v1(),
        elementary=evaluate_elementary_direction_from_observation_acceptance_v1(
            second, bound_instrument_key=_key(), current_mark=11.0
        ),
        acceptor=second,
    )
    non_distinct = non_advancing_observation_acceptance_result_v1(
        bound_instrument_key=_key(),
        market_observation_epoch=second.state_after.market_observation_epoch,
    )
    bear_identity = evaluate_elementary_direction_v1(previous_mark=11.0, current_mark=9.0)
    out = _lifecycle(
        prior=activated.presence,
        elementary=bear_identity,
        acceptor=non_distinct,
    )
    assert out.presence.kind is SingleLanePresenceKindV1.INACTIVE
    assert out.activated_new_sequence is False
    assert out.reason_code == SingleLaneLifecycleReasonV1.IDENTITY_CHANGE_WITHOUT_DISTINCT.value


def test_s2_dual_carrier_padding_is_not_authoritative() -> None:
    presence = inactive_single_lane_presence_v1()
    carrier = persist_single_lane_into_dual_carrier_v1(
        presence=presence,
        session_id="sess-od1",
        venue="okx_eea",
        instrument=_key(),
        padding_epoch=MarketObservationEpoch(value=0),
    )
    decoded = prior_presence_from_dual_carrier_v1(carrier)
    assert decoded.kind is SingleLanePresenceKindV1.INACTIVE
    assert decoded.confirmation_progress is None
