"""Valid evaluable rebalance-observation semantics for CS short-horizon return-reversal fade v1.

Counts only valid evaluable rebalance timestamps. Does not count trades, bars,
instruments, orders, discarded rebalances, or invalid cross-sections.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from src.research.cross_sectional_short_horizon_return_reversal_v1_development_evaluation_v1.constants_v1 import (
    DEFAULT_LOOKBACK_N,
    DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEFAULT_SIGNAL_LAG_BARS,
    MINIMUM_REBALANCE_OBSERVATIONS,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_selection_v1 import (
    CrossSectionalShortHorizonReturnReversalRankIntentV1,
    is_rebalance_epoch_v1,
    select_single_top1_rank_intent_v1,
)


@dataclass(frozen=True)
class RebalanceObservationV1:
    epoch_index: int
    timestamp_utc: str
    evaluable: bool
    eligible_member_count: int
    reason: str


def is_valid_evaluable_rebalance_observation(
    intent: CrossSectionalShortHorizonReturnReversalRankIntentV1,
) -> bool:
    """A rebalance timestamp is evaluable iff selection emitted on a rebalance epoch
    with sufficient universe breadth (invalid cross-sections excluded).
    """
    return classify_rebalance_observation(intent, timestamp_utc="").evaluable


def classify_rebalance_observation(
    intent: CrossSectionalShortHorizonReturnReversalRankIntentV1, *, timestamp_utc: str
) -> RebalanceObservationV1:
    if not is_rebalance_epoch_v1(
        intent.epoch_index, rebalance_interval_bars=intent.rebalance_interval_bars
    ):
        return RebalanceObservationV1(
            epoch_index=intent.epoch_index,
            timestamp_utc=timestamp_utc,
            evaluable=False,
            eligible_member_count=intent.eligible_member_count,
            reason="NOT_REBALANCE_EPOCH",
        )
    if not intent.selection_emitted:
        return RebalanceObservationV1(
            epoch_index=intent.epoch_index,
            timestamp_utc=timestamp_utc,
            evaluable=False,
            eligible_member_count=intent.eligible_member_count,
            reason="SELECTION_NOT_EMITTED",
        )
    if intent.insufficient_universe:
        return RebalanceObservationV1(
            epoch_index=intent.epoch_index,
            timestamp_utc=timestamp_utc,
            evaluable=False,
            eligible_member_count=intent.eligible_member_count,
            reason="INVALID_CROSS_SECTION_INSUFFICIENT_UNIVERSE",
        )
    if intent.eligible_member_count < DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK:
        return RebalanceObservationV1(
            epoch_index=intent.epoch_index,
            timestamp_utc=timestamp_utc,
            evaluable=False,
            eligible_member_count=intent.eligible_member_count,
            reason="INVALID_CROSS_SECTION_ELIGIBLE_BELOW_MIN",
        )
    return RebalanceObservationV1(
        epoch_index=intent.epoch_index,
        timestamp_utc=timestamp_utc,
        evaluable=True,
        eligible_member_count=intent.eligible_member_count,
        reason="VALID_EVALUABLE_REBALANCE_TIMESTAMP",
    )


def collect_valid_evaluable_rebalance_observations(
    closes_by_instrument: Mapping[str, Sequence[float]],
    timestamps_utc: Sequence[str],
    *,
    lookback_n: int = DEFAULT_LOOKBACK_N,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    rebalance_interval_bars: int = DEFAULT_REBALANCE_INTERVAL_BARS,
    min_eligible_members_for_rank: int = DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK,
) -> tuple[RebalanceObservationV1, ...]:
    if len(timestamps_utc) == 0:
        return ()
    # Use any series length; callers must align panel lengths.
    bar_count = min(len(v) for v in closes_by_instrument.values()) if closes_by_instrument else 0
    bar_count = min(bar_count, len(timestamps_utc))
    observations: list[RebalanceObservationV1] = []
    prior: CrossSectionalShortHorizonReturnReversalRankIntentV1 | None = None
    for epoch_index in range(bar_count):
        intent = select_single_top1_rank_intent_v1(
            closes_by_instrument,
            epoch_index=epoch_index,
            lookback_n=lookback_n,
            signal_lag_bars=signal_lag_bars,
            min_eligible_members_for_rank=min_eligible_members_for_rank,
            rebalance_interval_bars=rebalance_interval_bars,
            prior_intent=prior,
        )
        if is_rebalance_epoch_v1(epoch_index, rebalance_interval_bars=rebalance_interval_bars):
            observations.append(
                classify_rebalance_observation(intent, timestamp_utc=timestamps_utc[epoch_index])
            )
        prior = intent
    return tuple(observations)


def count_valid_evaluable_rebalance_observations(
    observations: Sequence[RebalanceObservationV1],
) -> int:
    return sum(1 for obs in observations if obs.evaluable)


def minimum_rebalance_observations_pass(count: int) -> bool:
    return count >= MINIMUM_REBALANCE_OBSERVATIONS
