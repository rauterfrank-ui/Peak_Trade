"""Cross-sectional funding-rate persistence reversal filter v0 score and selection primitives.

Pure offline, deterministic persistence-duration + decay-stability + reversal-risk-gate
scoring for crowded-funding reversal rotation. Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_SCORING_V0=true"

SCORE_FORMULA_VERSION = "cross_sectional_funding_rate_persistence_reversal_filter_v0"
SCORE_FORMULA_EXPRESSION = (
    "persistence_score = max_consecutive_same_sign_epochs / window_length; "
    "decay_stability = 1 - min(1, std(abs(funding))/max(mean(abs(funding)), epsilon)); "
    "combined_score = persistence_score * decay_stability; "
    "reversal_blocked if sign flip with |delta| > adverse_reversal_threshold; "
    "long_leg = highest combined_score among negative mean funding instruments; "
    "short_leg = highest combined_score among positive mean funding instruments; "
    "single_slot selects leg with higher combined_score"
)
PERSISTENCE_LOOKBACK_K = 4
MIN_PERSISTENCE_EPOCHS = 3
DECAY_STABILITY_MIN_RATIO = 0.6
REVERSAL_RISK_LOOKBACK_K = 2
ADVERSE_REVERSAL_THRESHOLD = 0.00005
MIN_PERSISTENCE_SCORE_FOR_ENTRY = 0.5
FUNDING_SIGNAL_LAG = 1
DECAY_STABILITY_EPSILON = 1e-12


class FundingPersistenceScoreStatusV0(str, Enum):
    COMPUTE_OK = "COMPUTE_OK"
    WARMUP_INCOMPLETE = "WARMUP_INCOMPLETE"
    MISSING_REQUIRED_FUNDING_HISTORY = "MISSING_REQUIRED_FUNDING_HISTORY"
    NON_FINITE_INPUT = "NON_FINITE_INPUT"
    REVERSAL_BLOCKED = "REVERSAL_BLOCKED"
    INSUFFICIENT_PERSISTENCE = "INSUFFICIENT_PERSISTENCE"
    DECAY_STABILITY_BELOW_MIN = "DECAY_STABILITY_BELOW_MIN"


class FundingPersistenceLeg(str, Enum):
    FLAT = "FLAT"
    LONG_CROWDED_SHORT_REVERSAL = "LONG_CROWDED_SHORT_REVERSAL"
    SHORT_CROWDED_LONG_REVERSAL = "SHORT_CROWDED_LONG_REVERSAL"


@dataclass(frozen=True)
class FundingPersistenceScoreResultV0:
    instrument_id: str
    persistence_score: float
    decay_stability: float
    combined_score: float
    mean_funding: float
    max_consecutive_same_sign_epochs: int
    reversal_blocked: bool
    warmup_complete: bool
    score_status: FundingPersistenceScoreStatusV0 = FundingPersistenceScoreStatusV0.COMPUTE_OK
    signal_eligible: bool = True


@dataclass(frozen=True)
class FundingPersistenceExtremeSelectionV0:
    leg: FundingPersistenceLeg
    instrument_id: str | None
    long_leg_instrument_id: str | None
    short_leg_instrument_id: str | None
    long_leg_combined_score: float | None
    short_leg_combined_score: float | None


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def _max_consecutive_same_sign_epochs(rates: Sequence[float]) -> int:
    max_run = 0
    current_run = 0
    current_sign = 0
    for rate in rates:
        if rate == 0.0:
            current_run = 0
            current_sign = 0
            continue
        sign = 1 if rate > 0.0 else -1
        if sign == current_sign:
            current_run += 1
        else:
            current_run = 1
            current_sign = sign
        max_run = max(max_run, current_run)
    return max_run


def compute_persistence_score_v0(
    rates: Sequence[float],
    *,
    window_length: int,
) -> tuple[float, int]:
    if window_length <= 0:
        return 0.0, 0
    max_consecutive = _max_consecutive_same_sign_epochs(rates)
    return max_consecutive / window_length, max_consecutive


def compute_decay_stability_v0(
    rates: Sequence[float],
    *,
    epsilon: float = DECAY_STABILITY_EPSILON,
) -> float:
    abs_rates = [abs(rate) for rate in rates if math.isfinite(rate)]
    if not abs_rates:
        return 0.0
    mean_abs = max(sum(abs_rates) / len(abs_rates), epsilon)
    if len(abs_rates) < 2:
        return 1.0
    mean_val = sum(abs_rates) / len(abs_rates)
    variance = sum((value - mean_val) ** 2 for value in abs_rates) / len(abs_rates)
    std_abs = math.sqrt(variance)
    ratio = min(1.0, std_abs / mean_abs)
    return 1.0 - ratio


def detect_adverse_reversal_blocked_v0(
    rates: Sequence[float],
    *,
    adverse_reversal_threshold: float = ADVERSE_REVERSAL_THRESHOLD,
) -> bool:
    for index in range(1, len(rates)):
        previous = rates[index - 1]
        current = rates[index]
        if previous * current < 0.0:
            delta = abs(current - previous)
            if delta > adverse_reversal_threshold:
                return True
    return False


def compute_instrument_funding_persistence_score_v0(
    instrument_id: str,
    funding_rates: Sequence[float | None],
    *,
    persistence_lookback_k: int = PERSISTENCE_LOOKBACK_K,
    reversal_risk_lookback_k: int = REVERSAL_RISK_LOOKBACK_K,
    signal_lag_bars: int = FUNDING_SIGNAL_LAG,
    min_persistence_epochs: int = MIN_PERSISTENCE_EPOCHS,
    decay_stability_min_ratio: float = DECAY_STABILITY_MIN_RATIO,
    adverse_reversal_threshold: float = ADVERSE_REVERSAL_THRESHOLD,
    epoch_index: int,
) -> FundingPersistenceScoreResultV0 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None

    lag_end = epoch_index - signal_lag_bars
    persistence_start = lag_end - persistence_lookback_k + 1
    reversal_start = lag_end - reversal_risk_lookback_k + 1
    if persistence_start < 0 or reversal_start < 0:
        return None

    persistence_window = funding_rates[persistence_start : lag_end + 1]
    reversal_window = funding_rates[reversal_start : lag_end + 1]
    if any(rate is None for rate in persistence_window) or any(
        rate is None for rate in reversal_window
    ):
        return FundingPersistenceScoreResultV0(
            instrument_id=instrument_id,
            persistence_score=float("nan"),
            decay_stability=float("nan"),
            combined_score=float("nan"),
            mean_funding=float("nan"),
            max_consecutive_same_sign_epochs=0,
            reversal_blocked=False,
            warmup_complete=False,
            score_status=FundingPersistenceScoreStatusV0.MISSING_REQUIRED_FUNDING_HISTORY,
            signal_eligible=False,
        )

    persistence_values = [float(rate) for rate in persistence_window]
    reversal_values = [float(rate) for rate in reversal_window]
    if not all(math.isfinite(value) for value in persistence_values + reversal_values):
        return FundingPersistenceScoreResultV0(
            instrument_id=instrument_id,
            persistence_score=float("nan"),
            decay_stability=float("nan"),
            combined_score=float("nan"),
            mean_funding=float("nan"),
            max_consecutive_same_sign_epochs=0,
            reversal_blocked=False,
            warmup_complete=False,
            score_status=FundingPersistenceScoreStatusV0.NON_FINITE_INPUT,
            signal_eligible=False,
        )

    window_length = len(persistence_values)
    persistence_score, max_consecutive = compute_persistence_score_v0(
        persistence_values,
        window_length=window_length,
    )
    decay_stability = compute_decay_stability_v0(persistence_values)
    combined_score = persistence_score * decay_stability
    mean_funding = sum(persistence_values) / len(persistence_values)
    reversal_blocked = detect_adverse_reversal_blocked_v0(
        reversal_values,
        adverse_reversal_threshold=adverse_reversal_threshold,
    )

    if reversal_blocked:
        return FundingPersistenceScoreResultV0(
            instrument_id=instrument_id,
            persistence_score=persistence_score,
            decay_stability=decay_stability,
            combined_score=combined_score,
            mean_funding=mean_funding,
            max_consecutive_same_sign_epochs=max_consecutive,
            reversal_blocked=True,
            warmup_complete=True,
            score_status=FundingPersistenceScoreStatusV0.REVERSAL_BLOCKED,
            signal_eligible=False,
        )
    if max_consecutive < min_persistence_epochs:
        return FundingPersistenceScoreResultV0(
            instrument_id=instrument_id,
            persistence_score=persistence_score,
            decay_stability=decay_stability,
            combined_score=combined_score,
            mean_funding=mean_funding,
            max_consecutive_same_sign_epochs=max_consecutive,
            reversal_blocked=False,
            warmup_complete=True,
            score_status=FundingPersistenceScoreStatusV0.INSUFFICIENT_PERSISTENCE,
            signal_eligible=False,
        )
    if decay_stability < decay_stability_min_ratio:
        return FundingPersistenceScoreResultV0(
            instrument_id=instrument_id,
            persistence_score=persistence_score,
            decay_stability=decay_stability,
            combined_score=combined_score,
            mean_funding=mean_funding,
            max_consecutive_same_sign_epochs=max_consecutive,
            reversal_blocked=False,
            warmup_complete=True,
            score_status=FundingPersistenceScoreStatusV0.DECAY_STABILITY_BELOW_MIN,
            signal_eligible=False,
        )

    return FundingPersistenceScoreResultV0(
        instrument_id=instrument_id,
        persistence_score=persistence_score,
        decay_stability=decay_stability,
        combined_score=combined_score,
        mean_funding=mean_funding,
        max_consecutive_same_sign_epochs=max_consecutive,
        reversal_blocked=False,
        warmup_complete=True,
        score_status=FundingPersistenceScoreStatusV0.COMPUTE_OK,
        signal_eligible=True,
    )


def rank_funding_persistence_for_long_crowded_short_v0(
    scores: Sequence[FundingPersistenceScoreResultV0],
) -> tuple[FundingPersistenceScoreResultV0, ...]:
    eligible = [item for item in scores if item.mean_funding < 0.0 and item.signal_eligible]
    return tuple(sorted(eligible, key=lambda item: (-item.combined_score, item.instrument_id)))


def rank_funding_persistence_for_short_crowded_long_v0(
    scores: Sequence[FundingPersistenceScoreResultV0],
) -> tuple[FundingPersistenceScoreResultV0, ...]:
    eligible = [item for item in scores if item.mean_funding > 0.0 and item.signal_eligible]
    return tuple(sorted(eligible, key=lambda item: (-item.combined_score, item.instrument_id)))


def select_funding_persistence_extreme_single_leg_v0(
    scores: Sequence[FundingPersistenceScoreResultV0],
    *,
    min_persistence_score_for_entry: float = MIN_PERSISTENCE_SCORE_FOR_ENTRY,
) -> FundingPersistenceExtremeSelectionV0:
    if not scores:
        return FundingPersistenceExtremeSelectionV0(
            leg=FundingPersistenceLeg.FLAT,
            instrument_id=None,
            long_leg_instrument_id=None,
            short_leg_instrument_id=None,
            long_leg_combined_score=None,
            short_leg_combined_score=None,
        )

    long_ranked = rank_funding_persistence_for_long_crowded_short_v0(scores)
    short_ranked = rank_funding_persistence_for_short_crowded_long_v0(scores)
    long_item = long_ranked[0] if long_ranked else None
    short_item = short_ranked[0] if short_ranked else None

    long_score = long_item.combined_score if long_item is not None else None
    short_score = short_item.combined_score if short_item is not None else None
    long_id = long_item.instrument_id if long_item is not None else None
    short_id = short_item.instrument_id if short_item is not None else None

    long_eligible = long_score is not None and long_score >= min_persistence_score_for_entry
    short_eligible = short_score is not None and short_score >= min_persistence_score_for_entry
    if not long_eligible and not short_eligible:
        return FundingPersistenceExtremeSelectionV0(
            leg=FundingPersistenceLeg.FLAT,
            instrument_id=None,
            long_leg_instrument_id=long_id,
            short_leg_instrument_id=short_id,
            long_leg_combined_score=long_score,
            short_leg_combined_score=short_score,
        )

    if long_eligible and (
        not short_eligible
        or (long_score is not None and short_score is not None and long_score > short_score)
        or (
            long_score is not None
            and short_score is not None
            and long_score == short_score
            and long_id is not None
            and short_id is not None
            and long_id <= short_id
        )
    ):
        return FundingPersistenceExtremeSelectionV0(
            leg=FundingPersistenceLeg.LONG_CROWDED_SHORT_REVERSAL,
            instrument_id=long_id,
            long_leg_instrument_id=long_id,
            short_leg_instrument_id=short_id,
            long_leg_combined_score=long_score,
            short_leg_combined_score=short_score,
        )

    return FundingPersistenceExtremeSelectionV0(
        leg=FundingPersistenceLeg.SHORT_CROWDED_LONG_REVERSAL,
        instrument_id=short_id,
        long_leg_instrument_id=long_id,
        short_leg_instrument_id=short_id,
        long_leg_combined_score=long_score,
        short_leg_combined_score=short_score,
    )


def score_input_provenance_marker_v0() -> str:
    return "funding_persistence_reversal_filter_score_input_lagged_observation_v0"


def funding_cashflow_provenance_marker_v0() -> str:
    return "funding_cashflow_interval_settlement_v1"
