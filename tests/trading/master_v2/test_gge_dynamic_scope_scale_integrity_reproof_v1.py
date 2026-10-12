"""GGE × price scale covariance and fail-closed reproof (synthetic vectors only)."""

from __future__ import annotations

import math

import pytest

from trading.master_v2.canonical_volatility_estimate_feature_contract_v1 import (
    OUTPUT_UNIT as G17_OUTPUT_UNIT,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    compute_raw_volatility_times_price_scope_distance_v1,
)
from trading.master_v2.golden_geometry_engine_v1 import (
    GGE_OUTPUT_UNIT,
    compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1,
)
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    resolve_layer_c_event_distances_from_mark_and_volatility_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l10_bull_bear_switch_v1 import (
    apply_l10_bull_bear_switch_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    BullBearSwitchInputV1,
    RunningReferenceStateV1,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1
from tests.trading.master_v2.test_golden_geometry_engine_v1 import _ctx

REPRESENTATIVE_MARKS = (
    pytest.param(1e-5, id="P_0.00001"),
    pytest.param(0.02, id="P_0.02"),
    pytest.param(1.0, id="P_1"),
    pytest.param(100.0, id="P_100"),
    pytest.param(50_000.0, id="P_50000"),
    pytest.param(100_000.0, id="P_100000"),
)

SIGMA = 0.02
REL_TOL = 1e-9
ABS_TOL = 0.0


@pytest.mark.parametrize("mark", REPRESENTATIVE_MARKS)
def test_gge_distance_scales_linearly_with_mark(mark: float) -> None:
    result = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="scale-reproof",
        mark_price=float(mark),
        volatility_estimate=SIGMA,
    )
    assert result.ok and result.output is not None
    assert result.output.magnitude == pytest.approx(SIGMA * mark, rel=REL_TOL, abs=ABS_TOL)


def test_gge_scale_covariance_ratio_across_marks() -> None:
    p1, p2 = 0.02, 50_000.0
    d1 = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="a", mark_price=p1, volatility_estimate=SIGMA
    )
    d2 = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="b", mark_price=p2, volatility_estimate=SIGMA
    )
    assert d1.ok and d2.ok and d1.output and d2.output
    ratio = d2.output.magnitude / d1.output.magnitude
    assert ratio == pytest.approx(p2 / p1, rel=REL_TOL)


@pytest.mark.parametrize("mark", REPRESENTATIVE_MARKS)
def test_productive_raw_scope_adapter_matches_gge(mark: float) -> None:
    ctx = _ctx(mark=mark, sigma=SIGMA)
    raw = compute_raw_volatility_times_price_scope_distance_v1(ctx)
    gge = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id=ctx.instrument_id,
        mark_price=mark,
        volatility_estimate=SIGMA,
    )
    assert raw.failure_codes == ()
    assert gge.ok and gge.output is not None
    assert raw.distance == pytest.approx(gge.output.magnitude)
    assert raw.mark_price == pytest.approx(mark)
    assert raw.volatility_estimate == pytest.approx(SIGMA)


def test_layer_c_distances_scale_with_gge_magnitude() -> None:
    low = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
        mark_price=0.02, volatility_estimate=SIGMA, instrument_id="low"
    )
    high = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
        mark_price=100_000.0, volatility_estimate=SIGMA, instrument_id="high"
    )
    assert low.ok and high.ok
    assert low.dynamic_scope_magnitude is not None
    assert high.dynamic_scope_magnitude is not None
    ratio = high.dynamic_scope_magnitude / low.dynamic_scope_magnitude
    assert ratio == pytest.approx(100_000.0 / 0.02, rel=REL_TOL)
    assert low.up_distance is not None and high.up_distance is not None
    assert high.up_distance / low.up_distance == pytest.approx(ratio, rel=REL_TOL)


def test_l10_compares_cm_and_d_in_same_price_units() -> None:
    d_t = SIGMA * 100.0
    ref = RunningReferenceStateV1(instrument_id="u", reference_price_r_t=100.0)
    below = apply_l10_bull_bear_switch_v1(
        BullBearSwitchInputV1(
            regime_pre=NakedRegimeV1.BULL,
            cm_t=d_t - 1e-6,
            d_t=d_t,
            mark_price_m_t=100.0,
            running_reference_post=ref,
        )
    )
    at = apply_l10_bull_bear_switch_v1(
        BullBearSwitchInputV1(
            regime_pre=NakedRegimeV1.BULL,
            cm_t=d_t,
            d_t=d_t,
            mark_price_m_t=100.0,
            running_reference_post=ref,
        )
    )
    assert below.switch_condition_met is False
    assert at.switch_condition_met is True


@pytest.mark.parametrize(
    "mark,sigma,code",
    [
        (100.0, float("nan"), "volatility_non_positive"),
        (float("inf"), 0.01, "mark_price_non_positive"),
        (-1.0, 0.01, "mark_price_non_positive"),
        (100.0, 0.0, "volatility_non_positive"),
    ],
)
def test_gge_fail_closed_invalid_inputs(mark: float, sigma: float, code: str) -> None:
    result = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="invalid",
        mark_price=mark,
        volatility_estimate=sigma,
    )
    assert not result.ok
    assert code in result.failure_codes
    assert result.output is None


def test_small_price_distance_not_collapsed_to_zero() -> None:
    mark = 1e-5
    result = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="micro",
        mark_price=mark,
        volatility_estimate=SIGMA,
    )
    assert result.ok and result.output is not None
    expected = SIGMA * mark
    assert expected > 0.0
    assert result.output.magnitude == pytest.approx(expected)
    assert math.isfinite(result.output.magnitude)


def test_g17_and_gge_unit_semantics_documented() -> None:
    assert G17_OUTPUT_UNIT  # fraction / bar volatility contract
    assert GGE_OUTPUT_UNIT == "canonical_mark_price_unit"
