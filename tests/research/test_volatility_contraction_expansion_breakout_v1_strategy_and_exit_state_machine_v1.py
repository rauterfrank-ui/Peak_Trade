"""Focused tests for VCEB preregistration semantics, exit pairability, and binding."""

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
from src.research.volatility_contraction_expansion_breakout_v1_exit_state_machine_v1 import (
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    REGIME_INVALIDATION_PERCENTILE_LT_V1,
    TIME_EXIT_MAX_BARS_V1,
    TRAILING_STOP_FORBIDDEN_V1,
    VcebExitReasonV1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.research.volatility_contraction_expansion_breakout_v1_strategy_implementation_binding_v1 import (
    REQUIRED_DIGEST,
    load_and_validate_repo_binding,
)
from src.research.volatility_contraction_expansion_breakout_v1_strategy_v1 import (
    CONTRACTION_MIN_CONSECUTIVE_BARS_V1,
    CONTRACTION_PERCENTILE_INCLUSIVE_MAX_V1,
    ENTRY_ON_JOINT_TRIGGER_BAR_T_FORBIDDEN_V1,
    ENTRY_WINDOW_END_OFFSET_V1,
    ENTRY_WINDOW_START_OFFSET_V1,
    EXIT_PARAMS_V1,
    EXIT_STATE_MACHINE_IMPLEMENTED_V1,
    EXPANSION_ABSOLUTE_PERCENTILE_INCLUSIVE_MIN_V1,
    EXPANSION_RELATIVE_PERCENTILE_RISE_INCLUSIVE_MIN_V1,
    JOINT_COINCIDENCE_REQUIRED_V1,
    PREDECESSOR_STRATEGY_ID_V1,
    PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1,
    STRATEGY_IDENTITY_V1,
    VcebEventV1,
    VcebReasonV1,
    classify_price_channel_break_v1,
    compute_prior_high_low_channel_bounds_v1,
    generate_vceb_events_and_roundtrips_v1,
)
from src.research.volatility_contraction_expansion_breakout_v1_vol_state_v1 import (
    PERCENTILE_TIE_METHOD_V1,
    RV_PERIOD_V1,
)

REPO = Path(__file__).resolve().parents[2]


def test_binding_and_preregistration_semantics() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["exit_state_machine_implemented"] is True
    assert report["evaluation_authorized"] is False
    assert report["development_evaluation_authorized"] is False
    assert report["frozen_measurement_contract_digest"] == REQUIRED_DIGEST
    assert STRATEGY_IDENTITY_V1 == "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1"
    assert PREDECESSOR_STRATEGY_ID_V1 == ("VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1")
    assert RV_PERIOD_V1 == 24
    assert PERCENTILE_TIE_METHOD_V1 == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert CONTRACTION_MIN_CONSECUTIVE_BARS_V1 == 8
    assert CONTRACTION_PERCENTILE_INCLUSIVE_MAX_V1 == 0.30
    assert EXPANSION_ABSOLUTE_PERCENTILE_INCLUSIVE_MIN_V1 == 0.65
    assert EXPANSION_RELATIVE_PERCENTILE_RISE_INCLUSIVE_MIN_V1 == 0.25
    assert ENTRY_WINDOW_START_OFFSET_V1 == 1
    assert ENTRY_WINDOW_END_OFFSET_V1 == 1
    assert JOINT_COINCIDENCE_REQUIRED_V1 is True
    assert ENTRY_ON_JOINT_TRIGGER_BAR_T_FORBIDDEN_V1 is True
    assert EXIT_STATE_MACHINE_IMPLEMENTED_V1 is True
    assert TRAILING_STOP_FORBIDDEN_V1 is True
    assert EXIT_PARAMS_V1["trailing_stop_forbidden"] is True
    assert EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1 == (
        "INITIAL_STOP",
        "OPPOSITE_BREAK_INVALIDATION",
        "REGIME_INVALIDATION",
        "TIME_EXIT",
        "END_OF_INSTRUMENT_LIQUIDATION",
        "END_OF_PANEL_LIQUIDATION",
    )
    assert REGIME_INVALIDATION_PERCENTILE_LT_V1 == 0.40
    assert CHANNEL_LOOKBACK_COMPLETED_BARS_V1 == 20
    assert (REPO / PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1).is_file()
    assert compute_prior_high_low_channel_bounds_v1 is core_bounds
    assert classify_price_channel_break_v1 is core_classify


def test_ex_ante_reachability_gate() -> None:
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=100) is True
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=59) is False
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=60) is True


def _long_pos(*, fill: int = 0, entry: float = 100.0, atr: float = 1.0):
    return open_position_from_fill_v1(
        side="LONG", fill_index=fill, entry_price=entry, atr_at_fill=atr
    )


def test_precedence_initial_stop_beats_opposite_break_and_regime() -> None:
    pos = _long_pos()
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=98.0,
        close=90.0,  # opposite break vs lower=95
        percentile_rank=0.10,  # regime
        upper_channel=110.0,
        lower_channel=95.0,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is VcebExitReasonV1.INITIAL_STOP


def test_opposite_break_beats_regime_when_stop_not_hit() -> None:
    pos = _long_pos()
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=99.0,
        close=90.0,
        percentile_rank=0.10,
        upper_channel=110.0,
        lower_channel=95.0,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is VcebExitReasonV1.OPPOSITE_BREAK_INVALIDATION


def test_trailing_stop_not_in_precedence() -> None:
    assert "TRAILING_STOP" not in EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1


def test_joint_entry_and_pairable_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 80
    idx = pd.date_range("2022-01-01", periods=n, freq="h", tz="UTC")
    close = pd.Series(100.0, index=idx, dtype=float)
    # Build a clean long break on bar t=30: prior highs < 105, close[30]=106
    high = close + 0.5
    low = close - 0.5
    for j in range(10, 30):
        high.iloc[j] = 104.0
        low.iloc[j] = 99.0
        close.iloc[j] = 100.0
    high.iloc[30] = 106.5
    low.iloc[30] = 100.0
    close.iloc[30] = 106.0
    open_ = close.copy()
    df = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": 1.0},
        index=idx,
    )

    ranks = np.full(n, 0.50, dtype=float)
    # contraction through t-1=29: bars 22..29 <= 0.30
    ranks[22:30] = 0.20
    # expansion on t=30
    ranks[30] = 0.70  # rise 0.50 from 0.20
    rv = np.full(n, 0.01, dtype=float)
    rv[30] = 0.02  # strictly increasing
    atr = pd.Series(1.0, index=idx)

    monkeypatch.setattr(
        "src.research.volatility_contraction_expansion_breakout_v1_strategy_v1."
        "compute_realized_volatility_24_v1",
        lambda *a, **k: pd.Series(rv, index=idx),
    )
    monkeypatch.setattr(
        "src.research.volatility_contraction_expansion_breakout_v1_strategy_v1."
        "compute_percentile_rank_120_realized_vol_v1",
        lambda *a, **k: pd.Series(ranks, index=idx),
    )
    monkeypatch.setattr(
        "src.research.volatility_contraction_expansion_breakout_v1_strategy_v1.compute_atr14_v1",
        lambda *a, **k: atr,
    )

    rows, roundtrips = generate_vceb_events_and_roundtrips_v1(df)
    assert rows[30].event is VcebEventV1.ENTRY_EVENT
    assert rows[30].entry_side.value == "LONG"
    # No fill on trigger bar t
    assert rows[30].reason is VcebReasonV1.SUCCESSFUL_ENTRY
    assert rows[31].reason is VcebReasonV1.POSITION_OPEN
    assert len(roundtrips) == 1
    rt = roundtrips[0]
    assert rt.signal_index == 30
    assert rt.fill_index == 31
    assert rt.exit_index > rt.fill_index
    assert rt.side == "LONG"


def test_expansion_without_break_resets(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 60
    idx = pd.date_range("2022-01-01", periods=n, freq="h", tz="UTC")
    close = pd.Series(100.0, index=idx, dtype=float)
    high = close + 0.5
    low = close - 0.5
    open_ = close.copy()
    df = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": 1.0},
        index=idx,
    )
    ranks = np.full(n, 0.50, dtype=float)
    ranks[22:30] = 0.20
    ranks[30] = 0.70
    rv = np.full(n, 0.01, dtype=float)
    rv[30] = 0.02
    atr = pd.Series(1.0, index=idx)
    monkeypatch.setattr(
        "src.research.volatility_contraction_expansion_breakout_v1_strategy_v1."
        "compute_realized_volatility_24_v1",
        lambda *a, **k: pd.Series(rv, index=idx),
    )
    monkeypatch.setattr(
        "src.research.volatility_contraction_expansion_breakout_v1_strategy_v1."
        "compute_percentile_rank_120_realized_vol_v1",
        lambda *a, **k: pd.Series(ranks, index=idx),
    )
    monkeypatch.setattr(
        "src.research.volatility_contraction_expansion_breakout_v1_strategy_v1.compute_atr14_v1",
        lambda *a, **k: atr,
    )
    rows, roundtrips = generate_vceb_events_and_roundtrips_v1(df)
    assert rows[30].event is VcebEventV1.NONE
    assert rows[30].reason is VcebReasonV1.JOINT_TRIGGER_WITHOUT_BREAK_RESET
    assert roundtrips == []


def test_time_exit_pairability() -> None:
    pos = _long_pos(fill=0)
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=TIME_EXIT_MAX_BARS_V1,
        high=101.0,
        low=99.0,
        close=100.5,
        percentile_rank=0.55,
        upper_channel=110.0,
        lower_channel=90.0,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is VcebExitReasonV1.TIME_EXIT
