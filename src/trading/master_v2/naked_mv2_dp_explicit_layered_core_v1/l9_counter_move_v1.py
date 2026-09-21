"""L9 — counter move CM_t from running reference."""

from __future__ import annotations

from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1
from trading.master_v2.naked_mv2_dp_single_boundary_purification_v1 import (
    compute_counter_move_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    CounterMoveInputV1,
    CounterMoveOutputV1,
    CounterMoveStateV1,
)

L9_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l9_counter_move_v1"


def _regime_to_direction(regime: NakedRegimeV1) -> ScopeDirectionState:
    if regime is NakedRegimeV1.BULL:
        return ScopeDirectionState.LONG
    return ScopeDirectionState.SHORT


def apply_l9_counter_move_v1(inp: CounterMoveInputV1) -> CounterMoveOutputV1:
    direction = _regime_to_direction(inp.regime)
    cm_t = compute_counter_move_v1(
        direction=direction,
        mark_price=float(inp.mark_price_m_t),
        reference_price=float(inp.running_reference.reference_price_r_t),
    )
    return CounterMoveOutputV1(
        counter_move=CounterMoveStateV1(
            instrument_id=inp.running_reference.instrument_id,
            cm_t=cm_t,
        )
    )


__all__ = ["L9_OWNER", "apply_l9_counter_move_v1"]
