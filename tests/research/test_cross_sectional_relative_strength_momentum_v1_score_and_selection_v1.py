"""Unit/contract tests for CS RS momentum v1 score and selection (synthetic only)."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from src.research.cross_sectional_relative_strength_momentum_v1_score_v1 import (
    DEFAULT_LOOKBACK_N,
    LOOKBACK_N_CANDIDATES,
    SCORE_FORMULA_VERSION,
    VOL_NORMALIZATION,
    compute_instrument_score_v1,
    compute_raw_trailing_log_return_v1,
    rank_scores_deterministic_v1,
    validate_lookback_n,
)
from src.research.cross_sectional_relative_strength_momentum_v1_selection_v1 import (
    DIRECTIONAL_FORM,
    RankIntentSideV1,
    resolve_symmetric_top1_sign_v1,
    select_single_top1_rank_intent_v1,
)
from src.research.cross_sectional_relative_strength_momentum_v1_strategy_implementation_binding_v1 import (
    load_and_validate_repo_binding,
)

REPO = Path(__file__).resolve().parents[2]


def _closes_up(start: float = 100.0, n: int = 40, step: float = 1.01) -> tuple[float, ...]:
    values = [start]
    for _ in range(n - 1):
        values.append(values[-1] * step)
    return tuple(values)


def _closes_down(start: float = 100.0, n: int = 40, step: float = 0.99) -> tuple[float, ...]:
    values = [start]
    for _ in range(n - 1):
        values.append(values[-1] * step)
    return tuple(values)


def test_score_formula_is_raw_trailing_not_vol_normalized() -> None:
    assert SCORE_FORMULA_VERSION == "raw_trailing_log_return_fixed_lookback_v1"
    assert VOL_NORMALIZATION is False
    assert DEFAULT_LOOKBACK_N == 20
    assert LOOKBACK_N_CANDIDATES == (10, 20, 48)


def test_raw_trailing_log_return_matches_telescoping_sum() -> None:
    closes = _closes_up(n=30)
    epoch = 25
    lookback = 10
    lag = 1
    score = compute_raw_trailing_log_return_v1(
        closes, lookback_n=lookback, signal_lag_bars=lag, epoch_index=epoch
    )
    assert score is not None
    lag_idx = epoch - lag
    expected = math.log(closes[lag_idx] / closes[lag_idx - lookback])
    assert score == pytest.approx(expected)
    # Explicit bar-sum equivalence
    total = 0.0
    for k in range(1, lookback + 1):
        total += math.log(closes[lag_idx - k + 1] / closes[lag_idx - k])
    assert score == pytest.approx(total)


def test_bitcoin_excluded_and_ranking_tie_break() -> None:
    assert (
        compute_instrument_score_v1(
            "okx:linear_perpetual:BTC-USDT",
            _closes_up(),
            lookback_n=10,
            epoch_index=20,
        )
        is None
    )
    a = compute_instrument_score_v1(
        "okx:linear_perpetual:AAA-USDT", _closes_up(step=1.02), lookback_n=10, epoch_index=20
    )
    b = compute_instrument_score_v1(
        "okx:linear_perpetual:BBB-USDT", _closes_up(step=1.02), lookback_n=10, epoch_index=20
    )
    assert a is not None and b is not None
    # Equal scores -> instrument_id ascending
    ranked = rank_scores_deterministic_v1([b, a])
    assert ranked[0].instrument_id < ranked[1].instrument_id


def test_directional_form_d_symmetric_top1_sign() -> None:
    assert DIRECTIONAL_FORM == "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION"
    assert resolve_symmetric_top1_sign_v1(0.1) == RankIntentSideV1.LONG_TOP1
    assert resolve_symmetric_top1_sign_v1(-0.1) == RankIntentSideV1.SHORT_TOP1
    assert resolve_symmetric_top1_sign_v1(0.0) == RankIntentSideV1.FLAT


def test_selection_picks_strongest_and_holds_between_rebalances() -> None:
    closes = {
        "okx:linear_perpetual:ETH-USDT": _closes_up(step=1.01),
        "okx:linear_perpetual:SOL-USDT": _closes_up(step=1.03),
        "okx:linear_perpetual:AVAX-USDT": _closes_up(step=1.02),
        "okx:linear_perpetual:LINK-USDT": _closes_down(step=0.99),
        "okx:linear_perpetual:DOT-USDT": _closes_up(step=1.015),
    }
    intent = select_single_top1_rank_intent_v1(
        closes,
        epoch_index=28,
        lookback_n=10,
        rebalance_interval_bars=4,
    )
    assert intent.selection_emitted is True
    assert intent.insufficient_universe is False
    assert intent.selected_instrument_id == "okx:linear_perpetual:SOL-USDT"
    assert intent.intent_side == RankIntentSideV1.LONG_TOP1
    assert intent.double_play_remains_sole_authority is True

    held = select_single_top1_rank_intent_v1(
        closes,
        epoch_index=29,
        lookback_n=10,
        rebalance_interval_bars=4,
        prior_intent=intent,
    )
    assert held.selection_emitted is False
    assert held.selected_instrument_id == intent.selected_instrument_id
    assert held.intent_side == intent.intent_side


def test_insufficient_universe_and_invalid_grid_fail_closed() -> None:
    closes = {
        "okx:linear_perpetual:ETH-USDT": _closes_up(),
        "okx:linear_perpetual:SOL-USDT": _closes_up(step=1.02),
    }
    intent = select_single_top1_rank_intent_v1(
        closes, epoch_index=25, lookback_n=10, min_eligible_members_for_rank=5
    )
    assert intent.insufficient_universe is True
    assert intent.intent_side == RankIntentSideV1.FLAT
    assert validate_lookback_n(99) is False
    with pytest.raises(ValueError, match="LOOKBACK_N_NOT_IN_PREREGISTERED_GRID"):
        select_single_top1_rank_intent_v1(closes, epoch_index=25, lookback_n=99)


def test_implementation_binding_and_frozen_measurement_digest() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["strategy_implementation_present"] is True
    assert report["evaluation_authorized"] is False
    assert report["holdout_authorized"] is False
    assert (
        report["frozen_digest"]
        == "54a6e4222ecb286a579780c53dddf509f2308f3b997ebef9e3a123a95ae1c3ed"
    )
