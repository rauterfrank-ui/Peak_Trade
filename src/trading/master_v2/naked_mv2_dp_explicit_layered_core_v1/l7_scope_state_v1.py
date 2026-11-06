"""L7 — materialize scope state from validated D_t and NullLine provenance."""

from __future__ import annotations

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    ScopeStateMaterializationInputV1,
    ScopeStateMaterializationOutputV1,
    ScopeStateV1,
)

L7_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l7_scope_state_v1"


def apply_l7_scope_state_materialization_v1(
    inp: ScopeStateMaterializationInputV1,
) -> ScopeStateMaterializationOutputV1:
    gen = inp.generator_output
    if gen.fail_closed or gen.d_t is None:
        return ScopeStateMaterializationOutputV1(
            scope=None,
            fail_closed=True,
            fail_reasons=gen.fail_reasons or ("l7_generator_fail_closed",),
        )
    nullline = inp.nullline
    scope = ScopeStateV1(
        instrument_id=nullline.instrument_id,
        d_t=float(gen.d_t),
        nullline_price=nullline.nullline_price,
        nullline_provenance_epoch=nullline.provenance_mark_epoch,
        generator_id=gen.generator_id,
        valid=True,
    )
    return ScopeStateMaterializationOutputV1(
        scope=scope,
        fail_closed=False,
        fail_reasons=(),
    )


__all__ = ["L7_OWNER", "apply_l7_scope_state_materialization_v1"]
