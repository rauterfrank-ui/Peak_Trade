"""
Shadow Pipeline Data Models.

Immutable Dataclasses für Ticks und OHLCV Bars.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Tick:
    """
    Ein einzelner Trade Tick.

    Attributes:
        ts_ms: UTC Timestamp in Millisekunden
        price: Trade Price
        volume: Trade Volume
        symbol: Symbol (z.B. "XBT/EUR", "BTC-EUR")
        source: Datenquelle (default: "kraken_ws")
    """

    ts_ms: int
    price: float
    volume: float
    symbol: str
    source: str = "kraken_ws"

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError(f"Invalid price: {self.price}")
        if self.volume <= 0:
            raise ValueError(f"Invalid volume: {self.volume}")
        if self.ts_ms <= 0:
            raise ValueError(f"Invalid timestamp: {self.ts_ms}")


@dataclass(frozen=True)
class Bar:
    """
    OHLCV Bar für einen Timeframe.

    Attributes:
        start_ts_ms: Bar Start (inklusiv)
        end_ts_ms: Bar End (exklusiv)
        open: Open Price (erster Tick nach ts_ms sort)
        high: High Price
        low: Low Price
        close: Close Price (letzter Tick nach ts_ms sort)
        volume: Summe aller Volumes
        vwap: Volume-Weighted Average Price (optional)
        symbol: Symbol
        timeframe: Timeframe String ("1m", "5m", "1h")
    """

    start_ts_ms: int
    end_ts_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Union[float, None]
    symbol: str
    timeframe: str

    def __post_init__(self) -> None:
        if self.start_ts_ms >= self.end_ts_ms:
            raise ValueError(f"Invalid bar times: start={self.start_ts_ms} >= end={self.end_ts_ms}")
        if any(p <= 0 for p in [self.open, self.high, self.low, self.close]):
            raise ValueError("OHLC prices must be > 0")
        if self.volume < 0:
            raise ValueError(f"Invalid volume: {self.volume}")
