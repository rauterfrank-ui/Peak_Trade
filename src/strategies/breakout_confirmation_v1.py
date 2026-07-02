"""
Deterministic Donchian breakout confirmation v1 (offline research architecture).

Fail-closed, bar-close-only confirmation semantics for composite signal binding.
No runtime, order, risk, sizing, or promotion authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pandas as pd

CONFIRMATION_EPOCHS_V1 = 1
CONFIRMATION_OWNER = "src.strategies.breakout_confirmation_v1"


class BreakoutConfirmationError(ValueError):
    """Fail-closed breakout confirmation error."""


class PendingDirection(str, Enum):
    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class PendingCandidateV1:
    direction: PendingDirection
    boundary_reference: float
    candidate_index_pos: int


def _fail_closed(condition: bool, reason: str) -> None:
    if condition:
        raise BreakoutConfirmationError(reason)


def compute_donchian_channel_bounds_v1(
    price: pd.Series,
    *,
    lookback: int,
) -> tuple[pd.Series, pd.Series]:
    """Donchian bounds from prior finalized bars only (excludes current bar)."""
    _fail_closed(lookback < 2, "lookback_below_minimum")
    rolling_high = price.shift(1).rolling(lookback, min_periods=lookback).max()
    rolling_low = price.shift(1).rolling(lookback, min_periods=lookback).min()
    return rolling_high, rolling_low


def _bar_is_finalized(data: pd.DataFrame, index_pos: int) -> bool:
    if "is_final" not in data.columns:
        return True
    value = data["is_final"].iloc[index_pos]
    if pd.isna(value):
        return False
    return bool(value)


def _scalar_value(series: pd.Series, index_pos: int) -> Optional[float]:
    value = series.iloc[index_pos]
    if pd.isna(value):
        return None
    return float(value)


def generate_confirmed_breakout_signals_v1(
    data: pd.DataFrame,
    *,
    lookback: int,
    price_col: str = "close",
    confirmation_epochs: int = CONFIRMATION_EPOCHS_V1,
) -> pd.Series:
    """
    Generate confirmed breakout position signals with immutable candidate boundaries.

    Semantics:
    - Breach on bar t creates a candidate only (no entry signal on t).
    - Confirmation on bar t+confirmation_epochs when close remains beyond bound reference.
    - Bound reference is frozen at candidate creation and never replaced by moving bands.
    - Opposite breach resets an open candidate.
    - Unfinalized bars never confirm or create candidates.
    """
    _fail_closed(price_col not in data.columns, f"price_col_missing:{price_col}")
    _fail_closed(confirmation_epochs != CONFIRMATION_EPOCHS_V1, "confirmation_epochs_not_allowed")
    _fail_closed(len(data.index) == 0, "bars_empty")
    if not isinstance(data.index, pd.DatetimeIndex):
        raise BreakoutConfirmationError("index_not_datetime")

    price = data[price_col].astype(float)
    rolling_high, rolling_low = compute_donchian_channel_bounds_v1(price, lookback=lookback)

    output = pd.Series(0, index=data.index, dtype="int64")
    position = 0
    pending: Optional[PendingCandidateV1] = None

    for index_pos in range(len(data.index)):
        if not _bar_is_finalized(data, index_pos):
            pending = None
            output.iloc[index_pos] = position
            continue

        close_value = _scalar_value(price, index_pos)
        high_bound = _scalar_value(rolling_high, index_pos)
        low_bound = _scalar_value(rolling_low, index_pos)
        if close_value is None or high_bound is None or low_bound is None:
            pending = None
            output.iloc[index_pos] = position
            continue

        if pending is not None:
            confirm_pos = pending.candidate_index_pos + confirmation_epochs
            if index_pos == confirm_pos:
                if pending.direction is PendingDirection.LONG:
                    if close_value >= pending.boundary_reference:
                        position = 1
                elif close_value <= pending.boundary_reference:
                    position = -1
                pending = None
            elif index_pos > confirm_pos:
                pending = None

        long_breach = close_value > high_bound
        short_breach = close_value < low_bound
        if long_breach and short_breach:
            pending = None
        elif long_breach:
            if pending is not None and pending.direction is PendingDirection.SHORT:
                pending = None
            pending = PendingCandidateV1(
                direction=PendingDirection.LONG,
                boundary_reference=high_bound,
                candidate_index_pos=index_pos,
            )
        elif short_breach:
            if pending is not None and pending.direction is PendingDirection.LONG:
                pending = None
            pending = PendingCandidateV1(
                direction=PendingDirection.SHORT,
                boundary_reference=low_bound,
                candidate_index_pos=index_pos,
            )

        output.iloc[index_pos] = position

    output.name = "signal"
    return output.astype(int)
