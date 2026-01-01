"""
Bar Aggregator - Ticks → Bars (OHLCV)

Aggregates live ticks into OHLCV bars, matching backtest normalization.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from src.data.shadow.models import Bar, Tick

logger = logging.getLogger(__name__)


@dataclass
class BarBuffer:
    """
    Buffer for accumulating ticks into a bar.

    Attributes:
        start_ts_ms: Bar start timestamp
        end_ts_ms: Bar end timestamp
        open: First tick price
        high: Highest tick price
        low: Lowest tick price
        close: Last tick price
        volume: Accumulated volume
        vwap: Volume-weighted average price
        symbol: Symbol
        timeframe: Timeframe string
        tick_count: Number of ticks in buffer
    """

    start_ts_ms: int
    end_ts_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    vwap: Optional[float] = None
    symbol: str = ""
    timeframe: str = "1m"
    tick_count: int = 0

    def update(self, tick: Tick) -> None:
        """
        Update bar buffer with a new tick.

        Args:
            tick: New tick to incorporate
        """
        # Always update high/low/close
        if self.tick_count == 0:
            # First tick - initialize all values
            self.open = tick.price
            self.high = tick.price
            self.low = tick.price
        else:
            # Subsequent ticks - update high/low
            self.high = max(self.high, tick.price)
            self.low = min(self.low, tick.price)

        # Always update close and volume
        self.close = tick.price
        self.volume += tick.volume

        if self.tick_count == 0:
            self.symbol = tick.symbol

        self.tick_count += 1

        # Update VWAP (simplified)
        if self.volume > 0:
            self.vwap = self.close  # Simplified approximation

    def to_bar(self) -> Bar:
        """
        Convert buffer to a Bar.

        Returns:
            Bar object
        """
        return Bar(
            start_ts_ms=self.start_ts_ms,
            end_ts_ms=self.end_ts_ms,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            vwap=self.vwap,
            symbol=self.symbol,
            timeframe=self.timeframe,
        )


class BarAggregator:
    """
    Aggregates live ticks into OHLCV bars.

    Matches backtest normalization:
    - Same bar boundaries
    - Same OHLCV calculation
    - Same quality guarantees

    Usage:
        >>> aggregator = BarAggregator(timeframe_ms=60_000)  # 1 minute
        >>> for tick in ticks:
        ...     bar = aggregator.add_tick(tick)
        ...     if bar:
        ...         print(f"New bar: {bar}")
    """

    def __init__(
        self,
        timeframe_ms: int = 60_000,  # 1 minute default
        timeframe_str: str = "1m",
    ):
        """
        Args:
            timeframe_ms: Timeframe in milliseconds
            timeframe_str: Timeframe string (e.g., "1m", "5m", "1h")
        """
        self.timeframe_ms = timeframe_ms
        self.timeframe_str = timeframe_str

        # Buffer per symbol
        self._buffers: dict[str, BarBuffer] = {}

        # Stats
        self._bars_emitted = 0
        self._ticks_processed = 0

    def add_tick(self, tick: Tick) -> Optional[Bar]:
        """
        Add a tick and potentially emit a completed bar.

        Args:
            tick: Tick to add

        Returns:
            Bar if current bar is complete, None otherwise
        """
        self._ticks_processed += 1

        symbol = tick.symbol

        # Get or create buffer for this symbol
        if symbol not in self._buffers:
            # Create new buffer aligned to timeframe
            bar_start_ms = self._align_to_timeframe(tick.ts_ms)
            bar_end_ms = bar_start_ms + self.timeframe_ms

            self._buffers[symbol] = BarBuffer(
                start_ts_ms=bar_start_ms,
                end_ts_ms=bar_end_ms,
                open=0.0,  # Will be set by first update
                high=0.0,
                low=0.0,
                close=0.0,
                volume=0.0,
                symbol=symbol,
                timeframe=self.timeframe_str,
                tick_count=0,
            )

        buffer = self._buffers[symbol]

        # Check if tick belongs to current bar
        if tick.ts_ms < buffer.end_ts_ms:
            # Tick belongs to current bar
            buffer.update(tick)
            return None
        else:
            # Tick belongs to next bar → emit current bar
            completed_bar = buffer.to_bar()
            self._bars_emitted += 1

            # Create new buffer for next bar
            bar_start_ms = self._align_to_timeframe(tick.ts_ms)
            bar_end_ms = bar_start_ms + self.timeframe_ms

            self._buffers[symbol] = BarBuffer(
                start_ts_ms=bar_start_ms,
                end_ts_ms=bar_end_ms,
                open=0.0,
                high=0.0,
                low=0.0,
                close=0.0,
                volume=0.0,
                symbol=symbol,
                timeframe=self.timeframe_str,
                tick_count=0,
            )
            self._buffers[symbol].update(tick)

            return completed_bar

    def flush(self, symbol: Optional[str] = None) -> list[Bar]:
        """
        Flush pending bars (force emit current buffers).

        Args:
            symbol: Specific symbol to flush, or None to flush all

        Returns:
            List of flushed bars
        """
        bars = []

        if symbol:
            if symbol in self._buffers:
                buffer = self._buffers[symbol]
                if buffer.tick_count > 0:
                    bars.append(buffer.to_bar())
                    self._bars_emitted += 1
                del self._buffers[symbol]
        else:
            # Flush all symbols
            for sym, buffer in self._buffers.items():
                if buffer.tick_count > 0:
                    bars.append(buffer.to_bar())
                    self._bars_emitted += 1
            self._buffers.clear()

        return bars

    def _align_to_timeframe(self, ts_ms: int) -> int:
        """
        Align timestamp to timeframe boundary.

        Args:
            ts_ms: Timestamp in milliseconds

        Returns:
            Aligned timestamp (start of bar)
        """
        return (ts_ms // self.timeframe_ms) * self.timeframe_ms

    def get_stats(self) -> dict[str, int]:
        """Get aggregator statistics."""
        return {
            "ticks_processed": self._ticks_processed,
            "bars_emitted": self._bars_emitted,
            "active_buffers": len(self._buffers),
        }
