"""Venue-neutral in-memory candle types and a fake candle source for tests.

This module does not perform exchange I/O and is not a venue adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

import pandas as pd


@dataclass
class LiveCandle:
    """A single OHLCV candle used by shadow/paper session tests."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_complete: bool = True

    def to_series(self) -> pd.Series:
        return pd.Series(
            {
                "open": self.open,
                "high": self.high,
                "low": self.low,
                "close": self.close,
                "volume": self.volume,
            },
            name=self.timestamp,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "is_complete": self.is_complete,
        }


@dataclass
class LiveExchangeConfig:
    """Explicit live-exchange connection settings. No implicit venue host."""

    name: str
    base_url: str
    use_sandbox: bool = True
    rate_limit_ms: int = 1000
    max_retries: int = 3
    retry_delay_seconds: float = 5.0


@dataclass
class ShadowPaperConfig:
    """Shadow/paper session settings. Simulation only; not a venue client."""

    enabled: bool = True
    mode: str = "paper"
    symbol: str = "BTC/EUR"
    timeframe: str = "1m"
    poll_interval_seconds: float = 60.0
    warmup_candles: int = 200
    start_balance: float = 10000.0
    position_fraction: float = 0.1
    fee_rate: float = 0.0026
    slippage_bps: float = 5.0


class CandleSource(Protocol):
    """Protocol for candle data sources used by shadow/paper sessions."""

    def warmup(self) -> List[LiveCandle]: ...

    def poll_latest(self) -> Optional[LiveCandle]: ...

    def get_buffer(self) -> pd.DataFrame: ...

    def get_latest_price(self) -> Optional[float]: ...


class FakeCandleSource:
    """In-memory candle source for tests. No network and no venue I/O."""

    def __init__(
        self,
        candles: Optional[List[LiveCandle]] = None,
        symbol: str = "BTC/EUR",
    ) -> None:
        self._candles = list(candles) if candles else []
        self._index = 0
        self._buffer: List[LiveCandle] = []
        self.symbol = symbol

    def warmup(self) -> List[LiveCandle]:
        warmup_count = max(1, int(len(self._candles) * 0.8))
        self._buffer = self._candles[:warmup_count]
        self._index = warmup_count
        return list(self._buffer)

    def poll_latest(self) -> Optional[LiveCandle]:
        if self._index >= len(self._candles):
            return None
        candle = self._candles[self._index]
        self._buffer.append(candle)
        self._index += 1
        return candle

    def poll(self) -> None:
        self.poll_latest()

    def get_buffer(self) -> pd.DataFrame:
        if not self._buffer:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        data = [c.to_dict() for c in self._buffer]
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        df.drop(columns=["is_complete"], inplace=True, errors="ignore")
        return df

    def get_latest_price(self) -> Optional[float]:
        if not self._buffer:
            return None
        return self._buffer[-1].close

    def get_latest_candle(self) -> Optional[LiveCandle]:
        if not self._buffer:
            return None
        return self._buffer[-1]

    def reset(self) -> None:
        self._index = 0
        self._buffer.clear()


def load_shadow_paper_config(cfg: Any) -> ShadowPaperConfig:
    return ShadowPaperConfig(
        enabled=cfg.get("shadow_paper.enabled", True),
        mode=cfg.get("shadow_paper.mode", "paper"),
        symbol=cfg.get("shadow_paper.symbol", "BTC/EUR"),
        timeframe=cfg.get("shadow_paper.timeframe", "1m"),
        poll_interval_seconds=cfg.get("shadow_paper.poll_interval_seconds", 60.0),
        warmup_candles=cfg.get("shadow_paper.warmup_candles", 200),
        start_balance=cfg.get("shadow_paper.start_balance", 10000.0),
        position_fraction=cfg.get("shadow_paper.position_fraction", 0.1),
        fee_rate=cfg.get("shadow_paper.fee_rate", 0.0026),
        slippage_bps=cfg.get("shadow_paper.slippage_bps", 5.0),
    )


def load_live_exchange_config(cfg: Any) -> LiveExchangeConfig:
    name = cfg.get("live_exchange.name")
    if name is None or str(name).strip() == "":
        raise ValueError("live_exchange.name is required; no implicit venue default is authorized")
    base_url = cfg.get("live_exchange.base_url")
    if base_url is None or str(base_url).strip() == "":
        raise ValueError("live_exchange.base_url is required; no implicit venue host is authorized")
    return LiveExchangeConfig(
        name=str(name).strip(),
        use_sandbox=cfg.get("live_exchange.use_sandbox", True),
        base_url=str(base_url).strip(),
        rate_limit_ms=cfg.get("live_exchange.rate_limit_ms", 1000),
        max_retries=cfg.get("live_exchange.max_retries", 3),
        retry_delay_seconds=cfg.get("live_exchange.retry_delay_seconds", 5.0),
    )
