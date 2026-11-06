"""S2 — L1–L5 initialization pipeline."""

from __future__ import annotations

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationCandidateV1,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.initialization_pipeline_v1 import (
    run_initialization_l1_through_l5_v1,
)
from trading.master_v2.naked_mv2_dp_mechanical_core_v1 import NakedRegimeV1


def _key() -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id="BTC-PERP",
        venue_instrument_id="BTC-USDT-SWAP",
    )


def _selected() -> SelectedFutureInputV1:
    key = _key()
    return SelectedFutureInputV1(instrument_id=key.canonical_instrument_id, instrument_key=key)


def _cand(*, t: float, mark: float) -> ObservationCandidateV1:
    key = _key()
    return ObservationCandidateV1(
        venue=key.venue,
        canonical_instrument_id=key.canonical_instrument_id,
        venue_instrument_id=key.venue_instrument_id,
        venue_event_time=t,
        mark_price=mark,
    )


def test_rising_initialization_reaches_nullline_bull() -> None:
    result = run_initialization_l1_through_l5_v1(
        selected=_selected(),
        observation_candidates=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=105.0)],
    )
    assert not result.fail_closed
    assert result.l5_reached
    assert result.nullline is not None
    assert result.nullline.nullline_price == 105.0


def test_falling_initialization_reaches_nullline_bear() -> None:
    result = run_initialization_l1_through_l5_v1(
        selected=_selected(),
        observation_candidates=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=95.0)],
    )
    assert not result.fail_closed
    assert result.nullline is not None
    assert result.nullline.nullline_price == 95.0


def test_equal_second_distinct_fail_closed_before_l5() -> None:
    result = run_initialization_l1_through_l5_v1(
        selected=_selected(),
        observation_candidates=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=100.0)],
    )
    assert result.fail_closed
    assert result.l5_reached is False


def test_single_observation_fail_closed_before_l4() -> None:
    result = run_initialization_l1_through_l5_v1(
        selected=_selected(),
        observation_candidates=[_cand(t=1.0, mark=100.0)],
    )
    assert result.fail_closed
    assert result.l4_reached is False
    assert result.l5_reached is False


def test_nullline_is_not_running_reference_field() -> None:
    result = run_initialization_l1_through_l5_v1(
        selected=_selected(),
        observation_candidates=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=101.0)],
    )
    assert result.nullline is not None
    assert hasattr(result.nullline, "nullline_price")
    assert not hasattr(result.nullline, "reference_price_r_t")
