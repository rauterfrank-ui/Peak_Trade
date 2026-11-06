"""L5 — explicit NullLine / initial price basis (not R_t)."""

from __future__ import annotations

import math

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    NullLineInputV1,
    NullLineOutputV1,
    NullLineStateV1,
)

L5_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l5_nullline_v1"


def apply_l5_nullline_v1(inp: NullLineInputV1) -> NullLineOutputV1:
    mark = float(inp.initialization_mark)
    if not math.isfinite(mark) or mark <= 0.0:
        raise ValueError("l5_initialization_mark_invalid")
    nullline = NullLineStateV1(
        instrument_id=inp.regime_state.instrument_id,
        nullline_price=mark,
        provenance_mark_epoch=int(inp.market_observation_epoch),
    )
    return NullLineOutputV1(nullline=nullline)


__all__ = ["L5_OWNER", "apply_l5_nullline_v1"]
