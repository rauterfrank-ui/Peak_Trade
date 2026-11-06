"""
Dependency-free protocols for the Exchange layer.
===============================================

Motivation:
- Keep the "core" type surface importable without optional deps (e.g. ccxt)
  and without heavy runtime requirements.
- Provider implementations (e.g. ccxt-backed) can implement these protocols.

NOTE:
- This module must not import pandas/ccxt.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ExchangeClient(Protocol):
    """
    Minimal read-only ExchangeClient Protocol.

    Implementations may return richer objects (e.g. pandas DataFrames),
    therefore return types are intentionally kept broad (Any) to avoid
    pulling heavy dependencies into the protocol layer.
    """

    def get_name(self) -> str: ...

    def load_markets(self) -> Any: ...

    def fetch_ticker(self, symbol: str) -> Any: ...

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        since: int | None = None,
        limit: int | None = None,
    ) -> Any: ...
