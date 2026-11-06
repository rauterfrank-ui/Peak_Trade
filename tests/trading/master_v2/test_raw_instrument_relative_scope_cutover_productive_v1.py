"""Productive Scope policy cutover: canonical instrument-relative (σ×mark) via bridge defaults."""

from __future__ import annotations

import hashlib

import pytest

from trading.master_v2.canonical_core_runtime_integration_bridge_v0 import (
    _default_policies as bridge_default_policies,
)
from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    FEATURE_CONTRACT_VERSION,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    SCOPE_INITIALIZATION_POLICY_INSTRUMENT_RELATIVE_VERSION,
    CanonicalScopeInitializationPolicyV1,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    clamp_scope_band,
    compute_raw_volatility_times_price_scope_distance_v1,
    default_instrument_relative_scope_initialization_policy_v1,
    initialize_canonical_scope,
    resolve_authoritative_scope_band_v1,
    scope_initialization_policy_uses_instrument_relative_magnitude_v1,
    snapshot_uses_instrument_relative_scope_magnitude_v1,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1,
)


def _ctx(*, mark: float, sigma: float) -> CanonicalMarketContextV1:
    return with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id="ctx-cutover-v1",
            instrument_id="inst-cutover-v1",
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=1,
            market_event_time="2026-10-03T12:00:00+00:00",
            decision_time="2026-10-03T12:00:01+00:00",
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


def test_bridge_default_policies_use_canonical_instrument_relative_policy() -> None:
    policy = bridge_default_policies().scope_initialization
    expected = default_instrument_relative_scope_initialization_policy_v1()
    assert policy == expected
    assert scope_initialization_policy_uses_instrument_relative_magnitude_v1(policy)


def test_parity_harness_embedded_policy_matches_bridge() -> None:
    from pathlib import Path

    harness_path = (
        Path(__file__).resolve().parents[3]
        / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py"
    )
    source = harness_path.read_text(encoding="utf-8")
    assert (
        "scope_initialization=default_instrument_relative_scope_initialization_policy_v1()"
        in source
    )
    assert "min_scope_band=50.0" not in source.split("IntegratedOfflineReplayPoliciesV1")[1][:800]
    assert (
        bridge_default_policies().scope_initialization
        == default_instrument_relative_scope_initialization_policy_v1()
    )


def test_raw_distance_is_sigma_times_mark() -> None:
    ctx = _ctx(mark=2500.0, sigma=0.04)
    raw = compute_raw_volatility_times_price_scope_distance_v1(ctx)
    assert raw.failure_codes == ()
    assert raw.distance == pytest.approx(100.0)


def test_micro_raw_below_fifty_not_rebound_to_fifty() -> None:
    ctx = _ctx(mark=10.0, sigma=0.01)
    raw = compute_raw_volatility_times_price_scope_distance_v1(ctx)
    assert raw.distance == pytest.approx(0.1)
    policy = default_instrument_relative_scope_initialization_policy_v1()
    init = initialize_canonical_scope(
        ctx,
        policy,
        ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        reinitialization_guard=ScopeReinitializationGuardV1(),
    )
    assert init.scope is not None
    assert init.scope.scope_band == pytest.approx(0.1)
    assert init.scope.scope_band != 50.0


def test_high_raw_above_five_hundred_not_capped() -> None:
    ctx = _ctx(mark=10_000.0, sigma=0.5)
    policy = default_instrument_relative_scope_initialization_policy_v1()
    init = initialize_canonical_scope(
        ctx,
        policy,
        ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        reinitialization_guard=ScopeReinitializationGuardV1(),
    )
    assert init.scope is not None
    assert init.scope.scope_band == pytest.approx(5000.0)
    assert init.scope.scope_band != 500.0


def test_s4_resolve_authoritative_band_is_raw_on_ir_policy() -> None:
    policy = default_instrument_relative_scope_initialization_policy_v1()
    assert resolve_authoritative_scope_band_v1(0.75, policy) == pytest.approx(0.75)
    legacy = CanonicalScopeInitializationPolicyV1(
        min_scope_band=50.0,
        max_scope_band=500.0,
        policy_version="v1",
    )
    assert resolve_authoritative_scope_band_v1(25.0, legacy) == 50.0


def test_sub_one_raw_survives_without_one_point_zero_floor() -> None:
    ctx = _ctx(mark=80.0, sigma=0.005)
    policy = default_instrument_relative_scope_initialization_policy_v1()
    init = initialize_canonical_scope(
        ctx,
        policy,
        ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        reinitialization_guard=ScopeReinitializationGuardV1(),
    )
    assert init.scope is not None
    assert init.scope.initial_volatility_distance == pytest.approx(0.4)
    assert init.scope.scope_band == pytest.approx(0.4)
    assert init.scope.scope_band != 1.0


def test_s6_snapshot_propagates_instrument_relative_policy_version() -> None:
    ctx = _ctx(mark=1000.0, sigma=0.02)
    policy = default_instrument_relative_scope_initialization_policy_v1()
    init = initialize_canonical_scope(
        ctx,
        policy,
        ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        reinitialization_guard=ScopeReinitializationGuardV1(),
    )
    assert init.scope is not None
    assert snapshot_uses_instrument_relative_scope_magnitude_v1(init.scope)
    assert init.scope.policy_version == SCOPE_INITIALIZATION_POLICY_INSTRUMENT_RELATIVE_VERSION


def test_dynamic_scope_layer_c_accepts_positive_finite_raw_magnitude() -> None:
    band = 0.35
    lc = resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(band)
    assert lc.ok
    assert lc.up_distance > 0


def test_normalized_scale_equivalence_scope_over_mark() -> None:
    sigma = 0.02
    for mark in (100.0, 1000.0, 10_000.0):
        ctx = _ctx(mark=mark, sigma=sigma)
        policy = default_instrument_relative_scope_initialization_policy_v1()
        init = initialize_canonical_scope(
            ctx,
            policy,
            ScopeInitializationPrerequisitesV1(
                required_window_complete=True,
                instrument_metadata_valid=True,
                finalized_market_context=True,
            ),
            reinitialization_guard=ScopeReinitializationGuardV1(),
        )
        assert init.scope is not None
        assert init.scope.scope_band / mark == pytest.approx(sigma, rel=1e-9)


def test_generic_bounded_clamp_mechanics_preserved() -> None:
    assert clamp_scope_band(5.0, 50.0, 500.0) == 50.0
    assert clamp_scope_band(900.0, 50.0, 500.0) == 500.0


def test_no_touch_core_modules_still_present() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    paths = [
        "src/trading/master_v2/double_play_state.py",
        "src/trading/master_v2/double_play_composition_matrix_v1.py",
        "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
        "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
        "src/trading/master_v2/layer_c_scope_event_distance_binding_v1.py",
    ]
    for rel in paths:
        data = (root / rel).read_bytes()
        assert hashlib.sha256(data).hexdigest()
