"""Owner Dynamic Trailing Reversal Scope: σ×P magnitude and trailing geometry (deterministic)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    PRODUCTIVE_RAW_SCOPE_DISTANCE_PRODUCER_ID,
    SCOPE_INITIALIZATION_POLICY_INSTRUMENT_RELATIVE_VERSION,
    ScopeInitializationPrerequisitesV1,
    compute_raw_volatility_times_price_scope_distance_v1,
    default_instrument_relative_scope_initialization_policy_v1,
    initialize_canonical_scope,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _rules_for_cycle_v1,
    _seed_runtime_scope_from_snapshot_v1,
)
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1,
    resolve_layer_c_event_distances_from_mark_and_volatility_v1,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_state import (
    ActiveSide,
    DynamicScopeRules,
    RuntimeScopeState,
    update_dynamic_boundaries,
)
from tests.trading.master_v2.test_double_play_state import GOOD_ENVELOPE


def _context(*, mark: float, vol: float) -> CanonicalMarketContextV1:
    mark_f = float(mark)
    return CanonicalMarketContextV1(
        context_id="ctx-owner-scope-v1",
        instrument_id="inst-low-price",
        market_type=FuturesMarketType.PERPETUAL,
        trading_epoch=1,
        market_event_time="2026-10-01T12:00:00+00:00",
        decision_time="2026-10-01T12:00:01+00:00",
        bar_interval="1m",
        bar_finality_status=BarFinalityStatus.FINALIZED,
        mark_price=mark_f,
        index_price=mark_f,
        best_bid=mark_f,
        best_ask=mark_f,
        spread=0.0,
        volume=1.0,
        open_interest=1.0,
        funding_rate=0.0,
        volatility_estimate=float(vol),
        trend_feature_set={},
        momentum_feature_set={},
        liquidity_feature_set={},
        market_structure_feature_set={},
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        warmup_status=WarmupStatus.WARMUP_COMPLETE,
        feature_contract_version=FEATURE_CONTRACT_VERSION,
        input_digest="a" * 64,
    )


def test_price_scale_two_instruments_different_absolute_scope_same_vol() -> None:
    vol = 0.02
    low = compute_raw_volatility_times_price_scope_distance_v1(_context(mark=0.05, vol=vol))
    high = compute_raw_volatility_times_price_scope_distance_v1(_context(mark=5000.0, vol=vol))
    assert low.failure_codes == ()
    assert high.failure_codes == ()
    assert low.distance is not None and high.distance is not None
    assert low.distance != pytest.approx(high.distance)
    assert low.distance == pytest.approx(vol * 0.05)
    assert high.distance == pytest.approx(vol * 5000.0)
    assert low.distance != 200.0
    assert high.distance != 200.0


def test_current_mark_price_used_not_stale_init_only() -> None:
    vol = 0.1
    first = compute_raw_volatility_times_price_scope_distance_v1(_context(mark=100.0, vol=vol))
    second = compute_raw_volatility_times_price_scope_distance_v1(_context(mark=150.0, vol=vol))
    assert first.distance == pytest.approx(10.0)
    assert second.distance == pytest.approx(15.0)


def test_volatility_update_changes_raw_scope() -> None:
    mark = 100.0
    low_vol = compute_raw_volatility_times_price_scope_distance_v1(_context(mark=mark, vol=0.01))
    high_vol = compute_raw_volatility_times_price_scope_distance_v1(_context(mark=mark, vol=0.05))
    assert low_vol.distance == pytest.approx(1.0)
    assert high_vol.distance == pytest.approx(5.0)


def test_bull_trailing_favorable_uncapped_reversal_below() -> None:
    st = RuntimeScopeState(anchor_price=100.0, now_tick=0)
    rules = DynamicScopeRules(
        min_band_width=2.0,
        max_band_width=1_000_000.0,
        min_switch_cooldown_ticks=0,
        max_switches_per_window=1_000_000,
        volatility_estimate=0.05,
    )
    st2 = update_dynamic_boundaries(
        mark_price=130.0, side=ActiveSide.LONG, st=st, rules=rules, env=GOOD_ENVELOPE
    )
    assert st2.anchor_price == 130.0
    assert st2.current_downscope_boundary < st2.anchor_price
    assert st2.current_upscope_boundary > st2.anchor_price
    band = st2.current_hysteresis_band
    assert st2.anchor_price - st2.current_downscope_boundary == pytest.approx(band)


def test_bear_trailing_favorable_uncapped_reversal_above() -> None:
    st = RuntimeScopeState(anchor_price=100.0, now_tick=0)
    rules = DynamicScopeRules(
        min_band_width=2.0,
        max_band_width=1_000_000.0,
        min_switch_cooldown_ticks=0,
        max_switches_per_window=1_000_000,
        volatility_estimate=0.05,
    )
    st2 = update_dynamic_boundaries(
        mark_price=70.0, side=ActiveSide.SHORT, st=st, rules=rules, env=GOOD_ENVELOPE
    )
    assert st2.anchor_price == 70.0
    assert st2.current_upscope_boundary > st2.anchor_price
    assert st2.current_downscope_boundary < st2.anchor_price


def test_productive_bind_seam_no_cap63_up_distance_as_proposed_d_t() -> None:
    repo = Path(__file__).resolve().parents[3]
    path = (
        repo / "src/ops/p5_10_productive_activation_and_binding_v1/productive_cycle_bind_seam_v1.py"
    )
    text = path.read_text(encoding="utf-8")
    assert "CANONICAL_UP_DISTANCE" not in text
    assert "compute_raw_volatility_times_price_scope_distance_v1" in text
    assert "explicit_dt_proposal" in text
    assert "PRODUCTIVE_RAW_SCOPE_DISTANCE_PRODUCER_ID" in text


def test_raw_scope_producer_id_is_canonical_scope_owner() -> None:
    assert "canonical_scope_initialization_v1" in PRODUCTIVE_RAW_SCOPE_DISTANCE_PRODUCER_ID


def test_single_magnitude_truth_productive_raw_equals_replay_scope_init() -> None:
    ctx = _context(mark=100.0, vol=0.02)
    raw = compute_raw_volatility_times_price_scope_distance_v1(ctx)
    policy = default_instrument_relative_scope_initialization_policy_v1()
    init = initialize_canonical_scope(
        ctx,
        policy,
        ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
    )
    assert raw.failure_codes == ()
    assert init.scope is not None
    assert init.scope.scope_band == pytest.approx(raw.distance)
    assert init.scope.scope_band == pytest.approx(2.0)
    assert init.scope.scope_band not in (50.0, 500.0, 200.0)
    assert init.scope.policy_version == SCOPE_INITIALIZATION_POLICY_INSTRUMENT_RELATIVE_VERSION


def test_layer_c_event_distances_derive_from_dynamic_scope_magnitude() -> None:
    d_t = 10.0
    derived = resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(d_t)
    assert derived.ok is True
    assert derived.up_distance == pytest.approx(10.0)
    assert derived.adverse_exit_distance == pytest.approx(4.0)
    assert derived.reversal_distance == pytest.approx(6.0)
    assert derived.up_distance != 200.0


def test_layer_c_scales_with_mark_and_vol_not_cap63_constants() -> None:
    low = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
        mark_price=0.05, volatility_estimate=0.02
    )
    high = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
        mark_price=5000.0, volatility_estimate=0.02
    )
    assert low.ok and high.ok
    assert low.up_distance == pytest.approx(0.001)
    assert high.up_distance == pytest.approx(100.0)
    assert low.up_distance not in (200.0, 80.0, 120.0)


def test_integrated_replay_source_uses_layer_c_binding_not_cap63() -> None:
    repo = Path(__file__).resolve().parents[3]
    replay = repo / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    text = replay.read_text(encoding="utf-8")
    assert "resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1" in text
    assert "up_distance=cycle_up_distance" in text


def test_hardening_v2_uses_layer_c_binding_not_decision_cfg_distances() -> None:
    repo = Path(__file__).resolve().parents[3]
    path = (
        repo
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "hardening_cycle_bridge_v2.py"
    )
    text = path.read_text(encoding="utf-8")
    assert "resolve_layer_c_event_distances_from_canonical_market_context_v1" in text
    assert "up_distance=cycle_up_distance" in text
    assert "up_distance=float(decision_cfg.up_distance)" not in text


def test_bridge_cycle_uses_layer_c_binding_for_replay_input() -> None:
    repo = Path(__file__).resolve().parents[3]
    path = (
        repo
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        / "decision_economics_cycle_bridge_v1.py"
    )
    text = path.read_text(encoding="utf-8")
    assert "resolve_layer_c_event_distances_from_mark_and_volatility_v1" in text
    assert "build_integrated_offline_replay_input_v1" in text
    assert text.count("up_distance=cycle_up_distance") >= 1


def test_replay_trailing_rules_do_not_apply_legacy_50_500_clamp() -> None:
    ctx = _context(mark=100.0, vol=0.01)
    policy = default_instrument_relative_scope_initialization_policy_v1()
    init = initialize_canonical_scope(
        ctx,
        policy,
        ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
    )
    assert init.scope is not None
    assert init.scope.scope_band == pytest.approx(1.0)
    rules = _rules_for_cycle_v1(provided=None, snapshot=init.scope, bound_context=ctx)
    assert rules.max_band_width == pytest.approx(1.0)
    assert rules.min_band_width == 0.0
    seeded = _seed_runtime_scope_from_snapshot_v1(snapshot=init.scope, now_tick=0)
    assert seeded.current_hysteresis_band == pytest.approx(1.0)
