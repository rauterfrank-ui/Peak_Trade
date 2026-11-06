"""VOLATILITY_COMPRESSION_BREAKOUT_V1 — entry-only research strategy producer.

Implements compression→expansion admission + shared price-channel break entry.
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
from src.research.volatility_compression_breakout_v1_vol_state_v1 import (
    compute_percentile_rank_120_normalized_atr_v1,
    compute_normalized_atr20_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
)

STRATEGY_IDENTITY_V1 = "VOLATILITY_COMPRESSION_BREAKOUT_V1"
STRATEGY_ID_V1 = "volatility_compression_breakout"
STRATEGY_VERSION_V1 = "v1"
SIGNAL_FAMILY_V1 = "VOLATILITY_REGIME"
PROGRAM_ID_V1 = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
BASELINE_ID_V1 = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"

COMPRESSION_PERCENTILE_MAX_V1 = 0.20
EXPANSION_PERCENTILE_MIN_V1 = 0.75
MIN_COMPRESSION_DURATION_BARS_V1 = 12
RELEASE_WINDOW_START_OFFSET_V1 = 1
RELEASE_WINDOW_END_OFFSET_V1 = 6
MAX_EXPANSION_TRIGGERS_PER_RELEASE_CYCLE_V1 = 1
COMPRESSION_CYCLE_MODE_V1 = "SINGLE_USE"
SIGNAL_LAG_BARS_V1 = 1
CHANNEL_LOOKBACK_BARS_V1 = CHANNEL_LOOKBACK_COMPLETED_BARS_V1

# Declarative exit binding (entry-only implementation; no exit producer here).
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
}


class VolatilityCompressionBreakoutEventV1(str, Enum):
    ENTRY_EVENT = "ENTRY_EVENT"
    NONE = "NONE"


class VolatilityCompressionBreakoutReasonV1(str, Enum):
    SUCCESSFUL_ENTRY = "SUCCESSFUL_ENTRY"
    CHANNEL_MISS = "CHANNEL_MISS"
    NO_EVENT = "NO_EVENT"
    WARMUP = "WARMUP"
    RELEASE_WINDOW_EXPIRED = "RELEASE_WINDOW_EXPIRED"


@dataclass(frozen=True)
class VolatilityCompressionBreakoutBarResultV1:
    """Canonical entry-event / directional carrier for one instrument bar."""

    event: VolatilityCompressionBreakoutEventV1
    entry_side: StrategyEntrySideCarrierV1
    event_kind: StrategyAgreementEventKindV1
    reason: VolatilityCompressionBreakoutReasonV1
    release_offset: Optional[int] = None
    percentile_rank_120: Optional[float] = None
    upper_channel: Optional[float] = None
    lower_channel: Optional[float] = None

    def __post_init__(self) -> None:
        if self.event is VolatilityCompressionBreakoutEventV1.ENTRY_EVENT:
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
    reason: VolatilityCompressionBreakoutReasonV1,
    *,
    release_offset: Optional[int] = None,
    percentile_rank_120: Optional[float] = None,
    upper_channel: Optional[float] = None,
    lower_channel: Optional[float] = None,
) -> VolatilityCompressionBreakoutBarResultV1:
    return VolatilityCompressionBreakoutBarResultV1(
        event=VolatilityCompressionBreakoutEventV1.NONE,
        entry_side=StrategyEntrySideCarrierV1.NONE,
        event_kind=StrategyAgreementEventKindV1.NONE,
        reason=reason,
        release_offset=release_offset,
        percentile_rank_120=percentile_rank_120,
        upper_channel=upper_channel,
        lower_channel=lower_channel,
    )


def _entry_result(
    side: StrategyEntrySideCarrierV1,
    *,
    release_offset: int,
    percentile_rank_120: float,
    upper_channel: float,
    lower_channel: float,
) -> VolatilityCompressionBreakoutBarResultV1:
    return VolatilityCompressionBreakoutBarResultV1(
        event=VolatilityCompressionBreakoutEventV1.ENTRY_EVENT,
        entry_side=side,
        event_kind=StrategyAgreementEventKindV1.ENTRY,
        reason=VolatilityCompressionBreakoutReasonV1.SUCCESSFUL_ENTRY,
        release_offset=release_offset,
        percentile_rank_120=percentile_rank_120,
        upper_channel=upper_channel,
        lower_channel=lower_channel,
    )


def generate_volatility_compression_breakout_events_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> list[VolatilityCompressionBreakoutBarResultV1]:
    """Generate per-bar entry events for a single-instrument OHLCV panel column.

    Instruments must be processed independently (no cross-instrument state).
    Only finalized/closed bars should be supplied by the caller.
    """
    for col in (high_col, low_col, close_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")

    high = data[high_col].astype(float)
    low = data[low_col].astype(float)
    close = data[close_col].astype(float)
    norm = compute_normalized_atr20_v1(high, low, close)
    rank = compute_percentile_rank_120_normalized_atr_v1(norm)
    upper, lower = compute_prior_high_low_channel_bounds_v1(
        high, low, lookback=CHANNEL_LOOKBACK_BARS_V1
    )

    compression_streak = 0
    release_active = False
    release_offset = 0
    results: list[VolatilityCompressionBreakoutBarResultV1] = []

    for i in range(len(data)):
        rank_i = rank.iloc[i]
        rank_valid = bool(np.isfinite(rank_i))
        rank_f = float(rank_i) if rank_valid else None
        u_i = upper.iloc[i]
        lo_i = lower.iloc[i]
        upper_f = float(u_i) if np.isfinite(u_i) else None
        lower_f = float(lo_i) if np.isfinite(lo_i) else None
        close_f = float(close.iloc[i]) if np.isfinite(close.iloc[i]) else float("nan")

        is_compression = (
            rank_valid and rank_f is not None and rank_f <= COMPRESSION_PERCENTILE_MAX_V1
        )
        is_expansion = rank_valid and rank_f is not None and rank_f >= EXPANSION_PERCENTILE_MIN_V1

        if release_active:
            release_offset += 1
            if release_offset > RELEASE_WINDOW_END_OFFSET_V1:
                # Offset 7+ is inadmissible; cycle already expired after offset 6.
                release_active = False
                release_offset = 0
                compression_streak = 0
                # Fall through to compression tracking on this bar.
            elif RELEASE_WINDOW_START_OFFSET_V1 <= release_offset <= RELEASE_WINDOW_END_OFFSET_V1:
                if is_expansion:
                    # First expansion trigger consumes the cycle regardless of channel.
                    release_active = False
                    consumed_offset = release_offset
                    release_offset = 0
                    compression_streak = 0
                    if upper_f is None or lower_f is None or not np.isfinite(close_f):
                        results.append(
                            _none_result(
                                VolatilityCompressionBreakoutReasonV1.CHANNEL_MISS,
                                release_offset=consumed_offset,
                                percentile_rank_120=rank_f,
                                upper_channel=upper_f,
                                lower_channel=lower_f,
                            )
                        )
                        continue
                    break_side = classify_price_channel_break_v1(close_f, upper_f, lower_f)
                    if break_side is PriceChannelBreakSideV1.LONG:
                        results.append(
                            _entry_result(
                                StrategyEntrySideCarrierV1.LONG,
                                release_offset=consumed_offset,
                                percentile_rank_120=float(rank_f),
                                upper_channel=upper_f,
                                lower_channel=lower_f,
                            )
                        )
                        continue
                    if break_side is PriceChannelBreakSideV1.SHORT:
                        results.append(
                            _entry_result(
                                StrategyEntrySideCarrierV1.SHORT,
                                release_offset=consumed_offset,
                                percentile_rank_120=float(rank_f),
                                upper_channel=upper_f,
                                lower_channel=lower_f,
                            )
                        )
                        continue
                    results.append(
                        _none_result(
                            VolatilityCompressionBreakoutReasonV1.CHANNEL_MISS,
                            release_offset=consumed_offset,
                            percentile_rank_120=rank_f,
                            upper_channel=upper_f,
                            lower_channel=lower_f,
                        )
                    )
                    continue

                if release_offset == RELEASE_WINDOW_END_OFFSET_V1:
                    # Window expiry after offset 6 with no expansion trigger.
                    release_active = False
                    expired_offset = release_offset
                    release_offset = 0
                    compression_streak = 0
                    results.append(
                        _none_result(
                            VolatilityCompressionBreakoutReasonV1.RELEASE_WINDOW_EXPIRED,
                            release_offset=expired_offset,
                            percentile_rank_120=rank_f,
                            upper_channel=upper_f,
                            lower_channel=lower_f,
                        )
                    )
                    continue

                # Active release, no expansion yet; no parallel compression cycle.
                results.append(
                    _none_result(
                        VolatilityCompressionBreakoutReasonV1.NO_EVENT,
                        release_offset=release_offset,
                        percentile_rank_120=rank_f,
                        upper_channel=upper_f,
                        lower_channel=lower_f,
                    )
                )
                continue

        # Not in an active release cycle: track compression / open cycle.
        if is_compression:
            compression_streak += 1
            results.append(
                _none_result(
                    VolatilityCompressionBreakoutReasonV1.NO_EVENT
                    if rank_valid
                    else VolatilityCompressionBreakoutReasonV1.WARMUP,
                    percentile_rank_120=rank_f,
                    upper_channel=upper_f,
                    lower_channel=lower_f,
                )
            )
            continue

        # Compression interrupted (or never started).
        if compression_streak >= MIN_COMPRESSION_DURATION_BARS_V1:
            # This bar is the first bar after the last qualifying compression bar.
            release_active = True
            release_offset = 1
            if is_expansion:
                release_active = False
                compression_streak = 0
                consumed_offset = 1
                release_offset = 0
                if upper_f is None or lower_f is None or not np.isfinite(close_f):
                    results.append(
                        _none_result(
                            VolatilityCompressionBreakoutReasonV1.CHANNEL_MISS,
                            release_offset=consumed_offset,
                            percentile_rank_120=rank_f,
                            upper_channel=upper_f,
                            lower_channel=lower_f,
                        )
                    )
                    continue
                break_side = classify_price_channel_break_v1(close_f, upper_f, lower_f)
                if break_side is PriceChannelBreakSideV1.LONG:
                    results.append(
                        _entry_result(
                            StrategyEntrySideCarrierV1.LONG,
                            release_offset=consumed_offset,
                            percentile_rank_120=float(rank_f),
                            upper_channel=upper_f,
                            lower_channel=lower_f,
                        )
                    )
                    continue
                if break_side is PriceChannelBreakSideV1.SHORT:
                    results.append(
                        _entry_result(
                            StrategyEntrySideCarrierV1.SHORT,
                            release_offset=consumed_offset,
                            percentile_rank_120=float(rank_f),
                            upper_channel=upper_f,
                            lower_channel=lower_f,
                        )
                    )
                    continue
                results.append(
                    _none_result(
                        VolatilityCompressionBreakoutReasonV1.CHANNEL_MISS,
                        release_offset=consumed_offset,
                        percentile_rank_120=rank_f,
                        upper_channel=upper_f,
                        lower_channel=lower_f,
                    )
                )
                continue

            compression_streak = 0
            results.append(
                _none_result(
                    VolatilityCompressionBreakoutReasonV1.NO_EVENT,
                    release_offset=release_offset,
                    percentile_rank_120=rank_f,
                    upper_channel=upper_f,
                    lower_channel=lower_f,
                )
            )
            continue

        compression_streak = 0
        results.append(
            _none_result(
                VolatilityCompressionBreakoutReasonV1.WARMUP
                if not rank_valid
                else VolatilityCompressionBreakoutReasonV1.NO_EVENT,
                percentile_rank_120=rank_f,
                upper_channel=upper_f,
                lower_channel=lower_f,
            )
        )

    return results


def generate_volatility_compression_breakout_event_series_v1(
    data: pd.DataFrame,
    **kwargs: object,
) -> pd.DataFrame:
    """DataFrame view of per-bar strategy events (synthetic/unit-test friendly)."""
    rows = generate_volatility_compression_breakout_events_v1(data, **kwargs)  # type: ignore[arg-type]
    return pd.DataFrame(
        {
            "event": [r.event.value for r in rows],
            "entry_side": [r.entry_side.value for r in rows],
            "event_kind": [r.event_kind.value for r in rows],
            "reason": [r.reason.value for r in rows],
            "release_offset": [r.release_offset for r in rows],
            "percentile_rank_120": [r.percentile_rank_120 for r in rows],
            "upper_channel": [r.upper_channel for r in rows],
            "lower_channel": [r.lower_channel for r in rows],
        },
        index=data.index,
    )


__all__ = [
    "BASELINE_ID_V1",
    "CHANNEL_LOOKBACK_BARS_V1",
    "COMPRESSION_CYCLE_MODE_V1",
    "COMPRESSION_PERCENTILE_MAX_V1",
    "EXIT_PARAMS_DECLARATIVE_V1",
    "EXPANSION_PERCENTILE_MIN_V1",
    "MAX_EXPANSION_TRIGGERS_PER_RELEASE_CYCLE_V1",
    "MIN_COMPRESSION_DURATION_BARS_V1",
    "PROGRAM_ID_V1",
    "RELEASE_WINDOW_END_OFFSET_V1",
    "RELEASE_WINDOW_START_OFFSET_V1",
    "SIGNAL_FAMILY_V1",
    "SIGNAL_LAG_BARS_V1",
    "STRATEGY_ID_V1",
    "STRATEGY_IDENTITY_V1",
    "STRATEGY_VERSION_V1",
    "VolatilityCompressionBreakoutBarResultV1",
    "VolatilityCompressionBreakoutEventV1",
    "VolatilityCompressionBreakoutReasonV1",
    "generate_volatility_compression_breakout_event_series_v1",
    "generate_volatility_compression_breakout_events_v1",
]
