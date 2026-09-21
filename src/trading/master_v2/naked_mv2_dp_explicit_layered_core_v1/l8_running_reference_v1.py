"""L8 — running reference R_t (distinct from NullLine)."""

from __future__ import annotations

import math

from trading.master_v2.double_play_state import ActiveSide, RuntimeScopeState
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1
from trading.master_v2.naked_mv2_dp_single_boundary_purification_v1 import (
    update_scope_internal_reference_state_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    RunningReferenceStateV1,
    RunningReferenceStepInputV1,
    RunningReferenceStepOutputV1,
)

L8_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l8_running_reference_v1"


def _regime_to_side(regime: NakedRegimeV1) -> ActiveSide:
    if regime is NakedRegimeV1.BULL:
        return ActiveSide.LONG
    return ActiveSide.SHORT


def initial_running_reference_state_v1(
    *,
    instrument_id: str,
    reference_price_r_t: float,
) -> RunningReferenceStateV1:
    return RunningReferenceStateV1(
        instrument_id=instrument_id,
        reference_price_r_t=float(reference_price_r_t),
    )


def apply_l8_running_reference_step_v1(
    inp: RunningReferenceStepInputV1,
) -> RunningReferenceStepOutputV1:
    m_t = float(inp.mark_price_m_t)
    if not math.isfinite(m_t) or m_t <= 0.0:
        raise ValueError("l8_mark_price_invalid")
    prev_r = float(inp.previous.reference_price_r_t)
    runtime = RuntimeScopeState(anchor_price=prev_r)
    side = _regime_to_side(inp.regime)
    runtime_post = update_scope_internal_reference_state_v1(
        mark_price=m_t,
        side=side,
        st=runtime,
    )
    updated = float(runtime_post.anchor_price)
    return RunningReferenceStepOutputV1(
        previous_r_t=prev_r,
        updated_r_t=updated,
        state=RunningReferenceStateV1(
            instrument_id=inp.previous.instrument_id,
            reference_price_r_t=updated,
        ),
    )


__all__ = [
    "L8_OWNER",
    "initial_running_reference_state_v1",
    "apply_l8_running_reference_step_v1",
]
