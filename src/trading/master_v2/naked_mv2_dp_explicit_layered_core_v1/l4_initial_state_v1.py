"""L4 — initial BULL/BEAR regime establishment (no neutral fallback)."""

from __future__ import annotations

from trading.market_state.elementary_direction_v1 import (
    ElementaryDirectionStatusV1,
    ElementaryDirectionV1,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    InitialStateInitializationInputV1,
    InitialStateInitializationOutputV1,
    InitialRegimeStateV1,
)

L4_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l4_initial_state_v1"


def apply_l4_initial_state_initialization_v1(
    inp: InitialStateInitializationInputV1,
) -> InitialStateInitializationOutputV1:
    dr = inp.direction.direction_result
    if dr.status is not ElementaryDirectionStatusV1.EVALUATED:
        return InitialStateInitializationOutputV1(
            regime_state=InitialRegimeStateV1(
                instrument_id=inp.selected.instrument_id,
                regime=NakedRegimeV1.BULL,
            ),
            fail_closed=True,
            fail_reasons=(f"l4_direction_rejected:{dr.reason_code}",),
        )
    if dr.direction is ElementaryDirectionV1.NEUTRAL:
        return InitialStateInitializationOutputV1(
            regime_state=InitialRegimeStateV1(
                instrument_id=inp.selected.instrument_id,
                regime=NakedRegimeV1.BULL,
            ),
            fail_closed=True,
            fail_reasons=(f"l4_no_distinct_initial_direction:{dr.reason_code}",),
        )
    regime = (
        NakedRegimeV1.BULL if dr.direction is ElementaryDirectionV1.BULL else NakedRegimeV1.BEAR
    )
    return InitialStateInitializationOutputV1(
        regime_state=InitialRegimeStateV1(
            instrument_id=inp.selected.instrument_id,
            regime=regime,
        ),
        fail_closed=False,
        fail_reasons=(),
    )


__all__ = ["L4_OWNER", "apply_l4_initial_state_initialization_v1"]
