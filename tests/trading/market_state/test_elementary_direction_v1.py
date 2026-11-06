"""Deterministic tests for elementary C1 mark-to-mark direction identity."""

from __future__ import annotations

import math

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationCandidateV1,
    ObservationClassification,
    ObservationReasonCode,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.elementary_direction_v1 import (
    AUTHORITY_EFFECT_NONE,
    ELEMENTARY_DIRECTION_COMPONENT,
    ELEMENTARY_DIRECTION_PURITY,
    ORDER_EFFECT_NONE,
    RUNTIME_EFFECT_NONE,
    ElementaryDirectionReasonCodeV1,
    ElementaryDirectionStatusV1,
    ElementaryDirectionV1,
    evaluate_elementary_direction_from_observation_acceptance_v1,
    evaluate_elementary_direction_v1,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1


def _key(
    *,
    venue: str = "okx_eea",
    canonical: str = "ETH-USD-SWAP-CANON",
    venue_inst: str = "ETH-USD-SWAP",
) -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue=venue,
        canonical_instrument_id=canonical,
        venue_instrument_id=venue_inst,
    )


def _candidate(
    *,
    venue: str = "okx_eea",
    canonical: str = "ETH-USD-SWAP-CANON",
    venue_inst: str = "ETH-USD-SWAP",
    event_time: float = 1_700_000_000.0,
    mark: float = 3000.0,
) -> ObservationCandidateV1:
    return ObservationCandidateV1(
        venue=venue,
        canonical_instrument_id=canonical,
        venue_instrument_id=venue_inst,
        venue_event_time=event_time,
        mark_price=mark,
    )


def test_component_is_identity_only() -> None:
    assert ELEMENTARY_DIRECTION_COMPONENT == "ElementaryDirectionV1"
    assert ELEMENTARY_DIRECTION_PURITY == "PURE_DETERMINISTIC_NO_IO"
    assert set(item.value for item in ElementaryDirectionV1) == {"bull", "bear", "neutral"}
    assert "long" not in {item.value for item in ElementaryDirectionV1}
    assert "short" not in {item.value for item in ElementaryDirectionV1}


def test_first_observation_none_previous_is_neutral() -> None:
    result = evaluate_elementary_direction_v1(previous_mark=None, current_mark=3000.0)
    assert result.status is ElementaryDirectionStatusV1.EVALUATED
    assert result.direction is ElementaryDirectionV1.NEUTRAL
    assert result.previous_mark is None
    assert result.current_mark == 3000.0
    assert result.reason_code == ElementaryDirectionReasonCodeV1.FIRST_OBSERVATION.value
    assert result.authority_effect == AUTHORITY_EFFECT_NONE
    assert result.runtime_effect == RUNTIME_EFFECT_NONE
    assert result.order_effect == ORDER_EFFECT_NONE


def test_equal_marks_are_neutral() -> None:
    result = evaluate_elementary_direction_v1(previous_mark=3000.0, current_mark=3000.0)
    assert result.direction is ElementaryDirectionV1.NEUTRAL
    assert result.reason_code == ElementaryDirectionReasonCodeV1.MARK_UNCHANGED.value


def test_increase_is_bull() -> None:
    result = evaluate_elementary_direction_v1(previous_mark=3000.0, current_mark=3000.25)
    assert result.direction is ElementaryDirectionV1.BULL
    assert result.reason_code == ElementaryDirectionReasonCodeV1.MARK_INCREASED.value
    assert result.previous_mark == 3000.0
    assert result.current_mark == 3000.25


def test_decrease_is_bear() -> None:
    result = evaluate_elementary_direction_v1(previous_mark=3000.0, current_mark=2999.5)
    assert result.direction is ElementaryDirectionV1.BEAR
    assert result.reason_code == ElementaryDirectionReasonCodeV1.MARK_DECREASED.value


def test_invalid_current_mark_is_rejected_not_neutral() -> None:
    for raw, code in (
        (None, ElementaryDirectionReasonCodeV1.INVALID_CURRENT_MARK_MISSING),
        (math.nan, ElementaryDirectionReasonCodeV1.INVALID_CURRENT_MARK_NON_FINITE),
        (math.inf, ElementaryDirectionReasonCodeV1.INVALID_CURRENT_MARK_NON_FINITE),
        (0.0, ElementaryDirectionReasonCodeV1.INVALID_CURRENT_MARK_NON_POSITIVE),
        (-1.0, ElementaryDirectionReasonCodeV1.INVALID_CURRENT_MARK_NON_POSITIVE),
        (True, ElementaryDirectionReasonCodeV1.INVALID_CURRENT_MARK_NON_FINITE),
        ("3000", ElementaryDirectionReasonCodeV1.INVALID_CURRENT_MARK_NON_FINITE),
    ):
        result = evaluate_elementary_direction_v1(previous_mark=None, current_mark=raw)
        assert result.status is ElementaryDirectionStatusV1.REJECTED
        assert result.direction is None
        assert result.reason_code == code.value


def test_invalid_previous_mark_is_rejected_not_neutral() -> None:
    result = evaluate_elementary_direction_v1(previous_mark=math.nan, current_mark=3000.0)
    assert result.status is ElementaryDirectionStatusV1.REJECTED
    assert result.direction is None
    assert (
        result.reason_code == ElementaryDirectionReasonCodeV1.INVALID_PREVIOUS_MARK_NON_FINITE.value
    )


def test_join_first_distinct_is_neutral_from_state_before_none() -> None:
    bound = _key()
    state = initial_observation_acceptance_state_v1(bound_instrument_key=bound)
    acceptance = evaluate_distinct_market_observation_v1(state, _candidate(mark=3000.0))
    assert acceptance.classification is ObservationClassification.DISTINCT
    assert acceptance.state_before.last_accepted_observation_identity is None
    result = evaluate_elementary_direction_from_observation_acceptance_v1(
        acceptance,
        bound_instrument_key=bound,
        current_mark=3000.0,
    )
    assert result.direction is ElementaryDirectionV1.NEUTRAL
    assert result.previous_mark is None
    assert result.reason_code == ElementaryDirectionReasonCodeV1.FIRST_OBSERVATION.value


def test_join_predecessor_is_state_before_not_state_after() -> None:
    bound = _key()
    first = evaluate_distinct_market_observation_v1(
        initial_observation_acceptance_state_v1(bound_instrument_key=bound),
        _candidate(event_time=1_700_000_000.0, mark=3000.0),
    )
    second = evaluate_distinct_market_observation_v1(
        first.state_after,
        _candidate(event_time=1_700_000_060.0, mark=3010.0),
    )
    assert second.classification is ObservationClassification.DISTINCT
    before = second.state_before.last_accepted_observation_identity
    after = second.state_after.last_accepted_observation_identity
    assert before is not None and after is not None
    assert before.mark_price == 3000.0
    assert after.mark_price == 3010.0
    result = evaluate_elementary_direction_from_observation_acceptance_v1(
        second,
        bound_instrument_key=bound,
        current_mark=3010.0,
    )
    assert result.direction is ElementaryDirectionV1.BULL
    assert result.previous_mark == 3000.0
    assert result.current_mark == 3010.0
    assert result.previous_mark != after.mark_price


def test_join_equal_distinct_marks_are_neutral() -> None:
    bound = _key()
    first = evaluate_distinct_market_observation_v1(
        initial_observation_acceptance_state_v1(bound_instrument_key=bound),
        _candidate(event_time=1_700_000_000.0, mark=3000.0),
    )
    second = evaluate_distinct_market_observation_v1(
        first.state_after,
        _candidate(event_time=1_700_000_060.0, mark=3000.0),
    )
    result = evaluate_elementary_direction_from_observation_acceptance_v1(
        second,
        bound_instrument_key=bound,
        current_mark=3000.0,
    )
    assert result.direction is ElementaryDirectionV1.NEUTRAL
    assert result.reason_code == ElementaryDirectionReasonCodeV1.MARK_UNCHANGED.value


def test_join_decrease_is_bear() -> None:
    bound = _key()
    first = evaluate_distinct_market_observation_v1(
        initial_observation_acceptance_state_v1(bound_instrument_key=bound),
        _candidate(event_time=1_700_000_000.0, mark=3000.0),
    )
    second = evaluate_distinct_market_observation_v1(
        first.state_after,
        _candidate(event_time=1_700_000_060.0, mark=2990.0),
    )
    result = evaluate_elementary_direction_from_observation_acceptance_v1(
        second,
        bound_instrument_key=bound,
        current_mark=2990.0,
    )
    assert result.direction is ElementaryDirectionV1.BEAR


def test_join_instrument_mismatch_does_not_normalize() -> None:
    bound = _key()
    other = _key(canonical="SOL-USD-SWAP-CANON", venue_inst="SOL-USD-SWAP")
    first = evaluate_distinct_market_observation_v1(
        initial_observation_acceptance_state_v1(bound_instrument_key=bound),
        _candidate(event_time=1_700_000_000.0, mark=3000.0),
    )
    second = evaluate_distinct_market_observation_v1(
        first.state_after,
        _candidate(event_time=1_700_000_060.0, mark=3010.0),
    )
    result = evaluate_elementary_direction_from_observation_acceptance_v1(
        second,
        bound_instrument_key=other,
        current_mark=3010.0,
    )
    assert result.status is ElementaryDirectionStatusV1.REJECTED
    assert result.direction is None
    assert result.reason_code == ElementaryDirectionReasonCodeV1.INSTRUMENT_MISMATCH.value


def test_join_rejects_candle_close_substitution_as_current_mark() -> None:
    bound = _key()
    first = evaluate_distinct_market_observation_v1(
        initial_observation_acceptance_state_v1(bound_instrument_key=bound),
        _candidate(event_time=1_700_000_000.0, mark=3000.0),
    )
    second = evaluate_distinct_market_observation_v1(
        first.state_after,
        _candidate(event_time=1_700_000_060.0, mark=3010.0),
    )
    candle_close = 3015.0
    result = evaluate_elementary_direction_from_observation_acceptance_v1(
        second,
        bound_instrument_key=bound,
        current_mark=candle_close,
    )
    assert result.status is ElementaryDirectionStatusV1.REJECTED
    assert result.direction is None
    assert (
        result.reason_code == ElementaryDirectionReasonCodeV1.CURRENT_MARK_PROVENANCE_MISMATCH.value
    )


def test_join_rejects_trailing_anchor_substitution_as_current_mark() -> None:
    bound = _key()
    first = evaluate_distinct_market_observation_v1(
        initial_observation_acceptance_state_v1(bound_instrument_key=bound),
        _candidate(event_time=1_700_000_000.0, mark=3000.0),
    )
    trailing_anchor = 2800.0
    result = evaluate_elementary_direction_from_observation_acceptance_v1(
        first,
        bound_instrument_key=bound,
        current_mark=trailing_anchor,
    )
    assert result.status is ElementaryDirectionStatusV1.REJECTED
    assert result.reason_code == (
        ElementaryDirectionReasonCodeV1.CURRENT_MARK_PROVENANCE_MISMATCH.value
    )


def test_join_c1_fail_closed_is_not_neutral() -> None:
    bound = _key()
    first = evaluate_distinct_market_observation_v1(
        initial_observation_acceptance_state_v1(bound_instrument_key=bound),
        _candidate(event_time=1_700_000_100.0, mark=3000.0),
    )
    out_of_order = evaluate_distinct_market_observation_v1(
        first.state_after,
        _candidate(event_time=1_700_000_000.0, mark=4000.0),
    )
    assert out_of_order.classification is ObservationClassification.OUT_OF_ORDER
    result = evaluate_elementary_direction_from_observation_acceptance_v1(
        out_of_order,
        bound_instrument_key=bound,
        current_mark=4000.0,
    )
    assert result.status is ElementaryDirectionStatusV1.REJECTED
    assert result.direction is None
    assert result.reason_code.startswith(ElementaryDirectionReasonCodeV1.C1_NOT_COMPARABLE.value)


def test_join_identity_conflict_is_not_neutral() -> None:
    bound = _key()
    incoming = _candidate(
        canonical="SOL-USD-SWAP-CANON",
        venue_inst="SOL-USD-SWAP",
        event_time=1_700_000_060.0,
        mark=3010.0,
    )
    result_c1 = evaluate_distinct_market_observation_v1(
        initial_observation_acceptance_state_v1(bound_instrument_key=bound),
        incoming,
    )
    assert result_c1.classification is ObservationClassification.IDENTITY_CONFLICT
    assert result_c1.reason_code in {
        ObservationReasonCode.IDENTITY_CONFLICT_CANONICAL_MAPPING.value,
        ObservationReasonCode.IDENTITY_CONFLICT_INSTRUMENT.value,
    }
    result = evaluate_elementary_direction_from_observation_acceptance_v1(
        result_c1,
        bound_instrument_key=bound,
        current_mark=3010.0,
    )
    assert result.status is ElementaryDirectionStatusV1.REJECTED
    assert result.direction is None
