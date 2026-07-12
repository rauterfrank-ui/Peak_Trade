"""Cross-sectional open-interest z-score reversion v0 score and single-leg selection.

Pure offline, deterministic panel dispersion-gated z-score mean-reversion scoring for
long-min-z / short-max-z rotation on lagged open-interest levels. Research-only; no
runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_INTEREST_ZSCORE_REVERSION_SCORING_V0=true"

SCORE_FORMULA_VERSION = "cross_sectional_open_interest_zscore_reversion_v0"
SCORE_FORMULA_EXPRESSION = (
    "z_score_i(t) = (open_interest_i(t-lag) - panel_mean) / panel_std; "
    "panel_std uses population variance (divide by N); "
    "long_leg = instrument with minimum z_score; "
    "short_leg = instrument with maximum z_score; "
    "single_slot selects leg with larger absolute z_score when dispersion gate passes"
)
OPEN_INTEREST_SIGNAL_LAG = 1
MIN_ELIGIBLE_MEMBERS = 5
MIN_ABS_ZSCORE_FOR_ENTRY = 1.0


class OpenInterestZscoreScoreStatusV0(str, Enum):
    COMPUTE_OK = "COMPUTE_OK"
    WARMUP_INCOMPLETE = "WARMUP_INCOMPLETE"
    MISSING_REQUIRED_OPEN_INTEREST = "MISSING_REQUIRED_OPEN_INTEREST"
    NON_FINITE_INPUT = "NON_FINITE_INPUT"
    INSUFFICIENT_PANEL_DISPERSION = "INSUFFICIENT_PANEL_DISPERSION"


class OpenInterestZscoreLeg(str, Enum):
    FLAT = "FLAT"
    LONG_MIN_ZSCORE = "LONG_MIN_ZSCORE"
    SHORT_MAX_ZSCORE = "SHORT_MAX_ZSCORE"


@dataclass(frozen=True)
class OpenInterestZscoreScoreResultV0:
    instrument_id: str
    open_interest_level_lag: float
    panel_mean: float
    panel_std: float
    z_score: float
    warmup_complete: bool
    score_status: OpenInterestZscoreScoreStatusV0 = OpenInterestZscoreScoreStatusV0.COMPUTE_OK
    signal_eligible: bool = True


@dataclass(frozen=True)
class PanelOpenInterestDispersionSnapshotV0:
    panel_mean: float
    panel_std: float
    eligible_count: int
    dispersion_gate_passes: bool


@dataclass(frozen=True)
class OpenInterestZscoreExtremeSelectionV0:
    leg: OpenInterestZscoreLeg
    instrument_id: str | None
    min_zscore_instrument_id: str | None
    max_zscore_instrument_id: str | None
    min_zscore: float | None
    max_zscore: float | None
    panel_dispersion_gate_passes: bool


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def _parse_open_interest(value: float | str | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return None


def compute_panel_oi_dispersion_snapshot_v0(
    panel_open_interest_levels: Sequence[tuple[str, float | str | None]],
) -> PanelOpenInterestDispersionSnapshotV0 | None:
    eligible: list[float] = []
    for _instrument_id, raw_level in panel_open_interest_levels:
        level = _parse_open_interest(raw_level)
        if level is not None and math.isfinite(level):
            eligible.append(level)
    if not eligible:
        return None
    panel_mean = sum(eligible) / len(eligible)
    if len(eligible) == 1:
        panel_std = 0.0
    else:
        variance = sum((level - panel_mean) ** 2 for level in eligible) / len(eligible)
        panel_std = math.sqrt(variance)
    dispersion_gate_passes = panel_std > 0.0
    return PanelOpenInterestDispersionSnapshotV0(
        panel_mean=panel_mean,
        panel_std=panel_std,
        eligible_count=len(eligible),
        dispersion_gate_passes=dispersion_gate_passes,
    )


def compute_instrument_open_interest_zscore_score_v0(
    instrument_id: str,
    panel_open_interest_levels: Sequence[tuple[str, float | str | None]],
    *,
    signal_lag_bars: int = OPEN_INTEREST_SIGNAL_LAG,
    epoch_index: int,
) -> OpenInterestZscoreScoreResultV0 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    if epoch_index < signal_lag_bars:
        return None

    snapshot = compute_panel_oi_dispersion_snapshot_v0(panel_open_interest_levels)
    if snapshot is None:
        return None
    if not snapshot.dispersion_gate_passes:
        return OpenInterestZscoreScoreResultV0(
            instrument_id=instrument_id,
            open_interest_level_lag=float("nan"),
            panel_mean=snapshot.panel_mean,
            panel_std=snapshot.panel_std,
            z_score=float("nan"),
            warmup_complete=True,
            score_status=OpenInterestZscoreScoreStatusV0.INSUFFICIENT_PANEL_DISPERSION,
            signal_eligible=False,
        )

    instrument_level: float | None = None
    for iid, raw_level in panel_open_interest_levels:
        if iid == instrument_id:
            instrument_level = _parse_open_interest(raw_level)
            break
    if instrument_level is None or not math.isfinite(instrument_level):
        return OpenInterestZscoreScoreResultV0(
            instrument_id=instrument_id,
            open_interest_level_lag=float("nan"),
            panel_mean=snapshot.panel_mean,
            panel_std=snapshot.panel_std,
            z_score=float("nan"),
            warmup_complete=False,
            score_status=OpenInterestZscoreScoreStatusV0.MISSING_REQUIRED_OPEN_INTEREST,
            signal_eligible=False,
        )

    z_score = (instrument_level - snapshot.panel_mean) / snapshot.panel_std
    if not math.isfinite(z_score):
        return OpenInterestZscoreScoreResultV0(
            instrument_id=instrument_id,
            open_interest_level_lag=instrument_level,
            panel_mean=snapshot.panel_mean,
            panel_std=snapshot.panel_std,
            z_score=z_score,
            warmup_complete=False,
            score_status=OpenInterestZscoreScoreStatusV0.NON_FINITE_INPUT,
            signal_eligible=False,
        )
    return OpenInterestZscoreScoreResultV0(
        instrument_id=instrument_id,
        open_interest_level_lag=instrument_level,
        panel_mean=snapshot.panel_mean,
        panel_std=snapshot.panel_std,
        z_score=z_score,
        warmup_complete=True,
        score_status=OpenInterestZscoreScoreStatusV0.COMPUTE_OK,
        signal_eligible=True,
    )


def rank_open_interest_zscores_for_long_min_v0(
    scores: Sequence[OpenInterestZscoreScoreResultV0],
) -> tuple[OpenInterestZscoreScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (item.z_score, item.instrument_id)))


def rank_open_interest_zscores_for_short_max_v0(
    scores: Sequence[OpenInterestZscoreScoreResultV0],
) -> tuple[OpenInterestZscoreScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (-item.z_score, item.instrument_id)))


def select_open_interest_zscore_extreme_single_leg_v0(
    scores: Sequence[OpenInterestZscoreScoreResultV0],
    *,
    min_abs_zscore_for_entry: float = MIN_ABS_ZSCORE_FOR_ENTRY,
    panel_dispersion_gate_passes: bool = True,
) -> OpenInterestZscoreExtremeSelectionV0:
    if not scores or not panel_dispersion_gate_passes:
        return OpenInterestZscoreExtremeSelectionV0(
            leg=OpenInterestZscoreLeg.FLAT,
            instrument_id=None,
            min_zscore_instrument_id=None,
            max_zscore_instrument_id=None,
            min_zscore=None,
            max_zscore=None,
            panel_dispersion_gate_passes=panel_dispersion_gate_passes,
        )
    long_ranked = rank_open_interest_zscores_for_long_min_v0(scores)
    short_ranked = rank_open_interest_zscores_for_short_max_v0(scores)
    min_item = long_ranked[0]
    max_item = short_ranked[0]
    if (
        abs(min_item.z_score) < min_abs_zscore_for_entry
        and abs(max_item.z_score) < min_abs_zscore_for_entry
    ):
        return OpenInterestZscoreExtremeSelectionV0(
            leg=OpenInterestZscoreLeg.FLAT,
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
        leg = OpenInterestZscoreLeg.LONG_MIN_ZSCORE
        selected_id = min_item.instrument_id
    else:
        leg = OpenInterestZscoreLeg.SHORT_MAX_ZSCORE
        selected_id = max_item.instrument_id
    return OpenInterestZscoreExtremeSelectionV0(
        leg=leg,
        instrument_id=selected_id,
        min_zscore_instrument_id=min_item.instrument_id,
        max_zscore_instrument_id=max_item.instrument_id,
        min_zscore=min_item.z_score,
        max_zscore=max_item.z_score,
        panel_dispersion_gate_passes=True,
    )


def score_input_provenance_marker_v0() -> str:
    return "open_interest_zscore_score_input_lagged_observation_v0"
