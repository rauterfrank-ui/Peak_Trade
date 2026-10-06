"""Canonical geometry volatility authority v1 — fail-closed typed G17 only."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from trading.master_v2.canonical_geometry_volatility_v1 import (
    CanonicalGeometryVolatilityError,
    CanonicalGeometryVolatilityErrorCode,
    GEOMETRY_VOLATILITY_UNIT,
    resolve_canonical_geometry_volatility_v1,
)
from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
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
    compute_canonical_base_geometry_magnitude_from_market_context_v1,
)

AS_OF = datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc)


def _estimate(**overrides: object):
    base: dict[str, object] = {
        "value": 0.04,
        "observation_count": 60,
        "as_of_event_time": AS_OF,
    }
    base.update(overrides)
    return build_canonical_volatility_estimate_v1(**base)  # type: ignore[arg-type]


def _context(**overrides: object) -> CanonicalMarketContextV1:
    base: dict = {
        "context_id": "ctx-geom-vol",
        "instrument_id": "inst-a",
        "market_type": FuturesMarketType.PERPETUAL,
        "trading_epoch": 1,
        "market_event_time": "2026-06-30T12:00:00+00:00",
        "decision_time": "2026-06-30T12:00:01+00:00",
        "bar_interval": "1m",
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "mark_price": 2500.0,
        "index_price": 2499.5,
        "best_bid": 2499.8,
        "best_ask": 2500.2,
        "spread": 0.4,
        "volume": 1.0,
        "open_interest": 1.0,
        "funding_rate": 0.0,
        "volatility_estimate": 0.04,
        "trend_feature_set": {},
        "momentum_feature_set": {},
        "liquidity_feature_set": {},
        "market_structure_feature_set": {},
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "warmup_status": WarmupStatus.WARMUP_COMPLETE,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "input_digest": "",
        "canonical_volatility_estimate": None,
    }
    base.update(overrides)
    return CanonicalMarketContextV1(**base)


def _typed_ctx(**overrides: object) -> CanonicalMarketContextV1:
    est = _estimate()
    ctx = _context(**overrides)
    return bind_typed_canonical_volatility_estimate_into_market_context_v1(ctx, est)


def test_valid_typed_geometry_volatility_carries_identity() -> None:
    ctx = _typed_ctx()
    geom = resolve_canonical_geometry_volatility_v1(ctx)
    assert geom.instrument_id == "inst-a"
    assert geom.unit == GEOMETRY_VOLATILITY_UNIT
    assert geom.value == pytest.approx(0.04)


def test_feature_float_only_rejected_for_geometry() -> None:
    ctx = with_computed_input_digest(_context(volatility_estimate=0.99))
    with pytest.raises(CanonicalGeometryVolatilityError) as exc:
        resolve_canonical_geometry_volatility_v1(ctx)
    assert exc.value.code == CanonicalGeometryVolatilityErrorCode.MISSING_TYPED_ESTIMATE


def test_instrument_id_mismatch_fail_closed() -> None:
    ctx = _typed_ctx(instrument_id="inst-a")
    with pytest.raises(CanonicalGeometryVolatilityError) as exc:
        resolve_canonical_geometry_volatility_v1(ctx, bound_instrument_id="inst-b")
    assert exc.value.code == CanonicalGeometryVolatilityErrorCode.INSTRUMENT_ID_MISMATCH


def test_blank_instrument_id_fail_closed() -> None:
    ctx = _typed_ctx(instrument_id="")
    with pytest.raises(CanonicalGeometryVolatilityError) as exc:
        resolve_canonical_geometry_volatility_v1(ctx)
    assert exc.value.code == CanonicalGeometryVolatilityErrorCode.BLANK_INSTRUMENT_ID


def test_legacy_float_mismatch_with_typed_rejected() -> None:
    est = _estimate(value=0.04)
    bound = bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), est)
    mismatched = _context(
        instrument_id=bound.instrument_id,
        volatility_estimate=0.99,
        canonical_volatility_estimate=bound.canonical_volatility_estimate,
        input_digest=bound.input_digest,
    )
    with pytest.raises(CanonicalGeometryVolatilityError) as exc:
        resolve_canonical_geometry_volatility_v1(mismatched)
    assert exc.value.code == CanonicalGeometryVolatilityErrorCode.LEGACY_FLOAT_MISMATCH


def test_gge_cmc_path_rejects_untyped_feature_volatility() -> None:
    ctx = with_computed_input_digest(_context(volatility_estimate=0.04))
    gge = compute_canonical_base_geometry_magnitude_from_market_context_v1(ctx)
    assert not gge.ok
    assert gge.failure_codes is not None
    assert any("missing_typed" in c for c in gge.failure_codes)


def test_gge_parity_d_equals_sigma_times_p_with_typed() -> None:
    ctx = _typed_ctx(mark_price=2500.0)
    gge = compute_canonical_base_geometry_magnitude_from_market_context_v1(ctx)
    assert gge.ok and gge.output is not None
    assert gge.output.magnitude == pytest.approx(100.0)


def test_ranking_volatility_surface_not_imported_in_geometry_module() -> None:
    import trading.master_v2.canonical_geometry_volatility_v1 as mod

    src = open(mod.__file__).read()
    assert "population_sigma_log_returns" not in src
    assert "balanced_movement" not in src
    assert "feature_regime" not in src
