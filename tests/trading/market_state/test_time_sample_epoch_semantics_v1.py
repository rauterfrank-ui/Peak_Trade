"""Contract tests for MASTER_V2_TIME_SAMPLE_EPOCH_SEMANTICS_V1."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import pytest

from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentSignalV1,
    ConfirmationProgressInputV1,
    ConfirmationProgressReasonCodeV1,
    ConfirmationSideV1,
    evaluate_confirmation_progress_v1,
    initial_confirmation_progress_state_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationClassification,
    ObservationTransportMetadataV1,
)
from trading.market_state.observation_identity_v1 import MarketObservationEpoch
from trading.market_state.time_sample_epoch_semantics_v1 import (
    DETERMINISTIC_REPLAY_PASS,
    DISTINCT_OBSERVATION_POLICY_COMPLETE,
    DUPLICATE_SAMPLE_POLICY_COMPLETE,
    EVENT_TIME_CANONICAL,
    MARKET_SAMPLE_IDENTITY_FIELDS,
    NO_DECISION_AUTHORITY_CHANGED,
    NO_PARAMETER_CHANGE,
    OFFLINE_RUNTIME_EQUIVALENCE,
    OUT_OF_ORDER_POLICY_COMPLETE,
    POLL_RATE_INDEPENDENT,
    READY_FOR_RUNTIME_ACTIVATION,
    RUNTIME_WIRING_INCLUDED,
    TIME_SAMPLE_EPOCH_SEMANTICS_CAPABILITY_ID,
    TIME_SAMPLE_SEMANTICS_COMPLETE,
    DecisionEpochV1,
    EventTimeInstantV1,
    MarketSampleIdentityV1,
    RuntimeCycleIndexV1,
    TimeSampleEpochSemanticsErrorV1,
    WallclockCooldownAnchorV1,
    WallclockDurationV1,
    WallclockInstantV1,
    WallclockTimeExitAnchorV1,
    accept_distinct_market_sample_v1,
    assert_capability_flags_v1,
    assert_decision_epoch_not_confirmation_authority_v1,
    assert_domain_separation_v1,
    assert_offline_runtime_time_equivalence_v1,
    assert_poll_cannot_synthesize_market_event_time_v1,
    assert_runtime_cycle_not_market_observation_epoch_v1,
    confirmation_may_advance_only_on_distinct_v1,
    deterministic_time_object_fingerprint_v1,
    initial_market_sample_acceptance_state_v1,
    select_event_time_lookback_window_v1,
    wallclock_cooldown_elapsed_v1,
    wallclock_time_exit_due_v1,
)
from trading.market_state.trading_epoch_compatibility_v1 import (
    TradingEpochCompatibilityErrorV1,
)


def _sample(
    *,
    event_time: float = 1_700_000_000.0,
    mark: float = 42000.5,
    venue: str = "okx_eea",
    canonical: str = "BTC-USD-SWAP-CANON",
    venue_inst: str = "BTC-USD-SWAP",
) -> MarketSampleIdentityV1:
    return MarketSampleIdentityV1(
        venue=venue,
        canonical_instrument_id=canonical,
        venue_instrument_id=venue_inst,
        event_time=EventTimeInstantV1(unix_seconds=event_time),
        mark_price=mark,
    )


def _transport(
    *,
    receive_time: Optional[float] = 1_700_000_001.0,
    poll_attempt: Optional[int] = 1,
    runtime_cycle_index: Optional[int] = None,
    wallclock_now: Optional[float] = None,
) -> ObservationTransportMetadataV1:
    return ObservationTransportMetadataV1(
        receive_time=receive_time,
        poll_attempt=poll_attempt,
        runtime_cycle_index=runtime_cycle_index,
        wallclock_now=wallclock_now,
    )


def _accept_chain(
    samples: Sequence[MarketSampleIdentityV1],
    *,
    transports: Optional[Sequence[Optional[ObservationTransportMetadataV1]]] = None,
) -> Tuple[List[ObservationClassification], object]:
    state = initial_market_sample_acceptance_state_v1(
        bound_instrument_key=_sample().instrument_key()
    )
    classifications: List[ObservationClassification] = []
    for idx, sample in enumerate(samples):
        transport = None if transports is None else transports[idx]
        result, state = accept_distinct_market_sample_v1(
            current_state=state, sample=sample, transport=transport
        )
        classifications.append(result.classification)
    return classifications, state


# ---------------------------------------------------------------------------
# Capability flags / domain separation
# ---------------------------------------------------------------------------


def test_capability_flags_and_domain_separation() -> None:
    flags = assert_capability_flags_v1()
    assert flags["TIME_SAMPLE_SEMANTICS_COMPLETE"] is True
    assert TIME_SAMPLE_SEMANTICS_COMPLETE is True
    assert DISTINCT_OBSERVATION_POLICY_COMPLETE is True
    assert DUPLICATE_SAMPLE_POLICY_COMPLETE is True
    assert OUT_OF_ORDER_POLICY_COMPLETE is True
    assert EVENT_TIME_CANONICAL is True
    assert POLL_RATE_INDEPENDENT is True
    assert OFFLINE_RUNTIME_EQUIVALENCE is True
    assert DETERMINISTIC_REPLAY_PASS is True
    assert NO_DECISION_AUTHORITY_CHANGED is True
    assert NO_PARAMETER_CHANGE is True
    assert RUNTIME_WIRING_INCLUDED is False
    assert READY_FOR_RUNTIME_ACTIVATION is False
    assert TIME_SAMPLE_EPOCH_SEMANTICS_CAPABILITY_ID == ("MASTER_V2_TIME_SAMPLE_EPOCH_SEMANTICS_V1")
    assert MARKET_SAMPLE_IDENTITY_FIELDS == (
        "venue",
        "canonical_instrument_id",
        "venue_instrument_id",
        "venue_event_time",
        "mark_price",
    )
    assert_domain_separation_v1()


# ---------------------------------------------------------------------------
# Canonical Market Sample Identity + persistence
# ---------------------------------------------------------------------------


def test_market_sample_identity_roundtrip_and_c1_bridge() -> None:
    sample = _sample()
    oid = sample.to_observation_identity()
    restored = MarketSampleIdentityV1.from_observation_identity(oid)
    assert restored == sample
    payload = sample.to_dict()
    assert MarketSampleIdentityV1.from_dict(payload) == sample
    assert sample.distinctness_key() == oid.distinctness_key()
    fp1 = deterministic_time_object_fingerprint_v1(payload)
    fp2 = deterministic_time_object_fingerprint_v1(
        MarketSampleIdentityV1.from_dict(payload).to_dict()
    )
    assert fp1 == fp2


def test_event_decision_runtime_domains_are_typed_distinct() -> None:
    event = EventTimeInstantV1(unix_seconds=1_700_000_000.0)
    decision = DecisionEpochV1(value=7)
    runtime = RuntimeCycleIndexV1(value=7)
    market_epoch = MarketObservationEpoch(value=7)
    assert type(event) is not type(decision)
    assert type(decision) is not type(runtime)
    assert type(market_epoch) is not type(decision)
    assert type(market_epoch) is not type(runtime)
    assert decision.to_dict() == DecisionEpochV1.from_dict(decision.to_dict()).to_dict()
    assert runtime.to_dict() == RuntimeCycleIndexV1.from_dict(runtime.to_dict()).to_dict()


# ---------------------------------------------------------------------------
# Distinct / Duplicate / Out-of-order policies
# ---------------------------------------------------------------------------


def test_distinct_then_duplicate_sample_policy() -> None:
    first = _sample(event_time=1_700_000_000.0, mark=42000.5)
    duplicate = _sample(event_time=1_700_000_000.0, mark=42000.5)
    classifications, state = _accept_chain([first, duplicate])
    assert classifications == [
        ObservationClassification.DISTINCT,
        ObservationClassification.DUPLICATE,
    ]
    assert state.market_observation_epoch.value == 1


def test_transport_only_duplicate_does_not_advance() -> None:
    first = _sample(event_time=1_700_000_000.0)
    same = _sample(event_time=1_700_000_000.0)
    transports = [
        _transport(receive_time=1.0, poll_attempt=1),
        _transport(receive_time=2.0, poll_attempt=99, runtime_cycle_index=5),
    ]
    classifications, state = _accept_chain([first, same], transports=transports)
    assert classifications[0] is ObservationClassification.DISTINCT
    assert classifications[1] in {
        ObservationClassification.DUPLICATE,
        ObservationClassification.TRANSPORT_ONLY_DUPLICATE,
    }
    assert state.market_observation_epoch.value == 1


def test_out_of_order_sample_policy_fail_closed() -> None:
    first = _sample(event_time=1_700_000_010.0)
    older = _sample(event_time=1_700_000_000.0)
    classifications, state = _accept_chain([first, older])
    assert classifications == [
        ObservationClassification.DISTINCT,
        ObservationClassification.OUT_OF_ORDER,
    ]
    assert state.market_observation_epoch.value == 1


def test_orderly_distinct_chain_advances_epoch_monotonically() -> None:
    samples = [_sample(event_time=1_700_000_000.0 + i, mark=42000.0 + i) for i in range(5)]
    classifications, state = _accept_chain(samples)
    assert all(c is ObservationClassification.DISTINCT for c in classifications)
    assert state.market_observation_epoch.value == 5


# ---------------------------------------------------------------------------
# Confirmation advances only on DISTINCT
# ---------------------------------------------------------------------------


def test_confirmation_progress_only_on_distinct_observations() -> None:
    instrument = _sample().instrument_key()
    state = initial_market_sample_acceptance_state_v1(bound_instrument_key=instrument)
    c2 = initial_confirmation_progress_state_v1(
        session_id="sess-time-sample",
        venue=instrument.venue,
        instrument=instrument,
        side=ConfirmationSideV1.LONG,
    )

    distinct_sample = _sample(event_time=1_700_000_000.0)
    distinct_result, state = accept_distinct_market_sample_v1(
        current_state=state, sample=distinct_sample
    )
    assert confirmation_may_advance_only_on_distinct_v1(distinct_result) is True
    progress = evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=c2,
            session_id="sess-time-sample",
            venue=instrument.venue,
            instrument=instrument,
            side=ConfirmationSideV1.LONG,
            observation_acceptance_result=distinct_result,
            assessment_signal=ConfirmationAssessmentSignalV1.CANDIDATE,
            confirmation_threshold=2,
        )
    )
    assert progress.accepted is True
    assert progress.state_after.distinct_confirmation_observation_count == 1
    c2 = progress.state_after

    duplicate_sample = _sample(event_time=1_700_000_000.0)
    duplicate_result, state = accept_distinct_market_sample_v1(
        current_state=state, sample=duplicate_sample
    )
    assert confirmation_may_advance_only_on_distinct_v1(duplicate_result) is False
    blocked = evaluate_confirmation_progress_v1(
        ConfirmationProgressInputV1(
            prior_state=c2,
            session_id="sess-time-sample",
            venue=instrument.venue,
            instrument=instrument,
            side=ConfirmationSideV1.LONG,
            observation_acceptance_result=duplicate_result,
            assessment_signal=ConfirmationAssessmentSignalV1.CANDIDATE,
            confirmation_threshold=2,
        )
    )
    assert blocked.state_after.distinct_confirmation_observation_count == 1
    assert blocked.state_after.assessment_state == c2.assessment_state

    decision_reject = assert_decision_epoch_not_confirmation_authority_v1(
        prior_confirmation_state=c2
    )
    assert decision_reject.fail_closed is True
    assert decision_reject.reason_code is ConfirmationProgressReasonCodeV1.DECISION_EPOCH_FORBIDDEN


# ---------------------------------------------------------------------------
# Poll-rate independence + no market-time synthesis
# ---------------------------------------------------------------------------


def test_poll_cannot_synthesize_market_event_time() -> None:
    with pytest.raises(TimeSampleEpochSemanticsErrorV1, match="POLL_CANNOT_SYNTHESIZE"):
        assert_poll_cannot_synthesize_market_event_time_v1(
            venue_event_time=None,
            receive_time=1_700_000_001.0,
            poll_attempt=3,
        )
    with pytest.raises(TimeSampleEpochSemanticsErrorV1, match="POLL_CANNOT_SYNTHESIZE"):
        assert_poll_cannot_synthesize_market_event_time_v1(
            venue_event_time=float("nan"),
            runtime_cycle_index=9,
        )
    with pytest.raises(TimeSampleEpochSemanticsErrorV1, match="WALLCLOCK_CANNOT_SYNTHESIZE"):
        assert_poll_cannot_synthesize_market_event_time_v1(
            venue_event_time=None,
            wallclock_now=1_700_000_999.0,
        )
    # Valid venue event time coexists with transport metadata (non-authority).
    assert_poll_cannot_synthesize_market_event_time_v1(
        venue_event_time=1_700_000_000.0,
        receive_time=1_700_000_001.0,
        poll_attempt=99,
        runtime_cycle_index=12,
        wallclock_now=1_700_000_050.0,
    )


def test_poll_rate_independence_same_event_time() -> None:
    sample = _sample(event_time=1_700_000_000.0)
    slow_transports = [
        _transport(receive_time=1.0, poll_attempt=1),
        _transport(receive_time=2.0, poll_attempt=2),
        _transport(receive_time=3.0, poll_attempt=3),
    ]
    fast_transports = [
        _transport(receive_time=10.0, poll_attempt=100),
        _transport(receive_time=10.1, poll_attempt=101),
        _transport(receive_time=10.2, poll_attempt=102),
    ]
    slow_classes, slow_state = _accept_chain([sample, sample, sample], transports=slow_transports)
    fast_classes, fast_state = _accept_chain([sample, sample, sample], transports=fast_transports)
    assert slow_classes[0] is ObservationClassification.DISTINCT
    assert fast_classes[0] is ObservationClassification.DISTINCT
    assert slow_classes[1:] == fast_classes[1:]
    assert slow_state.market_observation_epoch == fast_state.market_observation_epoch
    assert (
        slow_state.last_accepted_observation_identity
        == fast_state.last_accepted_observation_identity
    )


def test_runtime_cycle_rejected_as_market_observation_epoch() -> None:
    with pytest.raises(TradingEpochCompatibilityErrorV1, match="runtime_cycle_assignment_rejected"):
        assert_runtime_cycle_not_market_observation_epoch_v1(RuntimeCycleIndexV1(value=3))


# ---------------------------------------------------------------------------
# Event-time lookback + wallclock foundation
# ---------------------------------------------------------------------------


def test_event_time_lookback_selection() -> None:
    samples = [
        _sample(event_time=100.0, mark=1.0),
        _sample(event_time=150.0, mark=2.0),
        _sample(event_time=200.0, mark=3.0),
        _sample(event_time=250.0, mark=4.0),
    ]
    window = select_event_time_lookback_window_v1(
        samples,
        as_of_event_time=EventTimeInstantV1(unix_seconds=200.0),
        lookback_seconds=50.0,
    )
    assert [s.event_time.unix_seconds for s in window] == [150.0, 200.0]


def test_wallclock_cooldown_and_time_exit_foundation() -> None:
    cooldown = WallclockCooldownAnchorV1(
        started_at_wallclock=WallclockInstantV1(unix_seconds=1_000.0),
        duration=WallclockDurationV1(seconds=30.0),
    )
    assert (
        wallclock_cooldown_elapsed_v1(
            cooldown, now_wallclock=WallclockInstantV1(unix_seconds=1_029.0)
        )
        is False
    )
    assert (
        wallclock_cooldown_elapsed_v1(
            cooldown, now_wallclock=WallclockInstantV1(unix_seconds=1_030.0)
        )
        is True
    )

    time_exit = WallclockTimeExitAnchorV1(
        opened_at_wallclock=WallclockInstantV1(unix_seconds=2_000.0),
        max_hold_duration=WallclockDurationV1(seconds=60.0),
    )
    assert (
        wallclock_time_exit_due_v1(
            time_exit, now_wallclock=WallclockInstantV1(unix_seconds=2_059.0)
        )
        is False
    )
    assert (
        wallclock_time_exit_due_v1(
            time_exit, now_wallclock=WallclockInstantV1(unix_seconds=2_060.0)
        )
        is True
    )

    # Persistence roundtrip (foundation objects only — no policy wiring).
    assert WallclockCooldownAnchorV1.from_dict(cooldown.to_dict()) == cooldown
    assert WallclockTimeExitAnchorV1.from_dict(time_exit.to_dict()) == time_exit


# ---------------------------------------------------------------------------
# Offline/runtime equivalence + deterministic replay
# ---------------------------------------------------------------------------


def test_offline_runtime_equivalence_and_replay_fingerprint() -> None:
    offline = _sample(event_time=1_700_000_123.0, mark=41111.25)
    runtime = _sample(event_time=1_700_000_123.0, mark=41111.25)
    assert_offline_runtime_time_equivalence_v1(offline_sample=offline, runtime_sample=runtime)
    with pytest.raises(TimeSampleEpochSemanticsErrorV1, match="OFFLINE_RUNTIME"):
        assert_offline_runtime_time_equivalence_v1(
            offline_sample=offline,
            runtime_sample=_sample(event_time=1_700_000_124.0, mark=41111.25),
        )

    samples = [_sample(event_time=1_700_000_000.0 + i, mark=42000.0 + i) for i in range(4)]
    classes_a, state_a = _accept_chain(samples)
    classes_b, state_b = _accept_chain(samples)
    assert classes_a == classes_b
    assert state_a.to_dict() == state_b.to_dict()
    fp_a = deterministic_time_object_fingerprint_v1(
        {"samples": [s.to_dict() for s in samples], "state": state_a.to_dict()}
    )
    fp_b = deterministic_time_object_fingerprint_v1(
        {"samples": [s.to_dict() for s in samples], "state": state_b.to_dict()}
    )
    assert fp_a == fp_b


def test_invalid_market_sample_construction_fail_closed() -> None:
    with pytest.raises(TimeSampleEpochSemanticsErrorV1):
        EventTimeInstantV1(unix_seconds=0.0)
    with pytest.raises(TimeSampleEpochSemanticsErrorV1):
        MarketSampleIdentityV1(
            venue="",
            canonical_instrument_id="x",
            venue_instrument_id="y",
            event_time=EventTimeInstantV1(unix_seconds=1.0),
            mark_price=1.0,
        )
    with pytest.raises(TimeSampleEpochSemanticsErrorV1):
        DecisionEpochV1(value=-1)
