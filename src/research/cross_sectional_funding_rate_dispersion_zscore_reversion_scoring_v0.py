"""Cross-sectional funding-rate dispersion z-score reversion v0 score and single-leg selection.

Pure offline, deterministic panel dispersion-gated z-score mean-reversion scoring for
long-min-z / short-max-z rotation. Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_DISPERSION_ZSCORE_REVERSION_SCORING_V0=true"

SCORE_FORMULA_VERSION = "cross_sectional_funding_rate_dispersion_zscore_reversion_v0"
SCORE_FORMULA_EXPRESSION = (
    "z_score_i(t) = (funding_i(t-lag) - panel_mean) / panel_std; "
    "long_leg = instrument with minimum z_score; "
    "short_leg = instrument with maximum z_score; "
    "single_slot selects leg with larger absolute z_score when dispersion gate passes"
)
FUNDING_SIGNAL_LAG = 1
MIN_ELIGIBLE_MEMBERS = 5
MIN_PANEL_FUNDING_DISPERSION = 1e-5
MIN_ABS_ZSCORE_FOR_ENTRY = 1.0


class FundingZscoreScoreStatusV0(str, Enum):
    COMPUTE_OK = "COMPUTE_OK"
    WARMUP_INCOMPLETE = "WARMUP_INCOMPLETE"
    MISSING_REQUIRED_FUNDING_HISTORY = "MISSING_REQUIRED_FUNDING_HISTORY"
    NON_FINITE_INPUT = "NON_FINITE_INPUT"
    INSUFFICIENT_PANEL_DISPERSION = "INSUFFICIENT_PANEL_DISPERSION"


class FundingZscoreLeg(str, Enum):
    FLAT = "FLAT"
    LONG_MIN_ZSCORE = "LONG_MIN_ZSCORE"
    SHORT_MAX_ZSCORE = "SHORT_MAX_ZSCORE"


@dataclass(frozen=True)
class FundingZscoreScoreResultV0:
    instrument_id: str
    funding_rate_lag: float
    panel_mean: float
    panel_std: float
    z_score: float
    warmup_complete: bool
    score_status: FundingZscoreScoreStatusV0 = FundingZscoreScoreStatusV0.COMPUTE_OK
    signal_eligible: bool = True


@dataclass(frozen=True)
class PanelDispersionSnapshotV0:
    panel_mean: float
    panel_std: float
    eligible_count: int
    dispersion_gate_passes: bool


@dataclass(frozen=True)
class FundingZscoreExtremeSelectionV0:
    leg: FundingZscoreLeg
    instrument_id: str | None
    min_zscore_instrument_id: str | None
    max_zscore_instrument_id: str | None
    min_zscore: float | None
    max_zscore: float | None
    panel_dispersion_gate_passes: bool


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def compute_panel_dispersion_snapshot_v0(
    panel_funding_rates: Sequence[tuple[str, float | None]],
    *,
    min_panel_funding_dispersion: float = MIN_PANEL_FUNDING_DISPERSION,
) -> PanelDispersionSnapshotV0 | None:
    eligible = [
        rate
        for _instrument_id, rate in panel_funding_rates
        if rate is not None and math.isfinite(rate)
    ]
    if not eligible:
        return None
    panel_mean = sum(eligible) / len(eligible)
    if len(eligible) == 1:
        panel_std = 0.0
    else:
        variance = sum((rate - panel_mean) ** 2 for rate in eligible) / len(eligible)
        panel_std = math.sqrt(variance)
    dispersion_gate_passes = panel_std >= min_panel_funding_dispersion
    return PanelDispersionSnapshotV0(
        panel_mean=panel_mean,
        panel_std=panel_std,
        eligible_count=len(eligible),
        dispersion_gate_passes=dispersion_gate_passes,
    )


def compute_instrument_funding_zscore_score_v0(
    instrument_id: str,
    panel_funding_rates: Sequence[tuple[str, float | None]],
    *,
    signal_lag_bars: int = FUNDING_SIGNAL_LAG,
    min_panel_funding_dispersion: float = MIN_PANEL_FUNDING_DISPERSION,
    epoch_index: int,
) -> FundingZscoreScoreResultV0 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    if epoch_index < signal_lag_bars:
        return None

    snapshot = compute_panel_dispersion_snapshot_v0(
        panel_funding_rates,
        min_panel_funding_dispersion=min_panel_funding_dispersion,
    )
    if snapshot is None:
        return None
    if not snapshot.dispersion_gate_passes:
        return FundingZscoreScoreResultV0(
            instrument_id=instrument_id,
            funding_rate_lag=float("nan"),
            panel_mean=snapshot.panel_mean,
            panel_std=snapshot.panel_std,
            z_score=float("nan"),
            warmup_complete=True,
            score_status=FundingZscoreScoreStatusV0.INSUFFICIENT_PANEL_DISPERSION,
            signal_eligible=False,
        )

    instrument_rate: float | None = None
    for iid, rate in panel_funding_rates:
        if iid == instrument_id:
            instrument_rate = rate
            break
    if instrument_rate is None or not math.isfinite(instrument_rate):
        return FundingZscoreScoreResultV0(
            instrument_id=instrument_id,
            funding_rate_lag=float("nan"),
            panel_mean=snapshot.panel_mean,
            panel_std=snapshot.panel_std,
            z_score=float("nan"),
            warmup_complete=False,
            score_status=FundingZscoreScoreStatusV0.MISSING_REQUIRED_FUNDING_HISTORY,
            signal_eligible=False,
        )

    z_score = (instrument_rate - snapshot.panel_mean) / snapshot.panel_std
    if not math.isfinite(z_score):
        return FundingZscoreScoreResultV0(
            instrument_id=instrument_id,
            funding_rate_lag=instrument_rate,
            panel_mean=snapshot.panel_mean,
            panel_std=snapshot.panel_std,
            z_score=z_score,
            warmup_complete=False,
            score_status=FundingZscoreScoreStatusV0.NON_FINITE_INPUT,
            signal_eligible=False,
        )
    return FundingZscoreScoreResultV0(
        instrument_id=instrument_id,
        funding_rate_lag=instrument_rate,
        panel_mean=snapshot.panel_mean,
        panel_std=snapshot.panel_std,
        z_score=z_score,
        warmup_complete=True,
        score_status=FundingZscoreScoreStatusV0.COMPUTE_OK,
        signal_eligible=True,
    )


def rank_funding_zscores_for_long_min_v0(
    scores: Sequence[FundingZscoreScoreResultV0],
) -> tuple[FundingZscoreScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (item.z_score, item.instrument_id)))


def rank_funding_zscores_for_short_max_v0(
    scores: Sequence[FundingZscoreScoreResultV0],
) -> tuple[FundingZscoreScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (-item.z_score, item.instrument_id)))


def select_funding_zscore_extreme_single_leg_v0(
    scores: Sequence[FundingZscoreScoreResultV0],
    *,
    min_abs_zscore_for_entry: float = MIN_ABS_ZSCORE_FOR_ENTRY,
    panel_dispersion_gate_passes: bool = True,
) -> FundingZscoreExtremeSelectionV0:
    if not scores or not panel_dispersion_gate_passes:
        return FundingZscoreExtremeSelectionV0(
            leg=FundingZscoreLeg.FLAT,
            instrument_id=None,
            min_zscore_instrument_id=None,
            max_zscore_instrument_id=None,
            min_zscore=None,
            max_zscore=None,
            panel_dispersion_gate_passes=panel_dispersion_gate_passes,
        )
    long_ranked = rank_funding_zscores_for_long_min_v0(scores)
    short_ranked = rank_funding_zscores_for_short_max_v0(scores)
    min_item = long_ranked[0]
    max_item = short_ranked[0]
    if (
        abs(min_item.z_score) < min_abs_zscore_for_entry
        and abs(max_item.z_score) < min_abs_zscore_for_entry
    ):
        return FundingZscoreExtremeSelectionV0(
            leg=FundingZscoreLeg.FLAT,
            instrument_id=None,
            min_zscore_instrument_id=min_item.instrument_id,
            max_zscore_instrument_id=max_item.instrument_id,
            min_zscore=min_item.z_score,
            max_zscore=max_item.z_score,
            panel_dispersion_gate_passes=True,
        )
    min_abs = abs(min_item.z_score)
    max_abs = abs(max_item.z_score)
    if min_abs > max_abs or (
        min_abs == max_abs and min_item.instrument_id <= max_item.instrument_id
    ):
        leg = FundingZscoreLeg.LONG_MIN_ZSCORE
        selected_id = min_item.instrument_id
    else:
        leg = FundingZscoreLeg.SHORT_MAX_ZSCORE
        selected_id = max_item.instrument_id
    return FundingZscoreExtremeSelectionV0(
        leg=leg,
        instrument_id=selected_id,
        min_zscore_instrument_id=min_item.instrument_id,
        max_zscore_instrument_id=max_item.instrument_id,
        min_zscore=min_item.z_score,
        max_zscore=max_item.z_score,
        panel_dispersion_gate_passes=True,
    )


def score_input_provenance_marker_v0() -> str:
    return "funding_zscore_score_input_lagged_observation_v0"


def funding_cashflow_provenance_marker_v0() -> str:
    return "funding_cashflow_interval_settlement_v1"
