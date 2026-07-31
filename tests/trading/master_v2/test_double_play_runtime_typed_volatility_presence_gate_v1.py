"""Focused tests for Double-Play runtime typed volatility presence gate v1."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextBlockReason,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
    with_mutated_field_for_tests_v1,
)
from trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1 import (
    CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1,
    ProductiveTypedBindingFailClosedReasonV1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    TypedRuntimeProducerOutcomeV1,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionDirectionState,
    PositionManagementContext,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    DoublePlayEntryExitPolicyV0,
    ENTRY_EXIT_POLICY_VERSION,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
    EntryExitDirectionState,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    CAPABILITY_ID,
    DOUBLE_PLAY_TYPED_CUTOVER,
    PACKAGE_MARKER,
    TYPED_VOLATILITY_ESTIMATE_MISSING_REASON,
    assert_architecture_guards_v1,
    assert_capability_non_goals_v1,
    demote_trading_gate_for_typed_presence_failure_v1,
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
    evaluate_protection_authority_when_typed_absent_v1,
    protection_authority_required_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _REPLAY_DEFAULT_VOL_QUARANTINE,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)

ROOT = Path(__file__).resolve().parents[3]
VENUE = "okx_europe"
CANON = "ETH-USD_UM_XPERP-310404"
VENUE_INST = "ETH-USD_UM_XPERP-310404"
T0 = 1_700_000_000.0


def _price_at(i: int) -> float:
    return 100.0 * math.exp(0.001 * i)


def _sample(i: int) -> MarketSampleIdentityV1:
    return MarketSampleIdentityV1(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        event_time=EventTimeInstantV1(unix_seconds=T0 + float(i * 60)),
        mark_price=_price_at(i),
    )


def _context(**overrides: object) -> CanonicalMarketContextV1:
    base: dict = {
        "context_id": "ctx-eth-presence-gate",
        "instrument_id": CANON,
        "market_type": FuturesMarketType.PERPETUAL,
        "trading_epoch": 1,
        "market_event_time": "2026-06-30T12:00:00+00:00",
        "decision_time": "2026-06-30T12:00:01+00:00",
        "bar_interval": "1m",
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "mark_price": 3500.0,
        "index_price": 3499.5,
        "best_bid": 3499.8,
        "best_ask": 3500.2,
        "spread": 0.4,
        "volume": 1_250_000.0,
        "open_interest": 85_000_000.0,
        "funding_rate": 0.00012,
        "volatility_estimate": 0.38,
        "trend_feature_set": {"slope": 0.02},
        "momentum_feature_set": {"rsi": 55.0},
        "liquidity_feature_set": {"depth_score": 0.88},
        "market_structure_feature_set": {"range_ratio": 0.42},
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "warmup_status": WarmupStatus.WARMUP_COMPLETE,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "input_digest": "",
        "canonical_volatility_estimate": None,
    }
    base.update(overrides)
    return CanonicalMarketContextV1(**base)


def _valid_estimate(*, value: float = 0.004321):
    return build_canonical_volatility_estimate_v1(
        value=value,
        observation_count=61,
        as_of_event_time=datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc),
        fallback_used=False,
        source_digest="a" * 64,
    )


def _host(
    tmp_path: Path | None = None,
) -> CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1:
    path = None if tmp_path is None else tmp_path / "mark_history.json"
    return CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=path,
    )


def _ingest_range(host, ctx, start: int, end: int):
    result = None
    for i in range(start, end + 1):
        result = host.apply_to_market_context_v1(
            ctx,
            sample=_sample(i),
            transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
            ingest_sample=True,
        )
    assert result is not None
    return result


# ---------------------------------------------------------------------------
# A. Productive runtime
# ---------------------------------------------------------------------------


def test_a1_typed_present_float_synced_allows_double_play() -> None:
    estimate = _valid_estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context(volatility_estimate=0.0)),
        estimate,
    )
    elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx, eligibility=elig)
    assert gate.typed_estimate_present is True
    assert gate.alpha_scope_entry_authority_allowed is True
    assert gate.eligibility is elig
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON not in gate.reason_codes


def test_a2_typed_missing_feature_regime_float_fail_closed() -> None:
    ctx = with_computed_input_digest(_context(volatility_estimate=0.38))
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx)
    assert gate.alpha_scope_entry_authority_allowed is False
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON in gate.reason_codes
    assert CanonicalMarketContextBlockReason.TYPED_VOLATILITY_ESTIMATE_MISSING in gate.block_reasons


def test_a3_typed_missing_other_legacy_float_fail_closed() -> None:
    ctx = with_computed_input_digest(_context(volatility_estimate=0.02))
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx)
    assert gate.alpha_scope_entry_authority_allowed is False
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON in gate.reason_codes


def test_a4_typed_present_float_mismatch_fail_closed() -> None:
    from dataclasses import replace

    estimate = _valid_estimate(value=0.004321)
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context(volatility_estimate=0.0)),
        estimate,
    )
    mismatched = replace(ctx, volatility_estimate=0.99)
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(mismatched)
    assert gate.alpha_scope_entry_authority_allowed is False
    assert (
        CanonicalMarketContextBlockReason.TYPED_VOLATILITY_LEGACY_FLOAT_MISMATCH
        in gate.block_reasons
    )


def test_a5_typed_present_float_absent_atomic_bind_invariant() -> None:
    """Binder always sets both; missing float after typed is mismatch/invalid path."""
    estimate = _valid_estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context()),
        estimate,
    )
    assert ctx.canonical_volatility_estimate is not None
    assert ctx.volatility_estimate == pytest.approx(estimate.value)


def test_a6_wrong_unit_horizon_annualization_blocked() -> None:
    estimate = _valid_estimate()
    bad = with_mutated_field_for_tests_v1(estimate, unit="percent")
    with pytest.raises(Exception):
        bind_typed_canonical_volatility_estimate_into_market_context_v1(
            with_computed_input_digest(_context()),
            bad,
        )


# ---------------------------------------------------------------------------
# B. Lifecycle
# ---------------------------------------------------------------------------


def test_b_lifecycle_warmup_restart_produced_duplicate_cycle_rejects(
    tmp_path: Path,
) -> None:
    host = _host(tmp_path)
    # Warmup without estimate
    warm = host.apply_to_market_context_v1(
        _context(),
        sample=_sample(0),
        transport=ObservationTransportMetadataV1(receive_time=T0 + 0.5),
        ingest_sample=True,
    )
    assert warm.bound_estimate is None
    gate_w = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        warm.context, eligibility=warm.typed_binding_eligibility
    )
    assert gate_w.alpha_scope_entry_authority_allowed is False

    # Fill history to PRODUCED
    produced = _ingest_range(host, _context(), 1, 60)
    assert produced.producer_result.outcome is TypedRuntimeProducerOutcomeV1.PRODUCED
    assert produced.bound_estimate is not None
    gate_p = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        produced.context, eligibility=produced.typed_binding_eligibility
    )
    assert gate_p.alpha_scope_entry_authority_allowed is True

    # Duplicate with prior — reuse allowed
    dup = host.apply_to_market_context_v1(
        _context(),
        sample=_sample(60),
        transport=ObservationTransportMetadataV1(receive_time=T0 + 60 * 60 + 0.5),
        ingest_sample=True,
    )
    assert dup.producer_result.outcome is TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP
    assert dup.bound_estimate is not None
    gate_d = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        dup.context, eligibility=dup.typed_binding_eligibility
    )
    assert gate_d.alpha_scope_entry_authority_allowed is True

    # Cycle without sample with prior — reuse allowed
    cycle = host.apply_to_market_context_v1(_context(), ingest_sample=False)
    assert cycle.bound_estimate is not None
    gate_c = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        cycle.context, eligibility=cycle.typed_binding_eligibility
    )
    assert gate_c.alpha_scope_entry_authority_allowed is True

    # Restart without rematerialized estimate
    path = tmp_path / "mark_history.json"
    restored = (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.restore_from_persistence_v1(
            persistence_path=path,
        )
    )
    restart = restored.apply_to_market_context_v1(_context(), ingest_sample=False)
    assert restart.bound_estimate is None
    assert (
        restart.telemetry.fail_closed_reason
        == ProductiveTypedBindingFailClosedReasonV1.RESTART_WITHOUT_ESTIMATE.value
    )
    gate_r = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        restart.context, eligibility=restart.typed_binding_eligibility
    )
    assert gate_r.alpha_scope_entry_authority_allowed is False


def test_b_duplicate_without_prior_blocks(tmp_path: Path) -> None:
    host = _host(tmp_path)
    # Single sample — warmup, not enough for PRODUCED; then duplicate same sample
    first = host.apply_to_market_context_v1(
        _context(),
        sample=_sample(0),
        transport=ObservationTransportMetadataV1(receive_time=T0 + 0.5),
        ingest_sample=True,
    )
    assert first.bound_estimate is None
    # Fresh host duplicate-without-prior: ingest same identity on new host after one sample
    host2 = _host(tmp_path / "h2")
    host2.apply_to_market_context_v1(
        _context(),
        sample=_sample(0),
        transport=ObservationTransportMetadataV1(receive_time=T0 + 0.5),
        ingest_sample=True,
    )
    dup = host2.apply_to_market_context_v1(
        _context(),
        sample=_sample(0),
        transport=ObservationTransportMetadataV1(receive_time=T0 + 1.0),
        ingest_sample=True,
    )
    assert dup.bound_estimate is None
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        dup.context, eligibility=dup.typed_binding_eligibility
    )
    assert gate.alpha_scope_entry_authority_allowed is False


def test_b_out_of_order_history_gap_block(tmp_path: Path) -> None:
    host = _host(tmp_path)
    warm = _ingest_range(host, _context(), 0, 5)
    ooo = host.apply_to_market_context_v1(
        warm.context,
        sample=_sample(3),
        ingest_sample=True,
    )
    assert ooo.producer_result.outcome is TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED
    assert ooo.bound_estimate is None
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        ooo.context, eligibility=ooo.typed_binding_eligibility
    )
    assert gate.alpha_scope_entry_authority_allowed is False

    host3 = _host(tmp_path / "gap2")
    produced = _ingest_range(host3, _context(), 0, 60)
    assert produced.bound_estimate is not None
    jumped = host3.apply_to_market_context_v1(
        produced.context,
        sample=_sample(63),
        ingest_sample=True,
    )
    assert jumped.producer_result.outcome is TypedRuntimeProducerOutcomeV1.HISTORY_GAP_REJECTED
    assert jumped.bound_estimate is None
    gate_g = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        jumped.context, eligibility=jumped.typed_binding_eligibility
    )
    assert gate_g.alpha_scope_entry_authority_allowed is False


def test_b_persistence_and_materialization_fail_closed(tmp_path: Path) -> None:
    # Persistence restore without rematerialized estimate → presence gate fail-closed.
    host = _host(tmp_path)
    produced = _ingest_range(host, _context(), 0, 60)
    assert produced.bound_estimate is not None
    path = tmp_path / "mark_history.json"
    restored = (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.restore_from_persistence_v1(
            persistence_path=path,
        )
    )
    cycle = restored.apply_to_market_context_v1(_context(), ingest_sample=False)
    assert cycle.bound_estimate is None
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        cycle.context, eligibility=cycle.typed_binding_eligibility
    )
    assert gate.alpha_scope_entry_authority_allowed is False
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON in gate.reason_codes


# ---------------------------------------------------------------------------
# C. Authority separation
# ---------------------------------------------------------------------------


def test_c_entry_scope_boundary_blocked_safety_preserved() -> None:
    ctx = with_computed_input_digest(_context(volatility_estimate=0.38))
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx)
    assert gate.alpha_scope_entry_authority_allowed is False
    assert gate.exit_risk_safety_authority_preserved is True
    assert demote_trading_gate_for_typed_presence_failure_v1(TradingGate.ENTRY_ALLOWED) is (
        TradingGate.EXIT_ONLY
    )

    policy = DoublePlayEntryExitPolicyV0(policy_version=ENTRY_EXIT_POLICY_VERSION)

    # Safety exit still executable
    safety = evaluate_protection_authority_when_typed_absent_v1(
        instrument_id=CANON,
        trading_epoch=1,
        context_reference="ctx",
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        position_state=PositionState.OPEN_FULL,
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        safety_mode=SafetyMode.EXIT_ONLY,
        data_integrity_state=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        cooldown_pass=True,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        safety_exit_signal=PolicySignalV0(triggered=True, reason_code="safety"),
        previous_direction_state=CompositionDirectionState.LONG,
        position_management_context=PositionManagementContext.LONG_POSITION,
        entry_exit_policy=policy,
        gate=gate,
    )
    assert safety.decision_outcome is DecisionOutcome.EXIT

    # Hard-risk reduce still executable
    hard = evaluate_protection_authority_when_typed_absent_v1(
        instrument_id=CANON,
        trading_epoch=1,
        context_reference="ctx",
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        position_state=PositionState.OPEN_FULL,
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        safety_mode=SafetyMode.NORMAL,
        data_integrity_state=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        cooldown_pass=True,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=True, reason_code="hard"),
        safety_exit_signal=PolicySignalV0(triggered=False),
        previous_direction_state=CompositionDirectionState.LONG,
        position_management_context=PositionManagementContext.LONG_POSITION,
        entry_exit_policy=policy,
        gate=gate,
    )
    assert hard.decision_outcome is DecisionOutcome.REDUCE

    # Reconciliation still executable
    recon = evaluate_protection_authority_when_typed_absent_v1(
        instrument_id=CANON,
        trading_epoch=1,
        context_reference="ctx",
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        position_state=PositionState.RECONCILIATION_REQUIRED,
        reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        safety_mode=SafetyMode.NORMAL,
        data_integrity_state=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        cooldown_pass=True,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        safety_exit_signal=PolicySignalV0(triggered=False),
        previous_direction_state=CompositionDirectionState.LONG,
        position_management_context=PositionManagementContext.LONG_POSITION,
        entry_exit_policy=policy,
        gate=gate,
    )
    assert recon.decision_outcome.value in {"reconcile_only", "blocked", "hold", "observe"}

    # Mandatory adverse-scope reduce still executable
    mandatory = evaluate_protection_authority_when_typed_absent_v1(
        instrument_id=CANON,
        trading_epoch=1,
        context_reference="ctx",
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        position_state=PositionState.OPEN_FULL,
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        safety_mode=SafetyMode.NORMAL,
        data_integrity_state=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        cooldown_pass=True,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
        scope_adverse_exit_signal=PolicySignalV0(triggered=True, reason_code="adverse"),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        safety_exit_signal=PolicySignalV0(triggered=False),
        previous_direction_state=CompositionDirectionState.LONG,
        position_management_context=PositionManagementContext.LONG_POSITION,
        entry_exit_policy=policy,
        gate=gate,
    )
    assert mandatory.decision_outcome is DecisionOutcome.REDUCE

    # Mandatory time exit still executable
    time_exit = evaluate_protection_authority_when_typed_absent_v1(
        instrument_id=CANON,
        trading_epoch=1,
        context_reference="ctx",
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        position_state=PositionState.OPEN_FULL,
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        safety_mode=SafetyMode.NORMAL,
        data_integrity_state=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        cooldown_pass=True,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=True, reason_code="time"),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        safety_exit_signal=PolicySignalV0(triggered=False),
        previous_direction_state=CompositionDirectionState.LONG,
        position_management_context=PositionManagementContext.LONG_POSITION,
        entry_exit_policy=policy,
        gate=gate,
    )
    assert time_exit.decision_outcome is DecisionOutcome.EXIT

    assert protection_authority_required_v1(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        reconciliation_state=ReconciliationState.RECONCILED,
        safety_exit_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        safety_mode=SafetyMode.NORMAL,
    )


# ---------------------------------------------------------------------------
# D. Isolation
# ---------------------------------------------------------------------------


def test_d_offline_research_scenario_isolation() -> None:
    from trading.master_v2.canonical_volatility_default_quarantine_v1 import (
        LEGACY_HISTORICAL_BIND_DEFAULT_VALUE,
        LEGACY_REPLAY_RULES_DEFAULT_VALUE,
    )
    from trading.master_v2.offline_double_play_scenario_replay_v0 import (
        _HIGH_VOL_RULES,
        _DEFAULT_RULES,
    )

    assert float(LEGACY_REPLAY_RULES_DEFAULT_VALUE) == 0.02
    assert float(_REPLAY_DEFAULT_VOL_QUARANTINE.legacy_value) == 0.02
    assert float(LEGACY_HISTORICAL_BIND_DEFAULT_VALUE) == 0.2
    assert float(_DEFAULT_RULES.volatility_estimate) == 0.02
    assert float(_HIGH_VOL_RULES.volatility_estimate) == 0.08

    non_goals = assert_capability_non_goals_v1()
    assert non_goals["global_typed_only_enforcement"] is False
    assert non_goals["numeric_max_age_policy_created"] is True
    assert non_goals["numeric_max_age_enforcement_enabled"] is False
    assert non_goals["numeric_max_age_decided"] is False
    assert non_goals["offline_replay_legacy_defaults_unchanged"] is True
    assert non_goals["research_legacy_fallbacks_unchanged"] is True
    assert non_goals["scenario_replay_unchanged"] is True

    # Offline eligibility without presence requirement still allows legacy float path.
    ctx = with_computed_input_digest(_context())
    from trading.master_v2.canonical_market_context_v1 import (
        evaluate_canonical_market_context_eligibility,
    )

    legacy_elig = evaluate_canonical_market_context_eligibility(ctx)
    assert legacy_elig.trading_decision_allowed is True


# ---------------------------------------------------------------------------
# E. Architecture guards
# ---------------------------------------------------------------------------


def test_e_architecture_guards() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["adapter_defs_in_typed"] == 1
    assert guards["binder_defs_in_binding"] == 1
    assert guards["validator_defs_in_typed"] == 1
    assert guards["double_play_typed_cutover"] is True
    assert guards["global_typed_only_enforcement"] is False
    assert guards["numeric_max_age_decided"] is False
    assert DOUBLE_PLAY_TYPED_CUTOVER is True
    assert PACKAGE_MARKER.startswith("MASTER_V2_DOUBLE_PLAY_RUNTIME")
    assert CAPABILITY_ID == "MASTER_V2_DOUBLE_PLAY_RUNTIME_TYPED_VOLATILITY_PRESENCE_GATE_V1"

    non_goals = assert_capability_non_goals_v1()
    assert non_goals["second_estimator_created"] is False
    assert non_goals["second_adapter_created"] is False
    assert non_goals["second_validator_created"] is False
    assert non_goals["local_typed_value_extraction_created"] is False
    assert non_goals["volatility_semantics_changed"] is False

    # feature_regime remains NON_ALIAS competing seed (not removed).
    feature_regime = (
        ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "feature_regime_pipeline_v2.py"
    ).read_text(encoding="utf-8")
    assert "compute_feature_regime_from_mid_prices_v2" in feature_regime

    # Productive path cannot bypass presence gate.
    bridge = (
        ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "hardening_cycle_bridge_v2.py"
    ).read_text(encoding="utf-8")
    assert "require_productive_typed_volatility_presence_gate=True" in bridge
    assert "evaluate_double_play_runtime_typed_volatility_presence_gate_v1" in bridge

    spec = (
        ROOT / "docs/ops/specs/MASTER_V2_DOUBLE_PLAY_RUNTIME_TYPED_VOLATILITY_PRESENCE_GATE_V1.md"
    ).read_text(encoding="utf-8")
    assert "DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_RUNTIME_TYPED_VOLATILITY_PRESENCE_GATE_V1" in spec


def test_eligibility_not_discarded_by_host(tmp_path: Path) -> None:
    host = _host(tmp_path)
    result = host.apply_to_market_context_v1(
        _context(),
        sample=_sample(0),
        transport=ObservationTransportMetadataV1(receive_time=T0 + 0.5),
        ingest_sample=True,
    )
    assert result.typed_binding_eligibility is not None
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        result.context, eligibility=result.typed_binding_eligibility
    )
    assert gate.eligibility is result.typed_binding_eligibility
