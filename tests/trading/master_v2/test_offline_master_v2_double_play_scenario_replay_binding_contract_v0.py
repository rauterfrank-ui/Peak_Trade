"""Contract: offline Master V2 double-play scenario replay binding (zero-order, deterministic)."""

from __future__ import annotations

import math
from unittest.mock import patch

import pytest

from trading.master_v2.double_play_dashboard_display import (
    DashboardDisplayStatus,
    build_dashboard_display_snapshot,
)
from trading.master_v2.double_play_futures_input import (
    FuturesFreshnessState,
    FuturesInputSnapshot,
    FuturesInstrumentMetadataStatus,
    FuturesMarketDataProvenanceStatus,
    FuturesReadinessStatus,
    evaluate_futures_input_snapshot,
)
from trading.master_v2.double_play_state import (
    ActiveSide,
    ScopeEvent,
    SideState,
    derive_active_side,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    SYNTHETIC_FUTURES_INSTRUMENT,
    OfflineDoublePlayProofEvent,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioTickV0,
    build_default_bull_bear_bull_scenario_ticks,
    build_offline_replay_futures_input_snapshot,
    build_master_v2_state_event_stream_validation_input_from_replay,
    compute_master_v2_replay_state_event_projection_digest,
    project_master_v2_state_event_stream_from_replay,
    project_master_v2_state_events_from_replay_records,
    replay_result_digest_coherent,
    resolve_replay_futures_input_snapshot,
    run_offline_double_play_scenario_replay_v0,
    validate_offline_double_play_scenario_replay_input_v0,
)
from src.ops.durable_completion_validation.validators.event_stream import (
    MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL,
    MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH,
    MasterV2StateEventRecord,
    build_master_v2_state_event_record,
    evaluate_master_v2_state_event_stream_validation,
)


def _default_input() -> OfflineDoublePlayScenarioReplayInputV0:
    return OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
        source_revision="offline-replay-test-v0",
    )


def _run_default():
    return run_offline_double_play_scenario_replay_v0(_default_input())


def test_owner_constant() -> None:
    assert OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER.endswith(
        "offline_double_play_scenario_replay_v0"
    )


def test_deterministic_identical_output() -> None:
    a = _run_default()
    b = _run_default()
    assert a.replay_pass is b.replay_pass
    assert len(a.tick_records) == len(b.tick_records)
    for left, right in zip(a.tick_records, b.tick_records):
        assert left.master_v2_decision_digest == right.master_v2_decision_digest
        assert left.bull_layer_state_digest == right.bull_layer_state_digest
        assert left.execution_intent_digest == right.execution_intent_digest


def test_default_scenario_replay_passes() -> None:
    result = _run_default()
    assert result.replay_pass, result.fail_reasons
    assert result.summary.tick_count < 100
    assert replay_result_digest_coherent(result)


def test_bull_hold_in_positive_trend() -> None:
    result = _run_default()
    assert OfflineDoublePlayProofEvent.BULL_HOLD in result.summary.proof_events
    bull_ticks = [r for r in result.tick_records if r.side_state == SideState.LONG_ACTIVE]
    assert bull_ticks
    assert all(r.price >= 100.0 for r in bull_ticks[:3])


def test_bull_to_bear_on_confirmed_negative_shift() -> None:
    result = _run_default()
    assert OfflineDoublePlayProofEvent.BULL_TO_BEAR in result.summary.proof_events
    assert any(r.side_state == SideState.SHORT_ACTIVE for r in result.tick_records)


def test_bear_hold_in_negative_trend() -> None:
    result = _run_default()
    assert OfflineDoublePlayProofEvent.BEAR_HOLD in result.summary.proof_events


def test_bear_to_bull_on_confirmed_positive_shift() -> None:
    result = _run_default()
    assert OfflineDoublePlayProofEvent.BEAR_TO_BULL in result.summary.proof_events
    long_after = [
        r.tick_index for r in result.tick_records if r.side_state == SideState.LONG_ACTIVE
    ]
    assert len(long_after) >= 2


def test_dynamic_scope_trailing_within_guardrails() -> None:
    result = _run_default()
    bands = {
        r.tick_index: r.scope_state.current_hysteresis_band
        for r in result.tick_records
        if r.active_side != ActiveSide.NEUTRAL
    }
    assert bands
    assert all(b > 0 for b in bands.values())
    assert len(set(bands.values())) > 1


def test_hysteresis_cooldown_prevents_flapping() -> None:
    result = _run_default()
    assert OfflineDoublePlayProofEvent.FLAPPING_BLOCKED in result.summary.proof_events
    blocked = [
        r
        for r in result.tick_records
        if r.transition_reason_code == "COOLDOWN_BLOCK"
        or r.scope_event in (ScopeEvent.DOWNSCOPE_CANDIDATE, ScopeEvent.UPSCOPE_CANDIDATE)
    ]
    assert blocked


def test_volatility_adaptation_changes_scope() -> None:
    result = _run_default()
    assert OfflineDoublePlayProofEvent.VOLATILITY_SCOPE_ADAPTED in result.summary.proof_events


def test_killswitch_blocks_activation() -> None:
    result = _run_default()
    assert OfflineDoublePlayProofEvent.KILLSWITCH_BLOCKED in result.summary.proof_events
    assert result.summary.final_side_state == SideState.KILL_ALL


def test_capital_slot_ratchet_without_reserve_top_up() -> None:
    result = _run_default()
    assert OfflineDoublePlayProofEvent.CAPITAL_SLOT_RATCHET_APPLIED in result.summary.proof_events
    bases = [r.scope_state.anchor_price for r in result.tick_records]
    assert bases


def test_inactivity_opportunity_cost_slot_release() -> None:
    result = _run_default()
    assert OfflineDoublePlayProofEvent.INACTIVITY_SLOT_RELEASED in result.summary.proof_events


def test_zero_order_all_ticks() -> None:
    result = _run_default()
    for rec in result.tick_records:
        assert rec.orders == 0
        assert rec.cancels == 0
        assert rec.fills == 0
        assert rec.positions_opened == 0
    assert result.summary.orders_total == 0


def test_decision_and_state_digests_canonical_and_stable() -> None:
    result = _run_default()
    digests = [r.master_v2_decision_digest for r in result.tick_records]
    assert all(d and len(d) == 64 for d in digests)
    binding = result.master_v2_decision_state_digest_binding
    assert binding is not None
    assert binding.master_v2_decision_digest == digests[-1]


@pytest.mark.parametrize(
    "instrument",
    ["BTC-PERP", "XBT-PERP", "ETH/USD", "BTCUSDT"],
)
def test_btc_spot_instruments_fail_closed(instrument: str) -> None:
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=instrument,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
    )
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert reasons


def test_non_monotone_timestamp_fail_closed() -> None:
    ticks = list(build_default_bull_bear_bull_scenario_ticks())
    ticks[2] = OfflineDoublePlayScenarioTickV0(
        tick_index=2,
        timestamp_ms=ticks[1].timestamp_ms,
        price=103.0,
        scope_event=ScopeEvent.NOOP,
    )
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=tuple(ticks),
    )
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert any("non-monotone" in r for r in reasons)


def test_invalid_price_fail_closed() -> None:
    ticks = list(build_default_bull_bear_bull_scenario_ticks())
    ticks[0] = OfflineDoublePlayScenarioTickV0(
        tick_index=0,
        timestamp_ms=ticks[0].timestamp_ms,
        price=math.nan,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
    )
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=tuple(ticks),
    )
    result = run_offline_double_play_scenario_replay_v0(inp)
    assert not result.replay_pass


def test_replay_resolves_canonical_futures_input_snapshot_for_eth_perp() -> None:
    inp = _default_input()
    snapshot = resolve_replay_futures_input_snapshot(inp)
    decision = evaluate_futures_input_snapshot(snapshot)
    assert decision.status is FuturesReadinessStatus.DATA_READY
    assert not decision.live_authorization


def test_replay_futures_input_admission_uses_canonical_owner() -> None:
    inp = _default_input()
    with patch(
        "trading.master_v2.offline_double_play_scenario_replay_v0.evaluate_futures_input_snapshot",
        wraps=evaluate_futures_input_snapshot,
    ) as mocked:
        reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
        assert not reasons
        assert mocked.called


def test_incomplete_futures_input_snapshot_fail_closed() -> None:
    base = build_offline_replay_futures_input_snapshot(SYNTHETIC_FUTURES_INSTRUMENT)
    blocked = FuturesInputSnapshot(
        candidate=base.candidate,
        ranking=base.ranking,
        instrument=FuturesInstrumentMetadataStatus(
            complete=False,
            contract_size_known=False,
            tick_size_known=False,
            step_size_known=False,
            min_qty_known=False,
            min_notional_known=False,
            margin_asset_known=False,
            settlement_asset_known=False,
            leverage_bounds_known=False,
            missing_fields=("contract_size",),
        ),
        provenance=base.provenance,
        volatility=base.volatility,
        liquidity=base.liquidity,
        derivatives=base.derivatives,
        opportunity=base.opportunity,
    )
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
        futures_input_snapshot=blocked,
    )
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert any("futures_input_admission_blocked" in r for r in reasons)
    result = run_offline_double_play_scenario_replay_v0(inp)
    assert not result.replay_pass
    assert result.summary.orders_total == 0


def test_stale_futures_input_provenance_fail_closed() -> None:
    base = build_offline_replay_futures_input_snapshot(SYNTHETIC_FUTURES_INSTRUMENT)
    stale = FuturesInputSnapshot(
        candidate=base.candidate,
        ranking=base.ranking,
        instrument=base.instrument,
        provenance=FuturesMarketDataProvenanceStatus(
            complete=True,
            freshness_state=FuturesFreshnessState.STALE,
            dataset_id=base.provenance.dataset_id,
            source=base.provenance.source,
            mark_available=True,
            index_available=True,
            last_available=True,
            ohlcv_available=True,
            funding_available=True,
            open_interest_available=True,
            missing_fields=(),
        ),
        volatility=base.volatility,
        liquidity=base.liquidity,
        derivatives=base.derivatives,
        opportunity=base.opportunity,
    )
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
        futures_input_snapshot=stale,
    )
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert any("futures_input_admission_blocked" in r for r in reasons)


def test_replay_binds_canonical_dashboard_display_projection_owner() -> None:
    inp = _default_input()
    with patch(
        "trading.master_v2.offline_double_play_scenario_replay_v0.build_dashboard_display_snapshot",
        wraps=build_dashboard_display_snapshot,
    ) as mocked:
        result = run_offline_double_play_scenario_replay_v0(inp)
        assert result.replay_pass, result.fail_reasons
        assert mocked.called
        assert mocked.call_count == len(inp.ticks)


def test_replay_dashboard_display_snapshot_from_canonical_model_outputs() -> None:
    result = _run_default()
    snap = result.dashboard_display_snapshot
    assert snap is not None
    assert snap.display_only is True
    assert snap.live_authorization is False
    assert snap.trading_ready is False
    assert snap.testnet_ready is False
    assert snap.live_ready is False
    panel_names = {p.name for p in snap.panels}
    assert panel_names == {
        "futures_input",
        "state_transition",
        "survival_envelope",
        "strategy_suitability",
        "capital_slot_ratchet",
        "capital_slot_release",
        "composition",
    }
    for panel in snap.panels:
        assert panel.live_authorization is False
        assert panel.is_authority is False
        assert panel.is_signal is False


def test_replay_final_display_reflects_kill_all_composition() -> None:
    result = _run_default()
    snap = result.dashboard_display_snapshot
    assert snap is not None
    assert result.summary.final_side_state == SideState.KILL_ALL
    comp_panel = next(p for p in snap.panels if p.name == "composition")
    assert comp_panel.status is DashboardDisplayStatus.DISPLAY_BLOCKED


def test_replay_display_projection_digest_deterministic() -> None:
    a = _run_default()
    b = _run_default()
    assert a.dashboard_display_projection_digest == b.dashboard_display_projection_digest
    assert a.dashboard_display_projection_digest is not None
    assert len(a.dashboard_display_projection_digest) == 64


def test_replay_display_snapshot_does_not_mutate_replay_decisions() -> None:
    without_patch = _run_default()
    with patch(
        "trading.master_v2.offline_double_play_scenario_replay_v0.build_dashboard_display_snapshot",
        side_effect=lambda **kwargs: build_dashboard_display_snapshot(**kwargs),
    ):
        with_patch = _run_default()
    assert without_patch.replay_pass == with_patch.replay_pass
    assert len(without_patch.tick_records) == len(with_patch.tick_records)
    for left, right in zip(without_patch.tick_records, with_patch.tick_records):
        assert left.composition_status == right.composition_status
        assert left.side_state == right.side_state
        assert left.master_v2_decision_digest == right.master_v2_decision_digest


def test_replay_display_projection_absent_on_validation_failure() -> None:
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id="BTC-PERP",
        ticks=build_default_bull_bear_bull_scenario_ticks(),
    )
    result = run_offline_double_play_scenario_replay_v0(inp)
    assert not result.replay_pass
    assert result.dashboard_display_snapshot is None
    assert result.dashboard_display_projection_digest is None


def test_replay_display_long_short_exclusive_via_composition_panel() -> None:
    result = _run_default()
    snap = result.dashboard_display_snapshot
    assert snap is not None
    long_ticks = [r for r in result.tick_records if r.side_state == SideState.LONG_ACTIVE]
    short_ticks = [r for r in result.tick_records if r.side_state == SideState.SHORT_ACTIVE]
    assert long_ticks
    assert short_ticks
    for rec in result.tick_records:
        assert not (
            rec.bull_layer_state == SideState.LONG_ACTIVE
            and rec.bear_layer_state == SideState.SHORT_ACTIVE
        )


def test_replay_display_evidence_in_result_not_parallel_surface() -> None:
    result = _run_default()
    assert hasattr(result, "dashboard_display_snapshot")
    assert hasattr(result, "dashboard_display_projection_digest")
    assert result.dashboard_display_snapshot is not None
    assert result.dashboard_display_projection_digest is not None


def test_replay_binding_carries_display_projection_digest() -> None:
    result = _run_default()
    binding = result.master_v2_decision_state_digest_binding
    assert binding is not None
    assert binding.dashboard_display_projection_digest == result.dashboard_display_projection_digest
    assert len(binding.dashboard_display_projection_digest) == 64


def test_replay_result_digest_coherent_includes_display_projection() -> None:
    result = _run_default()
    assert replay_result_digest_coherent(result)
    binding = result.master_v2_decision_state_digest_binding
    assert binding is not None
    assert binding.dashboard_display_projection_digest == result.dashboard_display_projection_digest


# --- Kill-All vs State-Switch scenario conformance (MD scenarios A–H) ---

_SCENARIO_MD_SOURCE = "Peak_Trade_Kill_All_vs_State_Switch_Favorable_Adverse_Extreme_Moves_v1.md"


def _default_ticks() -> tuple[OfflineDoublePlayScenarioTickV0, ...]:
    return build_default_bull_bear_bull_scenario_ticks()


def _run_ticks(
    ticks: tuple[OfflineDoublePlayScenarioTickV0, ...],
    *,
    futures_input_snapshot: FuturesInputSnapshot | None = None,
) -> OfflineDoublePlayScenarioReplayResultV0:
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=ticks,
        source_revision="scenario-conformance-v0",
        futures_input_snapshot=futures_input_snapshot,
    )
    return run_offline_double_play_scenario_replay_v0(inp)


def _assert_zero_order_boundary(result: OfflineDoublePlayScenarioReplayResultV0) -> None:
    assert result.summary.orders_total == 0
    assert result.summary.cancels_total == 0
    assert result.summary.fills_total == 0
    assert result.summary.positions_opened_total == 0
    for rec in result.tick_records:
        assert rec.orders == 0
        assert rec.cancels == 0
        assert rec.fills == 0
        assert rec.positions_opened == 0


def _assert_long_short_exclusive(
    result: OfflineDoublePlayScenarioReplayResultV0,
) -> None:
    for rec in result.tick_records:
        long_active = rec.side_state == SideState.LONG_ACTIVE
        short_active = rec.side_state == SideState.SHORT_ACTIVE
        assert not (long_active and short_active)
        assert not (
            rec.bull_layer_state == SideState.LONG_ACTIVE
            and rec.bear_layer_state == SideState.SHORT_ACTIVE
        )


def _assert_replay_executed(result: OfflineDoublePlayScenarioReplayResultV0) -> None:
    """Partial scenario slices may omit full default proof-event bundle; ticks must still replay."""
    assert result.tick_records, "scenario replay must produce tick records"
    blocking = [
        r
        for r in result.fail_reasons
        if "zero-order violated" in r
        or "decision snapshot missing" in r
        or "master_v2_decision_state_digest_binding missing" in r
        or "dashboard_display_projection_digest missing" in r
    ]
    assert not blocking, blocking


def _assert_no_automatic_kill_all(result: OfflineDoublePlayScenarioReplayResultV0) -> None:
    assert result.summary.final_side_state != SideState.KILL_ALL
    assert SideState.KILL_ALL not in {r.side_state for r in result.tick_records}
    assert OfflineDoublePlayProofEvent.KILLSWITCH_BLOCKED not in result.summary.proof_events


def test_scenario_a_conformance_long_positive_trend_no_kill_all() -> None:
    """Scenario A: LONG_ACTIVE + strong positive trend — no Kill-All from move strength."""
    ticks = _default_ticks()[:5]
    result = _run_ticks(ticks)
    _assert_replay_executed(result)
    _assert_no_automatic_kill_all(result)
    _assert_long_short_exclusive(result)
    _assert_zero_order_boundary(result)
    long_records = [r for r in result.tick_records if r.side_state == SideState.LONG_ACTIVE]
    assert long_records, "long must remain active during favorable uptrend"
    anchors = [r.scope_state.anchor_price for r in long_records]
    assert anchors[-1] > anchors[0], "trailing anchor must rise with favorable long trend"
    assert any(
        r.scope_state.current_downscope_boundary < r.scope_state.anchor_price for r in long_records
    ), "downscope boundary must trail below rising anchor"


def test_scenario_b_conformance_short_negative_trend_no_kill_all() -> None:
    """Scenario B: SHORT_ACTIVE + strong negative trend — no Kill-All from move strength."""
    ticks = _default_ticks()[:12]
    result = _run_ticks(ticks)
    _assert_replay_executed(result)
    _assert_no_automatic_kill_all(result)
    _assert_long_short_exclusive(result)
    _assert_zero_order_boundary(result)
    short_records = [r for r in result.tick_records if r.side_state == SideState.SHORT_ACTIVE]
    assert short_records, "short must remain active during favorable downtrend"
    anchors = [r.scope_state.anchor_price for r in short_records]
    assert anchors[-1] < anchors[0], "trailing anchor must fall with favorable short trend"
    assert OfflineDoublePlayProofEvent.BEAR_HOLD in result.summary.proof_events


def test_scenario_c_conformance_long_adverse_move_state_switch_not_kill_all() -> None:
    """Scenario C: LONG adverse move — state-switch path, not pauschaler Kill-All."""
    ticks = _default_ticks()[:6]
    result = _run_ticks(ticks)
    _assert_replay_executed(result)
    _assert_no_automatic_kill_all(result)
    _assert_long_short_exclusive(result)
    _assert_zero_order_boundary(result)
    assert OfflineDoublePlayProofEvent.BULL_TO_BEAR in result.summary.proof_events
    switch_states = {
        SideState.SWITCH_LONG_TO_SHORT_PENDING,
        SideState.LONG_BLOCKED,
        SideState.SHORT_ARMED,
        SideState.SHORT_ACTIVE,
    }
    assert any(r.side_state in switch_states for r in result.tick_records)
    assert any(
        r.transition_reason_code == "COOLDOWN_BLOCK"
        or r.scope_event in (ScopeEvent.DOWNSCOPE_CANDIDATE, ScopeEvent.UPSCOPE_CANDIDATE)
        for r in result.tick_records
    ) or any(r.side_state == SideState.SWITCH_LONG_TO_SHORT_PENDING for r in result.tick_records)


def test_scenario_d_conformance_short_adverse_move_state_switch_not_kill_all() -> None:
    """Scenario D: SHORT adverse move — upscope/state-switch, not pauschaler Kill-All."""
    ticks = _default_ticks()[:12] + _default_ticks()[16:20]
    result = _run_ticks(ticks)
    _assert_replay_executed(result)
    _assert_no_automatic_kill_all(result)
    _assert_long_short_exclusive(result)
    _assert_zero_order_boundary(result)
    assert OfflineDoublePlayProofEvent.BEAR_TO_BULL in result.summary.proof_events
    switch_states = {
        SideState.SWITCH_SHORT_TO_LONG_PENDING,
        SideState.SHORT_BLOCKED,
        SideState.LONG_ARMED,
        SideState.LONG_ACTIVE,
    }
    assert any(r.side_state in switch_states for r in result.tick_records)


def test_scenario_e_conformance_long_winning_stale_data_fail_closed() -> None:
    """Scenario E: favorable long direction cannot override stale data — fail-closed."""
    base = build_offline_replay_futures_input_snapshot(SYNTHETIC_FUTURES_INSTRUMENT)
    stale = FuturesInputSnapshot(
        candidate=base.candidate,
        ranking=base.ranking,
        instrument=base.instrument,
        provenance=FuturesMarketDataProvenanceStatus(
            complete=True,
            freshness_state=FuturesFreshnessState.STALE,
            dataset_id=base.provenance.dataset_id,
            source=base.provenance.source,
            mark_available=True,
            index_available=True,
            last_available=True,
            ohlcv_available=True,
            funding_available=True,
            open_interest_available=True,
            missing_fields=(),
        ),
        volatility=base.volatility,
        liquidity=base.liquidity,
        derivatives=base.derivatives,
        opportunity=base.opportunity,
    )
    ticks = _default_ticks()[:5]
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=ticks,
        futures_input_snapshot=stale,
    )
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert any("futures_input_admission_blocked" in r for r in reasons)
    result = run_offline_double_play_scenario_replay_v0(inp)
    assert not result.replay_pass
    _assert_zero_order_boundary(result)
    assert derive_active_side(result.summary.final_side_state) == ActiveSide.NEUTRAL


def test_scenario_f_conformance_short_winning_systemic_kill_all_blocks_both_sides() -> None:
    """Scenario F: favorable short PnL does not prevent systemic Kill-All."""
    favorable_short_ticks = _default_ticks()[:12]
    kill_tick = OfflineDoublePlayScenarioTickV0(
        tick_index=12,
        timestamp_ms=1_700_000_000_000 + 12 * 60_000,
        price=95.0,
        scope_event=ScopeEvent.KILL_ALL_REQUIRED,
        safety_decision_allowed=False,
    )
    result = _run_ticks(favorable_short_ticks + (kill_tick,))
    _assert_replay_executed(result)
    assert result.summary.final_side_state == SideState.KILL_ALL
    assert OfflineDoublePlayProofEvent.KILLSWITCH_BLOCKED in result.summary.proof_events
    _assert_zero_order_boundary(result)
    pre_kill = [r for r in result.tick_records if r.tick_index < kill_tick.tick_index]
    assert any(r.side_state == SideState.SHORT_ACTIVE for r in pre_kill)
    assert all(
        derive_active_side(r.side_state) != ActiveSide.LONG for r in result.tick_records[-1:]
    )


def test_scenario_g_conformance_high_volatility_same_direction_no_kill_all() -> None:
    """Scenario G: high volatility without direction break — dynamic scope adapts, no Kill-All."""
    ticks = _default_ticks()[:5] + (_default_ticks()[15],)
    result = _run_ticks(ticks)
    _assert_replay_executed(result)
    _assert_no_automatic_kill_all(result)
    _assert_long_short_exclusive(result)
    _assert_zero_order_boundary(result)
    assert OfflineDoublePlayProofEvent.VOLATILITY_SCOPE_ADAPTED in result.summary.proof_events
    assert any(r.side_state == SideState.LONG_ACTIVE for r in result.tick_records)


def test_scenario_h_conformance_high_volatility_flapping_chop_guard_not_kill_all() -> None:
    """Scenario H: flapping — chop/cooldown guard, no Kill-All without systemic breach."""
    ticks = _default_ticks()[:12] + _default_ticks()[12:15]
    result = _run_ticks(ticks)
    _assert_replay_executed(result)
    _assert_no_automatic_kill_all(result)
    _assert_long_short_exclusive(result)
    _assert_zero_order_boundary(result)
    assert OfflineDoublePlayProofEvent.FLAPPING_BLOCKED in result.summary.proof_events
    assert any(
        r.transition_reason_code == "COOLDOWN_BLOCK"
        or r.scope_event in (ScopeEvent.DOWNSCOPE_CANDIDATE, ScopeEvent.UPSCOPE_CANDIDATE)
        for r in result.tick_records
    )


def _projection_identity_digests() -> tuple[str, str, str]:
    return ("a" * 64, "b" * 64, "c" * 64)


def _default_projection(
    *,
    evidence_chain_profile: str | None = None,
):
    result = _run_default()
    completion, manifest, run = _projection_identity_digests()
    return project_master_v2_state_event_stream_from_replay(
        replay_result=result,
        correlation_id="offline-double-play-replay-v0-eth-perp",
        completion_identity_digest=completion,
        manifest_identity_digest=manifest,
        run_identity_digest=run,
        source_revision="offline-replay-test-v0",
        evidence_chain_profile=evidence_chain_profile,
    )


def test_state_event_projection_stable_dynamic_scope_non_authorizing() -> None:
    projection = _default_projection(
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH
    )
    assert projection.projection_pass, projection.fail_reasons
    stable = [
        record
        for record in projection.events
        if record.semantic_event_class == "dynamic_scope"
        and record.side_state_before == record.side_state_after
    ]
    assert stable
    assert all(not record.claims_live_authority for record in projection.events)
    assert all(not record.claims_execution_authority for record in projection.events)


def test_state_event_projection_state_switch_profile() -> None:
    projection = _default_projection(
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH
    )
    classes = {record.semantic_event_class for record in projection.events}
    assert "dynamic_scope" in classes
    assert "state_switch" in classes
    assert "kill_all_terminal" not in classes
    assert projection.validation_result is not None
    assert projection.validation_result["validation_pass"] is True
    assert projection.proof_binding is not None
    assert projection.proof_binding.event_stream_non_authorizing is True


def test_state_event_projection_kill_all_terminal_profile() -> None:
    projection = _default_projection(
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL
    )
    assert projection.projection_pass, projection.fail_reasons
    assert len(projection.events) == 1
    record = projection.events[0]
    assert record.semantic_event_class == "kill_all_terminal"
    assert record.scope_event == ScopeEvent.KILL_ALL_REQUIRED.value
    assert record.side_state_after == SideState.KILL_ALL.value


def test_state_event_projection_deterministic_digest_and_order() -> None:
    first = _default_projection(
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH
    )
    second = _default_projection(
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH
    )
    assert first.projection_digest == second.projection_digest
    assert [record.event_id for record in first.events] == [
        record.event_id for record in second.events
    ]
    sequences = [record.sequence for record in first.events]
    assert sequences == list(range(len(sequences)))


def test_state_event_projection_compatible_with_event_stream_validator() -> None:
    projection = _default_projection(
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH
    )
    assert projection.validation_input is not None
    result = evaluate_master_v2_state_event_stream_validation(projection.validation_input)
    assert result["validation_pass"] is True
    assert result["event_stream_non_authorizing"] is True


def test_state_event_projection_primary_evidence_validation_input_build() -> None:
    replay = _run_default()
    completion, manifest, run = _projection_identity_digests()
    validation_input, fail_reasons = (
        build_master_v2_state_event_stream_validation_input_from_replay(
            replay_result=replay,
            correlation_id="offline-double-play-replay-v0-eth-perp",
            completion_identity_digest=completion,
            manifest_identity_digest=manifest,
            run_identity_digest=run,
            source_revision="offline-replay-test-v0",
            evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL,
        )
    )
    assert not fail_reasons
    assert validation_input is not None
    binding = replay.master_v2_decision_state_digest_binding
    assert binding is not None
    assert validation_input.bound_dynamic_scope_state_digest == binding.dynamic_scope_state_digest
    assert all(
        record.scope_state_digest == binding.dynamic_scope_state_digest
        for record in validation_input.events
    )


def test_state_event_projection_missing_correlation_id_fail_closed() -> None:
    replay = _run_default()
    binding = replay.master_v2_decision_state_digest_binding
    assert binding is not None
    events, fail_reasons = project_master_v2_state_events_from_replay_records(
        records=replay.tick_records,
        correlation_id="",
        bound_scope_state_digest=binding.dynamic_scope_state_digest,
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL,
    )
    assert not events
    assert "correlation_id required" in fail_reasons


def test_state_event_projection_unknown_profile_fail_closed() -> None:
    replay = _run_default()
    binding = replay.master_v2_decision_state_digest_binding
    assert binding is not None
    events, fail_reasons = project_master_v2_state_events_from_replay_records(
        records=replay.tick_records,
        correlation_id="offline-double-play-replay-v0-eth-perp",
        bound_scope_state_digest=binding.dynamic_scope_state_digest,
        evidence_chain_profile="unsupported_profile_v0",
    )
    assert not events
    assert "unsupported evidence_chain_profile" in fail_reasons


def test_state_event_projection_authority_claims_fail_closed() -> None:
    replay = _run_default()
    binding = replay.master_v2_decision_state_digest_binding
    assert binding is not None
    events, _ = project_master_v2_state_events_from_replay_records(
        records=replay.tick_records,
        correlation_id="offline-double-play-replay-v0-eth-perp",
        bound_scope_state_digest=binding.dynamic_scope_state_digest,
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL,
    )
    assert events
    base = events[0]
    tampered = (
        MasterV2StateEventRecord(
            semantic_event_class=base.semantic_event_class,
            event_id=base.event_id,
            sequence=base.sequence,
            timestamp_utc=base.timestamp_utc,
            source=base.source,
            correlation_id=base.correlation_id,
            schema_version=base.schema_version,
            scope_event=base.scope_event,
            side_state_before=base.side_state_before,
            side_state_after=base.side_state_after,
            scope_state_digest=base.scope_state_digest,
            transition_allowed=base.transition_allowed,
            present=base.present,
            claims_live_authority=True,
            claims_execution_authority=False,
        ),
    )
    completion, manifest, run = _projection_identity_digests()
    from src.ops.durable_completion_validation.validators.event_stream import (
        MASTER_V2_STATE_EVENT_BOUNDARY_OWNER,
        MasterV2StateEventStreamValidationInput,
    )

    validation_input = MasterV2StateEventStreamValidationInput(
        boundary_owner=MASTER_V2_STATE_EVENT_BOUNDARY_OWNER,
        source_revision="offline-replay-test-v0",
        completion_identity_digest=completion,
        manifest_identity_digest=manifest,
        run_identity_digest=run,
        correlation_id="offline-double-play-replay-v0-eth-perp",
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL,
        bound_dynamic_scope_state_digest=binding.dynamic_scope_state_digest,
        events=tampered,
    )
    result = evaluate_master_v2_state_event_stream_validation(validation_input)
    assert result["validation_pass"] is False
    assert any("authority claims forbidden" in reason for reason in result["fail_reasons"])


def test_state_event_projection_digest_stable_for_explicit_events() -> None:
    record = build_master_v2_state_event_record(
        semantic_event_class="dynamic_scope",
        event_id="mv2-test-001",
        sequence=0,
        correlation_id="corr-1",
        scope_event=ScopeEvent.NOOP.value,
        side_state_before=SideState.LONG_ACTIVE.value,
        side_state_after=SideState.LONG_ACTIVE.value,
        scope_state_digest="d" * 64,
        transition_allowed=True,
    )
    first = compute_master_v2_replay_state_event_projection_digest(
        events=(record,),
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH,
        correlation_id="corr-1",
    )
    second = compute_master_v2_replay_state_event_projection_digest(
        events=(record,),
        evidence_chain_profile=MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH,
        correlation_id="corr-1",
    )
    assert first == second
