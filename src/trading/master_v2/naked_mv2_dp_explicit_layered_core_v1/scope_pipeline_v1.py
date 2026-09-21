"""Compose L5 → L6 → L7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    DynamicScopeGeneratorInputV1,
    DynamicScopeGeneratorV1,
    NullLineStateV1,
    ScopeStateMaterializationInputV1,
    ScopeStateV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1 import (
    apply_l6_dynamic_scope_generator_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l7_scope_state_v1 import (
    apply_l7_scope_state_materialization_v1,
)


@dataclass(frozen=True)
class ScopePipelineResultV1:
    scope: Optional[ScopeStateV1]
    fail_closed: bool
    fail_reasons: Tuple[str, ...]
    l6_reached: bool
    l7_reached: bool


def run_scope_l5_through_l7_v1(
    *,
    nullline: NullLineStateV1,
    proposed_d_t: Optional[float],
    generator: DynamicScopeGeneratorV1,
) -> ScopePipelineResultV1:
    l6_inp = DynamicScopeGeneratorInputV1(nullline=nullline, proposed_d_t=proposed_d_t)
    l6 = apply_l6_dynamic_scope_generator_v1(generator, l6_inp)
    if l6.fail_closed:
        return ScopePipelineResultV1(
            scope=None,
            fail_closed=True,
            fail_reasons=l6.fail_reasons,
            l6_reached=True,
            l7_reached=False,
        )
    l7 = apply_l7_scope_state_materialization_v1(
        ScopeStateMaterializationInputV1(nullline=nullline, generator_output=l6)
    )
    if l7.fail_closed:
        return ScopePipelineResultV1(
            scope=None,
            fail_closed=True,
            fail_reasons=l7.fail_reasons,
            l6_reached=True,
            l7_reached=True,
        )
    return ScopePipelineResultV1(
        scope=l7.scope,
        fail_closed=False,
        fail_reasons=(),
        l6_reached=True,
        l7_reached=True,
    )


__all__ = ["ScopePipelineResultV1", "run_scope_l5_through_l7_v1"]
