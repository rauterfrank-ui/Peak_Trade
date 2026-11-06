"""L3 — initial direction from consecutive distinct C1 marks."""

from __future__ import annotations

from trading.market_state.elementary_direction_v1 import (
    evaluate_elementary_direction_from_observation_acceptance_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    InitialDirectionInputV1,
    InitialDirectionOutputV1,
)

L3_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l3_initial_direction_v1"


def apply_l3_initial_direction_v1(inp: InitialDirectionInputV1) -> InitialDirectionOutputV1:
    direction = evaluate_elementary_direction_from_observation_acceptance_v1(
        inp.acceptance_result,
        bound_instrument_key=inp.bound_instrument_key,
        current_mark=inp.current_mark,
    )
    return InitialDirectionOutputV1(direction_result=direction)


__all__ = ["L3_OWNER", "apply_l3_initial_direction_v1"]
