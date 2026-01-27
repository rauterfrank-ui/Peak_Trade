"""
Peak_Trade Resilient Exchange Client (Shim)
==========================================

Dieses Modul darf ccxt NICHT importieren.
Die echte Implementierung liegt unter `src/data/providers/` und wird lazy geladen.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _load_impl():
    import importlib

    try:
        mod = importlib.import_module("src.data.providers.resilient_ccxt_exchange_client")
        return getattr(mod, "ResilientExchangeClient")
    except ModuleNotFoundError as exc:
        msg = (
            "Optional dependency missing while loading resilient ccxt exchange client.\n\n"
            "This feature depends on 'ccxt'. Install it (or the project's optional extra) and retry.\n\n"
            "Examples:\n"
            "  pip install ccxt\n"
            '  pip install -e ".[kraken]"\n'
        )
        raise ModuleNotFoundError(msg) from exc


class ResilientExchangeClient:
    def __init__(self, exchange_id: str = "kraken", config: Optional[Dict[str, Any]] = None):
        impl_cls = _load_impl()
        self._impl = impl_cls(exchange_id=exchange_id, config=config)

    def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1h", limit: int = 100, since: Optional[int] = None
    ) -> List[List]:
        return self._impl.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, since=since)

    def fetch_balance(self) -> Dict[str, Any]:
        return self._impl.fetch_balance()

    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        return self._impl.fetch_ticker(symbol)

    def _health_check(self) -> Tuple[bool, str]:
        return self._impl._health_check()


__all__ = ["ResilientExchangeClient"]
