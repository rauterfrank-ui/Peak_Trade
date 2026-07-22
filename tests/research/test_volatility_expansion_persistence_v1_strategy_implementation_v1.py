"""Deterministic tests for VOLATILITY_EXPANSION_PERSISTENCE_V1 implementation-only."""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.research.price_channel_breakout_core_v1 import (
    CHANNEL_LOOKBACK_COMPLETED_BARS_V1,
    PriceChannelBreakSideV1,
    classify_price_channel_break_v1,
    compute_prior_high_low_channel_bounds_v1,
)
from src.research.unconditional_20_bar_price_channel_breakout_v1 import (
    BASELINE_ID_V1,
    SHARED_CHANNEL_CORE_OWNER_V1,
    generate_unconditional_20_bar_price_channel_breakout_events_v1,
)
from src.research.volatility_expansion_persistence_v1_strategy_implementation_binding_v1 import (
    load_and_validate_repo_binding,
)
from src.research.volatility_expansion_persistence_v1_strategy_v1 import (
    COMPRESSION_REGIME_NOT_REQUIRED_V1,
    ENTRY_ON_CONFIRMATION_BAR_T_FORBIDDEN_V1,
    EXIT_PARAMS_DECLARATIVE_V1,
    EXPANSION_CONFIRMATION_THRESHOLD_V1,
    EXPANSION_EVENT_CONSUMPTION_V1,
    MAX_ENTRIES_PER_EXPANSION_EVENT_V1,
    PERSISTENCE_WINDOW_END_OFFSET_V1,
    PERSISTENCE_WINDOW_START_OFFSET_V1,
    REARM_THRESHOLD_EXCLUSIVE_MAX_V1,
    STRATEGY_IDENTITY_V1,
    VolatilityExpansionPersistenceEventV1,
    VolatilityExpansionPersistenceReasonV1,
    generate_volatility_expansion_persistence_events_v1,
)
from src.research.volatility_expansion_persistence_v1_vol_state_v1 import (
    ATR_PERIOD_V1,
    ATR_SMOOTHING_V1,
    PERCENTILE_TIE_METHOD_V1,
    compute_normalized_atr14_v1,
    compute_percentile_rank_120_normalized_atr_v1,
    percentile_rank_weak_leq_empirical_cdf_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyEntrySideCarrierV1,
)

REPO = Path(__file__).resolve().parents[2]


def _ohlc_from_close(closes: list[float], *, width: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=len(closes), freq="h", tz="UTC")
    close = pd.Series(closes, index=idx, dtype=float)
    high = close + width
    low = close - width
    open_ = close.copy()
    volume = pd.Series(1.0, index=idx)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume})


def _constant_tr_panel(n: int, *, close: float = 100.0, tr: float = 1.0) -> pd.DataFrame:
    closes = [close] * n
    return _ohlc_from_close(closes, width=tr / 2.0)


def _patch_vol(
    monkeypatch: pytest.MonkeyPatch,
    df: pd.DataFrame,
    ranks: np.ndarray,
    *,
    atr: float | np.ndarray = 0.01,
) -> None:
    rank_series = pd.Series(ranks, index=df.index)
    if isinstance(atr, (float, int)):
        atr_series = pd.Series(float(atr), index=df.index)
    else:
        atr_series = pd.Series(atr, index=df.index)
    monkeypatch.setattr(
        "src.research.volatility_expansion_persistence_v1_strategy_v1.compute_normalized_atr14_v1",
        lambda *a, **k: atr_series,
    )
    monkeypatch.setattr(
        "src.research.volatility_expansion_persistence_v1_strategy_v1."
        "compute_percentile_rank_120_normalized_atr_v1",
        lambda *a, **k: rank_series,
    )


# ---------------------------------------------------------------------------
# Vol state / percentile / ATR14
# ---------------------------------------------------------------------------


def test_percentile_and_atr14_constants() -> None:
    assert ATR_PERIOD_V1 == 14
    assert PERCENTILE_TIE_METHOD_V1 == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert ATR_SMOOTHING_V1 == "SIMPLE_MOVING_AVERAGE_OF_TRUE_RANGE"
    assert EXPANSION_CONFIRMATION_THRESHOLD_V1 == 0.80
    assert COMPRESSION_REGIME_NOT_REQUIRED_V1 is True
    assert ENTRY_ON_CONFIRMATION_BAR_T_FORBIDDEN_V1 is True
    assert EXPANSION_EVENT_CONSUMPTION_V1 == "SINGLE_USE"
    assert MAX_ENTRIES_PER_EXPANSION_EVENT_V1 == 1
    assert PERSISTENCE_WINDOW_START_OFFSET_V1 == 1
    assert PERSISTENCE_WINDOW_END_OFFSET_V1 == 6
    assert REARM_THRESHOLD_EXCLUSIVE_MAX_V1 == 0.80


def test_percentile_tie_and_warmup() -> None:
    window = [1.0, 2.0, 3.0]
    assert percentile_rank_weak_leq_empirical_cdf_v1(window, current_value=2.0) == pytest.approx(
        2.0 / 3.0
    )
    values = pd.Series(np.linspace(0.01, 1.20, 120))
    ranks = compute_percentile_rank_120_normalized_atr_v1(values)
    assert ranks.isna().iloc[:119].all()
    assert ranks.iloc[119] == pytest.approx(1.0)


def test_atr14_warmup_and_nonpositive_close_fail_closed() -> None:
    df = _constant_tr_panel(25, close=100.0, tr=2.0)
    norm = compute_normalized_atr14_v1(df["high"], df["low"], df["close"])
    assert norm.isna().iloc[:13].all()
    assert np.isfinite(norm.iloc[13])
    assert norm.iloc[13] == pytest.approx(2.0 / 100.0)
    bad = df.copy()
    bad.loc[bad.index[14], "close"] = 0.0
    assert np.isnan(compute_normalized_atr14_v1(bad["high"], bad["low"], bad["close"]).iloc[14])


def test_atr_no_cross_instrument_leak() -> None:
    a = _constant_tr_panel(30, close=100.0, tr=1.0)
    b = _constant_tr_panel(30, close=200.0, tr=10.0)
    na = compute_normalized_atr14_v1(a["high"], a["low"], a["close"])
    nb = compute_normalized_atr14_v1(b["high"], b["low"], b["close"])
    assert na.iloc[20] == pytest.approx(0.01)
    assert nb.iloc[20] == pytest.approx(0.05)
    b.loc[b.index[20], "high"] = 999.0
    na2 = compute_normalized_atr14_v1(a["high"], a["low"], a["close"])
    assert na2.iloc[20] == pytest.approx(na.iloc[20])


def test_strategy_and_baseline_share_identical_channel_core() -> None:
    import src.research.price_channel_breakout_core_v1 as core
    import src.research.unconditional_20_bar_price_channel_breakout_v1 as baseline_mod
    import src.research.volatility_expansion_persistence_v1_strategy_v1 as strategy_mod

    assert SHARED_CHANNEL_CORE_OWNER_V1 == "research.price_channel_breakout_core_v1"
    assert strategy_mod.compute_prior_high_low_channel_bounds_v1 is (
        core.compute_prior_high_low_channel_bounds_v1
    )
    assert baseline_mod.compute_prior_high_low_channel_bounds_v1 is (
        core.compute_prior_high_low_channel_bounds_v1
    )
    assert strategy_mod.classify_price_channel_break_v1 is core.classify_price_channel_break_v1
    src_strategy = inspect.getsource(strategy_mod)
    assert "shift(1).rolling" not in src_strategy


# ---------------------------------------------------------------------------
# Expansion / persistence state machine
# ---------------------------------------------------------------------------


def test_confirmation_and_entry_on_offset_not_on_t(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 170
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    # Confirmation at bar 150: t-2 < 0.80, t-1 and t >= 0.80, atr rising
    ranks[148] = 0.70
    ranks[149] = 0.85
    ranks[150] = 0.90
    atr[149] = 0.010
    atr[150] = 0.012
    # Entry at offset 2 (bar 152)
    ranks[151:157] = 0.90
    atr[151:157] = 0.012

    df = _ohlc_from_close([100.0] * n, width=1.0)
    df.loc[df.index[152], "close"] = 110.0
    df.loc[df.index[152], "high"] = 111.0
    df.loc[df.index[152], "low"] = 109.0
    _patch_vol(monkeypatch, df, ranks, atr=atr)

    results = generate_volatility_expansion_persistence_events_v1(df)
    assert results[150].reason is VolatilityExpansionPersistenceReasonV1.CONFIRMATION_OBSERVED
    assert results[150].event is VolatilityExpansionPersistenceEventV1.NONE
    assert results[150].persistence_offset is None
    assert results[151].persistence_offset == 1
    assert results[151].event is VolatilityExpansionPersistenceEventV1.NONE
    assert results[152].event is VolatilityExpansionPersistenceEventV1.ENTRY_EVENT
    assert results[152].entry_side is StrategyEntrySideCarrierV1.LONG
    assert results[152].persistence_offset == 2
    assert results[152].confirmation_bar_index == 150


def test_no_entry_when_confirmation_incomplete(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 160
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    # Only one bar >= 0.80 — not confirmation
    ranks[149] = 0.70
    ranks[150] = 0.90
    atr[150] = 0.02
    df = _ohlc_from_close([100.0] * n, width=1.0)
    df.loc[df.index[151], "close"] = 110.0
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_expansion_persistence_events_v1(df)
    assert all(r.event is VolatilityExpansionPersistenceEventV1.NONE for r in results[148:155])
    assert results[150].reason is not VolatilityExpansionPersistenceReasonV1.CONFIRMATION_OBSERVED


def test_atr_must_rise_on_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 160
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[148] = 0.70
    ranks[149] = 0.85
    ranks[150] = 0.90
    atr[149] = 0.012
    atr[150] = 0.010  # not rising
    df = _ohlc_from_close([100.0] * n, width=1.0)
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_expansion_persistence_events_v1(df)
    assert results[150].reason is VolatilityExpansionPersistenceReasonV1.NO_EVENT


def test_window_expiry_without_direction(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 170
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[148] = 0.70
    ranks[149] = 0.85
    ranks[150] = 0.90
    atr[149] = 0.010
    atr[150] = 0.012
    ranks[151:157] = 0.90
    atr[151:157] = 0.012
    df = _ohlc_from_close([100.0] * n, width=1.0)  # no channel break
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_expansion_persistence_events_v1(df)
    assert results[156].reason is VolatilityExpansionPersistenceReasonV1.PERSISTENCE_WINDOW_EXPIRED
    assert results[156].persistence_offset == 6
    assert all(r.persistence_offset != 7 for r in results)


def test_rearm_required_before_second_event(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 190
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    # First confirmation @150, entry @151
    ranks[148] = 0.70
    ranks[149] = 0.85
    ranks[150] = 0.90
    atr[149] = 0.010
    atr[150] = 0.012
    ranks[151] = 0.90
    atr[151] = 0.012
    # Keep percentile high so rearm does not clear; second confirmation pattern ignored
    ranks[152] = 0.90
    ranks[153] = 0.85
    ranks[154] = 0.90
    atr[153] = 0.012
    atr[154] = 0.014
    # Still high — awaiting rearm
    ranks[155:160] = 0.90
    # Rearm bar
    ranks[160] = 0.50
    # Fresh confirmation after rearm
    ranks[161] = 0.70
    ranks[162] = 0.85
    ranks[163] = 0.90
    atr[162] = 0.014
    atr[163] = 0.016

    df = _ohlc_from_close([100.0] * n, width=1.0)
    df.loc[df.index[151], "close"] = 110.0
    df.loc[df.index[151], "high"] = 111.0
    df.loc[df.index[151], "low"] = 109.0
    df.loc[df.index[164], "close"] = 130.0
    df.loc[df.index[164], "high"] = 131.0
    df.loc[df.index[164], "low"] = 129.0
    ranks[164] = 0.90
    atr[164] = 0.016
    _patch_vol(monkeypatch, df, ranks, atr=atr)

    results = generate_volatility_expansion_persistence_events_v1(df)
    assert results[151].event is VolatilityExpansionPersistenceEventV1.ENTRY_EVENT
    assert results[154].reason is VolatilityExpansionPersistenceReasonV1.AWAITING_REARM
    assert results[154].event is VolatilityExpansionPersistenceEventV1.NONE
    assert results[163].reason is VolatilityExpansionPersistenceReasonV1.CONFIRMATION_OBSERVED
    assert results[164].event is VolatilityExpansionPersistenceEventV1.ENTRY_EVENT


def test_short_entry_and_single_use(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 170
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[148] = 0.70
    ranks[149] = 0.85
    ranks[150] = 0.90
    atr[149] = 0.010
    atr[150] = 0.012
    ranks[151] = 0.90
    atr[151] = 0.012
    df = _ohlc_from_close([100.0] * n, width=1.0)
    df.loc[df.index[151], "close"] = 90.0
    df.loc[df.index[151], "high"] = 91.0
    df.loc[df.index[151], "low"] = 89.0
    # Would-be second break next bar — event already consumed
    df.loc[df.index[152], "close"] = 85.0
    ranks[152] = 0.90
    atr[152] = 0.012
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_expansion_persistence_events_v1(df)
    assert results[151].entry_side is StrategyEntrySideCarrierV1.SHORT
    assert results[152].event is VolatilityExpansionPersistenceEventV1.NONE


def test_deterministic_repeat(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 170
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[148] = 0.70
    ranks[149] = 0.85
    ranks[150] = 0.90
    atr[149] = 0.010
    atr[150] = 0.012
    ranks[151] = 0.90
    atr[151] = 0.012
    df = _ohlc_from_close([100.0] * n, width=1.0)
    df.loc[df.index[151], "close"] = 110.0
    df.loc[df.index[151], "high"] = 111.0
    df.loc[df.index[151], "low"] = 109.0
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    a = generate_volatility_expansion_persistence_events_v1(df)
    b = generate_volatility_expansion_persistence_events_v1(df)
    assert [r.event for r in a] == [r.event for r in b]
    assert [r.entry_side for r in a] == [r.entry_side for r in b]
    assert [r.reason for r in a] == [r.reason for r in b]


def test_no_lookahead_uses_only_prior_channel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert CHANNEL_LOOKBACK_COMPLETED_BARS_V1 == 20
    n = 170
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[148] = 0.70
    ranks[149] = 0.85
    ranks[150] = 0.90
    atr[149] = 0.010
    atr[150] = 0.012
    ranks[151] = 0.90
    atr[151] = 0.012
    df = _ohlc_from_close([100.0] * n, width=1.0)
    # Inflate current high on entry bar; channel must ignore it
    df.loc[df.index[151], "close"] = 110.0
    df.loc[df.index[151], "high"] = 500.0
    df.loc[df.index[151], "low"] = 109.0
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_expansion_persistence_events_v1(df)
    upper, _ = compute_prior_high_low_channel_bounds_v1(df["high"], df["low"], lookback=20)
    assert results[151].upper_channel == pytest.approx(float(upper.iloc[151]))
    assert results[151].upper_channel < 500.0
    assert classify_price_channel_break_v1(110.0, float(upper.iloc[151]), 99.0) is (
        PriceChannelBreakSideV1.LONG
    )


# ---------------------------------------------------------------------------
# Material difference vs VCB / baseline
# ---------------------------------------------------------------------------


def test_material_difference_from_vcb_constants() -> None:
    import src.research.volatility_compression_breakout_v1_strategy_v1 as vcb
    import src.research.volatility_expansion_persistence_v1_strategy_v1 as vep
    import src.research.volatility_compression_breakout_v1_vol_state_v1 as vcb_vol
    import src.research.volatility_expansion_persistence_v1_vol_state_v1 as vep_vol

    assert vep_vol.ATR_PERIOD_V1 == 14
    assert vcb_vol.ATR_PERIOD_V1 == 20
    assert vep.COMPRESSION_REGIME_NOT_REQUIRED_V1 is True
    assert not hasattr(vep, "COMPRESSION_PERCENTILE_MAX_V1")
    assert hasattr(vcb, "COMPRESSION_PERCENTILE_MAX_V1")
    assert vep.ENTRY_ON_CONFIRMATION_BAR_T_FORBIDDEN_V1 is True
    assert vep.EXPANSION_CONFIRMATION_THRESHOLD_V1 == 0.80
    assert vcb.EXPANSION_PERCENTILE_MIN_V1 == 0.75


def test_baseline_break_without_expansion_strategy_silent() -> None:
    closes = [100.0] * 25 + [130.0]
    df = _ohlc_from_close(closes, width=1.0)
    baseline = generate_unconditional_20_bar_price_channel_breakout_events_v1(df)
    strategy = generate_volatility_expansion_persistence_events_v1(df)
    last = len(df) - 1
    assert baseline[last].event == "ENTRY_EVENT"
    assert baseline[last].entry_side is StrategyEntrySideCarrierV1.LONG
    assert strategy[last].event is VolatilityExpansionPersistenceEventV1.NONE
    assert baseline[last].upper_channel == pytest.approx(strategy[last].upper_channel)


def test_baseline_id_and_exit_declarative_pnl_ref() -> None:
    assert BASELINE_ID_V1 == "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
    assert STRATEGY_IDENTITY_V1 == "VOLATILITY_EXPANSION_PERSISTENCE_V1"
    assert EXIT_PARAMS_DECLARATIVE_V1["exit_state_machine_implemented"] is False
    assert EXIT_PARAMS_DECLARATIVE_V1["second_pnl_truth_forbidden"] is True
    pnl_ref = EXIT_PARAMS_DECLARATIVE_V1["productive_exit_pnl_evaluator_ref"]
    assert (REPO / pnl_ref).is_file()


# ---------------------------------------------------------------------------
# Binding + negative scope + import safety
# ---------------------------------------------------------------------------


def test_implementation_binding_valid_and_measurement_unmutated() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["evaluation_authorized"] is False
    assert report["development_run_count"] == 0
    assert report["productive_pnl_evaluator_reused"] is True
    assert report["second_pnl_truth_created"] is False


def test_negative_scope_no_runner_eval_dataset_authority() -> None:
    binding = (
        REPO
        / "config/research/volatility_expansion_persistence_v1_strategy_implementation_binding_v1.json"
    )
    text = binding.read_text(encoding="utf-8")
    assert '"runner_present": false' in text
    assert '"evaluation_authorized": false' in text
    assert '"master_v2_mutation": false' in text
    assert "NO_DATASET_LOAD" in text
    assert "NO_SECOND_PNL_TRUTH" in text
    assert "NO_VOLATILITY_COMPRESSION_BREAKOUT_V1_RETRY" in text
    strategy_src = (
        REPO / "src/research/volatility_expansion_persistence_v1_strategy_v1.py"
    ).read_text(encoding="utf-8")
    assert "load_dataset" not in strategy_src
    assert "run_evaluate" not in strategy_src
    assert "__main__" not in strategy_src
    assert "holdout" not in strategy_src.lower()


def test_import_safe_no_side_effects() -> None:
    import src.research.volatility_expansion_persistence_v1_strategy_v1 as s
    import src.research.volatility_expansion_persistence_v1_vol_state_v1 as v
    import src.research.volatility_expansion_persistence_v1_strategy_implementation_binding_v1 as b

    assert s.STRATEGY_IDENTITY_V1 == "VOLATILITY_EXPANSION_PERSISTENCE_V1"
    assert v.ATR_PERIOD_V1 == 14
    assert b.REQUIRED_DIGEST.startswith("92e2117c")
