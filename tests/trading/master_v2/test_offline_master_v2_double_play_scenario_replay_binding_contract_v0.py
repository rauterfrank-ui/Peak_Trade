"""Contract: offline Master V2 double-play scenario replay binding (zero-order, deterministic)."""

from __future__ import annotations

import math
from unittest.mock import patch

import pytest

from trading.master_v2.double_play_futures_input import (
    FuturesFreshnessState,
    FuturesInputSnapshot,
    FuturesInstrumentMetadataStatus,
    FuturesMarketDataProvenanceStatus,
    FuturesReadinessStatus,
    evaluate_futures_input_snapshot,
)
from trading.master_v2.double_play_state import ActiveSide, ScopeEvent, SideState
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    SYNTHETIC_FUTURES_INSTRUMENT,
    OfflineDoublePlayProofEvent,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioTickV0,
    build_default_bull_bear_bull_scenario_ticks,
    build_offline_replay_futures_input_snapshot,
    replay_result_digest_coherent,
    resolve_replay_futures_input_snapshot,
    run_offline_double_play_scenario_replay_v0,
    validate_offline_double_play_scenario_replay_input_v0,
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
