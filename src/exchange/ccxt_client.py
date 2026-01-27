# src/exchange/ccxt_client.py
"""
Peak_Trade CCXT Exchange Client
================================
Read-only Exchange-Client basierend auf ccxt.

Dieses Modul implementiert das `ExchangeClient`-Protokoll mit ccxt als Backend.
Alle Methoden sind ausschließlich lesend – keine Order-Platzierung!

Unterstützte Exchanges:
    Alle von ccxt unterstützten Exchanges (140+), z.B.:
    - kraken
    - binance
    - coinbasepro
    - bitstamp

Verwendung:
    >>> client = CcxtExchangeClient("kraken")
    >>> ticker = client.fetch_ticker("BTC/EUR")
    >>> print(f"BTC: {ticker.last}")

    >>> # Mit API-Key für Balance-Abfragen
    >>> client = CcxtExchangeClient(
    ...     "kraken",
    ...     api_key="...",
    ...     secret="...",
    ...     sandbox=True,
    ... )
    >>> balance = client.fetch_balance()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from .base import Balance, ExchangeClient, Ticker
from .protocols import ExchangeClient as ExchangeClientProtocol


def _load_impl():
    """
    Lazy-load der ccxt-Implementierung aus dem Provider-Modul.
    Dadurch bleibt dieses Modul ohne ccxt importierbar.
    """
    import importlib

    try:
        mod = importlib.import_module("src.data.providers.ccxt_exchange_client")
        return getattr(mod, "CcxtExchangeClient")
    except ModuleNotFoundError as exc:
        # Provide a helpful error when optional dependency is missing.
        msg = (
            "Optional dependency missing while loading ccxt exchange client.\n\n"
            "This feature depends on 'ccxt'. Install it (or the project's optional extra) and retry.\n\n"
            "Examples:\n"
            "  pip install ccxt\n"
            '  pip install -e ".[kraken]"\n'
        )
        raise ModuleNotFoundError(msg) from exc


class CcxtExchangeClient:
    """
    Read-only ExchangeClient Shim.

    Wichtig: importiert ccxt NICHT beim Import dieses Moduls.
    Die echte Implementierung wird erst bei Instanziierung geladen.
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
        impl_cls = _load_impl()
        self._impl = impl_cls(
            exchange_id=exchange_id,
            api_key=api_key,
            secret=secret,
            enable_rate_limit=enable_rate_limit,
            sandbox=sandbox,
            extra_config=extra_config,
        )

    @property
    def exchange(self) -> Any:
        return getattr(self._impl, "exchange")

    def get_name(self) -> str:
        return self._impl.get_name()

    # Protocol compatibility (dependency-free protocol in src/exchange/protocols.py)
    def load_markets(self) -> Any:
        return self._impl.load_markets()

    def fetch_ticker(self, symbol: str) -> Ticker:
        return self._impl.fetch_ticker(symbol)

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        since: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        return self._impl.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)

    def fetch_balance(self) -> Balance:
        return self._impl.fetch_balance()

    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._impl.fetch_open_orders(symbol)

    def fetch_markets(self) -> List[Dict[str, Any]]:
        return self._impl.fetch_markets()

    def get_available_timeframes(self) -> List[str]:
        return self._impl.get_available_timeframes()

    def __repr__(self) -> str:
        return repr(self._impl)


# Static typing only: declare that shim satisfies the dependency-free protocol.
_shim_exchange_client_typecheck: ExchangeClientProtocol | None = None


__all__ = ["CcxtExchangeClient"]
