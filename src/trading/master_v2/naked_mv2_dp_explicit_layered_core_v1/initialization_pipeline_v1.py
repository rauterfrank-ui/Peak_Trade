"""Compose L1 → L2 → L3 → L4 → L5 for chain initialization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationCandidateV1,
    ObservationClassification,
)
from trading.market_state.elementary_direction_v1 import ElementaryDirectionV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    InitialDirectionInputV1,
    InitialStateInitializationInputV1,
    MarketObservationInputV1,
    NullLineInputV1,
    NullLineStateV1,
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l1_selected_future_v1 import (
    apply_l1_selected_future_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l2_market_observation_v1 import (
    apply_l2_market_observation_v1,
    initial_market_observation_state_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l3_initial_direction_v1 import (
    apply_l3_initial_direction_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l4_initial_state_v1 import (
    apply_l4_initial_state_initialization_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l5_nullline_v1 import (
    apply_l5_nullline_v1,
)


@dataclass(frozen=True)
class InitializationPipelineResultV1:
    nullline: Optional[NullLineStateV1]
    fail_closed: bool
    fail_reasons: Tuple[str, ...]
    l4_reached: bool
    l5_reached: bool


def run_initialization_l1_through_l5_v1(
    *,
    selected: SelectedFutureInputV1,
    observation_candidates: Sequence[ObservationCandidateV1],
) -> InitializationPipelineResultV1:
    l1 = apply_l1_selected_future_v1(selected)
    obs_state = initial_market_observation_state_v1(l1.state)

    for candidate in observation_candidates:
        l2 = apply_l2_market_observation_v1(
            MarketObservationInputV1(
                observation_state=obs_state,
                candidate=candidate,
            )
        )
        obs_state = l2.observation_state
        if l2.acceptance_result.classification is not ObservationClassification.DISTINCT:
            continue

        mark = float(candidate.mark_price)  # type: ignore[arg-type]
        l3 = apply_l3_initial_direction_v1(
            InitialDirectionInputV1(
                acceptance_result=l2.acceptance_result,
                bound_instrument_key=l1.state.instrument_key,
                current_mark=mark,
            )
        )
        direction = l3.direction_result.direction
        if direction not in (ElementaryDirectionV1.BULL, ElementaryDirectionV1.BEAR):
            continue

        l4 = apply_l4_initial_state_initialization_v1(
            InitialStateInitializationInputV1(
                selected=l1.state,
                direction=l3,
                initialization_mark=mark,
            )
        )
        if l4.fail_closed:
            return InitializationPipelineResultV1(
                nullline=None,
                fail_closed=True,
                fail_reasons=l4.fail_reasons,
                l4_reached=True,
                l5_reached=False,
            )

        epoch = int(l2.acceptance_result.state_after.market_observation_epoch.value)
        l5 = apply_l5_nullline_v1(
            NullLineInputV1(
                regime_state=l4.regime_state,
                initialization_mark=mark,
                market_observation_epoch=epoch,
            )
        )
        return InitializationPipelineResultV1(
            nullline=l5.nullline,
            fail_closed=False,
            fail_reasons=(),
            l4_reached=True,
            l5_reached=True,
        )

    return InitializationPipelineResultV1(
        nullline=None,
        fail_closed=True,
        fail_reasons=("l4_l5_not_reached_no_distinct_initial_direction",),
        l4_reached=False,
        l5_reached=False,
    )


__all__ = [
    "InitializationPipelineResultV1",
    "run_initialization_l1_through_l5_v1",
]
