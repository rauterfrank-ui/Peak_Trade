from __future__ import annotations

from dataclasses import replace
from typing import Tuple

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationCandidateV1,
    ObservationTransportMetadataV1,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1

from research.multi_future_ghv_counterfactual_distance_lab_v3.state_carrier_v3 import (
    FlightLaneStateRootV3,
)


def instrument_observation_key_v3(instrument_id: str) -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id=instrument_id,
        venue_instrument_id=instrument_id,
    )


def advance_c1_for_cycle_v3(
    state: FlightLaneStateRootV3,
    *,
    instrument_id: str,
    mark_price: float,
    cycle_id: int,
) -> Tuple[ObservationAcceptanceResultV1, FlightLaneStateRootV3]:
    """Productive C1 evaluate+commit; state_N+1 from CURRENT owner output."""
    key = state.confirmation_instrument or instrument_observation_key_v3(instrument_id)
    if state.c1_acceptance_state is None:
        c1_state = initial_observation_acceptance_state_v1(bound_instrument_key=key)
    else:
        c1_state = state.c1_acceptance_state
    event_time = state.c1_event_time_base + float(cycle_id)
    candidate = ObservationCandidateV1(
        venue=key.venue,
        canonical_instrument_id=key.canonical_instrument_id,
        venue_instrument_id=key.venue_instrument_id,
        venue_event_time=event_time,
        mark_price=float(mark_price),
        transport=ObservationTransportMetadataV1(
            receive_time=event_time + 0.5,
            poll_attempt=1,
            runtime_cycle_index=cycle_id,
        ),
    )
    result = evaluate_distinct_market_observation_v1(c1_state, candidate)
    committed = commit_observation_acceptance_v1(current_state=c1_state, result=result)
    updated = replace(
        state,
        c1_acceptance_state=committed,
        previous_mark=float(mark_price),
        confirmation_instrument=key,
    )
    return result, updated
