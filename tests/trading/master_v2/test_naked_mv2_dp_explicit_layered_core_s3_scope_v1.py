"""S3 — L6–L7 dynamic scope pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    DynamicScopeGeneratorInputV1,
    DynamicScopeGeneratorOutputV1,
    NullLineStateV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1 import (
    ExplicitPassthroughDynamicScopeGeneratorV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.scope_pipeline_v1 import (
    run_scope_l5_through_l7_v1,
)


def _nullline() -> NullLineStateV1:
    return NullLineStateV1(
        instrument_id="BTC-PERP",
        nullline_price=100.0,
        provenance_mark_epoch=2,
    )


def test_valid_d_t_materializes_scope_with_nullline_provenance() -> None:
    gen = ExplicitPassthroughDynamicScopeGeneratorV1()
    result = run_scope_l5_through_l7_v1(
        nullline=_nullline(),
        proposed_d_t=5.0,
        generator=gen,
    )
    assert not result.fail_closed
    assert result.l7_reached
    assert result.scope is not None
    assert result.scope.d_t == 5.0
    assert result.scope.nullline_price == 100.0
    assert result.scope.nullline_provenance_epoch == 2


def test_missing_d_t_fail_closed_l6_l7_not_reached() -> None:
    gen = ExplicitPassthroughDynamicScopeGeneratorV1()
    result = run_scope_l5_through_l7_v1(
        nullline=_nullline(),
        proposed_d_t=None,
        generator=gen,
    )
    assert result.fail_closed
    assert result.l6_reached
    assert result.l7_reached is False
    assert "naked_boundary_distance_unavailable" in result.fail_reasons


@dataclass(frozen=True)
class FixedTestScopeGeneratorV1:
    fixed_d_t: float
    generator_id: str = "test_fixed_scope_generator/v1"

    def generate(self, inp: DynamicScopeGeneratorInputV1) -> DynamicScopeGeneratorOutputV1:
        _ = inp
        return DynamicScopeGeneratorOutputV1(
            d_t=self.fixed_d_t,
            fail_closed=False,
            fail_reasons=(),
            generator_id=self.generator_id,
        )


def test_replaceable_generator_changes_d_t_only() -> None:
    nullline = _nullline()
    baseline = run_scope_l5_through_l7_v1(
        nullline=nullline,
        proposed_d_t=5.0,
        generator=ExplicitPassthroughDynamicScopeGeneratorV1(),
    )
    alt = run_scope_l5_through_l7_v1(
        nullline=nullline,
        proposed_d_t=None,
        generator=FixedTestScopeGeneratorV1(fixed_d_t=9.0),
    )
    assert baseline.scope is not None and alt.scope is not None
    assert baseline.scope.nullline_price == alt.scope.nullline_price
    assert baseline.scope.d_t == 5.0
    assert alt.scope.d_t == 9.0
    assert alt.scope.generator_id == "test_fixed_scope_generator/v1"
