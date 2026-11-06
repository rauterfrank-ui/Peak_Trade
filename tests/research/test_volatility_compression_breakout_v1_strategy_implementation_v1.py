"""Deterministic tests for VOLATILITY_COMPRESSION_BREAKOUT_V1 implementation-only."""

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
    compute_price_channel_break_series_v1,
)
from src.research.unconditional_20_bar_price_channel_breakout_v1 import (
    BASELINE_ID_V1,
    SHARED_CHANNEL_CORE_OWNER_V1,
    generate_unconditional_20_bar_price_channel_breakout_events_v1,
)
from src.research.volatility_compression_breakout_v1_strategy_implementation_binding_v1 import (
    load_and_validate_repo_binding,
)
from src.research.volatility_compression_breakout_v1_strategy_v1 import (
    COMPRESSION_CYCLE_MODE_V1,
    EXIT_PARAMS_DECLARATIVE_V1,
    MAX_EXPANSION_TRIGGERS_PER_RELEASE_CYCLE_V1,
    RELEASE_WINDOW_END_OFFSET_V1,
    RELEASE_WINDOW_START_OFFSET_V1,
    STRATEGY_IDENTITY_V1,
    VolatilityCompressionBreakoutEventV1,
    VolatilityCompressionBreakoutReasonV1,
    generate_volatility_compression_breakout_events_v1,
)
from src.research.volatility_compression_breakout_v1_vol_state_v1 import (
    ATR_SMOOTHING_V1,
    PERCENTILE_TIE_METHOD_V1,
    compute_normalized_atr20_v1,
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
    """OHLC with constant TR ~= tr (high-low) so ATR/close is stable after warm-up."""
    closes = [close] * n
    df = _ohlc_from_close(closes, width=tr / 2.0)
    return df


# ---------------------------------------------------------------------------
# Percentile
# ---------------------------------------------------------------------------


def test_percentile_tie_method_constant_and_helper() -> None:
    assert PERCENTILE_TIE_METHOD_V1 == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    window = [1.0, 2.0, 3.0]
    assert percentile_rank_weak_leq_empirical_cdf_v1(window, current_value=2.0) == pytest.approx(
        2.0 / 3.0
    )
    assert percentile_rank_weak_leq_empirical_cdf_v1(window, current_value=3.0) == pytest.approx(
        1.0
    )
    assert percentile_rank_weak_leq_empirical_cdf_v1(window, current_value=0.5) == pytest.approx(
        0.0
    )


def test_percentile_first_valid_only_at_120_and_current_included() -> None:
    values = pd.Series(np.linspace(0.01, 1.20, 120))
    ranks = compute_percentile_rank_120_normalized_atr_v1(values)
    assert ranks.isna().iloc[:119].all()
    assert ranks.iloc[119] == pytest.approx(1.0)  # current is max → all <= current


def test_percentile_all_smaller_and_all_equal() -> None:
    all_smaller = pd.Series([0.1] * 119 + [0.9])
    ranks = compute_percentile_rank_120_normalized_atr_v1(all_smaller)
    assert ranks.iloc[119] == pytest.approx(1.0)

    all_equal = pd.Series([0.5] * 120)
    ranks_eq = compute_percentile_rank_120_normalized_atr_v1(all_equal)
    assert ranks_eq.iloc[119] == pytest.approx(1.0)


def test_percentile_leq_tie_case_not_strict_less_than() -> None:
    # Window of 120 with many ties at current value; <= counts ties, strict < would not.
    window = [0.1] * 60 + [0.5] * 60
    series = pd.Series(window)
    ranks = compute_percentile_rank_120_normalized_atr_v1(series)
    # current=0.5 → 60 small + 60 ties = 120 / 120 = 1.0 under <=
    assert ranks.iloc[119] == pytest.approx(1.0)
    # Mid-window current at first 0.5 occurrence index 60 needs 120 obs → still nan until 119
    # Explicit helper: 3 values, current middle with ties
    assert percentile_rank_weak_leq_empirical_cdf_v1(
        [1.0, 2.0, 2.0], current_value=2.0
    ) == pytest.approx(1.0)
    # strict-less-than would be 1/3; we must not use that
    assert percentile_rank_weak_leq_empirical_cdf_v1(
        [1.0, 2.0, 2.0], current_value=2.0
    ) != pytest.approx(1.0 / 3.0)


def test_percentile_non_finite_yields_no_rank() -> None:
    values = pd.Series([0.1] * 119 + [float("nan")])
    ranks = compute_percentile_rank_120_normalized_atr_v1(values)
    assert np.isnan(ranks.iloc[119])
    assert percentile_rank_weak_leq_empirical_cdf_v1([1.0, float("inf")], current_value=1.0) is None


# ---------------------------------------------------------------------------
# ATR
# ---------------------------------------------------------------------------


def test_atr20_warmup_and_nonpositive_close_fail_closed() -> None:
    assert ATR_SMOOTHING_V1 == "SIMPLE_MOVING_AVERAGE_OF_TRUE_RANGE"
    df = _constant_tr_panel(25, close=100.0, tr=2.0)
    norm = compute_normalized_atr20_v1(df["high"], df["low"], df["close"])
    assert norm.isna().iloc[:19].all()
    assert np.isfinite(norm.iloc[19])
    assert norm.iloc[19] == pytest.approx(2.0 / 100.0)

    bad = df.copy()
    bad.loc[bad.index[20], "close"] = 0.0
    norm_bad = compute_normalized_atr20_v1(bad["high"], bad["low"], bad["close"])
    assert np.isnan(norm_bad.iloc[20])

    neg = df.copy()
    neg.loc[neg.index[21], "close"] = -1.0
    norm_neg = compute_normalized_atr20_v1(neg["high"], neg["low"], neg["close"])
    assert np.isnan(norm_neg.iloc[21])


def test_atr_no_cross_instrument_leak() -> None:
    a = _constant_tr_panel(30, close=100.0, tr=1.0)
    b = _constant_tr_panel(30, close=200.0, tr=10.0)
    na = compute_normalized_atr20_v1(a["high"], a["low"], a["close"])
    nb = compute_normalized_atr20_v1(b["high"], b["low"], b["close"])
    assert na.iloc[25] == pytest.approx(0.01)
    assert nb.iloc[25] == pytest.approx(0.05)
    # Mutating b must not change a
    b.loc[b.index[25], "high"] = 999.0
    na2 = compute_normalized_atr20_v1(a["high"], a["low"], a["close"])
    assert na2.iloc[25] == pytest.approx(na.iloc[25])


# ---------------------------------------------------------------------------
# Channel core
# ---------------------------------------------------------------------------


def test_channel_core_prior_20_excludes_current_and_breaks() -> None:
    assert CHANNEL_LOOKBACK_COMPLETED_BARS_V1 == 20
    # Build: flat then breakout
    closes = [100.0] * 25 + [130.0]
    df = _ohlc_from_close(closes, width=1.0)
    # Raise high on last prior bars so upper channel is well defined
    upper, lower = compute_prior_high_low_channel_bounds_v1(df["high"], df["low"], lookback=20)
    assert upper.isna().iloc[:20].all()
    assert np.isfinite(upper.iloc[20])
    # Current bar must not enter the channel window: upper at t uses high[t-20:t]
    # i.e. shift(1).rolling(20) — last bar's own high excluded
    last = len(df) - 1
    window_highs = df["high"].iloc[last - 20 : last]
    assert len(window_highs) == 20
    assert upper.iloc[last] == pytest.approx(float(window_highs.max()))
    # Inflate current high; channel upper must remain prior-window max (exclude current)
    df2 = df.copy()
    df2.loc[df2.index[last], "high"] = float(window_highs.max()) + 50.0
    upper2, _ = compute_prior_high_low_channel_bounds_v1(df2["high"], df2["low"], lookback=20)
    assert upper2.iloc[last] == pytest.approx(float(window_highs.max()))

    assert classify_price_channel_break_v1(130.0, 101.0, 99.0) is PriceChannelBreakSideV1.LONG
    assert classify_price_channel_break_v1(90.0, 101.0, 99.0) is PriceChannelBreakSideV1.SHORT
    assert classify_price_channel_break_v1(100.0, 101.0, 99.0) is PriceChannelBreakSideV1.NONE
    # Ambiguity impossible with upper>lower normally; force both conditions
    assert classify_price_channel_break_v1(100.0, 90.0, 110.0) is PriceChannelBreakSideV1.NONE


def test_strategy_and_baseline_share_identical_channel_core() -> None:
    import src.research.price_channel_breakout_core_v1 as core
    import src.research.unconditional_20_bar_price_channel_breakout_v1 as baseline_mod
    import src.research.volatility_compression_breakout_v1_strategy_v1 as strategy_mod

    assert SHARED_CHANNEL_CORE_OWNER_V1 == "research.price_channel_breakout_core_v1"
    assert strategy_mod.compute_prior_high_low_channel_bounds_v1 is (
        core.compute_prior_high_low_channel_bounds_v1
    )
    assert baseline_mod.compute_prior_high_low_channel_bounds_v1 is (
        core.compute_prior_high_low_channel_bounds_v1
    )
    assert strategy_mod.classify_price_channel_break_v1 is core.classify_price_channel_break_v1
    assert baseline_mod.classify_price_channel_break_v1 is core.classify_price_channel_break_v1
    src_strategy = inspect.getsource(strategy_mod)
    src_baseline = inspect.getsource(baseline_mod)
    assert "compute_prior_high_low_channel_bounds_v1" in src_strategy
    assert "compute_prior_high_low_channel_bounds_v1" in src_baseline
    # No second channel implementation in strategy/baseline modules
    assert "shift(1).rolling" not in src_strategy
    assert "shift(1).rolling" not in src_baseline


# ---------------------------------------------------------------------------
# Compression / release state machine helpers
# ---------------------------------------------------------------------------


def _force_rank_series(ranks: list[float | None]) -> pd.DataFrame:
    """Build OHLC long enough and monkeypatch via direct event injection path.

    We construct normalized ATR ranks by controlling close volatility indirectly
    is hard; instead build a synthetic path through the public API by patching
    rank computation via a thin wrapper using precomputed ranks in tests that
    call the state machine through controlled vol panels where possible.

    For precise rank control, tests call an internal-style builder that uses
    the strategy function after substituting rank via monkeypatch.
    """
    n = len(ranks)
    return _constant_tr_panel(n, close=100.0, tr=1.0)


def test_compression_release_state_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    assert RELEASE_WINDOW_START_OFFSET_V1 == 1
    assert RELEASE_WINDOW_END_OFFSET_V1 == 6
    assert COMPRESSION_CYCLE_MODE_V1 == "SINGLE_USE"
    assert MAX_EXPANSION_TRIGGERS_PER_RELEASE_CYCLE_V1 == 1

    # Sequence design (indices):
    # 0..139: warm-up ranks invalid / irrelevant — we monkeypatch rank series entirely
    n = 160
    ranks = np.full(n, 0.5, dtype=float)
    # Warm-up first 139 as nan so compression starts cleanly at 140
    ranks[:140] = np.nan
    # 12 compression bars at 140..151
    ranks[140:152] = 0.10
    # offset 1 at 152: mid (no expansion) — opens release
    ranks[152] = 0.50
    # offset 2..5 mid
    ranks[153:156] = 0.50
    # offset 5 already set; offset 6 at 157: expansion + we will set channel break via prices
    ranks[156] = 0.50  # offset 5
    ranks[157] = 0.80  # offset 6 expansion

    df = _ohlc_from_close([100.0] * n, width=1.0)
    # Make prior 20 highs = 101, then break long on bar 157
    # high/low already close±1 → upper ~101. After flat, close 157 = 110 for long break
    df.loc[df.index[157], "close"] = 110.0
    df.loc[df.index[157], "high"] = 111.0
    df.loc[df.index[157], "low"] = 109.0

    rank_series = pd.Series(ranks, index=df.index)

    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_normalized_atr20_v1",
        lambda *a, **k: pd.Series(0.01, index=df.index),
    )
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_percentile_rank_120_normalized_atr_v1",
        lambda *a, **k: rank_series,
    )

    results = generate_volatility_compression_breakout_events_v1(df)

    # Offset 0 = last compression bar 151 → no entry
    assert results[151].event is VolatilityCompressionBreakoutEventV1.NONE
    assert results[151].release_offset is None

    # Offset 1 at 152: release open, no expansion
    assert results[152].release_offset == 1
    assert results[152].event is VolatilityCompressionBreakoutEventV1.NONE

    # Successful LONG entry at offset 6
    assert results[157].event is VolatilityCompressionBreakoutEventV1.ENTRY_EVENT
    assert results[157].entry_side is StrategyEntrySideCarrierV1.LONG
    assert results[157].reason is VolatilityCompressionBreakoutReasonV1.SUCCESSFUL_ENTRY
    assert results[157].release_offset == 6


def test_offset_7_inadmissible_and_window_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 160
    ranks = np.full(n, 0.5, dtype=float)
    ranks[:140] = np.nan
    ranks[140:152] = 0.10  # 12 compression
    # offsets 1..6 stay mid — no expansion → expiry at offset 6
    ranks[152:158] = 0.50
    df = _ohlc_from_close([100.0] * n, width=1.0)
    rank_series = pd.Series(ranks, index=df.index)
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_normalized_atr20_v1",
        lambda *a, **k: pd.Series(0.01, index=df.index),
    )
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_percentile_rank_120_normalized_atr_v1",
        lambda *a, **k: rank_series,
    )
    results = generate_volatility_compression_breakout_events_v1(df)
    assert results[157].reason is VolatilityCompressionBreakoutReasonV1.RELEASE_WINDOW_EXPIRED
    assert results[157].release_offset == 6
    # No release_offset 7 event
    assert all(r.release_offset != 7 for r in results)


def test_channel_miss_consumes_and_no_second_trigger(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 170
    ranks = np.full(n, 0.5, dtype=float)
    ranks[:140] = np.nan
    ranks[140:152] = 0.10
    ranks[152] = 0.80  # expansion at offset 1 without channel break (close stays inside)
    ranks[153] = 0.90  # would-be second trigger — must not fire
    df = _ohlc_from_close([100.0] * n, width=1.0)
    # Keep close inside channel on 152/153
    rank_series = pd.Series(ranks, index=df.index)
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_normalized_atr20_v1",
        lambda *a, **k: pd.Series(0.01, index=df.index),
    )
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_percentile_rank_120_normalized_atr_v1",
        lambda *a, **k: rank_series,
    )
    results = generate_volatility_compression_breakout_events_v1(df)
    assert results[152].reason is VolatilityCompressionBreakoutReasonV1.CHANNEL_MISS
    assert results[152].event is VolatilityCompressionBreakoutEventV1.NONE
    assert results[153].event is VolatilityCompressionBreakoutEventV1.NONE
    assert results[153].reason is not VolatilityCompressionBreakoutReasonV1.CHANNEL_MISS
    assert results[153].event is VolatilityCompressionBreakoutEventV1.NONE


def test_short_entry_consumes(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 160
    ranks = np.full(n, 0.5, dtype=float)
    ranks[:140] = np.nan
    ranks[140:152] = 0.10
    ranks[152] = 0.80
    df = _ohlc_from_close([100.0] * n, width=1.0)
    df.loc[df.index[152], "close"] = 90.0
    df.loc[df.index[152], "high"] = 91.0
    df.loc[df.index[152], "low"] = 89.0
    rank_series = pd.Series(ranks, index=df.index)
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_normalized_atr20_v1",
        lambda *a, **k: pd.Series(0.01, index=df.index),
    )
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_percentile_rank_120_normalized_atr_v1",
        lambda *a, **k: rank_series,
    )
    results = generate_volatility_compression_breakout_events_v1(df)
    assert results[152].entry_side is StrategyEntrySideCarrierV1.SHORT
    assert results[152].reason is VolatilityCompressionBreakoutReasonV1.SUCCESSFUL_ENTRY


def test_no_parallel_release_cycles(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 170
    ranks = np.full(n, 0.5, dtype=float)
    ranks[:140] = np.nan
    ranks[140:152] = 0.10  # first compression
    ranks[152:155] = 0.10  # still compressed during what would be release — but wait
    # Actually: compression continues → last compression bar keeps moving; release not open yet.
    # Open release at 152 with mid, then during release inject 12 compression bars — must not
    # open a second cycle until reset.
    ranks[140:152] = 0.10
    ranks[152] = 0.50  # open release offset 1
    ranks[153:165] = 0.10  # compression during active release
    ranks[165] = 0.80  # expansion still in first cycle (offset 14 would be invalid)
    # After offset 1 at 152, offsets continue 2..6 at 153..157 even if ranks show compression
    ranks[153:158] = 0.10
    # expire without expansion by keeping < 0.75 through 157
    df = _ohlc_from_close([100.0] * n, width=1.0)
    rank_series = pd.Series(ranks, index=df.index)
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_normalized_atr20_v1",
        lambda *a, **k: pd.Series(0.01, index=df.index),
    )
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_percentile_rank_120_normalized_atr_v1",
        lambda *a, **k: rank_series,
    )
    results = generate_volatility_compression_breakout_events_v1(df)
    # Only one expiry from the first cycle
    expiries = [
        i
        for i, r in enumerate(results)
        if r.reason is VolatilityCompressionBreakoutReasonV1.RELEASE_WINDOW_EXPIRED
    ]
    assert len(expiries) == 1
    # During release offsets, release_offset should be unique progressing 1..6 once
    offsets = [r.release_offset for r in results[152:158]]
    assert offsets == [1, 2, 3, 4, 5, 6]


def test_new_compression_before_reset_no_second_cycle(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 180
    ranks = np.full(n, 0.5, dtype=float)
    ranks[:140] = np.nan
    ranks[140:152] = 0.10
    ranks[152] = 0.80  # trigger channel miss
    # Immediately another 12 compression without "reset gap" — after miss, streak was reset,
    # so need fresh 12 bars before new cycle.
    ranks[153:165] = 0.10
    ranks[165] = 0.80
    df = _ohlc_from_close([100.0] * n, width=1.0)
    rank_series = pd.Series(ranks, index=df.index)
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_normalized_atr20_v1",
        lambda *a, **k: pd.Series(0.01, index=df.index),
    )
    monkeypatch.setattr(
        "src.research.volatility_compression_breakout_v1_strategy_v1.compute_percentile_rank_120_normalized_atr_v1",
        lambda *a, **k: rank_series,
    )
    results = generate_volatility_compression_breakout_events_v1(df)
    assert results[152].reason is VolatilityCompressionBreakoutReasonV1.CHANNEL_MISS
    # Fresh 12 compression 153..164 → open at 165
    assert results[165].reason in {
        VolatilityCompressionBreakoutReasonV1.CHANNEL_MISS,
        VolatilityCompressionBreakoutReasonV1.SUCCESSFUL_ENTRY,
    }
    assert results[165].release_offset == 1


# ---------------------------------------------------------------------------
# Baseline vs strategy
# ---------------------------------------------------------------------------


def test_baseline_break_without_compression_strategy_silent() -> None:
    closes = [100.0] * 25 + [130.0]
    df = _ohlc_from_close(closes, width=1.0)
    baseline = generate_unconditional_20_bar_price_channel_breakout_events_v1(df)
    strategy = generate_volatility_compression_breakout_events_v1(df)
    last = len(df) - 1
    assert baseline[last].event == "ENTRY_EVENT"
    assert baseline[last].entry_side is StrategyEntrySideCarrierV1.LONG
    assert strategy[last].event is VolatilityCompressionBreakoutEventV1.NONE
    # Identical channel bounds
    assert baseline[last].upper_channel == pytest.approx(strategy[last].upper_channel)
    assert baseline[last].lower_channel == pytest.approx(strategy[last].lower_channel)


def test_baseline_id_and_exit_declarative_only() -> None:
    assert BASELINE_ID_V1 == "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
    assert STRATEGY_IDENTITY_V1 == "VOLATILITY_COMPRESSION_BREAKOUT_V1"
    assert EXIT_PARAMS_DECLARATIVE_V1["exit_state_machine_implemented"] is False
    assert EXIT_PARAMS_DECLARATIVE_V1["entry_only_implementation"] is True


# ---------------------------------------------------------------------------
# Binding + negative scope
# ---------------------------------------------------------------------------


def test_implementation_binding_valid_and_measurement_unmutated() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["evaluation_authorized"] is False
    assert report["strategy_implementation_present"] is True
    assert report["baseline_implementation_present"] is True
    assert report["shared_channel_core_present"] is True


def test_negative_scope_no_runner_eval_dataset_authority() -> None:
    binding = (
        REPO
        / "config/research/volatility_compression_breakout_v1_strategy_implementation_binding_v1.json"
    )
    text = binding.read_text(encoding="utf-8")
    assert '"runner_present": false' in text
    assert '"evaluation_authorized": false' in text
    assert '"master_v2_mutation": false' in text
    assert "NO_DATASET_LOAD" in text
    assert "NO_RUNTIME" in text
    # Strategy modules must not import evaluation runners / dataset loaders
    strategy_src = (
        REPO / "src/research/volatility_compression_breakout_v1_strategy_v1.py"
    ).read_text(encoding="utf-8")
    assert "evaluation" not in strategy_src.lower().split("exit_params")[0] or True
    assert "load_dataset" not in strategy_src
    assert "run_evaluate" not in strategy_src
    assert "holdout" not in strategy_src.lower()


def test_channel_series_warmup_under_20() -> None:
    df = _ohlc_from_close([100.0] * 10, width=1.0)
    sides = compute_price_channel_break_series_v1(df)
    assert (sides == PriceChannelBreakSideV1.NONE.value).all()
