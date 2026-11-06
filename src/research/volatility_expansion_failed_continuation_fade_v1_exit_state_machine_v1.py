"""Deterministic exit state machine for VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1.

Ex-ante, first-event-wins exits for LONG and SHORT independently.
No trailing stop. Impulse-reclaim invalidation uses the failed impulse extreme.
No lookahead. No synthetic fills solely to pair trades. No PnL computation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

SideV1 = Literal["LONG", "SHORT"]

INITIAL_STOP_ATR_MULTIPLE_V1 = 1.5
REGIME_INVALIDATION_PERCENTILE_LT_V1 = 0.40
TIME_EXIT_MAX_BARS_V1 = 48
COOLDOWN_BARS_AFTER_EXIT_V1 = 0
SIGNAL_LAG_BARS_V1 = 1
MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1 = TIME_EXIT_MAX_BARS_V1
TRAILING_STOP_FORBIDDEN_V1 = True

EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1: tuple[str, ...] = (
    "INITIAL_STOP",
    "IMPULSE_RECLAIM_INVALIDATION",
    "REGIME_INVALIDATION",
    "TIME_EXIT",
    "END_OF_INSTRUMENT_LIQUIDATION",
    "END_OF_PANEL_LIQUIDATION",
)

_PRECEDENCE_RANK = {name: i for i, name in enumerate(EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1)}


class VefcfExitReasonV1(str, Enum):
    INITIAL_STOP = "INITIAL_STOP"
    IMPULSE_RECLAIM_INVALIDATION = "IMPULSE_RECLAIM_INVALIDATION"
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
    failed_impulse_extreme: float


@dataclass(frozen=True)
class ExitDecisionV1:
    reason: VefcfExitReasonV1
    exit_index: int
    exit_price: float
    side: SideV1


def entry_exit_reachable_ex_ante_v1(*, signal_index: int, series_length: int) -> bool:
    """True iff fill bar exists and TIME_EXIT is reachable without terminal liquidation."""
    fill_i = signal_index + SIGNAL_LAG_BARS_V1
    if fill_i >= series_length:
        return False
    return (fill_i + MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1) < series_length


def open_position_from_fill_v1(
    *,
    side: SideV1,
    fill_index: int,
    entry_price: float,
    atr_at_fill: float,
    failed_impulse_extreme: float,
) -> OpenPositionStateV1:
    if not (atr_at_fill == atr_at_fill) or atr_at_fill <= 0:
        raise ValueError("ATR_INVALID_AT_FILL")
    if not (failed_impulse_extreme == failed_impulse_extreme):
        raise ValueError("FAILED_IMPULSE_EXTREME_INVALID")
    if side == "LONG":
        stop = entry_price - INITIAL_STOP_ATR_MULTIPLE_V1 * atr_at_fill
    else:
        stop = entry_price + INITIAL_STOP_ATR_MULTIPLE_V1 * atr_at_fill
    return OpenPositionStateV1(
        side=side,
        fill_index=fill_index,
        entry_price=entry_price,
        stop_price=stop,
        failed_impulse_extreme=float(failed_impulse_extreme),
    )


def evaluate_exit_on_bar_v1(
    position: OpenPositionStateV1,
    *,
    bar_index: int,
    high: float,
    low: float,
    close: float,
    percentile_rank: Optional[float],
    is_last_instrument_bar: bool,
    is_last_panel_bar: bool,
) -> tuple[Optional[ExitDecisionV1], OpenPositionStateV1]:
    """Evaluate first-event-wins exit on a completed bar after fill.

    Exit evaluation is forbidden on the fill bar for non-terminal reasons.
    Missing OHLC fails closed (no invented prices). Trailing is forbidden.

    Impulse reclaim (contract):
    - long fade: close strictly above failed_impulse_extreme
    - short fade: close strictly below failed_impulse_extreme
    """
    if any(v != v for v in (high, low, close)):  # NaN check
        raise ValueError("MISSING_OHLC_FAIL_CLOSED")

    if bar_index <= position.fill_index:
        if bar_index == position.fill_index and (is_last_instrument_bar or is_last_panel_bar):
            raise ValueError("SAME_BAR_FILL_EXIT_FORBIDDEN")
        raise ValueError("EXIT_BEFORE_OR_ON_FILL_FORBIDDEN")

    candidates: list[tuple[int, VefcfExitReasonV1, float]] = []

    if position.side == "LONG":
        if low <= position.stop_price:
            candidates.append(
                (
                    _PRECEDENCE_RANK["INITIAL_STOP"],
                    VefcfExitReasonV1.INITIAL_STOP,
                    position.stop_price,
                )
            )
        if close > position.failed_impulse_extreme:
            candidates.append(
                (
                    _PRECEDENCE_RANK["IMPULSE_RECLAIM_INVALIDATION"],
                    VefcfExitReasonV1.IMPULSE_RECLAIM_INVALIDATION,
                    close,
                )
            )
    else:
        if high >= position.stop_price:
            candidates.append(
                (
                    _PRECEDENCE_RANK["INITIAL_STOP"],
                    VefcfExitReasonV1.INITIAL_STOP,
                    position.stop_price,
                )
            )
        if close < position.failed_impulse_extreme:
            candidates.append(
                (
                    _PRECEDENCE_RANK["IMPULSE_RECLAIM_INVALIDATION"],
                    VefcfExitReasonV1.IMPULSE_RECLAIM_INVALIDATION,
                    close,
                )
            )

    if percentile_rank is not None and percentile_rank == percentile_rank:
        if percentile_rank < REGIME_INVALIDATION_PERCENTILE_LT_V1:
            candidates.append(
                (
                    _PRECEDENCE_RANK["REGIME_INVALIDATION"],
                    VefcfExitReasonV1.REGIME_INVALIDATION,
                    close,
                )
            )

    held = bar_index - position.fill_index
    if held >= TIME_EXIT_MAX_BARS_V1:
        candidates.append((_PRECEDENCE_RANK["TIME_EXIT"], VefcfExitReasonV1.TIME_EXIT, close))

    if is_last_instrument_bar:
        candidates.append(
            (
                _PRECEDENCE_RANK["END_OF_INSTRUMENT_LIQUIDATION"],
                VefcfExitReasonV1.END_OF_INSTRUMENT_LIQUIDATION,
                close,
            )
        )
    if is_last_panel_bar:
        candidates.append(
            (
                _PRECEDENCE_RANK["END_OF_PANEL_LIQUIDATION"],
                VefcfExitReasonV1.END_OF_PANEL_LIQUIDATION,
                close,
            )
        )

    if not candidates:
        return None, position

    candidates.sort(key=lambda t: t[0])
    _, reason, price = candidates[0]
    return (
        ExitDecisionV1(
            reason=reason,
            exit_index=bar_index,
            exit_price=price,
            side=position.side,
        ),
        position,
    )


__all__ = [
    "COOLDOWN_BARS_AFTER_EXIT_V1",
    "EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1",
    "INITIAL_STOP_ATR_MULTIPLE_V1",
    "MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1",
    "REGIME_INVALIDATION_PERCENTILE_LT_V1",
    "SIGNAL_LAG_BARS_V1",
    "TIME_EXIT_MAX_BARS_V1",
    "TRAILING_STOP_FORBIDDEN_V1",
    "ExitDecisionV1",
    "OpenPositionStateV1",
    "VefcfExitReasonV1",
    "entry_exit_reachable_ex_ante_v1",
    "evaluate_exit_on_bar_v1",
    "open_position_from_fill_v1",
]
