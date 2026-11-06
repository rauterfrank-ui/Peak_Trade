"""VOLATILITY_DECAY_BREAKOUT_V1 — entry-only research strategy producer.

Implements causally confirmed high→low vol decay + post-decay window channel-break entry.
No compression prerequisite. No expansion-persistence requirement. No entry on confirmation bar t.
Exit parameters are declared only (no exit state machine in this slice).
No evaluation, runner, dataset load, Master-V2 / Double-Play / risk / execution mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

from src.research.price_channel_breakout_core_v1 import (
    CHANNEL_LOOKBACK_COMPLETED_BARS_V1,
    PriceChannelBreakSideV1,
    classify_price_channel_break_v1,
    compute_prior_high_low_channel_bounds_v1,
)
from src.research.volatility_decay_breakout_v1_vol_state_v1 import (
    compute_normalized_atr14_v1,
    compute_percentile_rank_120_normalized_atr_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
)

STRATEGY_IDENTITY_V1 = "VOLATILITY_DECAY_BREAKOUT_V1"
STRATEGY_ID_V1 = "volatility_decay_breakout"
STRATEGY_VERSION_V1 = "v1"
SIGNAL_FAMILY_V1 = "VOLATILITY_REGIME"
PROGRAM_ID_V1 = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
BASELINE_ID_V1 = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"

HIGH_VOL_PRIOR_THRESHOLD_INCLUSIVE_MIN_V1 = 0.70
DECAY_CONFIRMATION_THRESHOLD_EXCLUSIVE_MAX_V1 = 0.40
DECAY_WINDOW_START_OFFSET_V1 = 1
DECAY_WINDOW_END_OFFSET_V1 = 8
MAX_ENTRIES_PER_DECAY_EVENT_V1 = 1
DECAY_EVENT_CONSUMPTION_V1 = "SINGLE_USE"
SIGNAL_LAG_BARS_V1 = 1
CHANNEL_LOOKBACK_BARS_V1 = CHANNEL_LOOKBACK_COMPLETED_BARS_V1
COMPRESSION_REGIME_NOT_REQUIRED_V1 = True
EXPANSION_PERSISTENCE_NOT_REQUIRED_V1 = True
ENTRY_ON_CONFIRMATION_BAR_T_FORBIDDEN_V1 = True
REARM_THRESHOLD_INCLUSIVE_MIN_V1 = 0.70

EXIT_PARAMS_DECLARATIVE_V1 = {
    "initial_stop_atr_multiple": 1.5,
    "trailing_stop_atr_multiple": 2.0,
    "regime_exit_percentile_rank_lt": 0.50,
    "time_exit_max_bars": 48,
    "first_event_wins": True,
    "reversal_forbidden": True,
    "scale_in_forbidden": True,
    "pyramiding_forbidden": True,
    "entry_only_implementation": True,
    "exit_state_machine_implemented": False,
    "new_pnl_implementation_forbidden": True,
    "second_pnl_truth_forbidden": True,
    "productive_exit_pnl_evaluator_ref": (
        "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
        "productive_exit_pnl_evaluator_v1.py"
    ),
}


class VolatilityDecayBreakoutEventV1(str, Enum):
    ENTRY_EVENT = "ENTRY_EVENT"
    NONE = "NONE"


class VolatilityDecayBreakoutReasonV1(str, Enum):
    SUCCESSFUL_ENTRY = "SUCCESSFUL_ENTRY"
    NO_EVENT = "NO_EVENT"
    WARMUP = "WARMUP"
    CONFIRMATION_OBSERVED = "CONFIRMATION_OBSERVED"
    DECAY_WINDOW_EXPIRED = "DECAY_WINDOW_EXPIRED"
    AWAITING_REARM = "AWAITING_REARM"


@dataclass(frozen=True)
class VolatilityDecayBreakoutBarResultV1:
    """Canonical entry-event / directional carrier for one instrument bar."""

    event: VolatilityDecayBreakoutEventV1
    entry_side: StrategyEntrySideCarrierV1
    event_kind: StrategyAgreementEventKindV1
    reason: VolatilityDecayBreakoutReasonV1
    decay_offset: Optional[int] = None
    confirmation_bar_index: Optional[int] = None
    percentile_rank_120: Optional[float] = None
    normalized_atr: Optional[float] = None
    upper_channel: Optional[float] = None
    lower_channel: Optional[float] = None

    def __post_init__(self) -> None:
        if self.event is VolatilityDecayBreakoutEventV1.ENTRY_EVENT:
            if self.entry_side is StrategyEntrySideCarrierV1.NONE:
                raise ValueError("entry_event_requires_long_or_short_side")
            if self.event_kind is not StrategyAgreementEventKindV1.ENTRY:
                raise ValueError("entry_event_kind_mismatch")
        else:
            if self.entry_side is not StrategyEntrySideCarrierV1.NONE:
                raise ValueError("none_event_requires_none_side")
            if self.event_kind is not StrategyAgreementEventKindV1.NONE:
                raise ValueError("none_event_kind_mismatch")


def _none_result(
    reason: VolatilityDecayBreakoutReasonV1,
    *,
    decay_offset: Optional[int] = None,
    confirmation_bar_index: Optional[int] = None,
    percentile_rank_120: Optional[float] = None,
    normalized_atr: Optional[float] = None,
    upper_channel: Optional[float] = None,
    lower_channel: Optional[float] = None,
) -> VolatilityDecayBreakoutBarResultV1:
    return VolatilityDecayBreakoutBarResultV1(
        event=VolatilityDecayBreakoutEventV1.NONE,
        entry_side=StrategyEntrySideCarrierV1.NONE,
        event_kind=StrategyAgreementEventKindV1.NONE,
        reason=reason,
        decay_offset=decay_offset,
        confirmation_bar_index=confirmation_bar_index,
        percentile_rank_120=percentile_rank_120,
        normalized_atr=normalized_atr,
        upper_channel=upper_channel,
        lower_channel=lower_channel,
    )


def _entry_result(
    side: StrategyEntrySideCarrierV1,
    *,
    decay_offset: int,
    confirmation_bar_index: int,
    percentile_rank_120: float,
    normalized_atr: float,
    upper_channel: float,
    lower_channel: float,
) -> VolatilityDecayBreakoutBarResultV1:
    return VolatilityDecayBreakoutBarResultV1(
        event=VolatilityDecayBreakoutEventV1.ENTRY_EVENT,
        entry_side=side,
        event_kind=StrategyAgreementEventKindV1.ENTRY,
        reason=VolatilityDecayBreakoutReasonV1.SUCCESSFUL_ENTRY,
        decay_offset=decay_offset,
        confirmation_bar_index=confirmation_bar_index,
        percentile_rank_120=percentile_rank_120,
        normalized_atr=normalized_atr,
        upper_channel=upper_channel,
        lower_channel=lower_channel,
    )


def _is_decay_confirmation(
    *,
    rank_t: Optional[float],
    rank_tm1: Optional[float],
    atr_t: Optional[float],
    atr_tm1: Optional[float],
) -> bool:
    """Preregistered high→low decay confirmation on completed bar t (past-only inputs)."""
    if rank_t is None or rank_tm1 is None or atr_t is None or atr_tm1 is None:
        return False
    return (
        rank_tm1 >= HIGH_VOL_PRIOR_THRESHOLD_INCLUSIVE_MIN_V1
        and rank_t < DECAY_CONFIRMATION_THRESHOLD_EXCLUSIVE_MAX_V1
        and atr_t < atr_tm1
    )


def generate_volatility_decay_breakout_events_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> list[VolatilityDecayBreakoutBarResultV1]:
    """Generate per-bar entry events for a single-instrument OHLCV series.

    Instruments must be processed independently (no cross-instrument state).
    Only finalized/closed bars should be supplied by the caller.
    """
    for col in (high_col, low_col, close_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")

    high = data[high_col].astype(float)
    low = data[low_col].astype(float)
    close = data[close_col].astype(float)
    norm = compute_normalized_atr14_v1(high, low, close)
    rank = compute_percentile_rank_120_normalized_atr_v1(norm)
    upper, lower = compute_prior_high_low_channel_bounds_v1(
        high, low, lookback=CHANNEL_LOOKBACK_BARS_V1
    )

    event_active = False
    confirmation_index: Optional[int] = None
    awaiting_rearm = False
    results: list[VolatilityDecayBreakoutBarResultV1] = []

    for i in range(len(data)):
        rank_i = rank.iloc[i]
        atr_i = norm.iloc[i]
        rank_valid = bool(np.isfinite(rank_i))
        atr_valid = bool(np.isfinite(atr_i))
        rank_f = float(rank_i) if rank_valid else None
        atr_f = float(atr_i) if atr_valid else None
        u_i = upper.iloc[i]
        lo_i = lower.iloc[i]
        upper_f = float(u_i) if np.isfinite(u_i) else None
        lower_f = float(lo_i) if np.isfinite(lo_i) else None
        close_f = float(close.iloc[i]) if np.isfinite(close.iloc[i]) else float("nan")

        rank_tm1 = float(rank.iloc[i - 1]) if i >= 1 and np.isfinite(rank.iloc[i - 1]) else None
        atr_tm1 = float(norm.iloc[i - 1]) if i >= 1 and np.isfinite(norm.iloc[i - 1]) else None

        # Rearm gate: after use/expiry, need >=1 completed bar with percentile >= 0.70.
        if awaiting_rearm and (not event_active):
            if rank_valid and rank_f is not None and rank_f >= REARM_THRESHOLD_INCLUSIVE_MIN_V1:
                awaiting_rearm = False
            else:
                results.append(
                    _none_result(
                        VolatilityDecayBreakoutReasonV1.AWAITING_REARM
                        if rank_valid
                        else VolatilityDecayBreakoutReasonV1.WARMUP,
                        percentile_rank_120=rank_f,
                        normalized_atr=atr_f,
                        upper_channel=upper_f,
                        lower_channel=lower_f,
                    )
                )
                continue

        if event_active and confirmation_index is not None:
            offset = i - confirmation_index
            if offset < DECAY_WINDOW_START_OFFSET_V1:
                results.append(
                    _none_result(
                        VolatilityDecayBreakoutReasonV1.NO_EVENT,
                        confirmation_bar_index=confirmation_index,
                        percentile_rank_120=rank_f,
                        normalized_atr=atr_f,
                        upper_channel=upper_f,
                        lower_channel=lower_f,
                    )
                )
                continue

            if offset > DECAY_WINDOW_END_OFFSET_V1:
                event_active = False
                confirmation_index = None
                awaiting_rearm = True
                results.append(
                    _none_result(
                        VolatilityDecayBreakoutReasonV1.AWAITING_REARM
                        if not (
                            rank_valid
                            and rank_f is not None
                            and rank_f >= REARM_THRESHOLD_INCLUSIVE_MIN_V1
                        )
                        else VolatilityDecayBreakoutReasonV1.NO_EVENT,
                        percentile_rank_120=rank_f,
                        normalized_atr=atr_f,
                        upper_channel=upper_f,
                        lower_channel=lower_f,
                    )
                )
                if rank_valid and rank_f is not None and rank_f >= REARM_THRESHOLD_INCLUSIVE_MIN_V1:
                    awaiting_rearm = False
                continue

            if DECAY_WINDOW_START_OFFSET_V1 <= offset <= DECAY_WINDOW_END_OFFSET_V1:
                if (
                    upper_f is not None
                    and lower_f is not None
                    and np.isfinite(close_f)
                    and rank_f is not None
                    and atr_f is not None
                ):
                    break_side = classify_price_channel_break_v1(close_f, upper_f, lower_f)
                    if break_side is PriceChannelBreakSideV1.LONG:
                        results.append(
                            _entry_result(
                                StrategyEntrySideCarrierV1.LONG,
                                decay_offset=offset,
                                confirmation_bar_index=confirmation_index,
                                percentile_rank_120=float(rank_f),
                                normalized_atr=float(atr_f),
                                upper_channel=upper_f,
                                lower_channel=lower_f,
                            )
                        )
                        event_active = False
                        confirmation_index = None
                        awaiting_rearm = True
                        continue
                    if break_side is PriceChannelBreakSideV1.SHORT:
                        results.append(
                            _entry_result(
                                StrategyEntrySideCarrierV1.SHORT,
                                decay_offset=offset,
                                confirmation_bar_index=confirmation_index,
                                percentile_rank_120=float(rank_f),
                                normalized_atr=float(atr_f),
                                upper_channel=upper_f,
                                lower_channel=lower_f,
                            )
                        )
                        event_active = False
                        confirmation_index = None
                        awaiting_rearm = True
                        continue

                if offset == DECAY_WINDOW_END_OFFSET_V1:
                    results.append(
                        _none_result(
                            VolatilityDecayBreakoutReasonV1.DECAY_WINDOW_EXPIRED,
                            decay_offset=offset,
                            confirmation_bar_index=confirmation_index,
                            percentile_rank_120=rank_f,
                            normalized_atr=atr_f,
                            upper_channel=upper_f,
                            lower_channel=lower_f,
                        )
                    )
                    event_active = False
                    confirmation_index = None
                    awaiting_rearm = True
                    continue

                results.append(
                    _none_result(
                        VolatilityDecayBreakoutReasonV1.NO_EVENT,
                        decay_offset=offset,
                        confirmation_bar_index=confirmation_index,
                        percentile_rank_120=rank_f,
                        normalized_atr=atr_f,
                        upper_channel=upper_f,
                        lower_channel=lower_f,
                    )
                )
                continue

        # No active event: evaluate decay confirmation on completed bar t (no entry on t).
        if not rank_valid or not atr_valid:
            results.append(
                _none_result(
                    VolatilityDecayBreakoutReasonV1.WARMUP,
                    percentile_rank_120=rank_f,
                    normalized_atr=atr_f,
                    upper_channel=upper_f,
                    lower_channel=lower_f,
                )
            )
            continue

        confirmed = _is_decay_confirmation(
            rank_t=rank_f,
            rank_tm1=rank_tm1,
            atr_t=atr_f,
            atr_tm1=atr_tm1,
        )
        if confirmed:
            confirmation_index = i
            event_active = True
            results.append(
                _none_result(
                    VolatilityDecayBreakoutReasonV1.CONFIRMATION_OBSERVED,
                    confirmation_bar_index=i,
                    percentile_rank_120=rank_f,
                    normalized_atr=atr_f,
                    upper_channel=upper_f,
                    lower_channel=lower_f,
                )
            )
            continue

        results.append(
            _none_result(
                VolatilityDecayBreakoutReasonV1.NO_EVENT,
                percentile_rank_120=rank_f,
                normalized_atr=atr_f,
                upper_channel=upper_f,
                lower_channel=lower_f,
            )
        )

    return results


def generate_volatility_decay_breakout_event_series_v1(
    data: pd.DataFrame,
    **kwargs: object,
) -> pd.DataFrame:
    """DataFrame view of per-bar strategy events (synthetic/unit-test friendly)."""
    rows = generate_volatility_decay_breakout_events_v1(data, **kwargs)  # type: ignore[arg-type]
    return pd.DataFrame(
        {
            "event": [r.event.value for r in rows],
            "entry_side": [r.entry_side.value for r in rows],
            "event_kind": [r.event_kind.value for r in rows],
            "reason": [r.reason.value for r in rows],
            "decay_offset": [r.decay_offset for r in rows],
            "confirmation_bar_index": [r.confirmation_bar_index for r in rows],
            "percentile_rank_120": [r.percentile_rank_120 for r in rows],
            "normalized_atr": [r.normalized_atr for r in rows],
            "upper_channel": [r.upper_channel for r in rows],
            "lower_channel": [r.lower_channel for r in rows],
        },
        index=data.index,
    )


__all__ = [
    "BASELINE_ID_V1",
    "CHANNEL_LOOKBACK_BARS_V1",
    "COMPRESSION_REGIME_NOT_REQUIRED_V1",
    "DECAY_CONFIRMATION_THRESHOLD_EXCLUSIVE_MAX_V1",
    "DECAY_EVENT_CONSUMPTION_V1",
    "DECAY_WINDOW_END_OFFSET_V1",
    "DECAY_WINDOW_START_OFFSET_V1",
    "ENTRY_ON_CONFIRMATION_BAR_T_FORBIDDEN_V1",
    "EXIT_PARAMS_DECLARATIVE_V1",
    "EXPANSION_PERSISTENCE_NOT_REQUIRED_V1",
    "HIGH_VOL_PRIOR_THRESHOLD_INCLUSIVE_MIN_V1",
    "MAX_ENTRIES_PER_DECAY_EVENT_V1",
    "PROGRAM_ID_V1",
    "REARM_THRESHOLD_INCLUSIVE_MIN_V1",
    "SIGNAL_FAMILY_V1",
    "SIGNAL_LAG_BARS_V1",
    "STRATEGY_ID_V1",
    "STRATEGY_IDENTITY_V1",
    "STRATEGY_VERSION_V1",
    "VolatilityDecayBreakoutBarResultV1",
    "VolatilityDecayBreakoutEventV1",
    "VolatilityDecayBreakoutReasonV1",
    "generate_volatility_decay_breakout_event_series_v1",
    "generate_volatility_decay_breakout_events_v1",
]
