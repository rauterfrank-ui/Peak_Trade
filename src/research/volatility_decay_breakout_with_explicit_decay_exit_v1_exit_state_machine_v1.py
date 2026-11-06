"""Deterministic exit state machine for VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1.

Ex-ante, first-event-wins exits for LONG and SHORT independently.
No lookahead. No synthetic fills solely to pair trades. No PnL computation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

SideV1 = Literal["LONG", "SHORT"]

INITIAL_STOP_ATR_MULTIPLE_V1 = 1.5
TRAILING_STOP_ATR_MULTIPLE_V1 = 2.0
SIGNAL_EXIT_PERCENTILE_INCLUSIVE_MIN_V1 = 0.70
REGIME_INVALIDATION_PERCENTILE_LT_V1 = 0.50
TIME_EXIT_MAX_BARS_V1 = 48
COOLDOWN_BARS_AFTER_EXIT_V1 = 0
SIGNAL_LAG_BARS_V1 = 1
MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1 = TIME_EXIT_MAX_BARS_V1

EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1: tuple[str, ...] = (
    "INITIAL_STOP",
    "TRAILING_STOP",
    "SIGNAL_EXIT",
    "REGIME_INVALIDATION",
    "TIME_EXIT",
    "END_OF_INSTRUMENT_LIQUIDATION",
    "END_OF_PANEL_LIQUIDATION",
)

_PRECEDENCE_RANK = {name: i for i, name in enumerate(EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1)}


class ExplicitDecayExitReasonV1(str, Enum):
    INITIAL_STOP = "INITIAL_STOP"
    TRAILING_STOP = "TRAILING_STOP"
    SIGNAL_EXIT = "SIGNAL_EXIT"
    REGIME_INVALIDATION = "REGIME_INVALIDATION"
    TIME_EXIT = "TIME_EXIT"
    END_OF_INSTRUMENT_LIQUIDATION = "END_OF_INSTRUMENT_LIQUIDATION"
    END_OF_PANEL_LIQUIDATION = "END_OF_PANEL_LIQUIDATION"


@dataclass(frozen=True)
class OpenPositionStateV1:
    side: SideV1
    fill_index: int
    entry_price: float
    stop_price: float
    extreme_price: float  # peak for LONG, trough for SHORT


@dataclass(frozen=True)
class ExitDecisionV1:
    reason: ExplicitDecayExitReasonV1
    exit_index: int
    exit_price: float
    side: SideV1


def entry_exit_reachable_ex_ante_v1(*, signal_index: int, series_length: int) -> bool:
    """True iff fill bar exists and TIME_EXIT is reachable without terminal liquidation."""
    fill_i = signal_index + SIGNAL_LAG_BARS_V1
    if fill_i >= series_length:
        return False
    # TIME_EXIT fires when held >= max_bars at bar j = fill_i + max_bars.
    return (fill_i + MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1) < series_length


def open_position_from_fill_v1(
    *,
    side: SideV1,
    fill_index: int,
    entry_price: float,
    atr_at_fill: float,
) -> OpenPositionStateV1:
    if not (atr_at_fill == atr_at_fill) or atr_at_fill <= 0:
        raise ValueError("ATR_INVALID_AT_FILL")
    if side == "LONG":
        stop = entry_price - INITIAL_STOP_ATR_MULTIPLE_V1 * atr_at_fill
        extreme = entry_price
    else:
        stop = entry_price + INITIAL_STOP_ATR_MULTIPLE_V1 * atr_at_fill
        extreme = entry_price
    return OpenPositionStateV1(
        side=side,
        fill_index=fill_index,
        entry_price=entry_price,
        stop_price=stop,
        extreme_price=extreme,
    )


def _update_extreme(position: OpenPositionStateV1, *, high: float, low: float) -> float:
    if position.side == "LONG":
        return max(position.extreme_price, high)
    return min(position.extreme_price, low)


def evaluate_exit_on_bar_v1(
    position: OpenPositionStateV1,
    *,
    bar_index: int,
    high: float,
    low: float,
    close: float,
    atr: Optional[float],
    percentile_rank: Optional[float],
    is_last_instrument_bar: bool,
    is_last_panel_bar: bool,
) -> tuple[Optional[ExitDecisionV1], OpenPositionStateV1]:
    """Evaluate first-event-wins exit on a completed bar after fill.

    Exit evaluation is forbidden on the fill bar for non-terminal reasons.
    Missing OHLC fails closed (no invented prices).
    """
    if any(v != v for v in (high, low, close)):  # NaN check
        raise ValueError("MISSING_OHLC_FAIL_CLOSED")

    if bar_index <= position.fill_index:
        if bar_index == position.fill_index and (is_last_instrument_bar or is_last_panel_bar):
            raise ValueError("SAME_BAR_FILL_EXIT_FORBIDDEN")
        raise ValueError("EXIT_BEFORE_OR_ON_FILL_FORBIDDEN")

    extreme = _update_extreme(position, high=high, low=low)
    updated = OpenPositionStateV1(
        side=position.side,
        fill_index=position.fill_index,
        entry_price=position.entry_price,
        stop_price=position.stop_price,
        extreme_price=extreme,
    )

    candidates: list[tuple[int, ExplicitDecayExitReasonV1, float]] = []

    if position.side == "LONG":
        if low <= position.stop_price:
            candidates.append(
                (
                    _PRECEDENCE_RANK["INITIAL_STOP"],
                    ExplicitDecayExitReasonV1.INITIAL_STOP,
                    position.stop_price,
                )
            )
        if atr is not None and atr == atr and atr > 0:
            trail = extreme - TRAILING_STOP_ATR_MULTIPLE_V1 * atr
            if low <= trail:
                candidates.append(
                    (
                        _PRECEDENCE_RANK["TRAILING_STOP"],
                        ExplicitDecayExitReasonV1.TRAILING_STOP,
                        trail,
                    )
                )
    else:
        if high >= position.stop_price:
            candidates.append(
                (
                    _PRECEDENCE_RANK["INITIAL_STOP"],
                    ExplicitDecayExitReasonV1.INITIAL_STOP,
                    position.stop_price,
                )
            )
        if atr is not None and atr == atr and atr > 0:
            trail = extreme + TRAILING_STOP_ATR_MULTIPLE_V1 * atr
            if high >= trail:
                candidates.append(
                    (
                        _PRECEDENCE_RANK["TRAILING_STOP"],
                        ExplicitDecayExitReasonV1.TRAILING_STOP,
                        trail,
                    )
                )

    if percentile_rank is not None and percentile_rank == percentile_rank:
        if percentile_rank >= SIGNAL_EXIT_PERCENTILE_INCLUSIVE_MIN_V1:
            candidates.append(
                (_PRECEDENCE_RANK["SIGNAL_EXIT"], ExplicitDecayExitReasonV1.SIGNAL_EXIT, close)
            )
        if percentile_rank < REGIME_INVALIDATION_PERCENTILE_LT_V1:
            candidates.append(
                (
                    _PRECEDENCE_RANK["REGIME_INVALIDATION"],
                    ExplicitDecayExitReasonV1.REGIME_INVALIDATION,
                    close,
                )
            )

    held = bar_index - position.fill_index
    if held >= TIME_EXIT_MAX_BARS_V1:
        candidates.append(
            (_PRECEDENCE_RANK["TIME_EXIT"], ExplicitDecayExitReasonV1.TIME_EXIT, close)
        )

    if is_last_instrument_bar:
        candidates.append(
            (
                _PRECEDENCE_RANK["END_OF_INSTRUMENT_LIQUIDATION"],
                ExplicitDecayExitReasonV1.END_OF_INSTRUMENT_LIQUIDATION,
                close,
            )
        )
    if is_last_panel_bar:
        candidates.append(
            (
                _PRECEDENCE_RANK["END_OF_PANEL_LIQUIDATION"],
                ExplicitDecayExitReasonV1.END_OF_PANEL_LIQUIDATION,
                close,
            )
        )

    if not candidates:
        return None, updated

    candidates.sort(key=lambda t: t[0])
    _, reason, price = candidates[0]
    return (
        ExitDecisionV1(
            reason=reason,
            exit_index=bar_index,
            exit_price=float(price),
            side=position.side,
        ),
        updated,
    )


__all__ = [
    "COOLDOWN_BARS_AFTER_EXIT_V1",
    "EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1",
    "ExitDecisionV1",
    "ExplicitDecayExitReasonV1",
    "INITIAL_STOP_ATR_MULTIPLE_V1",
    "MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1",
    "OpenPositionStateV1",
    "REGIME_INVALIDATION_PERCENTILE_LT_V1",
    "SIGNAL_EXIT_PERCENTILE_INCLUSIVE_MIN_V1",
    "SIGNAL_LAG_BARS_V1",
    "TIME_EXIT_MAX_BARS_V1",
    "TRAILING_STOP_ATR_MULTIPLE_V1",
    "entry_exit_reachable_ex_ante_v1",
    "evaluate_exit_on_bar_v1",
    "open_position_from_fill_v1",
]
