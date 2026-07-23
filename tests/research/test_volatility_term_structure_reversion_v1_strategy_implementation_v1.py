"""Focused tests for VTSR strategy implementation, exits, and binding."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.research.volatility_term_structure_reversion_v1_exit_state_machine_v1 import (
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    REGIME_INVALIDATION_RATIO_PERCENTILE_LT_V1,
    TERM_STRUCTURE_NORMALIZATION_RATIO_PERCENTILE_LT_V1,
    TIME_EXIT_MAX_BARS_V1,
    TRAILING_STOP_FORBIDDEN_V1,
    VtsrExitReasonV1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.research.volatility_term_structure_reversion_v1_strategy_implementation_binding_v1 import (
    REQUIRED_DIGEST,
    load_and_validate_repo_binding,
)
from src.research.volatility_term_structure_reversion_v1_strategy_v1 import (
    DEPRESSED_ENTRY_FORBIDDEN_IN_V1,
    ELEVATED_MIN_CONSECUTIVE_BARS_V1,
    ELEVATED_RATIO_PERCENTILE_INCLUSIVE_MIN_V1,
    EXIT_PARAMS_V1,
    EXIT_STATE_MACHINE_IMPLEMENTED_V1,
    HYPOTHESIS_ID_V1,
    NO_CHANNEL_BREAKOUT_REQUIRED_V1,
    PREDECESSOR_STRATEGY_ID_V1,
    PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1,
    REARM_RATIO_PERCENTILE_STRICTLY_BELOW_V1,
    STRATEGY_IDENTITY_V1,
    VEFCF_FAILED_CONTINUATION_FADE_ENTRY_FORBIDDEN_V1,
    VtsrEventV1,
    VtsrReasonV1,
    generate_vtsr_events_and_roundtrips_v1,
)
from src.research.volatility_term_structure_reversion_v1_vol_state_v1 import (
    PERCENTILE_TIE_METHOD_V1,
    RV_LONG_HORIZON_COMPLETED_BARS_V1,
    RV_SHORT_HORIZON_COMPLETED_BARS_V1,
    VOL_ESTIMATOR_FAMILY_V1,
    compute_percentile_rank_120_rv_term_structure_ratio_v1,
    compute_rv_term_structure_ratio_short_over_long_v1,
)
import src.research.volatility_term_structure_reversion_v1_strategy_v1 as strat

from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyEntrySideCarrierV1,
)

REPO = Path(__file__).resolve().parents[2]


def _patch_vol(
    monkeypatch: pytest.MonkeyPatch,
    n: int,
    *,
    ranks: np.ndarray | None = None,
    rank: float = 0.85,
) -> None:
    if ranks is None:
        ranks = np.full(n, rank, dtype=float)
    ratio = np.full(n, 1.5, dtype=float)
    short = np.full(n, 0.02, dtype=float)
    long = np.full(n, 0.01, dtype=float)
    monkeypatch.setattr(
        strat,
        "compute_percentile_rank_120_rv_term_structure_ratio_v1",
        lambda close_or_ratio: pd.Series(ranks, index=close_or_ratio.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_rv_term_structure_ratio_short_over_long_v1",
        lambda close: pd.Series(ratio, index=close.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_realized_volatility_short_8_v1",
        lambda close: pd.Series(short, index=close.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_realized_volatility_long_48_v1",
        lambda close: pd.Series(long, index=close.index),
    )
    monkeypatch.setattr(
        strat,
        "compute_atr14_v1",
        lambda h, l, c: pd.Series(1.0, index=c.index),
    )


def _synthetic_frame(n: int = 260, *, uptrend: bool = True) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="h", tz="UTC")
    drift = np.linspace(0, 2.0, n) if uptrend else np.linspace(2.0, 0, n)
    close = pd.Series(100.0, index=idx, dtype=float) + pd.Series(drift, index=idx)
    return pd.DataFrame(
        {"open": close.copy(), "high": close + 1.0, "low": close - 1.0, "close": close}
    )


def test_import_safety_and_binding() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["exit_state_machine_implemented"] is True
    assert report["evaluation_authorized"] is False
    assert report["development_evaluation_authorized"] is False
    assert report["frozen_measurement_contract_digest"] == REQUIRED_DIGEST
    assert STRATEGY_IDENTITY_V1 == "VOLATILITY_TERM_STRUCTURE_REVERSION_V1"
    assert HYPOTHESIS_ID_V1 == ("VOLATILITY_TERM_STRUCTURE_REVERSION_NON_BITCOIN_PERPETUALS_V1")
    assert PREDECESSOR_STRATEGY_ID_V1 == "VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1"
    assert RV_SHORT_HORIZON_COMPLETED_BARS_V1 == 8
    assert RV_LONG_HORIZON_COMPLETED_BARS_V1 == 48
    assert VOL_ESTIMATOR_FAMILY_V1 == "REALIZED_VOLATILITY_TERM_STRUCTURE"
    assert PERCENTILE_TIE_METHOD_V1 == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert ELEVATED_MIN_CONSECUTIVE_BARS_V1 == 2
    assert ELEVATED_RATIO_PERCENTILE_INCLUSIVE_MIN_V1 == 0.80
    assert REARM_RATIO_PERCENTILE_STRICTLY_BELOW_V1 == 0.50
    assert DEPRESSED_ENTRY_FORBIDDEN_IN_V1 is True
    assert NO_CHANNEL_BREAKOUT_REQUIRED_V1 is True
    assert VEFCF_FAILED_CONTINUATION_FADE_ENTRY_FORBIDDEN_V1 is True
    assert EXIT_STATE_MACHINE_IMPLEMENTED_V1 is True
    assert TRAILING_STOP_FORBIDDEN_V1 is True
    assert EXIT_PARAMS_V1["trailing_stop_forbidden"] is True
    assert EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1 == (
        "INITIAL_STOP",
        "TERM_STRUCTURE_NORMALIZATION_INVALIDATION",
        "REGIME_INVALIDATION",
        "TIME_EXIT",
        "END_OF_INSTRUMENT_LIQUIDATION",
        "END_OF_PANEL_LIQUIDATION",
    )
    assert TERM_STRUCTURE_NORMALIZATION_RATIO_PERCENTILE_LT_V1 == 0.55
    assert REGIME_INVALIDATION_RATIO_PERCENTILE_LT_V1 == 0.40
    assert TIME_EXIT_MAX_BARS_V1 == 48
    assert (REPO / PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1).is_file()


def test_ex_ante_reachability_gate() -> None:
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=100) is True
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=59) is False


def test_precedence_initial_stop_beats_normalization_and_regime() -> None:
    pos = open_position_from_fill_v1(
        side="LONG",
        fill_index=0,
        entry_price=100.0,
        atr_at_fill=1.0,
    )
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=98.0,
        close=100.5,
        ratio_percentile=0.10,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is VtsrExitReasonV1.INITIAL_STOP


def test_term_structure_normalization_beats_regime() -> None:
    pos = open_position_from_fill_v1(
        side="LONG",
        fill_index=0,
        entry_price=100.0,
        atr_at_fill=1.0,
    )
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=99.5,
        close=100.2,
        ratio_percentile=0.50,  # <0.55 and not <0.40
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is VtsrExitReasonV1.TERM_STRUCTURE_NORMALIZATION_INVALIDATION


def test_preregistered_long_fade_after_negative_short_horizon_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _synthetic_frame(260, uptrend=False)
    ranks = np.full(len(frame), 0.40, dtype=float)
    ranks[50] = 0.85
    ranks[51] = 0.90
    _patch_vol(monkeypatch, len(frame), ranks=ranks)
    events, roundtrips = generate_vtsr_events_and_roundtrips_v1(frame)
    entries = [e for e in events if e.event is VtsrEventV1.ENTRY_EVENT]
    assert len(entries) == 1
    assert entries[0].entry_side is StrategyEntrySideCarrierV1.LONG
    assert entries[0].signal_index == 51
    assert entries[0].short_horizon_signed_return is not None
    assert entries[0].short_horizon_signed_return < 0.0
    assert len(roundtrips) >= 1
    assert roundtrips[0].side == "LONG"
    assert roundtrips[0].fill_index == 52


def test_preregistered_short_fade_after_positive_short_horizon_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _synthetic_frame(260, uptrend=True)
    ranks = np.full(len(frame), 0.40, dtype=float)
    ranks[50] = 0.85
    ranks[51] = 0.90
    _patch_vol(monkeypatch, len(frame), ranks=ranks)
    events, roundtrips = generate_vtsr_events_and_roundtrips_v1(frame)
    entries = [e for e in events if e.event is VtsrEventV1.ENTRY_EVENT]
    assert len(entries) == 1
    assert entries[0].entry_side is StrategyEntrySideCarrierV1.SHORT
    assert entries[0].signal_index == 51
    assert entries[0].short_horizon_signed_return is not None
    assert entries[0].short_horizon_signed_return > 0.0
    assert roundtrips[0].side == "SHORT"


def test_neutral_when_not_elevated(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _synthetic_frame(220, uptrend=True)
    _patch_vol(monkeypatch, len(frame), rank=0.40)
    events, roundtrips = generate_vtsr_events_and_roundtrips_v1(frame)
    assert all(e.event is VtsrEventV1.NONE for e in events)
    assert roundtrips == []
    assert any(e.reason is VtsrReasonV1.NO_EVENT for e in events)


def test_warmup_before_valid_percentile(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _synthetic_frame(40, uptrend=True)
    ranks = np.full(40, np.nan, dtype=float)
    _patch_vol(monkeypatch, 40, ranks=ranks)
    events, roundtrips = generate_vtsr_events_and_roundtrips_v1(frame)
    assert roundtrips == []
    assert all(e.reason is VtsrReasonV1.WARMUP for e in events)
    assert all(e.entry_side is StrategyEntrySideCarrierV1.NONE for e in events)


def test_missing_ohlc_and_zero_return_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _synthetic_frame(260, uptrend=True)
    # Force flat closes around elevated confirmation so signed return == 0.
    frame.loc[frame.index[43:52], "close"] = 100.0
    frame.loc[frame.index[43:52], "open"] = 100.0
    ranks = np.full(len(frame), 0.40, dtype=float)
    ranks[50] = 0.85
    ranks[51] = 0.90
    _patch_vol(monkeypatch, len(frame), ranks=ranks)
    events, roundtrips = generate_vtsr_events_and_roundtrips_v1(frame)
    assert roundtrips == []
    assert events[51].reason is VtsrReasonV1.AMBIGUOUS_DIRECTION_FAIL_CLOSED
    assert events[51].entry_side is StrategyEntrySideCarrierV1.NONE


def test_deterministic_repeatability(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _synthetic_frame(260, uptrend=True)
    ranks = np.full(len(frame), 0.40, dtype=float)
    ranks[50] = 0.85
    ranks[51] = 0.90
    _patch_vol(monkeypatch, len(frame), ranks=ranks)
    a_events, a_rt = generate_vtsr_events_and_roundtrips_v1(frame)
    b_events, b_rt = generate_vtsr_events_and_roundtrips_v1(frame)
    assert [(e.event, e.entry_side, e.reason, e.signal_index) for e in a_events] == [
        (e.event, e.entry_side, e.reason, e.signal_index) for e in b_events
    ]
    assert [(r.side, r.signal_index, r.fill_index, r.exit_reason) for r in a_rt] == [
        (r.side, r.signal_index, r.fill_index, r.exit_reason) for r in b_rt
    ]


def test_no_lookahead_uses_only_past_completed_rank_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Future elevated ranks after the signal bar must not affect the entry decision."""
    frame = _synthetic_frame(260, uptrend=True)
    ranks = np.full(len(frame), 0.40, dtype=float)
    ranks[50] = 0.85
    ranks[51] = 0.90
    # Poison the future — must not create extra entries or change side.
    ranks[52:] = 0.99
    _patch_vol(monkeypatch, len(frame), ranks=ranks)
    events, _ = generate_vtsr_events_and_roundtrips_v1(frame)
    entries = [e for e in events if e.event is VtsrEventV1.ENTRY_EVENT]
    assert len(entries) == 1
    assert entries[0].signal_index == 51
    assert entries[0].entry_side is StrategyEntrySideCarrierV1.SHORT


def test_no_cross_instrument_state_leaks(monkeypatch: pytest.MonkeyPatch) -> None:
    frame_a = _synthetic_frame(260, uptrend=True)
    frame_b = _synthetic_frame(260, uptrend=False)
    ranks = np.full(len(frame_a), 0.40, dtype=float)
    ranks[50] = 0.85
    ranks[51] = 0.90
    _patch_vol(monkeypatch, len(frame_a), ranks=ranks)
    events_a, _ = generate_vtsr_events_and_roundtrips_v1(frame_a)
    events_b, _ = generate_vtsr_events_and_roundtrips_v1(frame_b)
    entry_a = next(e for e in events_a if e.event is VtsrEventV1.ENTRY_EVENT)
    entry_b = next(e for e in events_b if e.event is VtsrEventV1.ENTRY_EVENT)
    assert entry_a.entry_side is StrategyEntrySideCarrierV1.SHORT
    assert entry_b.entry_side is StrategyEntrySideCarrierV1.LONG


def test_vol_state_ratio_and_percentile_causal() -> None:
    idx = pd.date_range("2022-01-01", periods=200, freq="h", tz="UTC")
    rng = np.random.default_rng(7)
    close = pd.Series(100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, size=200))), index=idx)
    ratio = compute_rv_term_structure_ratio_short_over_long_v1(close)
    rank = compute_percentile_rank_120_rv_term_structure_ratio_v1(ratio)
    # First long-horizon RV needs 48 returns → index 48; first full percentile at 48+119=167.
    assert ratio.iloc[:48].isna().all()
    assert rank.iloc[:167].isna().all()
    assert np.isfinite(rank.iloc[167])
