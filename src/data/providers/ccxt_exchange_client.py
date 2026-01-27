"""
ccxt Exchange Client (Provider Module)
======================================

Dieses Modul ist absichtlich unter src/data/providers/ platziert, damit ccxt
als optionale Dependency ausschließlich in Provider-Modulen importiert wird.

Read-only: keine Order-Platzierung.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import ccxt
import pandas as pd

from src.exchange.base import Balance, Ticker


class CcxtExchangeClient:
    """
    Read-only ccxt-basierter Exchange-Client (Provider-Implementierung).

    Diese Klasse entspricht der bisherigen API aus `src.exchange.ccxt_client`.
    """

    def __init__(
        self,
        exchange_id: str,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        *,
        enable_rate_limit: bool = True,
        sandbox: bool = False,
        extra_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not hasattr(ccxt, exchange_id):
            available = [x for x in dir(ccxt) if not x.startswith("_") and x.islower()]
            raise ValueError(
                f"Unknown ccxt exchange id: {exchange_id!r}. "
                f"Available: {', '.join(available[:10])}... (and {len(available) - 10} more)"
            )

        klass = getattr(ccxt, exchange_id)
        config: Dict[str, Any] = {"enableRateLimit": enable_rate_limit}
        if extra_config:
            config.update(extra_config)

        self._exchange: ccxt.Exchange = klass(config)

        if api_key:
            self._exchange.apiKey = api_key
        if secret:
            self._exchange.secret = secret

        if sandbox:
            try:
                if hasattr(self._exchange, "set_sandbox_mode"):
                    self._exchange.set_sandbox_mode(True)
            except Exception:
                pass

        # ccxt types are not available/stable across versions; keep runtime behavior, relax typing.
        setattr(self._exchange, "checkRequiredCredentials", False)

    @property
    def exchange(self) -> ccxt.Exchange:
        return self._exchange

    def get_name(self) -> str:
        return str(self._exchange.id)

    def load_markets(self) -> Any:
        """Load markets via ccxt (may hit network depending on ccxt cache)."""
        return self._exchange.load_markets()

    def fetch_ticker(self, symbol: str) -> Ticker:
        raw = self._exchange.fetch_ticker(symbol)
        return Ticker(
            symbol=raw.get("symbol", symbol),
            last=float(raw["last"]) if raw.get("last") is not None else None,
            bid=float(raw["bid"]) if raw.get("bid") is not None else None,
            ask=float(raw["ask"]) if raw.get("ask") is not None else None,
            timestamp=raw.get("timestamp"),
            raw=raw,
        )

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        since: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        ohlcv = self._exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
        )

        if not ohlcv:
            return pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"],  # pyright: ignore[reportArgumentType]
                index=pd.DatetimeIndex([], name="timestamp", tz="UTC"),
            )

        df = pd.DataFrame(
            ohlcv,
            columns=["timestamp", "open", "high", "low", "close", "volume"],  # pyright: ignore[reportArgumentType]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.set_index("timestamp")
        return df

    def fetch_balance(self) -> Balance:
        raw = self._exchange.fetch_balance()

        def to_float_dict(d: Optional[Dict]) -> Dict[str, float]:
            if not d:
                return {}
            return {k: float(v) for k, v in d.items() if v is not None}

        return Balance(
            free=to_float_dict(raw.get("free")),
            used=to_float_dict(raw.get("used")),
            total=to_float_dict(raw.get("total")),
            raw=raw,
        )

    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        if symbol:
            return self._exchange.fetch_open_orders(symbol)
        return self._exchange.fetch_open_orders()

    def fetch_markets(self) -> List[Dict[str, Any]]:
        return self._exchange.fetch_markets()

    def get_available_timeframes(self) -> List[str]:
        return list(self._exchange.timeframes.keys()) if self._exchange.timeframes else []

    def __repr__(self) -> str:
        has_key = "with API-Key" if self._exchange.apiKey else "no API-Key"
        return f"<CcxtExchangeClient({self._exchange.id}, {has_key})>"


__all__ = ["CcxtExchangeClient"]
