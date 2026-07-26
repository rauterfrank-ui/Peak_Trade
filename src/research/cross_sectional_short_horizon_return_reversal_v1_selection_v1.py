"""Deterministic single-top1 rank-intent selection for CSRHR v1.

Directional form D: mutually exclusive directional selection via
``single_top1_by_score_desc`` + ``symmetric_top1_sign`` on
**negated** trailing log returns (reversal polarity).

Emits research rank intent only. Double-Play remains sole directional transition
authority. No evaluation, holdout, runtime, or Master-V2 mutation.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_short_horizon_return_reversal_v1_score_v1 import (
    DATASET_ID,
    DEFAULT_LOOKBACK_N,
    DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEFAULT_SELECTION_COUNT_FIXED_N,
    DEFAULT_SIGNAL_LAG_BARS,
    HYPOTHESIS_ID,
    PROGRAM_ID,
    SCORE_FORMULA_VERSION,
    SIGNAL_FAMILY,
    STRATEGY_ID,
    STRATEGY_IDENTITY,
    CrossSectionalShortHorizonReturnReversalScoreResultV1,
    compute_instrument_score_v1,
    rank_scores_deterministic_v1,
    validate_lookback_n,
    validate_rebalance_interval_bars,
    validate_signal_lag_bars,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_SELECTION_V1=true"

DIRECTIONAL_FORM = "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION"
SELECTION_MODE = "single_top1_by_score_desc"
DIRECTION_POLICY = "symmetric_top1_sign"
TIE_BREAK_POLICY = "score_desc_then_instrument_id_asc"
SOLE_DIRECTIONAL_TRANSITION_AUTHORITY = "trading.master_v2.double_play_state.transition_state"
MINIMUM_HOLD_POLICY = "until_next_rebalance"
COOLDOWN_POLICY = "no_cooldown"
SCHEMA_VERSION = "cross_sectional_short_horizon_return_reversal_v1_rank_intent.v1"


class RankIntentSideV1(str, Enum):
    FLAT = "FLAT"
    LONG_TOP1 = "LONG_TOP1"
    SHORT_TOP1 = "SHORT_TOP1"


@dataclass(frozen=True)
class CrossSectionalShortHorizonReturnReversalRankIntentV1:
    strategy_id: str
    strategy_identity: str
    hypothesis_id: str
    program_id: str
    signal_family: str
    directional_form: str
    score_formula_version: str
    dataset_id: str
    schema_version: str
    epoch_index: int
    lookback_n: int
    signal_lag_bars: int
    rebalance_interval_bars: int
    eligible_member_count: int
    ranked_instrument_ids: tuple[str, ...]
    top_score: float | None
    selected_instrument_id: str | None
    intent_side: RankIntentSideV1
    selection_emitted: bool
    insufficient_universe: bool
    double_play_remains_sole_authority: bool

    def to_provenance_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["intent_side"] = self.intent_side.value
        payload["ranked_instrument_ids"] = list(self.ranked_instrument_ids)
        return payload


def resolve_symmetric_top1_sign_v1(score: float | None) -> RankIntentSideV1:
    if score is None or not math.isfinite(score) or score == 0.0:
        return RankIntentSideV1.FLAT
    if score > 0.0:
        return RankIntentSideV1.LONG_TOP1
    return RankIntentSideV1.SHORT_TOP1


def is_rebalance_epoch_v1(epoch_index: int, *, rebalance_interval_bars: int) -> bool:
    if rebalance_interval_bars <= 0:
        return False
    return epoch_index % rebalance_interval_bars == 0


def _flat_intent(
    *,
    epoch_index: int,
    lookback_n: int,
    signal_lag_bars: int,
    rebalance_interval_bars: int,
    eligible_member_count: int = 0,
    ranked_instrument_ids: tuple[str, ...] = (),
    selection_emitted: bool = False,
    insufficient_universe: bool = False,
) -> CrossSectionalShortHorizonReturnReversalRankIntentV1:
    return CrossSectionalShortHorizonReturnReversalRankIntentV1(
        strategy_id=STRATEGY_ID,
        strategy_identity=STRATEGY_IDENTITY,
        hypothesis_id=HYPOTHESIS_ID,
        program_id=PROGRAM_ID,
        signal_family=SIGNAL_FAMILY,
        directional_form=DIRECTIONAL_FORM,
        score_formula_version=SCORE_FORMULA_VERSION,
        dataset_id=DATASET_ID,
        schema_version=SCHEMA_VERSION,
        epoch_index=epoch_index,
        lookback_n=lookback_n,
        signal_lag_bars=signal_lag_bars,
        rebalance_interval_bars=rebalance_interval_bars,
        eligible_member_count=eligible_member_count,
        ranked_instrument_ids=ranked_instrument_ids,
        top_score=None,
        selected_instrument_id=None,
        intent_side=RankIntentSideV1.FLAT,
        selection_emitted=selection_emitted,
        insufficient_universe=insufficient_universe,
        double_play_remains_sole_authority=True,
    )


def select_single_top1_rank_intent_v1(
    closes_by_instrument: Mapping[str, Sequence[float]],
    *,
    epoch_index: int,
    lookback_n: int = DEFAULT_LOOKBACK_N,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    min_eligible_members_for_rank: int = DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK,
    selection_count_fixed_n: int = DEFAULT_SELECTION_COUNT_FIXED_N,
    rebalance_interval_bars: int = DEFAULT_REBALANCE_INTERVAL_BARS,
    prior_intent: CrossSectionalShortHorizonReturnReversalRankIntentV1 | None = None,
    pit_membership: frozenset[str] | None = None,
) -> CrossSectionalShortHorizonReturnReversalRankIntentV1:
    """Select single top1 rank intent; hold prior intent between rebalance epochs.

    Optional ``pit_membership`` fail-closes instruments not in the point-in-time
    eligible set even if close series are supplied.
    """
    if selection_count_fixed_n != 1:
        raise ValueError("SELECTION_COUNT_MUST_BE_1")
    if not validate_lookback_n(lookback_n):
        raise ValueError("LOOKBACK_N_NOT_FROZEN_PARAMETER")
    if not validate_rebalance_interval_bars(rebalance_interval_bars):
        raise ValueError("REBALANCE_INTERVAL_NOT_FROZEN_PARAMETER")
    if not validate_signal_lag_bars(signal_lag_bars):
        raise ValueError("SIGNAL_LAG_NOT_FROZEN_PARAMETER")

    if not is_rebalance_epoch_v1(epoch_index, rebalance_interval_bars=rebalance_interval_bars):
        if prior_intent is None:
            return _flat_intent(
                epoch_index=epoch_index,
                lookback_n=lookback_n,
                signal_lag_bars=signal_lag_bars,
                rebalance_interval_bars=rebalance_interval_bars,
            )
        return CrossSectionalShortHorizonReturnReversalRankIntentV1(
            strategy_id=prior_intent.strategy_id,
            strategy_identity=prior_intent.strategy_identity,
            hypothesis_id=prior_intent.hypothesis_id,
            program_id=prior_intent.program_id,
            signal_family=prior_intent.signal_family,
            directional_form=prior_intent.directional_form,
            score_formula_version=prior_intent.score_formula_version,
            dataset_id=prior_intent.dataset_id,
            schema_version=prior_intent.schema_version,
            epoch_index=epoch_index,
            lookback_n=prior_intent.lookback_n,
            signal_lag_bars=prior_intent.signal_lag_bars,
            rebalance_interval_bars=prior_intent.rebalance_interval_bars,
            eligible_member_count=prior_intent.eligible_member_count,
            ranked_instrument_ids=prior_intent.ranked_instrument_ids,
            top_score=prior_intent.top_score,
            selected_instrument_id=prior_intent.selected_instrument_id,
            intent_side=prior_intent.intent_side,
            selection_emitted=False,
            insufficient_universe=prior_intent.insufficient_universe,
            double_play_remains_sole_authority=True,
        )

    scores: list[CrossSectionalShortHorizonReturnReversalScoreResultV1] = []
    for instrument_id, closes in closes_by_instrument.items():
        if pit_membership is not None and instrument_id not in pit_membership:
            continue
        result = compute_instrument_score_v1(
            instrument_id,
            closes,
            lookback_n=lookback_n,
            signal_lag_bars=signal_lag_bars,
            epoch_index=epoch_index,
        )
        if result is not None:
            scores.append(result)

    ranked = rank_scores_deterministic_v1(scores)
    ranked_ids = tuple(item.instrument_id for item in ranked)
    eligible = len(ranked)
    if eligible < min_eligible_members_for_rank:
        return _flat_intent(
            epoch_index=epoch_index,
            lookback_n=lookback_n,
            signal_lag_bars=signal_lag_bars,
            rebalance_interval_bars=rebalance_interval_bars,
            eligible_member_count=eligible,
            ranked_instrument_ids=ranked_ids,
            selection_emitted=True,
            insufficient_universe=True,
        )

    top = ranked[0]
    intent_side = resolve_symmetric_top1_sign_v1(top.score)
    selected_id = top.instrument_id if intent_side != RankIntentSideV1.FLAT else None
    return CrossSectionalShortHorizonReturnReversalRankIntentV1(
        strategy_id=STRATEGY_ID,
        strategy_identity=STRATEGY_IDENTITY,
        hypothesis_id=HYPOTHESIS_ID,
        program_id=PROGRAM_ID,
        signal_family=SIGNAL_FAMILY,
        directional_form=DIRECTIONAL_FORM,
        score_formula_version=SCORE_FORMULA_VERSION,
        dataset_id=DATASET_ID,
        schema_version=SCHEMA_VERSION,
        epoch_index=epoch_index,
        lookback_n=lookback_n,
        signal_lag_bars=signal_lag_bars,
        rebalance_interval_bars=rebalance_interval_bars,
        eligible_member_count=eligible,
        ranked_instrument_ids=ranked_ids,
        top_score=top.score,
        selected_instrument_id=selected_id,
        intent_side=intent_side,
        selection_emitted=True,
        insufficient_universe=False,
        double_play_remains_sole_authority=True,
    )
