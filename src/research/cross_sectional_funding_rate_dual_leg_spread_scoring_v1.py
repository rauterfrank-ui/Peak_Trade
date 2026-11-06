"""Cross-sectional funding-rate dual-leg spread v1 score and selection primitives.

Pure offline, deterministic funding-rate level spread ranking for simultaneous
long-low / short-high dual-leg book. Material difference vs PR4925 single-slot delta rotation.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_SCORING_V1=true"

SCORE_FORMULA_VERSION = "cross_sectional_funding_rate_level_spread_dual_leg_v1"
SCORE_FORMULA_EXPRESSION = (
    "spread(t) = funding_rate_max_panel(t) - funding_rate_min_panel(t); "
    "long_leg = instrument with minimum funding_rate; "
    "short_leg = instrument with maximum funding_rate; "
    "both legs held simultaneously when spread >= min_spread_bps_for_entry"
)


class DualLegSpreadTarget(str, Enum):
    FLAT = "FLAT"
    DUAL_LEG = "DUAL_LEG"


@dataclass(frozen=True)
class FundingLevelScoreResultV1:
    instrument_id: str
    funding_rate: float
    signal_eligible: bool


@dataclass(frozen=True)
class DualLegSpreadSelectionV1:
    target: DualLegSpreadTarget
    long_instrument_id: str | None
    short_instrument_id: str | None
    min_funding_rate: float | None
    max_funding_rate: float | None
    spread_bps: float | None


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def compute_instrument_funding_level_score_v1(
    instrument_id: str,
    funding_rates: Sequence[float],
    *,
    signal_lag_bars: int,
    epoch_index: int,
) -> FundingLevelScoreResultV1 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    lag_idx = epoch_index - signal_lag_bars
    if lag_idx < 0 or lag_idx >= len(funding_rates):
        return None
    raw = funding_rates[lag_idx]
    if not math.isfinite(raw):
        return None
    return FundingLevelScoreResultV1(
        instrument_id=instrument_id,
        funding_rate=raw,
        signal_eligible=True,
    )


def rank_funding_scores_for_long_low_v1(
    scores: Sequence[FundingLevelScoreResultV1],
) -> tuple[FundingLevelScoreResultV1, ...]:
    return tuple(sorted(scores, key=lambda item: (item.funding_rate, item.instrument_id)))


def rank_funding_scores_for_short_high_v1(
    scores: Sequence[FundingLevelScoreResultV1],
) -> tuple[FundingLevelScoreResultV1, ...]:
    return tuple(sorted(scores, key=lambda item: (-item.funding_rate, item.instrument_id)))


def select_dual_leg_spread_v1(
    scores: Sequence[FundingLevelScoreResultV1],
    *,
    min_spread_bps_for_entry: float,
) -> DualLegSpreadSelectionV1:
    if not scores:
        return DualLegSpreadSelectionV1(
            target=DualLegSpreadTarget.FLAT,
            long_instrument_id=None,
            short_instrument_id=None,
            min_funding_rate=None,
            max_funding_rate=None,
            spread_bps=None,
        )
    long_ranked = rank_funding_scores_for_long_low_v1(scores)
    short_ranked = rank_funding_scores_for_short_high_v1(scores)
    min_item = long_ranked[0]
    max_item = short_ranked[0]
    spread_bps = (max_item.funding_rate - min_item.funding_rate) * 10_000.0
    if min_item.instrument_id == max_item.instrument_id:
        return DualLegSpreadSelectionV1(
            target=DualLegSpreadTarget.FLAT,
            long_instrument_id=None,
            short_instrument_id=None,
            min_funding_rate=min_item.funding_rate,
            max_funding_rate=max_item.funding_rate,
            spread_bps=spread_bps,
        )
    if spread_bps < min_spread_bps_for_entry:
        return DualLegSpreadSelectionV1(
            target=DualLegSpreadTarget.FLAT,
            long_instrument_id=None,
            short_instrument_id=None,
            min_funding_rate=min_item.funding_rate,
            max_funding_rate=max_item.funding_rate,
            spread_bps=spread_bps,
        )
    return DualLegSpreadSelectionV1(
        target=DualLegSpreadTarget.DUAL_LEG,
        long_instrument_id=min_item.instrument_id,
        short_instrument_id=max_item.instrument_id,
        min_funding_rate=min_item.funding_rate,
        max_funding_rate=max_item.funding_rate,
        spread_bps=spread_bps,
    )
