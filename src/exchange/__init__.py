# src/exchange/__init__.py
"""
Peak_Trade Exchange Layer
=========================
Exchange-API für Marktdaten, Balances und Order-Platzierung.

Dieses Modul stellt eine abstrahierte Schnittstelle zu Crypto-Exchanges bereit:

Read-Only (ExchangeClient):
- Ticker (aktueller Preis)
- OHLCV-Daten (Candlestick-Daten)
- Balance (Kontostände)
- Open Orders (nur lesen)

Trading (TradingExchangeClient - Phase 38):
- Order-Platzierung (place_order)
- Order-Stornierung (cancel_order)
- Order-Status-Abfrage (get_order_status)

Verwendung:
    # Read-only Client
    from src.exchange import build_exchange_client_from_config
    client = build_exchange_client_from_config(cfg)
    ticker = client.fetch_ticker("BTC/EUR")

    # Trading Client (Phase 38)
    from src.exchange import build_trading_client_from_config
    trading_client = build_trading_client_from_config(cfg)
    order_id = trading_client.place_order("BTC/EUR", "buy", 0.01, "market")
"""

from __future__ import annotations

from .base import (
    ExchangeClient,
    TradingExchangeClient,
    Ticker,
    Balance,
    ExchangeOrderStatus,
    ExchangeOrderResult,
    TradingOrderSide,
    TradingOrderType,
)
from .ccxt_client import CcxtExchangeClient

__all__ = [
    # Read-only Exchange
    "ExchangeClient",
    "Ticker",
    "Balance",
    "CcxtExchangeClient",
    "build_exchange_client_from_config",
    # Trading Exchange (Phase 38)
    "TradingExchangeClient",
    "ExchangeOrderStatus",
    "ExchangeOrderResult",
    "TradingOrderSide",
    "TradingOrderType",
    "build_trading_client_from_config",
]


def build_exchange_client_from_config(cfg) -> CcxtExchangeClient:
    """
    Factory-Funktion: Erstellt CcxtExchangeClient (read-only) aus PeakConfig.

    Args:
        cfg: PeakConfig-Objekt (oder kompatibel mit .get())

    Returns:
        CcxtExchangeClient-Instanz

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config()
        >>> client = build_exchange_client_from_config(cfg)
        >>> ticker = client.fetch_ticker("BTC/EUR")
    """
    exchange_id = cfg.get("exchange.id", "kraken")
    sandbox = cfg.get("exchange.sandbox", True)
    enable_rate_limit = cfg.get("exchange.enable_rate_limit", True)

    api_key = cfg.get("exchange.credentials.api_key", "") or None
    secret = cfg.get("exchange.credentials.secret", "") or None

    # Leere Strings als None behandeln
    if api_key == "":
        api_key = None
    if secret == "":
        secret = None

    # Extra-Options aus Config zusammenstellen
    extra_config = {}
    timeout = cfg.get("exchange.options.timeout")
    if timeout:
        extra_config["timeout"] = timeout
    verbose = cfg.get("exchange.options.verbose", False)
    if verbose:
        extra_config["verbose"] = verbose

    return CcxtExchangeClient(
        exchange_id=exchange_id,
        api_key=api_key,
        secret=secret,
        enable_rate_limit=enable_rate_limit,
        sandbox=sandbox,
        extra_config=extra_config if extra_config else None,
    )


def build_trading_client_from_config(cfg) -> TradingExchangeClient:
    """
    Factory-Funktion: Erstellt TradingExchangeClient aus PeakConfig (Phase 38).

    Liest [exchange].default_type aus der Config und erstellt den
    entsprechenden Client:
    - "dummy": DummyExchangeClient (In-Memory, für Tests)
    - "kraken_testnet": KrakenTestnetClient (echte Testnet-API)

    Args:
        cfg: PeakConfig-Objekt (oder kompatibel mit .get())

    Returns:
        TradingExchangeClient-Instanz

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config()
        >>> client = build_trading_client_from_config(cfg)
        >>> order_id = client.place_order("BTC/EUR", "buy", 0.01, "market")
    """
    default_type = cfg.get("exchange.default_type", "dummy")

    if default_type == "dummy":
        from .dummy_client import DummyExchangeClient

        # Default-Preise für Dummy-Client aus Config oder Fallback
        default_prices = {
            "BTC/EUR": cfg.get("exchange.dummy.btc_eur_price", 50000.0),
            "ETH/EUR": cfg.get("exchange.dummy.eth_eur_price", 3000.0),
            "BTC/USD": cfg.get("exchange.dummy.btc_usd_price", 55000.0),
        }
        fee_bps = cfg.get("exchange.dummy.fee_bps", 10.0)
        slippage_bps = cfg.get("exchange.dummy.slippage_bps", 5.0)

        return DummyExchangeClient(
            simulated_prices=default_prices,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )

    elif default_type == "kraken_testnet":
        from .kraken_testnet import create_kraken_testnet_client_from_config

        return create_kraken_testnet_client_from_config(cfg)

    else:
        raise ValueError(
            f"Unbekannter exchange.default_type: {default_type!r}. "
            f"Verfügbar: 'dummy', 'kraken_testnet'"
        )
