"""
OHLCV Builder — Aggregiert Ticks zu Bars.

Deterministisch: Ticks werden nach ts_ms sortiert, Bars idempotent.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Union

from src.data.shadow.models import Bar, Tick


def tf_to_ms(timeframe: str) -> int:
    """
    Konvertiert Timeframe String zu Millisekunden.

    Args:
        timeframe: "1m", "5m", "1h", etc.

    Returns:
        Millisekunden

    Raises:
        ValueError: Wenn Format ungültig
    """
    timeframe = timeframe.lower().strip()

    # Parse: <number><unit>
    if not timeframe:
        raise ValueError("Empty timeframe")

    unit = timeframe[-1]
    try:
        number = int(timeframe[:-1])
    except ValueError:
        raise ValueError(f"Invalid timeframe format: {timeframe}")

    if unit == "s":
        return number * 1000
    elif unit == "m":
        return number * 60 * 1000
    elif unit == "h":
        return number * 60 * 60 * 1000
    elif unit == "d":
        return number * 24 * 60 * 60 * 1000
    else:
        raise ValueError(f"Unknown timeframe unit: {unit}")


class OHLCVBuilder:
    """
    Baut OHLCV Bars aus Ticks.

    Deterministisch: Bars sind idempotent bei wiederholtem add_ticks.
    """

    def __init__(self, symbol: str, timeframe: str) -> None:
        """
        Args:
            symbol: Symbol (muss mit Tick.symbol matchen)
            timeframe: "1m", "5m", "1h"
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.tf_ms = tf_to_ms(timeframe)

        # bar_start_ts → list[Tick]
        self._bars: dict[int, list[Tick]] = defaultdict(list)

    def add_ticks(self, ticks: list[Tick]) -> None:
        """
        Fügt Ticks hinzu.

        Args:
            ticks: Liste von Ticks (müssen self.symbol matchen)
        """
        for tick in ticks:
            # Symbol-Filter
            if tick.symbol != self.symbol:
                continue

            # Bar Start berechnen
            bar_start = (tick.ts_ms // self.tf_ms) * self.tf_ms

            self._bars[bar_start].append(tick)

    def finalize(self) -> list[Bar]:
        """
        Finalisiert Bars und gibt sortierte Liste zurück.

        Returns:
            List[Bar]: Sortiert nach start_ts_ms
        """
        bars: list[Bar] = []

        for bar_start, ticks in self._bars.items():
            if not ticks:
                continue

            # Sort ticks by ts_ms (deterministisch)
            sorted_ticks = sorted(ticks, key=lambda t: t.ts_ms)

            # OHLCV
            open_price = sorted_ticks[0].price
            close_price = sorted_ticks[-1].price
            high_price = max(t.price for t in sorted_ticks)
            low_price = min(t.price for t in sorted_ticks)

            # Volume + VWAP
            total_volume = sum(t.volume for t in sorted_ticks)
            vwap: Union[float, None] = None
            if total_volume > 0:
                weighted_sum = sum(t.price * t.volume for t in sorted_ticks)
                vwap = weighted_sum / total_volume

            bar = Bar(
                start_ts_ms=bar_start,
                end_ts_ms=bar_start + self.tf_ms,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=total_volume,
                vwap=vwap,
                symbol=self.symbol,
                timeframe=self.timeframe,
            )
            bars.append(bar)

        # Sort bars by start
        bars.sort(key=lambda b: b.start_ts_ms)

        return bars
