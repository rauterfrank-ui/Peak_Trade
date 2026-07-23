"""Focused tests for VEFCF strategy implementation, exits, and binding."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.research.price_channel_breakout_core_v1 import (
    CHANNEL_LOOKBACK_COMPLETED_BARS_V1,
    classify_price_channel_break_v1 as core_classify,
    compute_prior_high_low_channel_bounds_v1 as core_bounds,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_development_evaluation_v1.binding_v1 import (
    load_and_validate_entry_point_binding,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_development_evaluation_v1.entry_point_v1 import (
    run_dry_validate,
    run_preflight_only,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_exit_state_machine_v1 import (
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    REGIME_INVALIDATION_PERCENTILE_LT_V1,
    TIME_EXIT_MAX_BARS_V1,
    TRAILING_STOP_FORBIDDEN_V1,
    VefcfExitReasonV1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_strategy_implementation_binding_v1 import (
    REQUIRED_DIGEST,
    load_and_validate_repo_binding,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_strategy_v1 import (
    DEEP_PULLBACK_FRACTION_V1,
    ENTRY_ON_EXPANSION_CONFIRMATION_BAR_FORBIDDEN_V1,
    EXIT_PARAMS_V1,
    EXIT_STATE_MACHINE_IMPLEMENTED_V1,
    EXPANSION_MIN_CONSECUTIVE_BARS_V1,
    EXPANSION_PERCENTILE_INCLUSIVE_MIN_V1,
    FADE_TRIGGERS_FIRST_WINS_V1,
    IMMEDIATE_BREAKOUT_WITHOUT_FAILURE_FORBIDDEN_V1,
    MAX_MONITORING_BARS_INCLUSIVE_V1,
    MIN_PULLBACK_FRACTION_QUALIFYING_V1,
    PREDECESSOR_STRATEGY_ID_V1,
    PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1,
    STRATEGY_IDENTITY_V1,
    SUCCESSFUL_CONTINUATION_CANCELS_FADE_V1,
    VEPC_CONTINUATION_ENTRY_FORBIDDEN_V1,
    VefcfEventV1,
    VefcfFadeTriggerV1,
    classify_price_channel_break_v1,
    compute_prior_high_low_channel_bounds_v1,
    generate_vefcf_events_and_roundtrips_v1,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_vol_state_v1 import (
    PERCENTILE_TIE_METHOD_V1,
    RV_PERIOD_V1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyEntrySideCarrierV1,
)

REPO = Path(__file__).resolve().parents[2]


def _patch_vol(monkeypatch: pytest.MonkeyPatch, strat, n: int, *, rank: float = 0.70) -> None:
    ranks = np.full(n, rank, dtype=float)
    rv = np.full(n, 0.01, dtype=float)
    monkeypatch.setattr(
        strat,
        "compute_percentile_rank_120_realized_vol_v1",
        lambda close: pd.Series(ranks, index=close.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_realized_volatility_24_v1",
        lambda close: pd.Series(rv, index=close.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_atr14_v1",
        lambda h, l, c: pd.Series(1.0, index=c.index),
    )


def _synthetic_frame(n: int = 220) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="h", tz="UTC")
    close = pd.Series(100.0, index=idx, dtype=float) + pd.Series(np.linspace(0, 1, n), index=idx)
    return pd.DataFrame(
        {"open": close.copy(), "high": close + 1.0, "low": close - 1.0, "close": close}
    )


def _force_long_impulse(monkeypatch: pytest.MonkeyPatch, strat, frame: pd.DataFrame, bar: int = 50):
    monkeypatch.setattr(
        strat,
        "compute_prior_high_low_channel_bounds_v1",
        lambda high, low, lookback=20: (
            pd.Series(
                [109.0 if i == bar else 1000.0 for i in range(len(high))],
                index=high.index,
            ),
            pd.Series(0.0, index=low.index),
        ),
    )
    frame.loc[frame.index[bar], "close"] = 110.0
    frame.loc[frame.index[bar], "high"] = 112.0
    frame.loc[frame.index[bar], "low"] = 108.0  # range=4


def test_import_safety_and_binding() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["exit_state_machine_implemented"] is True
    assert report["evaluation_authorized"] is False
    assert report["development_evaluation_authorized"] is False
    assert report["frozen_measurement_contract_digest"] == REQUIRED_DIGEST
    assert STRATEGY_IDENTITY_V1 == "VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1"
    assert PREDECESSOR_STRATEGY_ID_V1 == "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1"
    assert RV_PERIOD_V1 == 24
    assert PERCENTILE_TIE_METHOD_V1 == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert EXPANSION_MIN_CONSECUTIVE_BARS_V1 == 4
    assert EXPANSION_PERCENTILE_INCLUSIVE_MIN_V1 == 0.65
    assert MIN_PULLBACK_FRACTION_QUALIFYING_V1 == 0.15
    assert DEEP_PULLBACK_FRACTION_V1 == 0.50
    assert MAX_MONITORING_BARS_INCLUSIVE_V1 == 8
    assert ENTRY_ON_EXPANSION_CONFIRMATION_BAR_FORBIDDEN_V1 is True
    assert IMMEDIATE_BREAKOUT_WITHOUT_FAILURE_FORBIDDEN_V1 is True
    assert VEPC_CONTINUATION_ENTRY_FORBIDDEN_V1 is True
    assert SUCCESSFUL_CONTINUATION_CANCELS_FADE_V1 is True
    assert FADE_TRIGGERS_FIRST_WINS_V1 == (
        "IMPULSE_EXTREME_BREAK_AGAINST_IMPULSE",
        "DEEP_PULLBACK_WITHOUT_CONTINUATION",
        "QUALIFYING_PULLBACK_WINDOW_EXHAUSTION_WITHOUT_CONTINUATION",
    )
    assert EXIT_STATE_MACHINE_IMPLEMENTED_V1 is True
    assert TRAILING_STOP_FORBIDDEN_V1 is True
    assert EXIT_PARAMS_V1["trailing_stop_forbidden"] is True
    assert EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1 == (
        "INITIAL_STOP",
        "IMPULSE_RECLAIM_INVALIDATION",
        "REGIME_INVALIDATION",
        "TIME_EXIT",
        "END_OF_INSTRUMENT_LIQUIDATION",
        "END_OF_PANEL_LIQUIDATION",
    )
    assert REGIME_INVALIDATION_PERCENTILE_LT_V1 == 0.40
    assert TIME_EXIT_MAX_BARS_V1 == 48
    assert CHANNEL_LOOKBACK_COMPLETED_BARS_V1 == 20
    assert (REPO / PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1).is_file()
    assert compute_prior_high_low_channel_bounds_v1 is core_bounds
    assert classify_price_channel_break_v1 is core_classify
    ep = load_and_validate_entry_point_binding(REPO)
    assert ep["status"] == "RUN_SLOT_CONSUMED_DEVELOPMENT_FAIL"
    assert ep["development_run_count"] == 1
    assert ep["runner_start_count"] == 1
    assert ep["evaluation_authorized"] is False
    assert ep["development_evaluation_executed"] is True
    assert ep["productive_pnl_evaluator_duplicated"] is False


def test_entry_point_preflight_and_dry_validate_no_slot_consume() -> None:
    pre = run_preflight_only(REPO)
    assert pre["runner_started"] is False
    assert pre["evaluation_executed"] is False
    assert pre["holdout_accessed"] is False
    assert pre["run_counters"]["contract_development_run_count"] == 1
    dry = run_dry_validate(REPO)
    assert dry["runner_started"] is False
    assert dry["evaluation_executed"] is False
    assert dry["status"] == "DRY_VALIDATE_PASS_EXECUTABLE_PATH_PRESENT"
    assert dry["run_counters"]["contract_development_run_count"] == 1


def test_ex_ante_reachability_gate() -> None:
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=100) is True
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=59) is False


def test_precedence_initial_stop_beats_reclaim_and_regime() -> None:
    pos = open_position_from_fill_v1(
        side="LONG",
        fill_index=0,
        entry_price=100.0,
        atr_at_fill=1.0,
        failed_impulse_extreme=99.0,
    )
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=98.0,
        close=100.5,  # also reclaim
        percentile_rank=0.10,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is VefcfExitReasonV1.INITIAL_STOP


def test_impulse_reclaim_beats_regime_when_stop_not_hit() -> None:
    pos = open_position_from_fill_v1(
        side="LONG",
        fill_index=0,
        entry_price=100.0,
        atr_at_fill=1.0,
        failed_impulse_extreme=99.0,
    )
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=99.5,
        close=99.5,  # > extreme 99
        percentile_rank=0.10,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is VefcfExitReasonV1.IMPULSE_RECLAIM_INVALIDATION


def test_short_reclaim_rule() -> None:
    pos = open_position_from_fill_v1(
        side="SHORT",
        fill_index=0,
        entry_price=100.0,
        atr_at_fill=1.0,
        failed_impulse_extreme=101.0,
    )
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=100.5,
        low=99.0,
        close=100.0,  # < extreme 101
        percentile_rank=0.80,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is VefcfExitReasonV1.IMPULSE_RECLAIM_INVALIDATION


def test_trailing_stop_not_in_precedence() -> None:
    assert "TRAILING_STOP" not in EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1


def test_expansion_bar_never_entry_and_no_immediate_breakout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research import volatility_expansion_failed_continuation_fade_v1_strategy_v1 as strat

    frame = _synthetic_frame(120)
    n = len(frame)
    ranks = np.full(n, 0.5, dtype=float)
    ranks[37:41] = 0.70
    ranks[41:] = 0.70
    rv = np.full(n, 0.01, dtype=float)
    monkeypatch.setattr(
        strat,
        "compute_percentile_rank_120_realized_vol_v1",
        lambda close: pd.Series(ranks, index=close.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_realized_volatility_24_v1",
        lambda close: pd.Series(rv, index=close.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_atr14_v1",
        lambda h, l, c: pd.Series(1.0, index=c.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_prior_high_low_channel_bounds_v1",
        lambda high, low, lookback=20: (
            pd.Series(90.0, index=high.index),
            pd.Series(80.0, index=low.index),
        ),
    )
    results, _ = generate_vefcf_events_and_roundtrips_v1(frame)
    assert results[40].event is VefcfEventV1.NONE  # expansion confirmation: never entry
    # Immediate post-expansion breakout without failure must not enter on bar 41.
    assert results[41].event is VefcfEventV1.NONE
    assert all(r.event is not VefcfEventV1.ENTRY_EVENT for r in results[:42])


def test_extreme_break_fade_short_against_long_impulse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research import volatility_expansion_failed_continuation_fade_v1_strategy_v1 as strat

    frame = _synthetic_frame(160)
    _patch_vol(monkeypatch, strat, len(frame))
    _force_long_impulse(monkeypatch, strat, frame, 50)
    # Extreme break against LONG: low < impulse_low=108
    frame.loc[frame.index[51], "high"] = 110.0
    frame.loc[frame.index[51], "low"] = 107.0
    frame.loc[frame.index[51], "close"] = 107.5
    results, rts = generate_vefcf_events_and_roundtrips_v1(frame)
    entries = [i for i, r in enumerate(results) if r.event is VefcfEventV1.ENTRY_EVENT]
    assert entries == [51]
    assert results[51].entry_side is StrategyEntrySideCarrierV1.SHORT
    assert results[51].fade_trigger is VefcfFadeTriggerV1.IMPULSE_EXTREME_BREAK_AGAINST_IMPULSE
    assert len(rts) == 1
    assert rts[0].side == "SHORT"


def test_deep_pullback_fade_without_continuation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research import volatility_expansion_failed_continuation_fade_v1_strategy_v1 as strat

    frame = _synthetic_frame(160)
    _patch_vol(monkeypatch, strat, len(frame))
    _force_long_impulse(monkeypatch, strat, frame, 50)
    # Deep pullback >=50% without breaking impulse_low: depth=(112-110)/4=0.5
    frame.loc[frame.index[51], "high"] = 111.5
    frame.loc[frame.index[51], "low"] = 110.0
    frame.loc[frame.index[51], "close"] = 110.5
    results, _ = generate_vefcf_events_and_roundtrips_v1(frame)
    entries = [i for i, r in enumerate(results) if r.event is VefcfEventV1.ENTRY_EVENT]
    assert entries == [51]
    assert results[51].entry_side is StrategyEntrySideCarrierV1.SHORT
    assert results[51].fade_trigger is VefcfFadeTriggerV1.DEEP_PULLBACK_WITHOUT_CONTINUATION


def test_window_exhaustion_fade_after_qualifying_pullback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research import volatility_expansion_failed_continuation_fade_v1_strategy_v1 as strat

    frame = _synthetic_frame(160)
    _patch_vol(monkeypatch, strat, len(frame))
    _force_long_impulse(monkeypatch, strat, frame, 50)
    # Qualifying ~25%: low to 111 -> depth (112-111)/4=0.25; no continuation / no deep
    for j in range(51, 59):
        frame.loc[frame.index[j], "high"] = 111.5
        frame.loc[frame.index[j], "low"] = 111.0
        frame.loc[frame.index[j], "close"] = 111.2  # not > swing high 111.5
    results, _ = generate_vefcf_events_and_roundtrips_v1(frame)
    entries = [i for i, r in enumerate(results) if r.event is VefcfEventV1.ENTRY_EVENT]
    assert entries == [58]
    assert results[58].fade_trigger is (
        VefcfFadeTriggerV1.QUALIFYING_PULLBACK_WINDOW_EXHAUSTION_WITHOUT_CONTINUATION
    )
    assert results[58].entry_side is StrategyEntrySideCarrierV1.SHORT


def test_successful_continuation_cancels_fade(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.research import volatility_expansion_failed_continuation_fade_v1_strategy_v1 as strat

    frame = _synthetic_frame(160)
    _patch_vol(monkeypatch, strat, len(frame))
    _force_long_impulse(monkeypatch, strat, frame, 50)
    frame.loc[frame.index[51], "high"] = 111.5
    frame.loc[frame.index[51], "low"] = 111.0
    frame.loc[frame.index[51], "close"] = 111.2
    # Continuation: close > frozen swing high
    frame.loc[frame.index[52], "high"] = 113.0
    frame.loc[frame.index[52], "low"] = 111.0
    frame.loc[frame.index[52], "close"] = 112.0
    results, rts = generate_vefcf_events_and_roundtrips_v1(frame)
    assert all(r.event is not VefcfEventV1.ENTRY_EVENT for r in results)
    assert rts == []
    assert results[52].reason.value == "CONTINUATION_CANCELLED_FADE"


def test_no_trigger_no_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.research import volatility_expansion_failed_continuation_fade_v1_strategy_v1 as strat

    frame = _synthetic_frame(160)
    _patch_vol(monkeypatch, strat, len(frame))
    _force_long_impulse(monkeypatch, strat, frame, 50)
    # Shallow only (<15%) through window
    for j in range(51, 59):
        frame.loc[frame.index[j], "high"] = 111.8
        frame.loc[frame.index[j], "low"] = 111.5  # depth (112-111.5)/4=0.125
        frame.loc[frame.index[j], "close"] = 111.6
    results, rts = generate_vefcf_events_and_roundtrips_v1(frame)
    assert all(r.event is not VefcfEventV1.ENTRY_EVENT for r in results)
    assert rts == []


def test_short_impulse_fade_long_direction(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.research import volatility_expansion_failed_continuation_fade_v1_strategy_v1 as strat

    frame = _synthetic_frame(160)
    _patch_vol(monkeypatch, strat, len(frame))
    monkeypatch.setattr(
        strat,
        "compute_prior_high_low_channel_bounds_v1",
        lambda high, low, lookback=20: (
            pd.Series(1000.0, index=high.index),
            pd.Series(
                [91.0 if i == 50 else 0.0 for i in range(len(low))],
                index=low.index,
            ),
        ),
    )
    frame.loc[frame.index[50], "close"] = 90.0
    frame.loc[frame.index[50], "high"] = 92.0
    frame.loc[frame.index[50], "low"] = 88.0  # range 4
    # Extreme break against SHORT: high > impulse_high=92
    frame.loc[frame.index[51], "high"] = 93.0
    frame.loc[frame.index[51], "low"] = 90.0
    frame.loc[frame.index[51], "close"] = 92.5
    results, _ = generate_vefcf_events_and_roundtrips_v1(frame)
    entries = [i for i, r in enumerate(results) if r.event is VefcfEventV1.ENTRY_EVENT]
    assert entries == [51]
    assert results[51].entry_side is StrategyEntrySideCarrierV1.LONG
    assert results[51].fade_trigger is VefcfFadeTriggerV1.IMPULSE_EXTREME_BREAK_AGAINST_IMPULSE


def test_deterministic_repeat(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.research import volatility_expansion_failed_continuation_fade_v1_strategy_v1 as strat

    frame = _synthetic_frame(160)
    _patch_vol(monkeypatch, strat, len(frame))
    _force_long_impulse(monkeypatch, strat, frame, 50)
    frame.loc[frame.index[51], "high"] = 110.0
    frame.loc[frame.index[51], "low"] = 107.0
    frame.loc[frame.index[51], "close"] = 107.5
    a, ra = generate_vefcf_events_and_roundtrips_v1(frame)
    b, rb = generate_vefcf_events_and_roundtrips_v1(frame)
    assert [r.event for r in a] == [r.event for r in b]
    assert [r.entry_side for r in a] == [r.entry_side for r in b]
    assert [(x.signal_index, x.side, x.exit_reason) for x in ra] == [
        (x.signal_index, x.side, x.exit_reason) for x in rb
    ]


def test_no_cross_instrument_state_leak(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.research import volatility_expansion_failed_continuation_fade_v1_strategy_v1 as strat

    frame_a = _synthetic_frame(160)
    frame_b = _synthetic_frame(160)
    _patch_vol(monkeypatch, strat, len(frame_a))
    _force_long_impulse(monkeypatch, strat, frame_a, 50)
    frame_a.loc[frame_a.index[51], "high"] = 110.0
    frame_a.loc[frame_a.index[51], "low"] = 107.0
    frame_a.loc[frame_a.index[51], "close"] = 107.5
    res_a, _ = generate_vefcf_events_and_roundtrips_v1(frame_a)
    res_b, rts_b = generate_vefcf_events_and_roundtrips_v1(frame_b)
    assert any(r.event is VefcfEventV1.ENTRY_EVENT for r in res_a)
    assert all(r.event is not VefcfEventV1.ENTRY_EVENT for r in res_b)
    assert rts_b == []


def test_no_lookahead_uses_only_completed_bar_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Channel bounds and ranks are bar-local; future bars must not change past decisions."""
    from src.research import volatility_expansion_failed_continuation_fade_v1_strategy_v1 as strat

    frame = _synthetic_frame(220)
    monkeypatch.setattr(
        strat,
        "compute_percentile_rank_120_realized_vol_v1",
        lambda close: pd.Series(np.full(len(close), 0.70), index=close.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_realized_volatility_24_v1",
        lambda close: pd.Series(np.full(len(close), 0.01), index=close.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_atr14_v1",
        lambda h, l, c: pd.Series(1.0, index=c.index),
    )
    _force_long_impulse(monkeypatch, strat, frame, 50)
    frame.loc[frame.index[51], "high"] = 110.0
    frame.loc[frame.index[51], "low"] = 107.0
    frame.loc[frame.index[51], "close"] = 107.5
    # Prefix long enough that ex-ante TIME_EXIT reachability matches the full series.
    prefix = frame.iloc[:160].copy()
    res_prefix, _ = generate_vefcf_events_and_roundtrips_v1(prefix)
    res_full, _ = generate_vefcf_events_and_roundtrips_v1(frame)
    for i in range(len(prefix)):
        assert res_prefix[i].event == res_full[i].event
        assert res_prefix[i].entry_side == res_full[i].entry_side
        assert res_prefix[i].fade_trigger == res_full[i].fade_trigger
