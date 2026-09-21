"""L2 — distinct market observation acceptance (C1)."""

from __future__ import annotations

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationClassification,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    MarketObservationInputV1,
    MarketObservationOutputV1,
    MarketObservationStateV1,
    SelectedFutureStateV1,
)

L2_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l2_market_observation_v1"


def initial_market_observation_state_v1(
    selected: SelectedFutureStateV1,
) -> MarketObservationStateV1:
    return MarketObservationStateV1(
        selected=selected,
        acceptance_state=initial_observation_acceptance_state_v1(
            bound_instrument_key=selected.instrument_key,
        ),
    )


def apply_l2_market_observation_v1(
    inp: MarketObservationInputV1,
) -> MarketObservationOutputV1:
    selected = inp.observation_state.selected
    result = evaluate_distinct_market_observation_v1(
        inp.observation_state.acceptance_state,
        inp.candidate,
    )
    if result.classification is ObservationClassification.DISTINCT:
        committed = commit_observation_acceptance_v1(
            current_state=inp.observation_state.acceptance_state,
            result=result,
        )
        next_state = MarketObservationStateV1(
            selected=selected,
            acceptance_state=committed,
        )
    else:
        next_state = inp.observation_state
    return MarketObservationOutputV1(
        observation_state=next_state,
        acceptance_result=result,
    )


__all__ = [
    "L2_OWNER",
    "initial_market_observation_state_v1",
    "apply_l2_market_observation_v1",
]
