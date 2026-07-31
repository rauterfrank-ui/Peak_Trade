"""Unit, property, and determinism tests for DirectionalConfirmationProgressV1 (C2)."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import pytest

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationAcceptanceStateV1,
    ObservationCandidateV1,
    ObservationClassification,
    ObservationTransportMetadataV1,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.observation_identity_v1 import (
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
)
from trading.market_state.directional_confirmation_progress_v1 import (
    CONFIRMATION_PROGRESS_CAPABILITY_ID,
    CONFIRMATION_PROGRESS_COMPONENT,
    CONFIRMATION_PROGRESS_PURITY,
    CONFIRMED_COUNT_POLICY,
    ConfirmationAssessmentSignalV1,
    ConfirmationAssessmentStateV1,
    ConfirmationProgressInputV1,
    ConfirmationProgressReasonCodeV1,
    ConfirmationProgressStateV1,
    ConfirmationSideV1,
    confirmation_progress_fingerprint_v1,
    evaluate_confirmation_progress_v1,
    initial_confirmation_progress_state_v1,
    reject_decision_epoch_confirmation_advance_v1,
    reject_receive_time_confirmation_advance_v1,
    reject_runtime_cycle_confirmation_advance_v1,
)


def _key(
    *,
    venue: str = "okx_eea",
    canonical: str = "BTC-USD-SWAP-CANON",
    venue_inst: str = "BTC-USD-SWAP",
) -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue=venue,
        canonical_instrument_id=canonical,
        venue_instrument_id=venue_inst,
    )


def _candidate(
    *,
    venue: str = "okx_eea",
    canonical: str = "BTC-USD-SWAP-CANON",
    venue_inst: str = "BTC-USD-SWAP",
    event_time: Optional[float] = 1_700_000_000.0,
    mark: Optional[float] = 42000.5,
    receive_time: Optional[float] = 1_700_000_001.0,
    poll_attempt: Optional[int] = 1,
    runtime_cycle_index: Optional[int] = None,
) -> ObservationCandidateV1:
    transport = None
    if receive_time is not None or poll_attempt is not None or runtime_cycle_index is not None:
        transport = ObservationTransportMetadataV1(
            receive_time=receive_time,
            poll_attempt=poll_attempt,
            runtime_cycle_index=runtime_cycle_index,
        )
    return ObservationCandidateV1(
        venue=venue,
        canonical_instrument_id=canonical,
        venue_instrument_id=venue_inst,
        venue_event_time=event_time,
        mark_price=mark,
        transport=transport,
    )


def _c2_state(
    *,
    session_id: str = "sess-a",
    venue: str = "okx_eea",
    instrument: Optional[InstrumentObservationKeyV1] = None,
    side: ConfirmationSideV1 = ConfirmationSideV1.LONG,
    epoch: int = 0,
) -> ConfirmationProgressStateV1:
    inst = instrument or _key(venue=venue)
    return initial_confirmation_progress_state_v1(
        session_id=session_id,
        venue=venue,
        instrument=inst,
        side=side,
        initial_market_observation_epoch=MarketObservationEpoch(value=epoch),
    )


def _eval_c1(
    state: ObservationAcceptanceStateV1,
    candidate: ObservationCandidateV1,
) -> Tuple[ObservationAcceptanceResultV1, ObservationAcceptanceStateV1]:
    result = evaluate_distinct_market_observation_v1(state, candidate)
    committed = commit_observation_acceptance_v1(current_state=state, result=result)
    return result, committed


def _progress(
    prior: ConfirmationProgressStateV1,
    acceptor: ObservationAcceptanceResultV1,
    *,
    signal: ConfirmationAssessmentSignalV1 = ConfirmationAssessmentSignalV1.CANDIDATE,
    threshold: int = 3,
    session_id: Optional[str] = None,
    venue: Optional[str] = None,
    instrument: Optional[InstrumentObservationKeyV1] = None,
    side: Optional[ConfirmationSideV1] = None,
    fingerprint: Optional[str] = None,
):
    return evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=prior,
            observation_acceptance_result=acceptor,
            session_id=session_id if session_id is not None else prior.session_id,
            venue=venue if venue is not None else prior.venue,
            instrument=instrument if instrument is not None else prior.instrument,
            side=side if side is not None else prior.side,
            assessment_signal=signal,
            confirmation_threshold=threshold,
            acceptor_result_fingerprint=fingerprint,
        )
    )


def _accept_distinct_chain(
    n: int,
    *,
    start_event: float = 1_000.0,
    start_mark: float = 100.0,
    venue: str = "okx_eea",
    canonical: str = "BTC-USD-SWAP-CANON",
    venue_inst: str = "BTC-USD-SWAP",
) -> List[ObservationAcceptanceResultV1]:
    c1 = initial_observation_acceptance_state_v1(
        bound_instrument_key=_key(venue=venue, canonical=canonical, venue_inst=venue_inst)
    )
    results: List[ObservationAcceptanceResultV1] = []
    for i in range(n):
        result, c1 = _eval_c1(
            c1,
            _candidate(
                venue=venue,
                canonical=canonical,
                venue_inst=venue_inst,
                event_time=start_event + i,
                mark=start_mark + i,
            ),
        )
        assert result.classification == ObservationClassification.DISTINCT
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# 1–2 Initial / first distinct candidate
# ---------------------------------------------------------------------------


def test_01_initial_state_is_observe_count_zero() -> None:
    state = _c2_state()
    assert state.assessment_state == ConfirmationAssessmentStateV1.OBSERVE
    assert state.distinct_confirmation_observation_count == 0
    assert state.candidate_started_at_epoch is None
    assert state.latest_accepted_market_observation_epoch.value == 0
    assert CONFIRMATION_PROGRESS_COMPONENT == "DirectionalConfirmationProgressV1"
    assert CONFIRMATION_PROGRESS_PURITY == "PURE_DETERMINISTIC_NO_IO"
    assert (
        CONFIRMATION_PROGRESS_CAPABILITY_ID
        == "MASTER_V2_DOUBLE_PLAY_C2_DIRECTIONAL_CONFIRMATION_PROGRESS_V1"
    )


def test_02_first_accepted_distinct_candidate_epoch_1_count_1() -> None:
    c2 = _c2_state()
    acceptor = _accept_distinct_chain(1)[0]
    result = _progress(c2, acceptor, signal=ConfirmationAssessmentSignalV1.CANDIDATE)
    assert result.accepted is True
    assert result.state_after.latest_accepted_market_observation_epoch.value == 1
    assert result.state_after.distinct_confirmation_observation_count == 1
    assert result.state_after.assessment_state == ConfirmationAssessmentStateV1.CANDIDATE
    assert result.confirmation_advanced is True
    assert result.reason_code == ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_PROGRESS


# ---------------------------------------------------------------------------
# 3–8 Non-distinct C1 classifications leave C2 unchanged
# ---------------------------------------------------------------------------


def test_03_duplicate_leaves_state_unchanged() -> None:
    c1 = initial_observation_acceptance_state_v1()
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    c2 = _progress(_c2_state(), first).state_after
    dup, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    assert dup.classification == ObservationClassification.DUPLICATE
    before = c2
    out = _progress(c2, dup)
    assert out.state_after == before
    assert out.state_changed is False
    assert out.confirmation_advanced is False
    assert out.reason_code == ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP


def test_04_transport_only_duplicate_unchanged() -> None:
    c1 = initial_observation_acceptance_state_v1()
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0, receive_time=1.0))
    c2 = _progress(_c2_state(), first).state_after
    transport_dup, _ = _eval_c1(
        c1, _candidate(event_time=1000.0, mark=10.0, receive_time=99.0, poll_attempt=9)
    )
    assert transport_dup.classification == ObservationClassification.TRANSPORT_ONLY_DUPLICATE
    out = _progress(c2, transport_dup)
    assert out.state_after == c2
    assert out.reason_code == ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP


def test_05_out_of_order_unchanged() -> None:
    c1 = initial_observation_acceptance_state_v1()
    first, c1 = _eval_c1(c1, _candidate(event_time=2000.0, mark=10.0))
    c2 = _progress(_c2_state(), first).state_after
    ooo, _ = _eval_c1(c1, _candidate(event_time=1999.0, mark=11.0))
    assert ooo.classification == ObservationClassification.OUT_OF_ORDER
    out = _progress(c2, ooo)
    assert out.state_after == c2
    assert out.reason_code == ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP


def test_06_identity_conflict_unchanged() -> None:
    c1 = initial_observation_acceptance_state_v1()
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    c2 = _progress(_c2_state(), first).state_after
    conflict, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.5))
    assert conflict.classification == ObservationClassification.IDENTITY_CONFLICT
    out = _progress(c2, conflict)
    assert out.state_after == c2
    assert out.reason_code == ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP


def test_07_invalid_event_time_unchanged() -> None:
    c1 = initial_observation_acceptance_state_v1()
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    c2 = _progress(_c2_state(), first).state_after
    invalid, _ = _eval_c1(c1, _candidate(event_time=None, mark=11.0))
    assert invalid.classification == ObservationClassification.INVALID_EVENT_TIME
    out = _progress(c2, invalid)
    assert out.state_after == c2
    assert out.reason_code == ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP


def test_08_invalid_mark_unchanged() -> None:
    c1 = initial_observation_acceptance_state_v1()
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    c2 = _progress(_c2_state(), first).state_after
    invalid, _ = _eval_c1(c1, _candidate(event_time=1001.0, mark=-1.0))
    assert invalid.classification == ObservationClassification.INVALID_MARK
    out = _progress(c2, invalid)
    assert out.state_after == c2
    assert out.reason_code == ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP


# ---------------------------------------------------------------------------
# 9 Idempotency
# ---------------------------------------------------------------------------


def test_09_same_result_replay_idempotent() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    first = _progress(_c2_state(), acceptor)
    replay = _progress(first.state_after, acceptor)
    assert replay.reason_code == ConfirmationProgressReasonCodeV1.IDEMPOTENT_REPLAY
    assert replay.state_after == first.state_after
    assert replay.fail_closed is False
    assert replay.confirmation_advanced is False
    assert replay.state_changed is False


# ---------------------------------------------------------------------------
# 10–11 Epoch gap / regression
# ---------------------------------------------------------------------------


def test_10_epoch_regression_fail_closed() -> None:
    chain = _accept_distinct_chain(2)
    c2 = _progress(_c2_state(), chain[0]).state_after
    # Feed older distinct result (epoch 1) after already at epoch 1 → regression
    out = _progress(c2, chain[0])
    # fingerprint may hit idempotent first; force different fingerprint with same epoch
    out = _progress(c2, chain[0], fingerprint="forced-regression-fingerprint")
    assert out.reason_code == ConfirmationProgressReasonCodeV1.EPOCH_REGRESSION
    assert out.fail_closed is True
    assert out.state_after == c2


def test_11_epoch_gap_fail_closed() -> None:
    chain = _accept_distinct_chain(3)
    # Skip epoch 1 result; jump to epoch 2 from empty C2 at epoch 0
    out = _progress(_c2_state(), chain[1])
    assert chain[1].state_after.market_observation_epoch.value == 2
    assert out.reason_code == ConfirmationProgressReasonCodeV1.EPOCH_GAP
    assert out.fail_closed is True
    assert out.state_after == _c2_state()


# ---------------------------------------------------------------------------
# 12–15 Binding mismatches
# ---------------------------------------------------------------------------


def test_12_foreign_session_fail_closed() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    out = _progress(_c2_state(), acceptor, session_id="other-session")
    assert out.reason_code == ConfirmationProgressReasonCodeV1.SESSION_MISMATCH
    assert out.fail_closed is True


def test_13_foreign_instrument_fail_closed() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    other = _key(canonical="ETH-CANON", venue_inst="ETH-USD-SWAP")
    out = _progress(_c2_state(), acceptor, instrument=other)
    assert out.reason_code == ConfirmationProgressReasonCodeV1.INSTRUMENT_MISMATCH
    assert out.fail_closed is True


def test_14_foreign_venue_fail_closed() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    # venue mismatch against prior.venue while keeping prior instrument is checked
    # before instrument compare when venue field differs.
    out = _progress(_c2_state(), acceptor, venue="other_venue")
    assert out.reason_code == ConfirmationProgressReasonCodeV1.VENUE_MISMATCH
    assert out.fail_closed is True


def test_15_foreign_side_fail_closed() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    out = _progress(
        _c2_state(side=ConfirmationSideV1.LONG), acceptor, side=ConfirmationSideV1.SHORT
    )
    assert out.reason_code == ConfirmationProgressReasonCodeV1.SIDE_MISMATCH
    assert out.fail_closed is True


# ---------------------------------------------------------------------------
# 16–17 Isolation
# ---------------------------------------------------------------------------


def test_16_long_and_short_fully_isolated() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    long_state = _c2_state(side=ConfirmationSideV1.LONG)
    short_state = _c2_state(side=ConfirmationSideV1.SHORT)
    long_out = _progress(long_state, acceptor, side=ConfirmationSideV1.LONG)
    short_out = _progress(short_state, acceptor, side=ConfirmationSideV1.SHORT)
    assert long_out.state_after.side == ConfirmationSideV1.LONG
    assert short_out.state_after.side == ConfirmationSideV1.SHORT
    assert long_out.state_after.assessment_state == ConfirmationAssessmentStateV1.CANDIDATE
    assert short_out.state_after.assessment_state == ConfirmationAssessmentStateV1.CANDIDATE
    # Cross-side application is rejected
    cross = _progress(long_out.state_after, acceptor, side=ConfirmationSideV1.SHORT)
    assert cross.reason_code == ConfirmationProgressReasonCodeV1.SIDE_MISMATCH


def test_17_two_instruments_fully_isolated() -> None:
    btc = _accept_distinct_chain(1, venue_inst="BTC-USD-SWAP", canonical="BTC-CANON")[0]
    eth = _accept_distinct_chain(1, venue_inst="ETH-USD-SWAP", canonical="ETH-CANON")[0]
    btc_c2 = _c2_state(instrument=_key(venue_inst="BTC-USD-SWAP", canonical="BTC-CANON"))
    eth_c2 = _c2_state(instrument=_key(venue_inst="ETH-USD-SWAP", canonical="ETH-CANON"))
    btc_out = _progress(btc_c2, btc, instrument=btc_c2.instrument)
    eth_out = _progress(eth_c2, eth, instrument=eth_c2.instrument)
    assert btc_out.state_after.instrument != eth_out.state_after.instrument
    cross = _progress(btc_out.state_after, eth, instrument=eth_c2.instrument)
    assert cross.reason_code == ConfirmationProgressReasonCodeV1.INSTRUMENT_MISMATCH


# ---------------------------------------------------------------------------
# 18–21 Non-authorities cannot advance confirmation
# ---------------------------------------------------------------------------


def test_18_runtime_cycle_count_does_not_affect_confirmation() -> None:
    c1_a = initial_observation_acceptance_state_v1()
    r1, c1_a = _eval_c1(c1_a, _candidate(event_time=1000.0, mark=10.0, runtime_cycle_index=1))
    r2, _ = _eval_c1(c1_a, _candidate(event_time=1001.0, mark=11.0, runtime_cycle_index=999))

    c1_b = initial_observation_acceptance_state_v1()
    s1, c1_b = _eval_c1(c1_b, _candidate(event_time=1000.0, mark=10.0, runtime_cycle_index=50))
    s2, _ = _eval_c1(c1_b, _candidate(event_time=1001.0, mark=11.0, runtime_cycle_index=51))

    path_a = _progress(_progress(_c2_state(), r1).state_after, r2)
    path_b = _progress(_progress(_c2_state(), s1).state_after, s2)
    assert path_a.state_after.assessment_state == path_b.state_after.assessment_state
    assert (
        path_a.state_after.distinct_confirmation_observation_count
        == path_b.state_after.distinct_confirmation_observation_count
    )
    assert (
        path_a.state_after.latest_accepted_market_observation_epoch
        == path_b.state_after.latest_accepted_market_observation_epoch
    )
    reject = reject_runtime_cycle_confirmation_advance_v1(_c2_state())
    assert reject.reason_code == ConfirmationProgressReasonCodeV1.RUNTIME_CYCLE_NOT_OBSERVATION
    assert reject.fail_closed is True


def test_19_poll_rate_variation_does_not_affect_confirmation() -> None:
    clean = _accept_distinct_chain(2)
    c1 = initial_observation_acceptance_state_v1()
    noisy_results: List[ObservationAcceptanceResultV1] = []
    for i, poll in enumerate((1, 2, 3, 1, 9)):
        event = 1000.0 + min(i, 1)  # only two distinct market events
        mark = 100.0 + min(i, 1)
        result, c1 = _eval_c1(
            c1,
            _candidate(event_time=event, mark=mark, poll_attempt=poll, receive_time=float(poll)),
        )
        if result.classification == ObservationClassification.DISTINCT:
            noisy_results.append(result)

    assert len(noisy_results) == 2
    clean_path = _progress(_progress(_c2_state(), clean[0]).state_after, clean[1])
    noisy_path = _progress(_progress(_c2_state(), noisy_results[0]).state_after, noisy_results[1])
    assert (
        clean_path.state_after.distinct_confirmation_observation_count
        == noisy_path.state_after.distinct_confirmation_observation_count
    )
    assert (
        clean_path.state_after.latest_accepted_market_observation_epoch
        == noisy_path.state_after.latest_accepted_market_observation_epoch
    )


def test_20_receive_time_variation_does_not_affect_confirmation() -> None:
    a = _accept_distinct_chain(1)[0]
    c1 = initial_observation_acceptance_state_v1()
    b, _ = _eval_c1(
        c1,
        _candidate(event_time=1000.0, mark=100.0, receive_time=9_999_999.0),
    )
    out_a = _progress(_c2_state(), a)
    out_b = _progress(_c2_state(), b)
    assert out_a.state_after.assessment_state == out_b.state_after.assessment_state
    assert (
        out_a.state_after.distinct_confirmation_observation_count
        == out_b.state_after.distinct_confirmation_observation_count
    )
    reject = reject_receive_time_confirmation_advance_v1(_c2_state())
    assert reject.reason_code == ConfirmationProgressReasonCodeV1.RECEIVE_TIME_NOT_EPOCH
    assert reject.fail_closed is True


def test_21_decision_epoch_cannot_be_advanced() -> None:
    prior = _c2_state()
    reject = reject_decision_epoch_confirmation_advance_v1(prior)
    assert reject.reason_code == ConfirmationProgressReasonCodeV1.DECISION_EPOCH_FORBIDDEN
    assert reject.fail_closed is True
    assert reject.state_after == prior
    assert reject.confirmation_advanced is False
    # evaluate API has no DecisionEpoch field; only MarketObservationEpoch advances
    acceptor = _accept_distinct_chain(1)[0]
    out = _progress(prior, acceptor)
    assert out.observation_epoch_after == acceptor.state_after.market_observation_epoch


# ---------------------------------------------------------------------------
# 22–23 Session / resume
# ---------------------------------------------------------------------------


def test_22_new_session_starts_empty() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    progressed = _progress(_c2_state(session_id="sess-old"), acceptor).state_after
    assert progressed.assessment_state == ConfirmationAssessmentStateV1.CANDIDATE
    fresh = _c2_state(session_id="sess-new")
    assert fresh.assessment_state == ConfirmationAssessmentStateV1.OBSERVE
    assert fresh.distinct_confirmation_observation_count == 0
    assert fresh.last_processed_acceptor_result_fingerprint is None


def test_23_no_implicit_resume() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    progressed = _progress(_c2_state(session_id="sess-a"), acceptor).state_after
    # Serialization reconstructs data but does not authorize resume across sessions.
    restored = ConfirmationProgressStateV1.from_dict(progressed.to_dict())
    assert restored == progressed
    mismatch = _progress(restored, acceptor, session_id="sess-b")
    assert mismatch.reason_code == ConfirmationProgressReasonCodeV1.SESSION_MISMATCH
    # New session must use initial_confirmation_progress_state_v1, not restored foreign state
    new_session = initial_confirmation_progress_state_v1(
        session_id="sess-b",
        venue=restored.venue,
        instrument=restored.instrument,
        side=restored.side,
    )
    assert new_session.assessment_state == ConfirmationAssessmentStateV1.OBSERVE
    assert new_session.distinct_confirmation_observation_count == 0


# ---------------------------------------------------------------------------
# 24–29 Transition matrix
# ---------------------------------------------------------------------------


def test_24_observe_to_candidate() -> None:
    out = _progress(
        _c2_state(),
        _accept_distinct_chain(1)[0],
        signal=ConfirmationAssessmentSignalV1.CANDIDATE,
    )
    assert out.state_after.assessment_state == ConfirmationAssessmentStateV1.CANDIDATE
    assert out.state_after.distinct_confirmation_observation_count == 1
    assert out.state_after.candidate_started_at_epoch == MarketObservationEpoch(value=1)


def test_25_candidate_to_candidate() -> None:
    chain = _accept_distinct_chain(2)
    s1 = _progress(_c2_state(), chain[0], threshold=3).state_after
    s2 = _progress(s1, chain[1], threshold=3)
    assert s2.state_after.assessment_state == ConfirmationAssessmentStateV1.CANDIDATE
    assert s2.state_after.distinct_confirmation_observation_count == 2
    assert s2.reason_code == ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_PROGRESS


def test_26_candidate_to_confirmed_exactly_at_threshold() -> None:
    chain = _accept_distinct_chain(3)
    state = _c2_state()
    for i, acceptor in enumerate(chain):
        out = _progress(state, acceptor, threshold=3)
        state = out.state_after
        if i < 2:
            assert state.assessment_state == ConfirmationAssessmentStateV1.CANDIDATE
        else:
            assert out.reason_code == ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_CONFIRMED
            assert state.assessment_state == ConfirmationAssessmentStateV1.CONFIRMED
            assert state.distinct_confirmation_observation_count == 3


def test_27_candidate_to_observe_reset() -> None:
    chain = _accept_distinct_chain(2)
    candidate = _progress(_c2_state(), chain[0]).state_after
    reset = _progress(candidate, chain[1], signal=ConfirmationAssessmentSignalV1.OBSERVE)
    assert reset.reason_code == ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_RESET
    assert reset.state_after.assessment_state == ConfirmationAssessmentStateV1.OBSERVE
    assert reset.state_after.distinct_confirmation_observation_count == 0
    assert reset.state_after.candidate_started_at_epoch is None


def test_28_confirmed_holds_stable_on_confirmed_signal() -> None:
    assert CONFIRMED_COUNT_POLICY == "HOLD_STABLE"
    chain = _accept_distinct_chain(4)
    state = _c2_state()
    for acceptor in chain[:2]:
        state = _progress(
            state, acceptor, threshold=2, signal=ConfirmationAssessmentSignalV1.CANDIDATE
        ).state_after
    assert state.assessment_state == ConfirmationAssessmentStateV1.CONFIRMED
    held_count = state.distinct_confirmation_observation_count
    hold = _progress(state, chain[2], threshold=2, signal=ConfirmationAssessmentSignalV1.CONFIRMED)
    assert hold.reason_code == ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_HOLD_CONFIRMED
    assert hold.state_after.assessment_state == ConfirmationAssessmentStateV1.CONFIRMED
    assert hold.state_after.distinct_confirmation_observation_count == held_count
    assert hold.confirmation_advanced is False
    # Further CANDIDATE signal also holds
    hold2 = _progress(
        hold.state_after, chain[3], threshold=2, signal=ConfirmationAssessmentSignalV1.CANDIDATE
    )
    assert hold2.state_after.distinct_confirmation_observation_count == held_count
    assert hold2.state_after.assessment_state == ConfirmationAssessmentStateV1.CONFIRMED


def test_29_confirmed_to_observe_reset() -> None:
    chain = _accept_distinct_chain(3)
    state = _c2_state()
    for acceptor in chain[:2]:
        state = _progress(state, acceptor, threshold=2).state_after
    assert state.assessment_state == ConfirmationAssessmentStateV1.CONFIRMED
    reset = _progress(state, chain[2], signal=ConfirmationAssessmentSignalV1.OBSERVE)
    assert reset.reason_code == ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_RESET
    assert reset.state_after.assessment_state == ConfirmationAssessmentStateV1.OBSERVE
    assert reset.state_after.distinct_confirmation_observation_count == 0


# ---------------------------------------------------------------------------
# 30–31 Consistency / serialization
# ---------------------------------------------------------------------------


def test_30_state_inconsistency_fail_closed() -> None:
    prior = _c2_state()
    object.__setattr__(prior, "distinct_confirmation_observation_count", 5)
    acceptor = _accept_distinct_chain(1)[0]
    out = _progress(prior, acceptor)
    assert out.reason_code == ConfirmationProgressReasonCodeV1.STATE_INCONSISTENT
    assert out.fail_closed is True
    assert out.state_after == prior

    invalid = ConfirmationProgressStateV1(
        session_id="sess-a",
        venue="okx_eea",
        instrument=_key(),
        side=ConfirmationSideV1.LONG,
        assessment_state=ConfirmationAssessmentStateV1.INVALID,
        latest_accepted_market_observation_epoch=MarketObservationEpoch(value=0),
        candidate_started_at_epoch=None,
        distinct_confirmation_observation_count=0,
        last_processed_acceptor_result_fingerprint=None,
    )
    out_invalid = _progress(invalid, acceptor)
    assert out_invalid.reason_code == ConfirmationProgressReasonCodeV1.STATE_INCONSISTENT


def test_31_serialization_roundtrip() -> None:
    chain = _accept_distinct_chain(2)
    state = _progress(_c2_state(), chain[0]).state_after
    state = _progress(state, chain[1]).state_after
    restored = ConfirmationProgressStateV1.from_dict(state.to_dict())
    assert restored == state
    assert restored.to_dict() == state.to_dict()


# ---------------------------------------------------------------------------
# 32–34 Property tests
# ---------------------------------------------------------------------------


def test_32_property_only_contiguous_accepted_distinct_epochs_raise_count() -> None:
    events: Sequence[ObservationCandidateV1] = [
        _candidate(event_time=1000.0, mark=10.0),
        _candidate(event_time=1000.0, mark=10.0),  # dup
        _candidate(event_time=1000.0, mark=10.0, receive_time=55.0, poll_attempt=9),
        _candidate(event_time=999.0, mark=11.0),  # ooo
        _candidate(event_time=1001.0, mark=10.0),  # distinct
        _candidate(event_time=None, mark=12.0),
        _candidate(event_time=1002.0, mark=-1.0),
        _candidate(event_time=1002.0, mark=12.0),  # distinct
        _candidate(event_time=1002.0, mark=13.0),  # identity conflict
        _candidate(event_time=1003.0, mark=13.0),  # distinct
    ]
    c1 = initial_observation_acceptance_state_v1()
    c2 = _c2_state()
    prev_count = 0
    distinct_applied = 0
    for cand in events:
        acceptor, c1 = _eval_c1(c1, cand)
        out = _progress(c2, acceptor, threshold=99)
        if (
            acceptor.classification == ObservationClassification.DISTINCT
            and acceptor.strategy_advance_allowed
            and acceptor.state_after.market_observation_epoch.value
            == c2.latest_accepted_market_observation_epoch.value + 1
        ):
            assert out.accepted is True
            assert out.state_after.distinct_confirmation_observation_count == prev_count + 1
            distinct_applied += 1
            prev_count = out.state_after.distinct_confirmation_observation_count
            c2 = out.state_after
        else:
            assert out.state_after.distinct_confirmation_observation_count == prev_count
            assert out.state_after == c2
    assert distinct_applied == 4
    assert c2.distinct_confirmation_observation_count == 4


def test_33_property_all_non_distinct_leave_full_state_unchanged() -> None:
    c1 = initial_observation_acceptance_state_v1()
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    c2 = _progress(_c2_state(), first).state_after
    non_distinct = [
        _candidate(event_time=1000.0, mark=10.0),
        _candidate(event_time=1000.0, mark=10.0, receive_time=7.0, poll_attempt=3),
        _candidate(event_time=999.0, mark=11.0),
        _candidate(event_time=1000.0, mark=10.5),
        _candidate(event_time=None, mark=11.0),
        _candidate(event_time=1001.0, mark=-1.0),
    ]
    for cand in non_distinct:
        acceptor, _ = _eval_c1(c1, cand)
        assert acceptor.classification != ObservationClassification.DISTINCT
        out = _progress(c2, acceptor)
        assert out.state_after == c2
        assert out.state_changed is False
        assert out.confirmation_advanced is False
        assert out.reason_code == ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP


def test_34_property_poll_and_runtime_cycle_repeats_create_no_progress() -> None:
    c1 = initial_observation_acceptance_state_v1()
    first, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0, poll_attempt=1))
    c2 = _progress(_c2_state(), first).state_after
    snapshot = c2
    for i in range(1, 8):
        acceptor, _ = _eval_c1(
            c1,
            _candidate(
                event_time=1000.0,
                mark=10.0,
                poll_attempt=i,
                runtime_cycle_index=i * 10,
                receive_time=float(i),
            ),
        )
        assert acceptor.classification != ObservationClassification.DISTINCT
        out = _progress(c2, acceptor)
        assert out.state_after == snapshot
        assert out.confirmation_advanced is False


# ---------------------------------------------------------------------------
# 35 Determinism
# ---------------------------------------------------------------------------


def test_35_determinism_identical_input_identical_result() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    prior = _c2_state()
    a = _progress(prior, acceptor)
    b = _progress(prior, acceptor)
    assert a == b
    assert a.to_dict() == b.to_dict()
    assert a.deterministic_fingerprint == b.deterministic_fingerprint
    assert confirmation_progress_fingerprint_v1(acceptor) == confirmation_progress_fingerprint_v1(
        acceptor
    )


def test_observe_plus_confirmed_respects_threshold() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    confirm = _progress(
        _c2_state(),
        acceptor,
        signal=ConfirmationAssessmentSignalV1.CONFIRMED,
        threshold=1,
    )
    assert confirm.state_after.assessment_state == ConfirmationAssessmentStateV1.CONFIRMED
    as_candidate = _progress(
        _c2_state(),
        acceptor,
        signal=ConfirmationAssessmentSignalV1.CONFIRMED,
        threshold=3,
    )
    assert as_candidate.state_after.assessment_state == ConfirmationAssessmentStateV1.CANDIDATE
    assert as_candidate.state_after.distinct_confirmation_observation_count == 1


def test_observe_plus_observe_advances_epoch_without_count() -> None:
    acceptor = _accept_distinct_chain(1)[0]
    out = _progress(
        _c2_state(),
        acceptor,
        signal=ConfirmationAssessmentSignalV1.OBSERVE,
    )
    assert out.state_after.assessment_state == ConfirmationAssessmentStateV1.OBSERVE
    assert out.state_after.distinct_confirmation_observation_count == 0
    assert out.state_after.latest_accepted_market_observation_epoch.value == 1
    assert out.confirmation_advanced is False
    assert out.reason_code == ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_PROGRESS
