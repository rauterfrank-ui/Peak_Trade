"""L6 — replaceable dynamic scope generator (explicit D_t validation only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from trading.master_v2.naked_mv2_dp_single_boundary_purification_v1 import (
    naked_boundary_fail_closed_reasons_from_distance,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    DynamicScopeGeneratorInputV1,
    DynamicScopeGeneratorOutputV1,
    DynamicScopeGeneratorV1,
)

L6_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1"
EXPLICIT_PASSTHROUGH_GENERATOR_ID = "explicit_external_d_t_passthrough/v1"


@dataclass(frozen=True)
class ExplicitPassthroughDynamicScopeGeneratorV1:
    """Validates and passes caller-supplied D_t; no formula selection."""

    generator_id: str = EXPLICIT_PASSTHROUGH_GENERATOR_ID

    def generate(self, inp: DynamicScopeGeneratorInputV1) -> DynamicScopeGeneratorOutputV1:
        reasons = naked_boundary_fail_closed_reasons_from_distance(inp.proposed_d_t)
        if reasons:
            return DynamicScopeGeneratorOutputV1(
                d_t=inp.proposed_d_t,
                fail_closed=True,
                fail_reasons=reasons,
                generator_id=self.generator_id,
            )
        assert inp.proposed_d_t is not None
        return DynamicScopeGeneratorOutputV1(
            d_t=float(inp.proposed_d_t),
            fail_closed=False,
            fail_reasons=(),
            generator_id=self.generator_id,
        )


def apply_l6_dynamic_scope_generator_v1(
    generator: DynamicScopeGeneratorV1,
    inp: DynamicScopeGeneratorInputV1,
) -> DynamicScopeGeneratorOutputV1:
    return generator.generate(inp)


__all__ = [
    "L6_OWNER",
    "EXPLICIT_PASSTHROUGH_GENERATOR_ID",
    "ExplicitPassthroughDynamicScopeGeneratorV1",
    "apply_l6_dynamic_scope_generator_v1",
]
