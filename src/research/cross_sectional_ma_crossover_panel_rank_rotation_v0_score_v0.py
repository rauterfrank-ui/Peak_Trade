"""Cross-sectional MA-crossover panel rank-rotation v0 score computation.

Pure offline deterministic score primitives aligned with canonical ``ma_crossover/v1``
signal geometry (fast/slow SMA spread on finalized close bars). Does not mutate
strategy runtime paths or authorize execution.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_SCORE_V0=true"

SCORE_FORMULA_VERSION = "canonical_ma_crossover_normalized_spread_v0"
SCORE_FORMULA_EXPRESSION = (
    "score_i = (SMA_fast(i,t-lag) - SMA_slow(i,t-lag)) / SMA_slow(i,t-lag); "
    "SMA_fast uses fast_window finalized close bars; "
    "SMA_slow uses slow_window finalized close bars; lag = signal_lag_bars"
)


@dataclass(frozen=True)
class MaCrossoverPanelScoreResultV0:
    instrument_id: str
    score: float
    fast_ma: float
    slow_ma: float
    warmup_complete: bool


def _simple_moving_average(closes: Sequence[float], window: int, end_index: int) -> float | None:
    start = end_index - window + 1
    if start < 0 or end_index >= len(closes):
        return None
    window_values = closes[start : end_index + 1]
    if len(window_values) != window:
        return None
    if any(value <= 0 for value in window_values):
        return None
    return sum(window_values) / window


def compute_ma_crossover_normalized_score_v0(
    closes: Sequence[float],
    *,
    fast_window: int,
    slow_window: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> tuple[float, float, float] | None:
    lag_idx = epoch_index - signal_lag_bars
    if lag_idx < slow_window - 1:
        return None
    fast_ma = _simple_moving_average(closes, fast_window, lag_idx)
    slow_ma = _simple_moving_average(closes, slow_window, lag_idx)
    if fast_ma is None or slow_ma is None or slow_ma <= 0:
        return None
    score = (fast_ma - slow_ma) / slow_ma
    if not math.isfinite(score):
        return None
    return score, fast_ma, slow_ma


def compute_instrument_score_v0(
    instrument_id: str,
    closes: Sequence[float],
    *,
    fast_window: int,
    slow_window: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> MaCrossoverPanelScoreResultV0 | None:
    computed = compute_ma_crossover_normalized_score_v0(
        closes,
        fast_window=fast_window,
        slow_window=slow_window,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if computed is None:
        return None
    score, fast_ma, slow_ma = computed
    return MaCrossoverPanelScoreResultV0(
        instrument_id=instrument_id,
        score=score,
        fast_ma=fast_ma,
        slow_ma=slow_ma,
        warmup_complete=True,
    )


def rank_scores_deterministic_v0(
    scores: Sequence[MaCrossoverPanelScoreResultV0],
) -> tuple[MaCrossoverPanelScoreResultV0, ...]:
    return tuple(
        sorted(
            scores,
            key=lambda item: (-item.score, item.instrument_id),
        )
    )
