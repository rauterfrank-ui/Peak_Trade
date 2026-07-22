"""Focused tests for VEPC strategy implementation, exits, and binding."""

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
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.binding_v1 import (
    load_and_validate_entry_point_binding,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.entry_point_v1 import (
    run_dry_validate,
    run_preflight_only,
)
from src.research.volatility_expansion_pullback_continuation_v1_exit_state_machine_v1 import (
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    REGIME_INVALIDATION_PERCENTILE_LT_V1,
    TIME_EXIT_MAX_BARS_V1,
    TRAILING_STOP_FORBIDDEN_V1,
    VepcExitReasonV1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.research.volatility_expansion_pullback_continuation_v1_strategy_implementation_binding_v1 import (
    REQUIRED_DIGEST,
    load_and_validate_repo_binding,
)
from src.research.volatility_expansion_pullback_continuation_v1_strategy_v1 import (
    ENTRY_ON_EXPANSION_CONFIRMATION_BAR_FORBIDDEN_V1,
    EXIT_PARAMS_V1,
    EXIT_STATE_MACHINE_IMPLEMENTED_V1,
    EXPANSION_MIN_CONSECUTIVE_BARS_V1,
    EXPANSION_PERCENTILE_INCLUSIVE_MIN_V1,
    IMMEDIATE_BREAKOUT_WITHOUT_PULLBACK_FORBIDDEN_V1,
    MAX_PULLBACK_BARS_INCLUSIVE_V1,
    MAX_PULLBACK_FRACTION_V1,
    MIN_PULLBACK_FRACTION_V1,
    PREDECESSOR_STRATEGY_ID_V1,
    PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1,
    STRATEGY_IDENTITY_V1,
    VepcEventV1,
    classify_price_channel_break_v1,
    compute_prior_high_low_channel_bounds_v1,
    generate_vepc_events_and_roundtrips_v1,
)
from src.research.volatility_expansion_pullback_continuation_v1_vol_state_v1 import (
    PERCENTILE_TIE_METHOD_V1,
    RV_PERIOD_V1,
)

REPO = Path(__file__).resolve().parents[2]


def test_import_safety_and_binding() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["exit_state_machine_implemented"] is True
    assert report["evaluation_authorized"] is False
    assert report["development_evaluation_authorized"] is False
    assert report["frozen_measurement_contract_digest"] == REQUIRED_DIGEST
    assert STRATEGY_IDENTITY_V1 == "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1"
    assert PREDECESSOR_STRATEGY_ID_V1 == "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1"
    assert RV_PERIOD_V1 == 24
    assert PERCENTILE_TIE_METHOD_V1 == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert EXPANSION_MIN_CONSECUTIVE_BARS_V1 == 4
    assert EXPANSION_PERCENTILE_INCLUSIVE_MIN_V1 == 0.65
    assert MIN_PULLBACK_FRACTION_V1 == 0.15
    assert MAX_PULLBACK_FRACTION_V1 == 0.50
    assert MAX_PULLBACK_BARS_INCLUSIVE_V1 == 8
    assert ENTRY_ON_EXPANSION_CONFIRMATION_BAR_FORBIDDEN_V1 is True
    assert IMMEDIATE_BREAKOUT_WITHOUT_PULLBACK_FORBIDDEN_V1 is True
    assert EXIT_STATE_MACHINE_IMPLEMENTED_V1 is True
    assert TRAILING_STOP_FORBIDDEN_V1 is True
    assert EXIT_PARAMS_V1["trailing_stop_forbidden"] is True
    assert EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1 == (
        "INITIAL_STOP",
        "PULLBACK_STRUCTURE_INVALIDATION",
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
    assert ep["status"] == "RUN_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT"
    assert ep["development_run_count"] == 1
    assert ep["runner_start_count"] == 1
    assert ep["development_evaluation_executed"] is False
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


def _long_pos(*, fill: int = 0, entry: float = 100.0, atr: float = 1.0):
    return open_position_from_fill_v1(
        side="LONG",
        fill_index=fill,
        entry_price=entry,
        atr_at_fill=atr,
        pullback_swing_high=101.0,
        pullback_swing_low=99.0,
    )


def test_precedence_initial_stop_beats_pullback_and_regime() -> None:
    pos = _long_pos()
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=98.0,
        close=90.0,
        percentile_rank=0.10,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is VepcExitReasonV1.INITIAL_STOP


def test_pullback_invalidation_beats_regime_when_stop_not_hit() -> None:
    pos = _long_pos()
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=99.5,
        close=98.5,  # below pullback_swing_low=99
        percentile_rank=0.10,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is VepcExitReasonV1.PULLBACK_STRUCTURE_INVALIDATION


def test_trailing_stop_not_in_precedence() -> None:
    assert "TRAILING_STOP" not in EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1


def _synthetic_frame(n: int = 220) -> pd.DataFrame:
    """Build a long series where RV/rank can be monkeypatched for admission tests."""
    idx = pd.date_range("2022-01-01", periods=n, freq="h", tz="UTC")
    close = pd.Series(100.0, index=idx, dtype=float)
    # mild noise so ATR/RV finite after warmup
    close = close + pd.Series(np.linspace(0, 1, n), index=idx)
    high = close + 1.0
    low = close - 1.0
    open_ = close.copy()
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})


def test_expansion_bar_never_entry_and_no_immediate_breakout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research import volatility_expansion_pullback_continuation_v1_strategy_v1 as strat

    frame = _synthetic_frame(120)
    n = len(frame)
    ranks = np.full(n, 0.5, dtype=float)
    # Expansion confirms at bar 40 (bars 37..40 >= 0.65)
    ranks[37:41] = 0.70
    # keep expansion active afterward for impulse
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
    # Force channel break on expansion confirmation bar 40 and next bars.
    monkeypatch.setattr(
        strat,
        "compute_prior_high_low_channel_bounds_v1",
        lambda high, low, lookback=20: (
            pd.Series(90.0, index=high.index),
            pd.Series(80.0, index=low.index),
        ),
    )

    results, roundtrips = generate_vepc_events_and_roundtrips_v1(frame)
    assert results[40].event is VepcEventV1.NONE  # expansion confirmation: never entry
    # Immediate post-expansion breakout without pullback must not enter on bar 41.
    assert results[41].event is VepcEventV1.NONE
    assert all(r.event is not VepcEventV1.ENTRY_EVENT for r in results[:42])
    assert roundtrips == []


def test_pullback_fraction_and_bar_limits_block_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.research import volatility_expansion_pullback_continuation_v1_strategy_v1 as strat
    from src.research.price_channel_breakout_core_v1 import PriceChannelBreakSideV1

    frame = _synthetic_frame(130)
    n = len(frame)
    ranks = np.full(n, 0.70, dtype=float)
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
            pd.Series(1000.0, index=high.index),  # no natural break
            pd.Series(0.0, index=low.index),
        ),
    )

    # Force impulse LONG only on bar 50; then shallow then deep pullbacks.
    def _break(close, upper, lower):
        # Called with scalars from strategy
        return PriceChannelBreakSideV1.NONE

    # Patch classify inside loop via side-effect on frame mutation is hard;
    # instead set upper below close only at bar 50 by mutating frame close/high/low.
    frame.loc[frame.index[50], "close"] = 110.0
    frame.loc[frame.index[50], "high"] = 112.0
    frame.loc[frame.index[50], "low"] = 100.0  # range=12
    monkeypatch.setattr(
        strat,
        "compute_prior_high_low_channel_bounds_v1",
        lambda high, low, lookback=20: (
            pd.Series(
                [109.0 if i == 50 else 1000.0 for i in range(len(high))],
                index=high.index,
            ),
            pd.Series(0.0, index=low.index),
        ),
    )

    # Pullback <15%: low only to 110.5 depth=(112-110.5)/12=0.125
    for j in range(51, 55):
        frame.loc[frame.index[j], "high"] = 111.0
        frame.loc[frame.index[j], "low"] = 110.5
        frame.loc[frame.index[j], "close"] = 110.8
    results, rts = generate_vepc_events_and_roundtrips_v1(frame)
    assert all(r.event is not VepcEventV1.ENTRY_EVENT for r in results[50:55])

    # Pullback >50%: low to 100 depth=(112-100)/12=1.0 -> invalidate, no entry
    frame2 = frame.copy()
    frame2.loc[frame2.index[51], "low"] = 100.0
    frame2.loc[frame2.index[51], "close"] = 101.0
    frame2.loc[frame2.index[51], "high"] = 111.0
    results2, _ = generate_vepc_events_and_roundtrips_v1(frame2)
    assert all(r.event is not VepcEventV1.ENTRY_EVENT for r in results2)

    # Pullback after >8 bars without valid fraction -> no entry
    frame3 = frame.copy()
    for j in range(51, 60):
        frame3.loc[frame3.index[j], "high"] = 111.5
        frame3.loc[frame3.index[j], "low"] = 110.8  # depth ~0.1
        frame3.loc[frame3.index[j], "close"] = 111.0
    results3, _ = generate_vepc_events_and_roundtrips_v1(frame3)
    assert all(r.event is not VepcEventV1.ENTRY_EVENT for r in results3[50:60])


def test_valid_pullback_requires_continuation_for_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.research import volatility_expansion_pullback_continuation_v1_strategy_v1 as strat

    frame = _synthetic_frame(160)
    n = len(frame)
    ranks = np.full(n, 0.70, dtype=float)
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
    # Impulse at 50: close breaks above upper=109
    monkeypatch.setattr(
        strat,
        "compute_prior_high_low_channel_bounds_v1",
        lambda high, low, lookback=20: (
            pd.Series(
                [109.0 if i == 50 else 1000.0 for i in range(len(high))],
                index=high.index,
            ),
            pd.Series(0.0, index=low.index),
        ),
    )
    frame.loc[frame.index[50], "close"] = 110.0
    frame.loc[frame.index[50], "high"] = 112.0
    frame.loc[frame.index[50], "low"] = 108.0  # range 4
    # Valid pullback ~25%: low to 111 -> depth (112-111)/4=0.25
    frame.loc[frame.index[51], "high"] = 111.5
    frame.loc[frame.index[51], "low"] = 111.0
    frame.loc[frame.index[51], "close"] = 111.2
    # No continuation yet (close not above swing high 111.5)
    frame.loc[frame.index[52], "high"] = 111.4
    frame.loc[frame.index[52], "low"] = 111.0
    frame.loc[frame.index[52], "close"] = 111.3
    results, rts = generate_vepc_events_and_roundtrips_v1(frame)
    assert results[51].event is VepcEventV1.NONE
    assert results[52].event is VepcEventV1.NONE
    # Continuation: close > frozen pullback_swing_high
    frame.loc[frame.index[53], "high"] = 113.0
    frame.loc[frame.index[53], "low"] = 111.0
    frame.loc[frame.index[53], "close"] = 112.0
    results2, rts2 = generate_vepc_events_and_roundtrips_v1(frame)
    entries = [i for i, r in enumerate(results2) if r.event is VepcEventV1.ENTRY_EVENT]
    assert entries == [53]
    assert results2[53].entry_side.value == "LONG"
    assert len(rts2) == 1
    assert rts2[0].exit_reason in VepcExitReasonV1


def test_short_side_symmetry_contract() -> None:
    # Contract-level: long/short mutually exclusive carriers exist.
    from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
        StrategyEntrySideCarrierV1,
    )

    assert StrategyEntrySideCarrierV1.LONG is not StrategyEntrySideCarrierV1.SHORT
    assert StrategyEntrySideCarrierV1.NONE is StrategyEntrySideCarrierV1.NONE
