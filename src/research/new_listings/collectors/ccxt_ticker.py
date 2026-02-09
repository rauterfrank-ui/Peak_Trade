# src/research/new_listings/collectors/ccxt_ticker.py
"""
CcxtTickerCollector – read-only public CCXT ticker/markets collector.

- Uses only public endpoints: fetch_tickers / fetch_markets (no auth, no keys).
- Rate-limited via config (rate_limit_ms).
- Emits one RawEvent per ticker (or batched payload) for reproducibility.
- ccxt is optional; lazy-import at collect() to keep module importable without ccxt.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .base import Collector, CollectorContext, RawEvent
from ..db import utc_now_iso


def _get_ccxt_config(cfg: Mapping[str, Any]) -> dict[str, Any]:
    """Extract sources.ccxt config with defaults. No secrets."""
    sources = cfg.get("sources") or {}
    ccxt_cfg = sources.get("ccxt") or {}
    return {
        "exchange": str(ccxt_cfg.get("exchange", "kraken")),
        "symbols": ccxt_cfg.get("symbols"),  # optional: list of symbols
        "market_type": ccxt_cfg.get("market_type"),  # optional: spot/future etc
        "max_markets": int(ccxt_cfg.get("max_markets", 50)),
        "rate_limit_ms": int(ccxt_cfg.get("rate_limit_ms", 1200)),
        "enabled": bool(ccxt_cfg.get("enabled", True)),
    }


class CcxtTickerCollector:
    """Collector that fetches public tickers/markets via CCXT (read-only, no auth)."""

    name = "ccxt_ticker"

    def __init__(self, config: Mapping[str, Any]) -> None:
        self._config = config
        self._ccxt_config = _get_ccxt_config(config)

    def collect(self, ctx: CollectorContext) -> Sequence[RawEvent]:
        if not self._ccxt_config["enabled"]:
            return []
        try:
            import ccxt
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "CcxtTickerCollector requires 'ccxt'. Install with: pip install ccxt (or pip install -e '.[kraken]')"
            ) from e

        exchange_id = self._ccxt_config["exchange"]
        max_markets = self._ccxt_config["max_markets"]
        rate_limit_ms = self._ccxt_config["rate_limit_ms"]
        symbols = self._ccxt_config["symbols"]
        market_type = self._ccxt_config["market_type"]

        if not hasattr(ccxt, exchange_id):
            avail = [x for x in dir(ccxt) if not x.startswith("_") and x.islower()]
            raise ValueError(
                f"Unknown ccxt exchange: {exchange_id!r}. Available (sample): {', '.join(avail[:10])}..."
            )

        klass = getattr(ccxt, exchange_id)
        options: dict[str, Any] = {
            "enableRateLimit": True,
            "rateLimit": rate_limit_ms,
        }
        # No apiKey/secret – public endpoints only
        ex = klass(options)
        if hasattr(ex, "checkRequiredCredentials"):
            ex.checkRequiredCredentials = False  # type: ignore[method-assign]

        if market_type and hasattr(ex, "options"):
            ex.options = getattr(ex, "options", {}) or {}
            ex.options["defaultType"] = market_type  # type: ignore[typeddict-unknown-key]

        observed_at = utc_now_iso()
        events: list[RawEvent] = []

        # Optional: fetch_markets for metadata (still public)
        try:
            markets = ex.fetch_markets()
        except Exception as e:
            # Emit one failure event so we have traceability
            events.append(
                RawEvent(
                    source=self.name,
                    venue_type="ccxt",
                    observed_at=observed_at,
                    payload={
                        "exchange": exchange_id,
                        "run_id": ctx.run_id,
                        "observed_at": observed_at,
                        "fetch_markets_error": str(e),
                        "tickers": [],
                    },
                )
            )
            return events

        # Fetch all tickers (public)
        try:
            tickers_raw = ex.fetch_tickers(symbols) if symbols else ex.fetch_tickers()
        except Exception as e:
            events.append(
                RawEvent(
                    source=self.name,
                    venue_type="ccxt",
                    observed_at=observed_at,
                    payload={
                        "exchange": exchange_id,
                        "run_id": ctx.run_id,
                        "observed_at": observed_at,
                        "fetch_tickers_error": str(e),
                        "tickers": [],
                    },
                )
            )
            return events

        if not isinstance(tickers_raw, dict):
            tickers_raw = {}

        # Limit to max_markets for rate/reproducibility
        ticker_items = list(tickers_raw.items())[:max_markets]
        for symbol, data in ticker_items:
            payload: dict[str, Any] = {
                "exchange": exchange_id,
                "symbol": symbol,
                "run_id": ctx.run_id,
                "observed_at": observed_at,
                "markets_count": len(markets),
            }
            if isinstance(data, dict):
                payload["ticker"] = {
                    k: v
                    for k, v in data.items()
                    if k
                    in (
                        "last",
                        "bid",
                        "ask",
                        "timestamp",
                        "symbol",
                        "high",
                        "low",
                        "volume",
                        "base",
                        "quote",
                    )
                }
            else:
                payload["ticker"] = data

            events.append(
                RawEvent(
                    source=self.name,
                    venue_type="ccxt",
                    observed_at=observed_at,
                    payload=payload,
                )
            )

        return events


__all__ = ["CcxtTickerCollector", "_get_ccxt_config"]
