"""Deterministic tests for VOLATILITY_DECAY_BREAKOUT_V1 implementation-only."""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.research.price_channel_breakout_core_v1 import (
    CHANNEL_LOOKBACK_COMPLETED_BARS_V1,
)
from src.research.unconditional_20_bar_price_channel_breakout_v1 import (
    SHARED_CHANNEL_CORE_OWNER_V1,
)
from src.research.volatility_decay_breakout_v1_strategy_implementation_binding_v1 import (
    load_and_validate_repo_binding,
)
from src.research.volatility_decay_breakout_v1_strategy_v1 import (
    COMPRESSION_REGIME_NOT_REQUIRED_V1,
    DECAY_CONFIRMATION_THRESHOLD_EXCLUSIVE_MAX_V1,
    DECAY_EVENT_CONSUMPTION_V1,
    DECAY_WINDOW_END_OFFSET_V1,
    DECAY_WINDOW_START_OFFSET_V1,
    ENTRY_ON_CONFIRMATION_BAR_T_FORBIDDEN_V1,
    EXIT_PARAMS_DECLARATIVE_V1,
    EXPANSION_PERSISTENCE_NOT_REQUIRED_V1,
    HIGH_VOL_PRIOR_THRESHOLD_INCLUSIVE_MIN_V1,
    MAX_ENTRIES_PER_DECAY_EVENT_V1,
    REARM_THRESHOLD_INCLUSIVE_MIN_V1,
    STRATEGY_IDENTITY_V1,
    VolatilityDecayBreakoutEventV1,
    VolatilityDecayBreakoutReasonV1,
    generate_volatility_decay_breakout_events_v1,
)
from src.research.volatility_decay_breakout_v1_vol_state_v1 import (
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
        "src.research.volatility_decay_breakout_v1_strategy_v1.compute_normalized_atr14_v1",
        lambda *a, **k: atr_series,
    )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_v1_strategy_v1."
        "compute_percentile_rank_120_normalized_atr_v1",
        lambda *a, **k: rank_series,
    )


def test_parameter_binding_matches_preregistration() -> None:
    assert ATR_PERIOD_V1 == 14
    assert PERCENTILE_TIE_METHOD_V1 == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert ATR_SMOOTHING_V1 == "SIMPLE_MOVING_AVERAGE_OF_TRUE_RANGE"
    assert HIGH_VOL_PRIOR_THRESHOLD_INCLUSIVE_MIN_V1 == 0.70
    assert DECAY_CONFIRMATION_THRESHOLD_EXCLUSIVE_MAX_V1 == 0.40
    assert COMPRESSION_REGIME_NOT_REQUIRED_V1 is True
    assert EXPANSION_PERSISTENCE_NOT_REQUIRED_V1 is True
    assert ENTRY_ON_CONFIRMATION_BAR_T_FORBIDDEN_V1 is True
    assert DECAY_EVENT_CONSUMPTION_V1 == "SINGLE_USE"
    assert MAX_ENTRIES_PER_DECAY_EVENT_V1 == 1
    assert DECAY_WINDOW_START_OFFSET_V1 == 1
    assert DECAY_WINDOW_END_OFFSET_V1 == 8
    assert REARM_THRESHOLD_INCLUSIVE_MIN_V1 == 0.70
    assert EXIT_PARAMS_DECLARATIVE_V1["entry_only_implementation"] is True
    assert EXIT_PARAMS_DECLARATIVE_V1["exit_state_machine_implemented"] is False
    assert EXIT_PARAMS_DECLARATIVE_V1["second_pnl_truth_forbidden"] is True
    assert STRATEGY_IDENTITY_V1 == "VOLATILITY_DECAY_BREAKOUT_V1"


def test_percentile_and_atr14_warmup() -> None:
    window = [1.0, 2.0, 3.0]
    assert percentile_rank_weak_leq_empirical_cdf_v1(window, current_value=2.0) == pytest.approx(
        2.0 / 3.0
    )
    values = pd.Series(np.linspace(0.01, 1.20, 120))
    ranks = compute_percentile_rank_120_normalized_atr_v1(values)
    assert ranks.isna().iloc[:119].all()
    assert ranks.iloc[119] == pytest.approx(1.0)
    df = _constant_tr_panel(25, close=100.0, tr=2.0)
    norm = compute_normalized_atr14_v1(df["high"], df["low"], df["close"])
    assert norm.isna().iloc[:13].all()
    assert np.isfinite(norm.iloc[13])
    bad = df.copy()
    bad.loc[bad.index[14], "close"] = 0.0
    assert np.isnan(compute_normalized_atr14_v1(bad["high"], bad["low"], bad["close"]).iloc[14])


def test_missing_columns_fail_closed() -> None:
    df = pd.DataFrame({"open": [1.0], "close": [1.0]})
    with pytest.raises(ValueError, match="missing_column"):
        generate_volatility_decay_breakout_events_v1(df)


def test_nan_inf_warmup(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 140
    ranks = np.full(n, np.nan)
    atr = np.full(n, np.nan)
    df = _ohlc_from_close([100.0] * n)
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_decay_breakout_events_v1(df)
    assert all(r.reason is VolatilityDecayBreakoutReasonV1.WARMUP for r in results)
    assert all(r.event is VolatilityDecayBreakoutEventV1.NONE for r in results)


def test_confirmation_and_entry_not_on_t(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 170
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    # Decay confirmation at bar 150: t-1 >= 0.70, t < 0.40, atr falling
    ranks[149] = 0.75
    ranks[150] = 0.30
    atr[149] = 0.012
    atr[150] = 0.010
    ranks[151:159] = 0.30
    atr[151:159] = 0.010
    df = _ohlc_from_close([100.0] * n, width=1.0)
    df.loc[df.index[152], "close"] = 110.0
    df.loc[df.index[152], "high"] = 111.0
    df.loc[df.index[152], "low"] = 109.0
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_decay_breakout_events_v1(df)
    assert results[150].reason is VolatilityDecayBreakoutReasonV1.CONFIRMATION_OBSERVED
    assert results[150].event is VolatilityDecayBreakoutEventV1.NONE
    assert results[151].decay_offset == 1
    assert results[151].event is VolatilityDecayBreakoutEventV1.NONE
    assert results[152].event is VolatilityDecayBreakoutEventV1.ENTRY_EVENT
    assert results[152].entry_side is StrategyEntrySideCarrierV1.LONG
    assert results[152].decay_offset == 2
    assert results[152].confirmation_bar_index == 150


def test_no_confirmation_without_high_vol_prior(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 160
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[149] = 0.60  # below 0.70
    ranks[150] = 0.30
    atr[149] = 0.012
    atr[150] = 0.010
    df = _ohlc_from_close([100.0] * n, width=1.0)
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_decay_breakout_events_v1(df)
    assert results[150].reason is VolatilityDecayBreakoutReasonV1.NO_EVENT


def test_atr_must_fall_on_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 160
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[149] = 0.75
    ranks[150] = 0.30
    atr[149] = 0.010
    atr[150] = 0.012  # not falling
    df = _ohlc_from_close([100.0] * n, width=1.0)
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_decay_breakout_events_v1(df)
    assert results[150].reason is VolatilityDecayBreakoutReasonV1.NO_EVENT


def test_window_expiry_without_direction(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 170
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[149] = 0.75
    ranks[150] = 0.30
    atr[149] = 0.012
    atr[150] = 0.010
    ranks[151:159] = 0.30
    atr[151:159] = 0.010
    df = _ohlc_from_close([100.0] * n, width=1.0)  # no channel break
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_decay_breakout_events_v1(df)
    assert results[158].reason is VolatilityDecayBreakoutReasonV1.DECAY_WINDOW_EXPIRED
    assert results[158].decay_offset == 8
    assert all(r.decay_offset != 9 for r in results)


def test_short_entry_and_single_use(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 170
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[149] = 0.75
    ranks[150] = 0.30
    atr[149] = 0.012
    atr[150] = 0.010
    ranks[151] = 0.30
    atr[151] = 0.010
    df = _ohlc_from_close([100.0] * n, width=1.0)
    df.loc[df.index[151], "close"] = 80.0
    df.loc[df.index[151], "high"] = 81.0
    df.loc[df.index[151], "low"] = 79.0
    # Ambiguous same-bar long+short impossible; second break later ignored (single-use)
    df.loc[df.index[152], "close"] = 120.0
    ranks[152] = 0.30
    atr[152] = 0.010
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_decay_breakout_events_v1(df)
    assert results[151].event is VolatilityDecayBreakoutEventV1.ENTRY_EVENT
    assert results[151].entry_side is StrategyEntrySideCarrierV1.SHORT
    assert results[152].event is VolatilityDecayBreakoutEventV1.NONE


def test_rearm_requires_high_vol_before_second_event(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 200
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[149] = 0.75
    ranks[150] = 0.30
    atr[149] = 0.012
    atr[150] = 0.010
    ranks[151] = 0.30
    atr[151] = 0.010
    # Stay below rearm threshold — no second confirmation possible without >=0.70
    ranks[152:160] = 0.30
    atr[152:160] = 0.010
    # Rearm bar (>=0.70), then fresh decay confirmation
    ranks[160] = 0.75
    atr[160] = 0.012
    ranks[161] = 0.25
    atr[161] = 0.008
    ranks[162] = 0.25
    atr[162] = 0.008

    df = _ohlc_from_close([100.0] * n, width=1.0)
    df.loc[df.index[151], "close"] = 110.0
    df.loc[df.index[151], "high"] = 111.0
    df.loc[df.index[151], "low"] = 109.0
    df.loc[df.index[162], "close"] = 130.0
    df.loc[df.index[162], "high"] = 131.0
    df.loc[df.index[162], "low"] = 129.0
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    results = generate_volatility_decay_breakout_events_v1(df)
    assert results[151].event is VolatilityDecayBreakoutEventV1.ENTRY_EVENT
    assert results[155].reason is VolatilityDecayBreakoutReasonV1.AWAITING_REARM
    assert all(
        r.event is VolatilityDecayBreakoutEventV1.NONE
        and r.reason is VolatilityDecayBreakoutReasonV1.AWAITING_REARM
        for r in results[152:160]
    )
    assert results[161].reason is VolatilityDecayBreakoutReasonV1.CONFIRMATION_OBSERVED
    assert results[162].event is VolatilityDecayBreakoutEventV1.ENTRY_EVENT


def test_deterministic_repeat(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 160
    ranks = np.full(n, 0.50, dtype=float)
    atr = np.full(n, 0.01, dtype=float)
    ranks[149] = 0.75
    ranks[150] = 0.30
    atr[149] = 0.012
    atr[150] = 0.010
    ranks[151] = 0.30
    df = _ohlc_from_close([100.0] * n, width=1.0)
    df.loc[df.index[151], "close"] = 110.0
    _patch_vol(monkeypatch, df, ranks, atr=atr)
    a = generate_volatility_decay_breakout_events_v1(df)
    b = generate_volatility_decay_breakout_events_v1(df)
    assert [(r.event, r.entry_side, r.reason, r.decay_offset) for r in a] == [
        (r.event, r.entry_side, r.reason, r.decay_offset) for r in b
    ]


def test_shared_channel_core_and_no_lookahead_helpers() -> None:
    import src.research.price_channel_breakout_core_v1 as core
    import src.research.unconditional_20_bar_price_channel_breakout_v1 as baseline_mod
    import src.research.volatility_decay_breakout_v1_strategy_v1 as strategy_mod

    assert SHARED_CHANNEL_CORE_OWNER_V1 == "research.price_channel_breakout_core_v1"
    assert strategy_mod.compute_prior_high_low_channel_bounds_v1 is (
        core.compute_prior_high_low_channel_bounds_v1
    )
    assert baseline_mod.compute_prior_high_low_channel_bounds_v1 is (
        core.compute_prior_high_low_channel_bounds_v1
    )
    assert strategy_mod.CHANNEL_LOOKBACK_BARS_V1 == CHANNEL_LOOKBACK_COMPLETED_BARS_V1
    src_strategy = inspect.getsource(strategy_mod)
    assert "shift(-1)" not in src_strategy
    assert "bfill" not in src_strategy


def test_import_safe_no_io_network() -> None:
    import src.research.volatility_decay_breakout_v1_strategy_v1 as s
    import src.research.volatility_decay_breakout_v1_vol_state_v1 as v
    import src.research.volatility_decay_breakout_v1_strategy_implementation_binding_v1 as b

    assert s.STRATEGY_IDENTITY_V1 == "VOLATILITY_DECAY_BREAKOUT_V1"
    assert v.ATR_PERIOD_V1 == 14
    assert "evaluate" not in b.__file__


def test_implementation_binding_and_owner_map() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["evaluation_authorized"] is False
    assert report["productive_pnl_evaluator_reused"] is True
    assert report["second_pnl_truth_created"] is False
    assert report["development_run_count"] == 1
    owners = __import__("json").loads(
        (
            REPO
            / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
        ).read_text(encoding="utf-8")
    )["allowed_optimization_surfaces"]
    assert "VOLATILITY_DECAY_BREAKOUT_V1_STRATEGY_IMPLEMENTATION_ONLY_V1" in owners
    gov = REPO / "docs/governance/VOLATILITY_DECAY_BREAKOUT_V1_STRATEGY_IMPLEMENTATION_ONLY_V1.md"
    assert gov.is_file()
    assert (
        "DOCS_TOKEN_VOLATILITY_DECAY_BREAKOUT_V1_STRATEGY_IMPLEMENTATION_ONLY_V1"
        in gov.read_text(encoding="utf-8")
    )


def test_backlog_marks_implementation_present() -> None:
    backlog = __import__("json").loads(
        (REPO / "config/research/volatility_regime_hypothesis_backlog_v1.json").read_text(
            encoding="utf-8"
        )
    )
    terminals = {t["strategy_identity"]: t for t in backlog["terminal_hypotheses"]}
    hyp = terminals["VOLATILITY_DECAY_BREAKOUT_V1"]
    assert hyp["implementation_present"] is True
    assert hyp["run_slot_consumed"] is True
    assert hyp["development_run_count"] == 1
    assert hyp["status"] == "TERMINAL_FAIL"
