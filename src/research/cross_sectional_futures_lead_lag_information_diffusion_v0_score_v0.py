"""Cross-sectional futures lead-lag information diffusion v0 score computation.

Pure offline, deterministic panel-median-benchmark lagged return diffusion scores.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_SCORE_V0=true"

SCORE_FORMULA_VERSION = "panel_median_benchmark_lagged_return_diffusion_v0"
SCORE_FORMULA_EXPRESSION = (
    "r_i = ln(close_i[t-lag] / close_i[t-lag-L]); "
    "r_med = median({r_j : j eligible at epoch}); "
    "score_i = r_med - r_i; lag = signal_lag_bars"
)

DEFAULT_LAG_WINDOW_L = 8
DEFAULT_SIGNAL_LAG_BARS = 1
MIN_ELIGIBLE_MEMBERS = 5
ADMISSIBLE_LAG_SURFACE = (4, 8, 12, 24)


@dataclass(frozen=True)
class LeadLagDiffusionScoreResultV0:
    instrument_id: str
    score: float
    lagged_return: float
    panel_median_return: float
    warmup_complete: bool


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def compute_lagged_log_return_v0(
    closes: Sequence[float],
    *,
    lag_window_l: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> float | None:
    lag_idx = epoch_index - signal_lag_bars
    base_idx = lag_idx - lag_window_l
    if base_idx < 0 or lag_idx < 0 or lag_idx >= len(closes):
        return None
    base = closes[base_idx]
    current = closes[lag_idx]
    if base <= 0 or current <= 0:
        return None
    value = math.log(current / base)
    if not math.isfinite(value):
        return None
    return value


def compute_panel_median_lagged_return_v0(
    instrument_closes: dict[str, Sequence[float]],
    *,
    lag_window_l: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> tuple[float, dict[str, float]] | None:
    lagged_returns: dict[str, float] = {}
    for instrument_id, closes in instrument_closes.items():
        if _is_bitcoin_instrument(instrument_id):
            continue
        lagged = compute_lagged_log_return_v0(
            closes,
            lag_window_l=lag_window_l,
            signal_lag_bars=signal_lag_bars,
            epoch_index=epoch_index,
        )
        if lagged is not None:
            lagged_returns[instrument_id] = lagged
    if len(lagged_returns) < MIN_ELIGIBLE_MEMBERS:
        return None
    return median(lagged_returns.values()), lagged_returns


def compute_diffusion_score_v0(
    lagged_return: float,
    panel_median_return: float,
) -> float | None:
    score = panel_median_return - lagged_return
    if not math.isfinite(score):
        return None
    return score


def compute_instrument_diffusion_score_v0(
    instrument_id: str,
    closes: Sequence[float],
    *,
    lag_window_l: int,
    signal_lag_bars: int,
    epoch_index: int,
    panel_median_return: float | None = None,
    instrument_closes: dict[str, Sequence[float]] | None = None,
) -> LeadLagDiffusionScoreResultV0 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    lagged_return = compute_lagged_log_return_v0(
        closes,
        lag_window_l=lag_window_l,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if lagged_return is None:
        return None
    if panel_median_return is None:
        if instrument_closes is None:
            return None
        panel = compute_panel_median_lagged_return_v0(
            instrument_closes,
            lag_window_l=lag_window_l,
            signal_lag_bars=signal_lag_bars,
            epoch_index=epoch_index,
        )
        if panel is None:
            return None
        panel_median_return, _ = panel
    score = compute_diffusion_score_v0(lagged_return, panel_median_return)
    if score is None:
        return None
    return LeadLagDiffusionScoreResultV0(
        instrument_id=instrument_id,
        score=score,
        lagged_return=lagged_return,
        panel_median_return=panel_median_return,
        warmup_complete=True,
    )


def rank_scores_deterministic_v0(
    scores: Sequence[LeadLagDiffusionScoreResultV0],
) -> tuple[LeadLagDiffusionScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (-item.score, item.instrument_id)))
