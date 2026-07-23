"""Unit/contract tests for CS intrabar CLV pressure continuation v1 score/selection."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_score_v1 import (
    DEFAULT_LOOKBACK_N,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEFAULT_SIGNAL_LAG_BARS,
    POLARITY,
    SCORE_FORMULA_VERSION,
    VOL_NORMALIZATION,
    compute_bar_clv_v1,
    compute_instrument_score_v1,
    compute_mean_clv_over_lookback_v1,
    is_eligible_universe_instrument_v1,
    rank_scores_deterministic_v1,
    validate_lookback_n,
)
from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_selection_v1 import (
    DIRECTIONAL_FORM,
    SELECTION_MODE,
    TIE_BREAK_POLICY,
    RankIntentSideV1,
    resolve_symmetric_top1_sign_v1,
    select_single_top1_rank_intent_v1,
)
from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_strategy_implementation_binding_v1 import (
    REQUIRED_DIGEST,
    load_and_validate_repo_binding,
)

REPO = Path(__file__).resolve().parents[2]
CSRHR_BACKLOG = (
    REPO
    / "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)
PROGRAM = (
    REPO
    / "config/research/cross_sectional_intrabar_close_location_pressure_continuation_research_program_v1.json"
)
CONTRACT = (
    REPO
    / "config/research/cross_sectional_intrabar_close_location_pressure_continuation_v1_preregistered_economic_hypothesis_measurement_contract_v1.json"
)
BACKLOG = (
    REPO
    / "config/research/cross_sectional_intrabar_close_location_pressure_continuation_hypothesis_backlog_v1.json"
)


def _ohlc_close_near_high(n: int = 80, *, start: float = 100.0) -> dict[str, tuple[float, ...]]:
    """Bars that close near the high → CLV near +1."""
    highs = []
    lows = []
    closes = []
    px = start
    for _ in range(n):
        low = px * 0.99
        high = px * 1.01
        close = high  # at high → CLV = +1
        highs.append(high)
        lows.append(low)
        closes.append(close)
        px = close
    return {"high": tuple(highs), "low": tuple(lows), "close": tuple(closes)}


def _ohlc_close_near_low(n: int = 80, *, start: float = 100.0) -> dict[str, tuple[float, ...]]:
    """Bars that close near the low → CLV near -1."""
    highs = []
    lows = []
    closes = []
    px = start
    for _ in range(n):
        low = px * 0.99
        high = px * 1.01
        close = low  # at low → CLV = -1
        highs.append(high)
        lows.append(low)
        closes.append(close)
        px = close
    return {"high": tuple(highs), "low": tuple(lows), "close": tuple(closes)}


def _ohlc_mid(n: int = 80, *, start: float = 100.0) -> dict[str, tuple[float, ...]]:
    """Bars that close at mid → CLV ~ 0 → ineligible after mean."""
    highs = []
    lows = []
    closes = []
    px = start
    for _ in range(n):
        low = px * 0.99
        high = px * 1.01
        close = (high + low) / 2.0
        highs.append(high)
        lows.append(low)
        closes.append(close)
        px = close
    return {"high": tuple(highs), "low": tuple(lows), "close": tuple(closes)}


def _ohlc_zero_range(n: int = 80, *, start: float = 100.0) -> dict[str, tuple[float, ...]]:
    flat = tuple(start for _ in range(n))
    return {"high": flat, "low": flat, "close": flat}


def test_score_formula_and_frozen_parameters() -> None:
    assert SCORE_FORMULA_VERSION == "mean_intrabar_close_location_value_fixed_lookback_v1"
    assert POLARITY == "INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION"
    assert VOL_NORMALIZATION is False
    assert DEFAULT_LOOKBACK_N == 36
    assert DEFAULT_REBALANCE_INTERVAL_BARS == 6
    assert DEFAULT_SIGNAL_LAG_BARS == 1
    assert SELECTION_MODE == "single_top1_by_score_desc"
    assert TIE_BREAK_POLICY == "score_desc_then_instrument_id_asc"
    assert DIRECTIONAL_FORM == "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION"


def test_bar_clv_formula_and_zero_range() -> None:
    assert compute_bar_clv_v1(high=110.0, low=100.0, close=110.0) == pytest.approx(1.0)
    assert compute_bar_clv_v1(high=110.0, low=100.0, close=100.0) == pytest.approx(-1.0)
    assert compute_bar_clv_v1(high=110.0, low=100.0, close=105.0) == pytest.approx(0.0)
    assert compute_bar_clv_v1(high=100.0, low=100.0, close=100.0) == pytest.approx(0.0)
    assert compute_bar_clv_v1(high=float("nan"), low=100.0, close=105.0) is None


def test_mean_clv_near_high_positive() -> None:
    ohlc = _ohlc_close_near_high()
    mean = compute_mean_clv_over_lookback_v1(
        ohlc["high"],
        ohlc["low"],
        ohlc["close"],
        lookback_n=36,
        signal_lag_bars=1,
        epoch_index=60,
    )
    assert mean is not None
    assert mean > 0.9


def test_universe_binding_non_bitcoin_perpetual_usdt() -> None:
    assert is_eligible_universe_instrument_v1("okx:linear_perpetual:ETH-USDT") is True
    assert is_eligible_universe_instrument_v1("okx:linear_perpetual:BTC-USDT") is False
    assert is_eligible_universe_instrument_v1("okx:spot:ETH-USDT") is False
    assert is_eligible_universe_instrument_v1("okx:linear_perpetual:ETH-USD") is False
    ohlc = _ohlc_close_near_high()
    assert (
        compute_instrument_score_v1(
            "okx:linear_perpetual:BTC-USDT",
            ohlc["high"],
            ohlc["low"],
            ohlc["close"],
            lookback_n=36,
            epoch_index=60,
        )
        is None
    )


def test_pit_safety_insufficient_history_and_lookahead_window() -> None:
    ohlc = _ohlc_close_near_high(n=30)
    assert (
        compute_mean_clv_over_lookback_v1(
            ohlc["high"],
            ohlc["low"],
            ohlc["close"],
            lookback_n=36,
            signal_lag_bars=1,
            epoch_index=29,
        )
        is None
    )
    long = _ohlc_close_near_high(n=80)
    epoch = 60
    lag = 1
    mean1 = compute_mean_clv_over_lookback_v1(
        long["high"],
        long["low"],
        long["close"],
        lookback_n=36,
        signal_lag_bars=lag,
        epoch_index=epoch,
    )
    assert mean1 is not None
    mutated_high = list(long["high"])
    mutated_high[epoch] = mutated_high[epoch] * 10.0
    mean2 = compute_mean_clv_over_lookback_v1(
        mutated_high,
        long["low"],
        long["close"],
        lookback_n=36,
        signal_lag_bars=lag,
        epoch_index=epoch,
    )
    assert mean2 is not None
    assert mean2 == pytest.approx(mean1)


def test_zero_score_and_nan_ineligible() -> None:
    mid = _ohlc_mid()
    assert (
        compute_instrument_score_v1(
            "okx:linear_perpetual:ETH-USDT",
            mid["high"],
            mid["low"],
            mid["close"],
            lookback_n=36,
            epoch_index=60,
        )
        is None
    )
    zero = _ohlc_zero_range()
    assert (
        compute_instrument_score_v1(
            "okx:linear_perpetual:ETH-USDT",
            zero["high"],
            zero["low"],
            zero["close"],
            lookback_n=36,
            epoch_index=60,
        )
        is None
    )
    nan_ohlc = _ohlc_close_near_high()
    highs = list(nan_ohlc["high"])
    highs[40] = float("nan")
    assert (
        compute_mean_clv_over_lookback_v1(
            highs,
            nan_ohlc["low"],
            nan_ohlc["close"],
            lookback_n=36,
            signal_lag_bars=1,
            epoch_index=60,
        )
        is None
    )


def test_deterministic_tie_break_instrument_id_asc() -> None:
    a_ohlc = _ohlc_close_near_high()
    b_ohlc = _ohlc_close_near_high()
    a = compute_instrument_score_v1(
        "okx:linear_perpetual:AAA-USDT",
        a_ohlc["high"],
        a_ohlc["low"],
        a_ohlc["close"],
        lookback_n=36,
        epoch_index=60,
    )
    b = compute_instrument_score_v1(
        "okx:linear_perpetual:BBB-USDT",
        b_ohlc["high"],
        b_ohlc["low"],
        b_ohlc["close"],
        lookback_n=36,
        epoch_index=60,
    )
    assert a is not None and b is not None
    assert a.score == pytest.approx(b.score)
    ranked = rank_scores_deterministic_v1([b, a])
    assert ranked[0].instrument_id == "okx:linear_perpetual:AAA-USDT"
    assert ranked[1].instrument_id == "okx:linear_perpetual:BBB-USDT"


def test_directional_form_d_symmetric_top1_sign() -> None:
    assert resolve_symmetric_top1_sign_v1(0.5) == RankIntentSideV1.LONG_TOP1
    assert resolve_symmetric_top1_sign_v1(-0.5) == RankIntentSideV1.SHORT_TOP1
    assert resolve_symmetric_top1_sign_v1(0.0) == RankIntentSideV1.FLAT
    assert resolve_symmetric_top1_sign_v1(float("nan")) == RankIntentSideV1.FLAT


def test_continuation_selection_prefers_higher_mean_clv() -> None:
    panel = {
        "okx:linear_perpetual:ETH-USDT": _ohlc_close_near_low(),
        "okx:linear_perpetual:SOL-USDT": _ohlc_close_near_high(),
        "okx:linear_perpetual:AVAX-USDT": _ohlc_close_near_low(),
        "okx:linear_perpetual:LINK-USDT": _ohlc_close_near_low(),
        "okx:linear_perpetual:DOT-USDT": _ohlc_close_near_low(),
    }
    intent = select_single_top1_rank_intent_v1(panel, epoch_index=60)
    assert intent.selection_emitted is True
    assert intent.insufficient_universe is False
    assert intent.selected_instrument_id == "okx:linear_perpetual:SOL-USDT"
    assert intent.intent_side == RankIntentSideV1.LONG_TOP1
    assert intent.double_play_remains_sole_authority is True

    held = select_single_top1_rank_intent_v1(panel, epoch_index=61, prior_intent=intent)
    assert held.selection_emitted is False
    assert held.selected_instrument_id == intent.selected_instrument_id


def test_short_top1_when_top_score_negative() -> None:
    panel = {
        "okx:linear_perpetual:ETH-USDT": _ohlc_close_near_low(),
        "okx:linear_perpetual:SOL-USDT": _ohlc_close_near_low(),
        "okx:linear_perpetual:AVAX-USDT": _ohlc_close_near_low(),
        "okx:linear_perpetual:LINK-USDT": _ohlc_close_near_low(),
        "okx:linear_perpetual:DOT-USDT": _ohlc_close_near_low(),
    }
    intent = select_single_top1_rank_intent_v1(panel, epoch_index=60)
    assert intent.selection_emitted is True
    assert intent.intent_side == RankIntentSideV1.SHORT_TOP1
    assert intent.top_score is not None and intent.top_score < 0.0
    assert intent.selected_instrument_id is not None


def test_insufficient_universe_and_frozen_param_fail_closed() -> None:
    panel = {
        "okx:linear_perpetual:ETH-USDT": _ohlc_close_near_high(),
        "okx:linear_perpetual:SOL-USDT": _ohlc_close_near_high(),
    }
    intent = select_single_top1_rank_intent_v1(panel, epoch_index=60)
    assert intent.insufficient_universe is True
    assert intent.intent_side == RankIntentSideV1.FLAT
    assert validate_lookback_n(24) is False
    with pytest.raises(ValueError, match="LOOKBACK_N_NOT_FROZEN_PARAMETER"):
        select_single_top1_rank_intent_v1(panel, epoch_index=60, lookback_n=24)


def test_empty_cross_section_fail_closed() -> None:
    intent = select_single_top1_rank_intent_v1({}, epoch_index=60)
    assert intent.insufficient_universe is True
    assert intent.selected_instrument_id is None
    assert intent.intent_side == RankIntentSideV1.FLAT


def test_implementation_binding_guards_and_csrhr_unchanged() -> None:
    import json

    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["strategy_implementation_present"] is True
    assert report["evaluation_authorized"] is False
    assert report["development_run_count"] == 1
    assert report["holdout_authorized"] is False
    assert report["frozen_digest"] == REQUIRED_DIGEST
    assert report["csrhr_unchanged"] is True

    csrhr = json.loads(CSRHR_BACKLOG.read_text(encoding="utf-8"))
    assert csrhr["status"] == "OPEN_BACKLOG"
    assert csrhr["development_run_count"] == 0

    program = json.loads(PROGRAM.read_text(encoding="utf-8"))
    assert program["development_run_count"] == 1
    assert program["evaluation_authorized"] is False
    assert program["strategy_implementation_present"] is True

    backlog = json.loads(BACKLOG.read_text(encoding="utf-8"))
    assert backlog["development_run_count"] == 1
    assert backlog["preregistered_hypotheses"][0]["implementation_present"] is True
    assert backlog["preregistered_hypotheses"][0]["run_slot_consumed"] is True

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["development_run_count"] == 1
    assert contract["evaluation_authorized"] is False
    assert contract["strategy_implementation_present"] is False
    assert contract["contract_digest"] == REQUIRED_DIGEST


def test_evaluation_path_not_imported_or_callable_in_impl_modules() -> None:
    score_src = (
        REPO
        / "src/research/cross_sectional_intrabar_close_location_pressure_continuation_v1_score_v1.py"
    ).read_text(encoding="utf-8")
    selection_src = (
        REPO
        / "src/research/cross_sectional_intrabar_close_location_pressure_continuation_v1_selection_v1.py"
    ).read_text(encoding="utf-8")
    binding_src = (
        REPO
        / "src/research/cross_sectional_intrabar_close_location_pressure_continuation_v1_strategy_implementation_binding_v1.py"
    ).read_text(encoding="utf-8")
    forbidden_snippets = (
        "run_evaluate_cross_sectional_intrabar",
        "development_evaluation_v1",
        "evaluate_path_v1",
        "from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_development_evaluation",
        "importlib.import_module",
        "offline_economic_reevaluation_sealed_long_panel_v1",
    )
    for src in (score_src, selection_src, binding_src):
        for snippet in forbidden_snippets:
            assert snippet not in src
    assert "runner_start" not in score_src
    assert "runner_start" not in selection_src
