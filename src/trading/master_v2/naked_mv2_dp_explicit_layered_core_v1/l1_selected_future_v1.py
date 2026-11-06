"""L1 — selected future binding."""

from __future__ import annotations

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    SelectedFutureInputV1,
    SelectedFutureOutputV1,
    SelectedFutureStateV1,
)

L1_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l1_selected_future_v1"


def apply_l1_selected_future_v1(inp: SelectedFutureInputV1) -> SelectedFutureOutputV1:
    key = inp.instrument_key
    if inp.instrument_id != key.canonical_instrument_id:
        raise ValueError("l1_instrument_id_canonical_mismatch")
    state = SelectedFutureStateV1(
        instrument_id=inp.instrument_id,
        instrument_key=key,
    )
    return SelectedFutureOutputV1(state=state)


__all__ = ["L1_OWNER", "apply_l1_selected_future_v1"]
