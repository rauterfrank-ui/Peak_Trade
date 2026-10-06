"""Golden Geometry Engine V1 — contract, invariants, golden vectors, scale and edge cases."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    FEATURE_CONTRACT_VERSION,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.golden_geometry_engine_v1 import (
    CURRENT_CONTROL_FORMULA,
    GGE_MODEL_ID,
    GGE_OUTPUT_UNIT,
    CanonicalGeometryInputV1,
    GoldenGeometryEngineV1,
    compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1,
    compute_canonical_base_geometry_magnitude_from_market_context_v1,
    compute_current_control_base_geometry_magnitude_v1,
)


def _ctx(*, mark: float, sigma: float) -> CanonicalMarketContextV1:
    base = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id="ctx-gge-v1",
            instrument_id="inst-gge-v1",
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=1,
            market_event_time="2026-10-06T12:00:00+00:00",
            decision_time="2026-10-06T12:00:01+00:00",
            bar_interval="1m",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=mark,
            index_price=mark - 0.5,
            best_bid=mark - 0.2,
            best_ask=mark + 0.2,
            spread=0.4,
            volume=1.0,
            open_interest=1.0,
            funding_rate=0.0,
            volatility_estimate=sigma,
            trend_feature_set={"slope": 0.0},
            momentum_feature_set={"rsi": 50.0},
            liquidity_feature_set={"depth_score": 0.5},
            market_structure_feature_set={"range_ratio": 0.5},
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=WarmupStatus.WARMUP_COMPLETE,
            feature_contract_version=FEATURE_CONTRACT_VERSION,
            input_digest="",
        )
    )
    estimate = build_canonical_volatility_estimate_v1(
        value=sigma,
        observation_count=60,
        as_of_event_time=datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc),
    )
    return bind_typed_canonical_volatility_estimate_into_market_context_v1(base, estimate)


GOLDEN_VECTORS = [
    pytest.param(2500.0, 0.04, 100.0, id="V18_current_control"),
    pytest.param(10.0, 0.01, 0.1, id="V02_low_price"),
    pytest.param(100_000.0, 0.02, 2000.0, id="V03_high_price"),
    pytest.param(100.0, 0.005, 0.5, id="V04_low_volatility"),
    pytest.param(100.0, 0.25, 25.0, id="V05_high_volatility"),
]


@pytest.mark.parametrize("mark,sigma,expected", GOLDEN_VECTORS)
def test_golden_vector_matches_current_control(mark: float, sigma: float, expected: float) -> None:
    inp = CanonicalGeometryInputV1(
        instrument_id="inst-gge-v1",
        mark_price=mark,
        volatility_estimate=sigma,
    )
    result = GoldenGeometryEngineV1.compute_base_geometry_magnitude_v1(inp)
    assert result.ok and result.output is not None
    assert result.output.magnitude == pytest.approx(expected)
    control = compute_current_control_base_geometry_magnitude_v1(
        mark_price=mark, volatility_estimate=sigma
    )
    assert control == pytest.approx(expected)
    assert result.output.model_id == GGE_MODEL_ID
    assert result.output.unit_semantic == GGE_OUTPUT_UNIT


@pytest.mark.parametrize(
    "mark",
    [0.05, 1.0, 100.0, 5000.0, 100_000.0],
)
def test_price_scale_linear_with_price(mark: float) -> None:
    sigma = 0.02
    base = mark * sigma
    result = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="scale",
        mark_price=mark,
        volatility_estimate=sigma,
    )
    assert result.ok and result.output is not None
    assert result.output.magnitude == pytest.approx(base)
    pct = result.output.magnitude / mark
    assert pct == pytest.approx(sigma)


def test_cmc_path_parity() -> None:
    ctx = _ctx(mark=2500.0, sigma=0.04)
    gge = compute_canonical_base_geometry_magnitude_from_market_context_v1(ctx)
    assert gge.ok and gge.output is not None
    assert gge.output.magnitude == pytest.approx(100.0)


def test_determinism_same_input_same_output() -> None:
    inp = CanonicalGeometryInputV1(
        instrument_id="d",
        mark_price=123.45,
        volatility_estimate=0.03,
        observation_lineage_id="line-1",
    )
    a = GoldenGeometryEngineV1.compute_base_geometry_magnitude_v1(inp)
    b = GoldenGeometryEngineV1.compute_base_geometry_magnitude_v1(inp)
    assert a.ok and b.ok
    assert a.output is not None and b.output is not None
    assert a.output.magnitude == b.output.magnitude
    assert a.output.input_digest == b.output.input_digest


@pytest.mark.parametrize(
    "mark,sigma,code",
    [
        (0.0, 0.01, "mark_price_non_positive"),
        (-1.0, 0.01, "mark_price_non_positive"),
        (100.0, 0.0, "volatility_non_positive"),
        (100.0, float("nan"), "volatility_non_positive"),
        (float("inf"), 0.01, "mark_price_non_positive"),
    ],
)
def test_edge_cases_fail_closed(mark: float, sigma: float, code: str) -> None:
    result = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="edge",
        mark_price=mark,
        volatility_estimate=sigma,
    )
    assert not result.ok
    assert code in result.failure_codes


def test_current_control_formula_documented() -> None:
    assert "volatility_estimate" in CURRENT_CONTROL_FORMULA
    assert "mark_price" in CURRENT_CONTROL_FORMULA


def test_no_silent_nan_output() -> None:
    result = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="nan",
        mark_price=1.0,
        volatility_estimate=float("nan"),
    )
    assert not result.ok
    assert result.output is None


def test_magnitude_finite_positive() -> None:
    result = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="ok",
        mark_price=50.0,
        volatility_estimate=0.1,
    )
    assert result.ok and result.output is not None
    assert math.isfinite(result.output.magnitude)
    assert result.output.magnitude > 0


def test_blank_instrument_id_fail_closed() -> None:
    result = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="",
        mark_price=50.0,
        volatility_estimate=0.1,
    )
    assert not result.ok
    assert "instrument_id_blank" in result.failure_codes
