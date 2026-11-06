"""UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1 baseline producer.

Uses the identical shared price-channel core as VOLATILITY_COMPRESSION_BREAKOUT_V1.
No compression, expansion, or release-cycle state.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.research.price_channel_breakout_core_v1 import (
    CHANNEL_LOOKBACK_COMPLETED_BARS_V1,
    PriceChannelBreakSideV1,
    classify_price_channel_break_v1,
    compute_prior_high_low_channel_bounds_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
)

BASELINE_ID_V1 = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
BASELINE_STRATEGY_ID_V1 = "unconditional_20_bar_price_channel_breakout"
CHANNEL_LOOKBACK_BARS_V1 = CHANNEL_LOOKBACK_COMPLETED_BARS_V1
SHARED_CHANNEL_CORE_OWNER_V1 = "research.price_channel_breakout_core_v1"


@dataclass(frozen=True)
class UnconditionalChannelBreakoutBarResultV1:
    event: str  # ENTRY_EVENT | NONE
    entry_side: StrategyEntrySideCarrierV1
    event_kind: StrategyAgreementEventKindV1
    upper_channel: float | None = None
    lower_channel: float | None = None


def generate_unconditional_20_bar_price_channel_breakout_events_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    lookback: int = CHANNEL_LOOKBACK_BARS_V1,
) -> list[UnconditionalChannelBreakoutBarResultV1]:
    """Emit ENTRY_EVENT on every valid LONG/SHORT channel break (no admission gate)."""
    for col in (high_col, low_col, close_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")

    high = data[high_col].astype(float)
    low = data[low_col].astype(float)
    close = data[close_col].astype(float)
    upper, lower = compute_prior_high_low_channel_bounds_v1(high, low, lookback=lookback)

    results: list[UnconditionalChannelBreakoutBarResultV1] = []
    for i in range(len(data)):
        u_i = upper.iloc[i]
        lo_i = lower.iloc[i]
        c_i = close.iloc[i]
        upper_f = float(u_i) if np.isfinite(u_i) else None
        lower_f = float(lo_i) if np.isfinite(lo_i) else None
        close_f = float(c_i) if np.isfinite(c_i) else float("nan")

        if upper_f is None or lower_f is None or not np.isfinite(close_f):
            results.append(
                UnconditionalChannelBreakoutBarResultV1(
                    event="NONE",
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    upper_channel=upper_f,
                    lower_channel=lower_f,
                )
            )
            continue

        break_side = classify_price_channel_break_v1(close_f, upper_f, lower_f)
        if break_side is PriceChannelBreakSideV1.LONG:
            results.append(
                UnconditionalChannelBreakoutBarResultV1(
                    event="ENTRY_EVENT",
                    entry_side=StrategyEntrySideCarrierV1.LONG,
                    event_kind=StrategyAgreementEventKindV1.ENTRY,
                    upper_channel=upper_f,
                    lower_channel=lower_f,
                )
            )
            continue
        if break_side is PriceChannelBreakSideV1.SHORT:
            results.append(
                UnconditionalChannelBreakoutBarResultV1(
                    event="ENTRY_EVENT",
                    entry_side=StrategyEntrySideCarrierV1.SHORT,
                    event_kind=StrategyAgreementEventKindV1.ENTRY,
                    upper_channel=upper_f,
                    lower_channel=lower_f,
                )
            )
            continue
        results.append(
            UnconditionalChannelBreakoutBarResultV1(
                event="NONE",
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                upper_channel=upper_f,
                lower_channel=lower_f,
            )
        )
    return results


def generate_unconditional_20_bar_price_channel_breakout_event_series_v1(
    data: pd.DataFrame,
    **kwargs: object,
) -> pd.DataFrame:
    rows = generate_unconditional_20_bar_price_channel_breakout_events_v1(
        data,
        **kwargs,  # type: ignore[arg-type]
    )
    return pd.DataFrame(
        {
            "event": [r.event for r in rows],
            "entry_side": [r.entry_side.value for r in rows],
            "event_kind": [r.event_kind.value for r in rows],
            "upper_channel": [r.upper_channel for r in rows],
            "lower_channel": [r.lower_channel for r in rows],
        },
        index=data.index,
    )


__all__ = [
    "BASELINE_ID_V1",
    "BASELINE_STRATEGY_ID_V1",
    "CHANNEL_LOOKBACK_BARS_V1",
    "SHARED_CHANNEL_CORE_OWNER_V1",
    "UnconditionalChannelBreakoutBarResultV1",
    "generate_unconditional_20_bar_price_channel_breakout_event_series_v1",
    "generate_unconditional_20_bar_price_channel_breakout_events_v1",
]
