"""Cross-sectional futures pairwise lead-lag spillover v1 score computation.

Pure offline, deterministic directed pairwise spillover strength scores from strictly
lagged leader returns to strictly future follower returns. Research-only; no runtime,
order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_SCORE_V0=true"

SCORE_FORMULA_VERSION = "pairwise_spillover_graph_v1"
SCORE_FORMULA_EXPRESSION = (
    "leader_lagged_return_i = ln(close_i[t-signal_lag] / close_i[t-signal_lag-L]); "
    "follower_future_return_j = ln(close_j[t+forward_lag] / close_j[t]); "
    "spillover_strength(i->j) = leader_lagged_return_i * follower_future_return_j; "
    "L = lag_window_L; signal_lag = signal_lag_bars; forward_lag = forward_lag_bars"
)

DEFAULT_LAG_WINDOW_L = 8
DEFAULT_SIGNAL_LAG_BARS = 1
DEFAULT_FORWARD_LAG_BARS = 1
MIN_ELIGIBLE_MEMBERS = 5


@dataclass(frozen=True)
class PairwiseSpilloverScoreResultV0:
    leader_id: str
    follower_id: str
    score: float
    leader_lagged_return: float
    follower_future_return: float
    warmup_complete: bool


@dataclass(frozen=True)
class InstrumentNetSpilloverScoreResultV0:
    instrument_id: str
    score: float
    inbound_spillover_sum: float
    outbound_spillover_sum: float
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


def compute_future_log_return_v0(
    closes: Sequence[float],
    *,
    forward_lag_bars: int,
    epoch_index: int,
) -> float | None:
    future_idx = epoch_index + forward_lag_bars
    if future_idx >= len(closes) or epoch_index < 0:
        return None
    base = closes[epoch_index]
    future = closes[future_idx]
    if base <= 0 or future <= 0:
        return None
    value = math.log(future / base)
    if not math.isfinite(value):
        return None
    return value


def compute_pairwise_spillover_strength_v0(
    leader_lagged_return: float,
    follower_future_return: float,
) -> float | None:
    score = leader_lagged_return * follower_future_return
    if not math.isfinite(score):
        return None
    return score


def compute_directed_pair_spillover_score_v0(
    leader_id: str,
    follower_id: str,
    leader_closes: Sequence[float],
    follower_closes: Sequence[float],
    *,
    lag_window_l: int,
    signal_lag_bars: int,
    forward_lag_bars: int,
    epoch_index: int,
) -> PairwiseSpilloverScoreResultV0 | None:
    if leader_id == follower_id:
        return None
    if _is_bitcoin_instrument(leader_id) or _is_bitcoin_instrument(follower_id):
        return None
    leader_lagged_return = compute_lagged_log_return_v0(
        leader_closes,
        lag_window_l=lag_window_l,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    follower_future_return = compute_future_log_return_v0(
        follower_closes,
        forward_lag_bars=forward_lag_bars,
        epoch_index=epoch_index,
    )
    if leader_lagged_return is None or follower_future_return is None:
        return None
    score = compute_pairwise_spillover_strength_v0(
        leader_lagged_return,
        follower_future_return,
    )
    if score is None:
        return None
    return PairwiseSpilloverScoreResultV0(
        leader_id=leader_id,
        follower_id=follower_id,
        score=score,
        leader_lagged_return=leader_lagged_return,
        follower_future_return=follower_future_return,
        warmup_complete=True,
    )


def compute_panel_pairwise_spillover_scores_v0(
    instrument_closes: dict[str, Sequence[float]],
    *,
    lag_window_l: int,
    signal_lag_bars: int,
    forward_lag_bars: int,
    epoch_index: int,
) -> tuple[PairwiseSpilloverScoreResultV0, ...] | None:
    eligible_ids = [
        instrument_id
        for instrument_id in sorted(instrument_closes)
        if not _is_bitcoin_instrument(instrument_id)
    ]
    if len(eligible_ids) < MIN_ELIGIBLE_MEMBERS:
        return None
    scores: list[PairwiseSpilloverScoreResultV0] = []
    for leader_id in eligible_ids:
        for follower_id in eligible_ids:
            if leader_id == follower_id:
                continue
            result = compute_directed_pair_spillover_score_v0(
                leader_id,
                follower_id,
                instrument_closes[leader_id],
                instrument_closes[follower_id],
                lag_window_l=lag_window_l,
                signal_lag_bars=signal_lag_bars,
                forward_lag_bars=forward_lag_bars,
                epoch_index=epoch_index,
            )
            if result is not None:
                scores.append(result)
    if not scores:
        return None
    return tuple(scores)


def compute_instrument_net_spillover_scores_v0(
    pair_scores: Sequence[PairwiseSpilloverScoreResultV0],
) -> tuple[InstrumentNetSpilloverScoreResultV0, ...]:
    inbound: dict[str, float] = {}
    outbound: dict[str, float] = {}
    instrument_ids: set[str] = set()
    for item in pair_scores:
        instrument_ids.add(item.leader_id)
        instrument_ids.add(item.follower_id)
        outbound[item.leader_id] = outbound.get(item.leader_id, 0.0) + item.score
        inbound[item.follower_id] = inbound.get(item.follower_id, 0.0) + item.score
    results: list[InstrumentNetSpilloverScoreResultV0] = []
    for instrument_id in sorted(instrument_ids):
        inbound_sum = inbound.get(instrument_id, 0.0)
        outbound_sum = outbound.get(instrument_id, 0.0)
        net_score = inbound_sum - outbound_sum
        if not math.isfinite(net_score):
            continue
        results.append(
            InstrumentNetSpilloverScoreResultV0(
                instrument_id=instrument_id,
                score=net_score,
                inbound_spillover_sum=inbound_sum,
                outbound_spillover_sum=outbound_sum,
                warmup_complete=True,
            )
        )
    return tuple(results)


def rank_pair_scores_deterministic_v0(
    scores: Sequence[PairwiseSpilloverScoreResultV0],
) -> tuple[PairwiseSpilloverScoreResultV0, ...]:
    return tuple(
        sorted(
            scores,
            key=lambda item: (-item.score, item.leader_id, item.follower_id),
        )
    )


def rank_instrument_net_spillover_scores_deterministic_v0(
    scores: Sequence[InstrumentNetSpilloverScoreResultV0],
) -> tuple[InstrumentNetSpilloverScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (-item.score, item.instrument_id)))
