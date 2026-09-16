"""CC-B/CC-C focused tests: clamp non-collapse and typed vol into DynamicScopeRules."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeLifecycleState,
    CanonicalScopeSnapshotV1,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
)
from trading.master_v2.canonical_volatility_default_quarantine_v1 import (
    CanonicalVolatilityQuarantineError,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    adapt_canonical_volatility_estimate_to_legacy_float_v1,
    build_canonical_volatility_estimate_v1,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_state import (
    ActiveSide,
    RuntimeScopeState,
    SideState,
    clamp_band_width,
    derive_active_side,
    update_dynamic_boundaries,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _DEFAULT_SCOPE_RULES,
    _DEFAULT_STATIC_LIMITS,
    _resolve_runtime_scope_state_for_cycle_v1,
    _rules_for_cycle_v1,
    _runtime_envelope_for_snapshot_v1,
)


def _snapshot(*, volatility_estimate: float = 0.02) -> CanonicalScopeSnapshotV1:
    vol_dist = volatility_estimate * 100.0
    band = max(vol_dist, 50.0)
    return CanonicalScopeSnapshotV1(
        scope_id="scope-cc-b",
        instrument_id="inst-eth-usdt-perp",
        initialized_at_trading_epoch=1,
        source_market_context_id="ctx",
        source_input_digest="a" * 64,
        lifecycle_state=CanonicalScopeLifecycleState.SCOPE_VALID,
        reference_price=1000.0,
        volatility_estimate=volatility_estimate,
        initial_volatility_distance=vol_dist,
        scope_band=band,
        neutral_upper_boundary=1000.0 + band,
        neutral_lower_boundary=1000.0 - band,
        trailing_anchor=1000.0,
        min_scope_band=50.0,
        max_scope_band=500.0,
        policy_version="v1",
        semantic_digest="b" * 64,
        reason_codes=(),
    )


def _seed(*, now_tick: int = 1) -> RuntimeScopeState:
    return RuntimeScopeState(
        anchor_price=1000.0,
        current_upscope_boundary=1050.0,
        current_downscope_boundary=950.0,
        current_hysteresis_band=50.0,
        last_switch_tick=-1_000_000,
        switches_in_window=0,
        window_start_tick=now_tick,
        chop_latched=False,
        now_tick=now_tick,
        last_completed_side_switch_tick=-1_000_000,
        scope_stability_ticks=0,
    )


def _typed_context(*, value: float) -> CanonicalMarketContextV1:
    estimate = build_canonical_volatility_estimate_v1(
        value=value,
        observation_count=61,
        as_of_event_time=datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc),
        fallback_used=False,
        source_digest="a" * 64,
    )
    adapted = float(adapt_canonical_volatility_estimate_to_legacy_float_v1(estimate))
    ctx = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id="ctx-cc-c-typed",
            instrument_id="inst-eth-usdt-perp",
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=1,
            market_event_time="2026-06-30T12:00:00+00:00",
            decision_time="2026-06-30T12:00:01+00:00",
            bar_interval="1m",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=1000.0,
            index_price=999.5,
            best_bid=999.8,
            best_ask=1000.2,
            spread=0.4,
            volume=1.0,
            open_interest=1.0,
            funding_rate=0.0,
            volatility_estimate=adapted,
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
    return bind_typed_canonical_volatility_estimate_into_market_context_v1(ctx, estimate)


def test_cc_b_snapshot_window_not_clipped_to_unratified_50_or_100() -> None:
    snap = _snapshot()
    rules = _rules_for_cycle_v1(provided=None, snapshot=snap)
    env = _runtime_envelope_for_snapshot_v1(snap)
    assert rules.min_band_width == pytest.approx(50.0)
    assert rules.max_band_width == pytest.approx(500.0)
    assert env.static.min_band_width == pytest.approx(50.0)
    assert env.static.max_band_width == pytest.approx(500.0)
    assert rules.max_band_width != pytest.approx(_DEFAULT_SCOPE_RULES.max_band_width)
    assert env.static.max_band_width != pytest.approx(_DEFAULT_STATIC_LIMITS.max_band_width)
    lo = max(rules.min_band_width, env.static.min_band_width)
    hi = min(rules.max_band_width, env.static.max_band_width)
    assert lo == pytest.approx(50.0)
    assert hi == pytest.approx(500.0)
    assert hi > lo


def test_cc_b_active_trail_varies_inside_snapshot_window() -> None:
    snap = _snapshot()
    env = _runtime_envelope_for_snapshot_v1(snap)
    seed = _seed()
    bands: list[float] = []
    for vol in (0.10, 0.20, 0.30):
        rules = _rules_for_cycle_v1(
            provided=None,
            snapshot=_snapshot(volatility_estimate=vol),
        )
        updated = update_dynamic_boundaries(
            mark_price=1000.0,
            side=ActiveSide.LONG,
            st=seed,
            rules=rules,
            env=env,
        )
        raw = float(vol) * 1000.0
        expected = clamp_band_width(raw, rules, env)
        assert expected == pytest.approx(raw)
        assert updated.current_hysteresis_band == pytest.approx(expected)
        bands.append(float(updated.current_hysteresis_band))
    assert bands == [100.0, 200.0, 300.0]


def test_cc_b_neutral_and_armed_freeze_trailing() -> None:
    snap = _snapshot(volatility_estimate=0.20)
    rules = _rules_for_cycle_v1(provided=None, snapshot=snap)
    env = _runtime_envelope_for_snapshot_v1(snap)
    seed = _seed()
    for side_state in (SideState.NEUTRAL_OBSERVE, SideState.LONG_ARMED, SideState.SHORT_ARMED):
        updated = update_dynamic_boundaries(
            mark_price=1200.0,
            side=derive_active_side(side_state),
            st=seed,
            rules=rules,
            env=env,
        )
        assert updated.current_hysteresis_band == pytest.approx(seed.current_hysteresis_band)
        assert updated.anchor_price == pytest.approx(seed.anchor_price)


def test_cc_c_typed_cmc_vol_binds_into_rules_without_floor() -> None:
    snap = _snapshot(volatility_estimate=0.02)
    ctx = _typed_context(value=0.15)
    rules = _rules_for_cycle_v1(provided=None, snapshot=snap, market_context=ctx)
    assert ctx.canonical_volatility_estimate is not None
    typed_float = float(
        adapt_canonical_volatility_estimate_to_legacy_float_v1(ctx.canonical_volatility_estimate)
    )
    assert rules.volatility_estimate == pytest.approx(0.15)
    assert rules.volatility_estimate != pytest.approx(0.02)
    integrated = Path(__file__).resolve().parents[3] / (
        "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    )
    text = integrated.read_text(encoding="utf-8")
    assert "max(float(snapshot.volatility_estimate), 1e-9)" not in text


def test_cc_c_legacy_snapshot_vol_still_admitted_when_typed_absent() -> None:
    snap = _snapshot(volatility_estimate=0.02)
    rules = _rules_for_cycle_v1(provided=None, snapshot=snap, market_context=None)
    assert rules.volatility_estimate == pytest.approx(0.02)


def test_cc_c_zero_snapshot_vol_still_fail_closed_when_typed_absent() -> None:
    snap = _snapshot(volatility_estimate=0.0)
    with pytest.raises(CanonicalVolatilityQuarantineError):
        _rules_for_cycle_v1(provided=None, snapshot=snap, market_context=None)


def test_cc_d_prior_runtime_scope_continues_on_same_instrument() -> None:
    snap = _snapshot()
    prior = replace(_seed(now_tick=4), current_hysteresis_band=180.0, anchor_price=1100.0)
    restored, reinitialized = _resolve_runtime_scope_state_for_cycle_v1(
        instrument_id="inst-eth-usdt-perp",
        current_scope=snap,
        now_tick=5,
        prior_state=prior,
        bound_instrument_id="inst-eth-usdt-perp",
        explicit_reset=False,
    )
    assert reinitialized is False
    assert restored.current_hysteresis_band == pytest.approx(180.0)
    assert restored.anchor_price == pytest.approx(1100.0)


def test_cc_d_instrument_mismatch_reseeds() -> None:
    snap = _snapshot()
    prior = _seed()
    restored, reinitialized = _resolve_runtime_scope_state_for_cycle_v1(
        instrument_id="inst-eth-usdt-perp",
        current_scope=snap,
        now_tick=5,
        prior_state=prior,
        bound_instrument_id="inst-other-perp",
        explicit_reset=False,
    )
    assert reinitialized is True
    assert restored.now_tick == 5
