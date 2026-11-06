"""Shared 20-bar high/low price-channel breakout core v1.

Used identically by VOLATILITY_COMPRESSION_BREAKOUT_V1 and
UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1.

Bound semantics (measurement contract directional_entry):
- channel_lookback_completed_bars = 20
- trigger bar excluded from channel window
- upper_channel = max(high of prior 20 completed bars)
- lower_channel = min(low of prior 20 completed bars)
- LONG iff close strictly above upper_channel
- SHORT iff close strictly below lower_channel
- LONG and SHORT mutually exclusive; ambiguity → NONE (fail-closed)
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

CHANNEL_LOOKBACK_COMPLETED_BARS_V1 = 20
PRICE_CHANNEL_BREAKOUT_CORE_OWNER = "research.price_channel_breakout_core_v1"
PRICE_CHANNEL_BREAKOUT_CORE_VERSION = "v1"


class PriceChannelBreakSideV1(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


def compute_prior_high_low_channel_bounds_v1(
    high: pd.Series,
    low: pd.Series,
    *,
    lookback: int = CHANNEL_LOOKBACK_COMPLETED_BARS_V1,
) -> tuple[pd.Series, pd.Series]:
    """Prior completed-bar high/low channel bounds (current bar excluded)."""
    if lookback < 1:
        raise ValueError("channel_lookback_below_minimum")
    upper = high.shift(1).rolling(window=lookback, min_periods=lookback).max()
    lower = low.shift(1).rolling(window=lookback, min_periods=lookback).min()
    return upper, lower


def classify_price_channel_break_v1(
    close: float,
    upper_channel: float,
    lower_channel: float,
) -> PriceChannelBreakSideV1:
    """Classify a single-bar channel break; ambiguity fails closed to NONE."""
    if not np.isfinite(close) or not np.isfinite(upper_channel) or not np.isfinite(lower_channel):
        return PriceChannelBreakSideV1.NONE
    long_break = close > upper_channel
    short_break = close < lower_channel
    if long_break and short_break:
        return PriceChannelBreakSideV1.NONE
    if long_break:
        return PriceChannelBreakSideV1.LONG
    if short_break:
        return PriceChannelBreakSideV1.SHORT
    return PriceChannelBreakSideV1.NONE


def compute_price_channel_break_series_v1(
    data: pd.DataFrame,
    *,
    lookback: int = CHANNEL_LOOKBACK_COMPLETED_BARS_V1,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.Series:
    """Vectorized channel-break side series (LONG/SHORT/NONE as strings)."""
    for col in (high_col, low_col, close_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")
    upper, lower = compute_prior_high_low_channel_bounds_v1(
        data[high_col].astype(float),
        data[low_col].astype(float),
        lookback=lookback,
    )
    close = data[close_col].astype(float)
    out: list[str] = []
    for i in range(len(data)):
        c = float(close.iloc[i]) if np.isfinite(close.iloc[i]) else float("nan")
        u = float(upper.iloc[i]) if np.isfinite(upper.iloc[i]) else float("nan")
        lo = float(lower.iloc[i]) if np.isfinite(lower.iloc[i]) else float("nan")
        out.append(classify_price_channel_break_v1(c, u, lo).value)
    return pd.Series(out, index=data.index, dtype="object", name="channel_break_side")


def channel_bounds_at_index_v1(
    upper: pd.Series,
    lower: pd.Series,
    index_pos: int,
) -> tuple[Optional[float], Optional[float]]:
    """Return finite channel bounds at index or (None, None) if incomplete."""
    if index_pos < 0 or index_pos >= len(upper):
        return None, None
    u = upper.iloc[index_pos]
    lo = lower.iloc[index_pos]
    if not np.isfinite(u) or not np.isfinite(lo):
        return None, None
    return float(u), float(lo)


__all__ = [
    "CHANNEL_LOOKBACK_COMPLETED_BARS_V1",
    "PRICE_CHANNEL_BREAKOUT_CORE_OWNER",
    "PRICE_CHANNEL_BREAKOUT_CORE_VERSION",
    "PriceChannelBreakSideV1",
    "channel_bounds_at_index_v1",
    "classify_price_channel_break_v1",
    "compute_prior_high_low_channel_bounds_v1",
    "compute_price_channel_break_series_v1",
]
