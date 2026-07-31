"""Unit, property, and determinism tests for DistinctMarketObservationAcceptorV1 (C1)."""

from __future__ import annotations

import copy
import math
from typing import List, Optional, Sequence, Tuple

import pytest

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    OBSERVATION_ACCEPTOR_COMPONENT,
    OBSERVATION_ACCEPTOR_PURITY,
    DistinctMarketObservationAcceptorV1,
    ObservationAcceptanceStateV1,
    ObservationCandidateV1,
    ObservationClassification,
    ObservationReasonCode,
    ObservationTransportMetadataV1,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.observation_identity_v1 import (
    DISTINCTNESS_IDENTITY_FIELDS,
    NON_DISTINCTNESS_AUTHORITY_FIELDS,
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
    ObservationIdentityV1,
    observation_candidate_from_normalized_public_market_data_v1,
    observation_identity_from_normalized_public_market_data_v1,
)
from trading.market_state.trading_epoch_compatibility_v1 import (
    TRADING_EPOCH_ALIAS_TARGET,
    TradingEpochCompatibilityErrorV1,
    assert_runtime_cycle_assignment_rejected_v1,
    assert_trading_epoch_alias_target_v1,
    market_observation_epoch_from_trading_epoch_alias_v1,
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


def _accept_sequence(
    candidates: Sequence[ObservationCandidateV1],
    *,
    bound: Optional[InstrumentObservationKeyV1] = None,
) -> Tuple[List[ObservationClassification], ObservationAcceptanceStateV1]:
    state = initial_observation_acceptance_state_v1(bound_instrument_key=bound)
    classifications: List[ObservationClassification] = []
    for cand in candidates:
        result = evaluate_distinct_market_observation_v1(state, cand)
        classifications.append(result.classification)
        state = commit_observation_acceptance_v1(current_state=state, result=result)
    return classifications, state


# ---------------------------------------------------------------------------
# 1–2 Initial / first distinct
# ---------------------------------------------------------------------------


def test_01_initial_state() -> None:
    state = DistinctMarketObservationAcceptorV1.initial_state()
    assert state.last_accepted_observation_identity is None
    assert state.market_observation_epoch.value == 0
    assert OBSERVATION_ACCEPTOR_COMPONENT == "DistinctMarketObservationAcceptorV1"
    assert OBSERVATION_ACCEPTOR_PURITY == "PURE_DETERMINISTIC_NO_IO"


def test_02_first_valid_observation_epoch_1() -> None:
    state = initial_observation_acceptance_state_v1()
    result = evaluate_distinct_market_observation_v1(state, _candidate())
    assert result.classification == ObservationClassification.DISTINCT
    assert result.strategy_advance_allowed is True
    assert result.state_after.market_observation_epoch.value == 1
    assert result.state_after.last_accepted_observation_identity is not None
    assert result.reason_code == ObservationReasonCode.ACCEPTED_DISTINCT_INITIAL.value


# ---------------------------------------------------------------------------
# 3–6 Duplicate / distinct variants
# ---------------------------------------------------------------------------


def test_03_exact_duplicate() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(state, _candidate())
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    second = evaluate_distinct_market_observation_v1(state, _candidate())
    assert second.classification == ObservationClassification.DUPLICATE
    assert second.strategy_advance_allowed is False
    assert second.state_after == second.state_before
    assert second.state_after.market_observation_epoch.value == 1


def test_04_transport_only_duplicate() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(
        state, _candidate(receive_time=100.0, poll_attempt=1)
    )
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    second = evaluate_distinct_market_observation_v1(
        state, _candidate(receive_time=999.0, poll_attempt=7)
    )
    assert second.classification == ObservationClassification.TRANSPORT_ONLY_DUPLICATE
    assert second.strategy_advance_allowed is False
    assert second.state_after == second.state_before


def test_05_same_price_new_event_time_is_distinct() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(
        state, _candidate(event_time=1000.0, mark=100.0)
    )
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    second = evaluate_distinct_market_observation_v1(
        state, _candidate(event_time=1001.0, mark=100.0)
    )
    assert second.classification == ObservationClassification.DISTINCT
    assert second.state_after.market_observation_epoch.value == 2


def test_06_new_price_new_event_time_is_distinct() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(
        state, _candidate(event_time=1000.0, mark=100.0)
    )
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    second = evaluate_distinct_market_observation_v1(
        state, _candidate(event_time=1001.0, mark=101.0)
    )
    assert second.classification == ObservationClassification.DISTINCT
    assert second.state_after.market_observation_epoch.value == 2


# ---------------------------------------------------------------------------
# 7–8 Identity conflict / out of order
# ---------------------------------------------------------------------------


def test_07_same_event_identity_conflicting_mark() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(
        state, _candidate(event_time=1000.0, mark=100.0)
    )
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    conflict = evaluate_distinct_market_observation_v1(
        state, _candidate(event_time=1000.0, mark=100.5)
    )
    assert conflict.classification == ObservationClassification.IDENTITY_CONFLICT
    assert conflict.strategy_advance_allowed is False
    assert conflict.fail_closed is True
    assert conflict.reason_code == ObservationReasonCode.IDENTITY_CONFLICT_MARK.value
    assert conflict.state_after == conflict.state_before


def test_08_earlier_event_time_out_of_order() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(
        state, _candidate(event_time=2000.0, mark=100.0)
    )
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    ooo = evaluate_distinct_market_observation_v1(state, _candidate(event_time=1999.0, mark=101.0))
    assert ooo.classification == ObservationClassification.OUT_OF_ORDER
    assert ooo.strategy_advance_allowed is False
    assert ooo.fail_closed is True
    assert ooo.state_after.market_observation_epoch.value == 1


# ---------------------------------------------------------------------------
# 9–11 Invalid event time
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "event_time,reason",
    [
        (None, ObservationReasonCode.INVALID_EVENT_TIME_MISSING),
        (math.nan, ObservationReasonCode.INVALID_EVENT_TIME_NON_FINITE),
        (math.inf, ObservationReasonCode.INVALID_EVENT_TIME_NON_FINITE),
        (-math.inf, ObservationReasonCode.INVALID_EVENT_TIME_NON_FINITE),
        (0.0, ObservationReasonCode.INVALID_EVENT_TIME_NON_POSITIVE),
        (-1.0, ObservationReasonCode.INVALID_EVENT_TIME_NON_POSITIVE),
    ],
)
def test_09_10_11_invalid_event_time(
    event_time: Optional[float], reason: ObservationReasonCode
) -> None:
    state = initial_observation_acceptance_state_v1()
    result = evaluate_distinct_market_observation_v1(state, _candidate(event_time=event_time))
    assert result.classification == ObservationClassification.INVALID_EVENT_TIME
    assert result.strategy_advance_allowed is False
    assert result.state_after == result.state_before
    assert result.reason_code == reason.value


# ---------------------------------------------------------------------------
# 12–16 Invalid mark
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mark,reason",
    [
        (None, ObservationReasonCode.INVALID_MARK_MISSING),
        (0.0, ObservationReasonCode.INVALID_MARK_NON_POSITIVE),
        (-1.0, ObservationReasonCode.INVALID_MARK_NON_POSITIVE),
        (math.nan, ObservationReasonCode.INVALID_MARK_NON_FINITE),
        (math.inf, ObservationReasonCode.INVALID_MARK_NON_FINITE),
        (-math.inf, ObservationReasonCode.INVALID_MARK_NON_FINITE),
    ],
)
def test_12_16_invalid_mark(mark: Optional[float], reason: ObservationReasonCode) -> None:
    state = initial_observation_acceptance_state_v1()
    result = evaluate_distinct_market_observation_v1(state, _candidate(mark=mark))
    assert result.classification == ObservationClassification.INVALID_MARK
    assert result.strategy_advance_allowed is False
    assert result.state_after == result.state_before
    assert result.reason_code == reason.value


# ---------------------------------------------------------------------------
# 17–19 Instrument / venue / mapping conflicts
# ---------------------------------------------------------------------------


def test_17_instrument_conflict() -> None:
    bound = _key(venue_inst="BTC-USD-SWAP")
    state = initial_observation_acceptance_state_v1(bound_instrument_key=bound)
    # Seed with matching instrument
    first = evaluate_distinct_market_observation_v1(state, _candidate())
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    other = evaluate_distinct_market_observation_v1(
        state,
        _candidate(venue_inst="ETH-USD-SWAP", canonical="ETH-USD-SWAP-CANON", event_time=2e9),
    )
    assert other.classification == ObservationClassification.IDENTITY_CONFLICT
    assert other.reason_code == ObservationReasonCode.IDENTITY_CONFLICT_INSTRUMENT.value


def test_18_venue_conflict() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(state, _candidate())
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    other = evaluate_distinct_market_observation_v1(
        state, _candidate(venue="other_venue", event_time=2e9)
    )
    assert other.classification == ObservationClassification.IDENTITY_CONFLICT
    assert other.reason_code == ObservationReasonCode.IDENTITY_CONFLICT_VENUE.value


def test_19_canonical_venue_instrument_mapping_conflict() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(state, _candidate())
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    other = evaluate_distinct_market_observation_v1(
        state,
        _candidate(canonical="OTHER-CANON", event_time=2e9),
    )
    assert other.classification == ObservationClassification.IDENTITY_CONFLICT
    assert other.reason_code == ObservationReasonCode.IDENTITY_CONFLICT_CANONICAL_MAPPING.value


# ---------------------------------------------------------------------------
# 20–23 State immutability / epoch rules / receive-time
# ---------------------------------------------------------------------------


def test_20_non_distinct_does_not_mutate_state() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(state, _candidate())
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    before = copy.deepcopy(state)
    for cand in (
        _candidate(),  # duplicate
        _candidate(event_time=999.0),  # out of order
        _candidate(event_time=None),  # invalid event
        _candidate(mark=-1.0),  # invalid mark
        _candidate(venue="x", event_time=3e9),  # conflict
    ):
        result = evaluate_distinct_market_observation_v1(state, cand)
        assert result.classification != ObservationClassification.DISTINCT
        assert result.state_after == result.state_before == before
        state = commit_observation_acceptance_v1(current_state=state, result=result)
        assert state == before


def test_21_each_distinct_advances_epoch_exactly_by_one() -> None:
    state = initial_observation_acceptance_state_v1()
    for i, event_time in enumerate((1000.0, 1001.0, 1002.0, 1003.0), start=1):
        result = evaluate_distinct_market_observation_v1(
            state, _candidate(event_time=event_time, mark=100.0 + i)
        )
        assert result.classification == ObservationClassification.DISTINCT
        assert (
            result.state_after.market_observation_epoch.value
            == result.state_before.market_observation_epoch.value + 1
        )
        assert result.state_after.market_observation_epoch.value == i
        state = commit_observation_acceptance_v1(current_state=state, result=result)


def test_22_epoch_cannot_be_advanced_by_runtime_cycle() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(state, _candidate(runtime_cycle_index=1))
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    # Same market identity, higher runtime cycle → transport-only / duplicate, no epoch bump
    again = evaluate_distinct_market_observation_v1(state, _candidate(runtime_cycle_index=99))
    assert again.classification in {
        ObservationClassification.TRANSPORT_ONLY_DUPLICATE,
        ObservationClassification.DUPLICATE,
    }
    assert again.state_after.market_observation_epoch.value == 1
    with pytest.raises(TradingEpochCompatibilityErrorV1):
        assert_runtime_cycle_assignment_rejected_v1(99)


def test_23_receive_time_change_does_not_create_distinct() -> None:
    state = initial_observation_acceptance_state_v1()
    first = evaluate_distinct_market_observation_v1(state, _candidate(receive_time=10.0))
    state = commit_observation_acceptance_v1(current_state=state, result=first)
    again = evaluate_distinct_market_observation_v1(state, _candidate(receive_time=999999.0))
    assert again.classification == ObservationClassification.TRANSPORT_ONLY_DUPLICATE
    assert again.strategy_advance_allowed is False
    assert again.state_after.market_observation_epoch.value == 1


# ---------------------------------------------------------------------------
# 24–25 Determinism / serialization
# ---------------------------------------------------------------------------


def test_24_deterministic_replay_identical_inputs() -> None:
    state = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    cand = _candidate()
    a = evaluate_distinct_market_observation_v1(state, cand)
    b = evaluate_distinct_market_observation_v1(state, cand)
    assert a.to_dict() == b.to_dict()
    assert a.classification == b.classification
    assert a.state_after.to_dict() == b.state_after.to_dict()


def test_25_serialization_roundtrip() -> None:
    state = initial_observation_acceptance_state_v1()
    result = evaluate_distinct_market_observation_v1(state, _candidate())
    state = commit_observation_acceptance_v1(current_state=state, result=result)
    restored = ObservationAcceptanceStateV1.from_dict(state.to_dict())
    assert restored == state
    assert restored.market_observation_epoch == state.market_observation_epoch
    identity = state.last_accepted_observation_identity
    assert identity is not None
    assert ObservationIdentityV1.from_dict(identity.to_dict()) == identity
    epoch = MarketObservationEpoch.from_dict({"value": 7})
    assert epoch.value == 7


# ---------------------------------------------------------------------------
# 26 Property tests
# ---------------------------------------------------------------------------


def test_26_property_epoch_monotonic_only_on_distinct_and_delta_at_most_one() -> None:
    events = [
        _candidate(event_time=1000.0, mark=10.0),
        _candidate(event_time=1000.0, mark=10.0),  # dup
        _candidate(event_time=1000.0, mark=10.0, receive_time=55.0, poll_attempt=9),
        _candidate(event_time=999.0, mark=11.0),  # ooo
        _candidate(event_time=1001.0, mark=10.0),  # distinct same mark
        _candidate(event_time=None, mark=12.0),
        _candidate(event_time=1002.0, mark=-1.0),
        _candidate(event_time=1002.0, mark=12.0),  # distinct
        _candidate(event_time=1002.0, mark=13.0),  # identity conflict
        _candidate(event_time=1003.0, mark=13.0),  # distinct
    ]
    state = initial_observation_acceptance_state_v1()
    prev_epoch = 0
    for cand in events:
        result = evaluate_distinct_market_observation_v1(state, cand)
        after = result.state_after.market_observation_epoch.value
        before = result.state_before.market_observation_epoch.value
        assert after >= before
        assert after - before in (0, 1)
        if result.classification == ObservationClassification.DISTINCT:
            assert after == before + 1
            assert result.strategy_advance_allowed is True
        else:
            assert after == before
            assert result.strategy_advance_allowed is False
        state = commit_observation_acceptance_v1(current_state=state, result=result)
        assert state.market_observation_epoch.value >= prev_epoch
        prev_epoch = state.market_observation_epoch.value
    assert state.market_observation_epoch.value == 4


# ---------------------------------------------------------------------------
# 27 Poll-rate independence
# ---------------------------------------------------------------------------


def test_27_poll_rate_independence_acceptor_level() -> None:
    market_seq = [
        _candidate(event_time=1000.0, mark=10.0, poll_attempt=1, receive_time=1.0),
        _candidate(event_time=1001.0, mark=11.0, poll_attempt=1, receive_time=2.0),
        _candidate(event_time=1002.0, mark=12.0, poll_attempt=1, receive_time=3.0),
    ]
    with_dup_polls = [
        market_seq[0],
        _candidate(event_time=1000.0, mark=10.0, poll_attempt=2, receive_time=1.5),
        _candidate(event_time=1000.0, mark=10.0, poll_attempt=3, receive_time=1.7),
        market_seq[1],
        _candidate(event_time=1001.0, mark=11.0, poll_attempt=2, receive_time=2.5),
        market_seq[2],
        _candidate(event_time=1002.0, mark=12.0, poll_attempt=9, receive_time=9.0),
    ]

    _, state_clean = _accept_sequence(market_seq)
    classes_poll, state_poll = _accept_sequence(with_dup_polls)

    assert state_clean.market_observation_epoch == state_poll.market_observation_epoch
    assert (
        state_clean.last_accepted_observation_identity
        == state_poll.last_accepted_observation_identity
    )
    accepted = [c for c in classes_poll if c == ObservationClassification.DISTINCT]
    assert len(accepted) == 3
    assert state_poll.market_observation_epoch.value == 3


# ---------------------------------------------------------------------------
# Extra: atomicity, compatibility, mapping, epoch type invariants
# ---------------------------------------------------------------------------


def test_atomicity_commit_compare_mismatch_rejected() -> None:
    state = initial_observation_acceptance_state_v1()
    result = evaluate_distinct_market_observation_v1(state, _candidate())
    other = initial_observation_acceptance_state_v1()
    # Force a different state object content-wise after first commit elsewhere
    other = ObservationAcceptanceStateV1(
        last_accepted_observation_identity=None,
        market_observation_epoch=MarketObservationEpoch(value=5),
    )
    with pytest.raises(ValueError, match="commit_compare_mismatch"):
        commit_observation_acceptance_v1(current_state=other, result=result)


def test_market_observation_epoch_rejects_negative_and_bool() -> None:
    with pytest.raises(ValueError):
        MarketObservationEpoch(value=-1)
    with pytest.raises(ValueError):
        MarketObservationEpoch(value=True)  # type: ignore[arg-type]


def test_trading_epoch_compatibility_alias_and_runtime_cycle_reject() -> None:
    assert assert_trading_epoch_alias_target_v1() == "MarketObservationEpoch"
    assert TRADING_EPOCH_ALIAS_TARGET == "MarketObservationEpoch"
    epoch = market_observation_epoch_from_trading_epoch_alias_v1(3)
    assert epoch == MarketObservationEpoch(value=3)
    with pytest.raises(TradingEpochCompatibilityErrorV1):
        market_observation_epoch_from_trading_epoch_alias_v1(-1)
    with pytest.raises(TradingEpochCompatibilityErrorV1):
        assert_runtime_cycle_assignment_rejected_v1(1)


def test_normalized_public_market_data_field_mapping() -> None:
    class _Normalized:
        venue = "okx_eea"
        canonical_instrument_id = "BTC-USD-SWAP-CANON"
        venue_instrument_id = "BTC-USD-SWAP"
        event_ts_unix = 1_700_000_000.0
        mark_px = 42000.5
        receive_ts_unix = 1_700_000_001.0

    identity = observation_identity_from_normalized_public_market_data_v1(_Normalized())
    assert identity.venue_event_time == 1_700_000_000.0
    assert identity.mark_price == 42000.5
    assert "receive_time" not in identity.to_dict()
    assert DISTINCTNESS_IDENTITY_FIELDS == (
        "venue",
        "canonical_instrument_id",
        "venue_instrument_id",
        "venue_event_time",
        "mark_price",
    )
    assert "receive_time" in NON_DISTINCTNESS_AUTHORITY_FIELDS

    candidate = observation_candidate_from_normalized_public_market_data_v1(
        _Normalized(), poll_attempt=2, runtime_cycle_index=8
    )
    assert candidate.transport is not None
    assert candidate.transport.receive_time == 1_700_000_001.0
    assert candidate.transport.runtime_cycle_index == 8

    state = initial_observation_acceptance_state_v1()
    result = evaluate_distinct_market_observation_v1(state, candidate)
    assert result.classification == ObservationClassification.DISTINCT


def test_multi_instrument_separate_states_no_shared_epoch() -> None:
    btc_key = _key(venue_inst="BTC-USD-SWAP", canonical="BTC-CANON")
    eth_key = _key(venue_inst="ETH-USD-SWAP", canonical="ETH-CANON")
    btc_state = initial_observation_acceptance_state_v1(bound_instrument_key=btc_key)
    eth_state = initial_observation_acceptance_state_v1(bound_instrument_key=eth_key)

    btc_r = evaluate_distinct_market_observation_v1(
        btc_state,
        _candidate(venue_inst="BTC-USD-SWAP", canonical="BTC-CANON", event_time=1.0),
    )
    eth_r = evaluate_distinct_market_observation_v1(
        eth_state,
        _candidate(venue_inst="ETH-USD-SWAP", canonical="ETH-CANON", event_time=1.0),
    )
    btc_state = commit_observation_acceptance_v1(current_state=btc_state, result=btc_r)
    eth_state = commit_observation_acceptance_v1(current_state=eth_state, result=eth_r)
    assert btc_state.market_observation_epoch.value == 1
    assert eth_state.market_observation_epoch.value == 1

    # ETH observation against BTC-bound state is conflict, not shared DISTINCT
    cross = evaluate_distinct_market_observation_v1(
        btc_state,
        _candidate(
            venue_inst="ETH-USD-SWAP",
            canonical="ETH-CANON",
            event_time=2.0,
            mark=2000.0,
        ),
    )
    assert cross.classification == ObservationClassification.IDENTITY_CONFLICT


def test_receive_time_cannot_replace_missing_event_time() -> None:
    state = initial_observation_acceptance_state_v1()
    result = evaluate_distinct_market_observation_v1(
        state,
        ObservationCandidateV1(
            venue="okx_eea",
            canonical_instrument_id="BTC-CANON",
            venue_instrument_id="BTC-USD-SWAP",
            venue_event_time=None,
            mark_price=100.0,
            transport=ObservationTransportMetadataV1(receive_time=1_700_000_000.0),
        ),
    )
    assert result.classification == ObservationClassification.INVALID_EVENT_TIME
