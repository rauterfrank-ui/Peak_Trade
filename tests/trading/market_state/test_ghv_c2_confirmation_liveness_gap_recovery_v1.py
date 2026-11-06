"""GHV C2 confirmation liveness gap-recovery regression (MOE 2..13 geometry)."""

from __future__ import annotations

from typing import List, Tuple

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationAcceptanceStateV1,
    ObservationCandidateV1,
    ObservationTransportMetadataV1,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentSignalV1,
    ConfirmationAssessmentStateV1,
    ConfirmationProgressInputV1,
    ConfirmationProgressReasonCodeV1,
    ConfirmationProgressResultV1,
    ConfirmationProgressStateV1,
    ConfirmationSideV1,
    evaluate_confirmation_progress_v1,
    initial_confirmation_progress_state_v1,
)
from trading.market_state.observation_identity_v1 import (
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
)


def _key() -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id="okx_eea:linear_perpetual:CAP:USDT:USDT:cap-usdt-swap",
        venue_instrument_id="okx_eea:linear_perpetual:CAP:USDT:USDT:cap-usdt-swap",
    )


def _candidate(*, event_time: float, mark: float) -> ObservationCandidateV1:
    return ObservationCandidateV1(
        venue="okx_eea",
        canonical_instrument_id="okx_eea:linear_perpetual:CAP:USDT:USDT:cap-usdt-swap",
        venue_instrument_id="okx_eea:linear_perpetual:CAP:USDT:USDT:cap-usdt-swap",
        venue_event_time=event_time,
        mark_price=mark,
        transport=ObservationTransportMetadataV1(
            receive_time=event_time + 1.0,
            poll_attempt=1,
            runtime_cycle_index=None,
        ),
    )


def _eval_c1(
    state: ObservationAcceptanceStateV1,
    candidate: ObservationCandidateV1,
) -> Tuple[ObservationAcceptanceResultV1, ObservationAcceptanceStateV1]:
    result = evaluate_distinct_market_observation_v1(state, candidate)
    committed = commit_observation_acceptance_v1(current_state=state, result=result)
    return result, committed


def _long_progress(
    prior: ConfirmationProgressStateV1,
    acceptor: ObservationAcceptanceResultV1,
    *,
    signal: ConfirmationAssessmentSignalV1 = ConfirmationAssessmentSignalV1.CONFIRMED,
    fingerprint: str | None = None,
) -> ConfirmationProgressResultV1:
    return evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=prior,
            observation_acceptance_result=acceptor,
            session_id=prior.session_id,
            venue=prior.venue,
            instrument=prior.instrument,
            side=ConfirmationSideV1.LONG,
            assessment_signal=signal,
            confirmation_threshold=2,
            acceptor_result_fingerprint=fingerprint,
        )
    )


def _long_state(*, epoch: int = 0) -> ConfirmationProgressStateV1:
    return initial_confirmation_progress_state_v1(
        session_id="ghv-sess",
        venue="okx_eea",
        instrument=_key(),
        side=ConfirmationSideV1.LONG,
        initial_market_observation_epoch=MarketObservationEpoch(value=epoch),
    )


def _build_moe_chain() -> List[ObservationAcceptanceResultV1]:
    """Twelve distinct C1 steps producing MOE 2..13 (GHV event-time cadence)."""
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    # Productive GHV bootstrap consumed MOE 1 before the twelve S5 cycles.
    _, c1 = _eval_c1(c1, _candidate(event_time=1790907360.0, mark=0.07376))
    marks = [
        (1790907420.0, 0.07377),
        (1790907480.0, 0.07375),
        (1790907540.0, 0.07432),
        (1790907600.0, 0.07459),
        (1790907660.0, 0.07490),
        (1790907720.0, 0.07588),
        (1790907780.0, 0.07622),
        (1790907840.0, 0.07703),
        (1790907900.0, 0.07691),
        (1790907960.0, 0.07694),
        (1790908020.0, 0.07668),
        (1790908080.0, 0.07700),
    ]
    acceptors: List[ObservationAcceptanceResultV1] = []
    for event_time, mark in marks:
        result, c1 = _eval_c1(c1, _candidate(event_time=event_time, mark=mark))
        acceptors.append(result)
    assert acceptors[0].state_after.market_observation_epoch.value == 2
    assert acceptors[-1].state_after.market_observation_epoch.value == 13
    return acceptors


def test_ghv_geometry_long_e_opposite_e_plus_one_long_e_plus_two_gap_recovery() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    e1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    e2, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    e3, _ = _eval_c1(c1, _candidate(event_time=1002.0, mark=12.0))
    assert e1.state_after.market_observation_epoch.value == 1
    assert e2.state_after.market_observation_epoch.value == 2
    assert e3.state_after.market_observation_epoch.value == 3

    long_state = _long_state()
    step_e = _long_progress(long_state, e1)
    assert step_e.reason_code is ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_PROGRESS
    assert step_e.state_after.distinct_confirmation_observation_count == 1

    step_e_plus_2 = _long_progress(step_e.state_after, e3)  # opposite @ E+1 skipped
    assert (
        step_e_plus_2.reason_code is ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_GAP_RECOVERY
    )
    assert step_e_plus_2.fail_closed is False
    assert step_e_plus_2.state_after.distinct_confirmation_observation_count == 1
    assert (
        step_e_plus_2.state_after.latest_accepted_market_observation_epoch.value
        == e3.state_after.market_observation_epoch.value
    )


def test_ghv_geometry_not_poisoned_after_first_gap_two_step_confirm() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    acceptors = []
    for idx in range(5):
        result, c1 = _eval_c1(c1, _candidate(event_time=1000.0 + idx, mark=10.0 + idx))
        acceptors.append(result)
    e, e1, e2, e3, e4 = acceptors
    long_state = _long_state()
    at_e = _long_progress(long_state, e)
    at_e2 = _long_progress(at_e.state_after, e2)
    assert at_e2.reason_code is ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_GAP_RECOVERY
    at_e3 = _long_progress(at_e2.state_after, e3)
    assert at_e3.reason_code is ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_CONFIRMED
    assert at_e3.state_after.distinct_confirmation_observation_count == 2
    assert at_e3.state_after.assessment_state is ConfirmationAssessmentStateV1.CONFIRMED
    hold = _long_progress(at_e3.state_after, e4)
    assert hold.state_after.assessment_state is ConfirmationAssessmentStateV1.CONFIRMED
    assert hold.state_after.distinct_confirmation_observation_count == 2


def test_ghv_12_cycle_semantics_before_would_stall_after_repair_recovers_at_moe_5() -> None:
    acceptors = _build_moe_chain()
    long_state = _long_state()
    # MOE 2 long (cycle 1)
    r1 = _long_progress(long_state, acceptors[0])
    assert r1.state_after.distinct_confirmation_observation_count == 1
    # MOE 3 short-only in GHV — skip long C2
    # MOE 4 long (cycle 3) — gap recovery under repaired contract
    r4 = _long_progress(r1.state_after, acceptors[2])
    assert r4.reason_code is ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_GAP_RECOVERY
    assert r4.state_after.distinct_confirmation_observation_count == 1
    # MOE 5 long (cycle 4) — contiguous second qualifying step
    r5 = _long_progress(r4.state_after, acceptors[3])
    assert r5.state_after.assessment_state is ConfirmationAssessmentStateV1.CONFIRMED
    assert r5.state_after.distinct_confirmation_observation_count == 2


def test_duplicate_epoch_does_not_advance() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    prior = _long_state()
    first = _long_progress(prior, a1)
    replay = _long_progress(first.state_after, a1)
    assert replay.reason_code is ConfirmationProgressReasonCodeV1.IDEMPOTENT_REPLAY
    assert replay.confirmation_advanced is False


def test_out_of_order_epoch_does_not_advance() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    a2, _ = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    prior = _long_progress(_long_state(), a1).state_after
    stale = _long_progress(prior, a1, fingerprint="forced-regression-fingerprint")
    assert stale.reason_code is ConfirmationProgressReasonCodeV1.EPOCH_REGRESSION
    assert stale.fail_closed is True
    assert stale.state_after == prior


def test_opposite_side_short_progress_does_not_mutate_long_state() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a_long, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=11.0))
    a_short, _ = _eval_c1(c1, _candidate(event_time=1001.0, mark=10.0))
    long_state = _long_progress(_long_state(), a_long).state_after
    short_state = initial_confirmation_progress_state_v1(
        session_id="ghv-sess",
        venue="okx_eea",
        instrument=_key(),
        side=ConfirmationSideV1.SHORT,
    )
    short_out = evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=short_state,
            observation_acceptance_result=a_short,
            session_id="ghv-sess",
            venue="okx_eea",
            instrument=_key(),
            side=ConfirmationSideV1.SHORT,
            assessment_signal=ConfirmationAssessmentSignalV1.OBSERVE,
            confirmation_threshold=2,
        )
    )
    assert short_out.confirmation_advanced is False
    assert long_state.distinct_confirmation_observation_count == 1
    assert long_state.side is ConfirmationSideV1.LONG


def test_two_contiguous_qualifying_reach_exactly_two_of_two() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    a2, _ = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    state = _long_state()
    first = _long_progress(state, a1)
    assert first.state_after.distinct_confirmation_observation_count == 1
    second = _long_progress(first.state_after, a2)
    assert second.state_after.distinct_confirmation_observation_count == 2
    assert second.state_after.assessment_state is ConfirmationAssessmentStateV1.CONFIRMED


def test_non_qualifying_observe_on_gap_remains_fail_closed() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    _, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    a3, _ = _eval_c1(c1, _candidate(event_time=1002.0, mark=12.0))
    prior = _long_progress(_long_state(), a1).state_after
    gap = _long_progress(
        prior,
        a3,
        signal=ConfirmationAssessmentSignalV1.OBSERVE,
    )
    assert gap.reason_code is ConfirmationProgressReasonCodeV1.EPOCH_GAP
    assert gap.fail_closed is True
    assert gap.state_after == prior


def test_session_mismatch_remains_fail_closed() -> None:
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    out = evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=_long_state(),
            observation_acceptance_result=a1,
            session_id="other-session",
            venue="okx_eea",
            instrument=_key(),
            side=ConfirmationSideV1.LONG,
            assessment_signal=ConfirmationAssessmentSignalV1.CONFIRMED,
            confirmation_threshold=2,
        )
    )
    assert out.reason_code is ConfirmationProgressReasonCodeV1.SESSION_MISMATCH
    assert out.fail_closed is True
