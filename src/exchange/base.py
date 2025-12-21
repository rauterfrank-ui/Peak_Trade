# src/exchange/base.py
"""
Peak_Trade Exchange Base Types
==============================
Protokoll-Definition und Datenklassen für den Exchange-Layer.

Dieses Modul definiert:
- `ExchangeClient`: Protokoll für read-only Exchange-Zugriffe
- `TradingExchangeClient`: Protokoll für Order-fähige Exchange-Clients (Phase 38)
- `Ticker`: Datenklasse für Preisinformationen
- `Balance`: Datenklasse für Kontostände
- `ExchangeOrderStatus`: Status-Enum für Exchange-Orders

Phase 38: TradingExchangeClient ermöglicht Order-Platzierung via Exchange-API.
          ExchangeClient bleibt weiterhin read-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Protocol, runtime_checkable

import pandas as pd


@dataclass
class Ticker:
    """
    Ticker-Daten für ein Symbol.

    Attributes:
        symbol: Trading-Paar (z.B. "BTC/EUR")
        last: Letzter gehandelter Preis
        bid: Bestes Gebot (optional)
        ask: Bestes Angebot (optional)
        timestamp: Unix-Timestamp in Millisekunden (optional)
        raw: Rohe Exchange-Response (optional, für Debugging)
    """

    symbol: str
    last: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    timestamp: Optional[int] = None
    raw: Optional[Dict[str, Any]] = None

    def spread(self) -> Optional[float]:
        """Berechnet Bid-Ask-Spread, falls verfügbar."""
        if self.bid is not None and self.ask is not None and self.bid > 0:
            return (self.ask - self.bid) / self.bid
        return None

    def spread_bps(self) -> Optional[float]:
        """Spread in Basispunkten (1 bp = 0.01%)."""
        s = self.spread()
        return s * 10000 if s is not None else None


@dataclass
class Balance:
    """
    Account-Balance für alle Assets.

    Attributes:
        free: Verfügbare Guthaben pro Asset
        used: Gebundene Guthaben (z.B. in offenen Orders)
        total: Gesamtguthaben pro Asset (free + used)
        raw: Rohe Exchange-Response (optional)
    """

    free: Dict[str, float] = field(default_factory=dict)
    used: Dict[str, float] = field(default_factory=dict)
    total: Dict[str, float] = field(default_factory=dict)
    raw: Optional[Dict[str, Any]] = None

    def get_asset(self, asset: str) -> Dict[str, float]:
        """
        Gibt Balance für ein einzelnes Asset zurück.

        Args:
            asset: Asset-Symbol (z.B. "BTC", "EUR")

        Returns:
            Dict mit free, used, total
        """
        return {
            "free": self.free.get(asset, 0.0),
            "used": self.used.get(asset, 0.0),
            "total": self.total.get(asset, 0.0),
        }

    def non_zero_assets(self) -> List[str]:
        """Gibt Liste aller Assets mit Guthaben > 0 zurück."""
        return [asset for asset, amount in self.total.items() if amount > 0]


@runtime_checkable
class ExchangeClient(Protocol):
    """
    Minimale read-only Exchange-API für Spot-Märkte.

    Dieses Protokoll definiert das Interface für Exchange-Clients.
    Alle Methoden sind ausschließlich lesend – keine Order-Platzierung!

    Implementierungen:
    - `CcxtExchangeClient`: Konkrete Implementierung mit ccxt

    Example:
        >>> client: ExchangeClient = CcxtExchangeClient("kraken")
        >>> ticker = client.fetch_ticker("BTC/EUR")
        >>> print(f"BTC/EUR: {ticker.last}")
    """

    def get_name(self) -> str:
        """
        Name/ID des Exchanges (z.B. 'kraken', 'binance').

        Returns:
            Exchange-ID als String
        """
        ...

    def fetch_ticker(self, symbol: str) -> Ticker:
        """
        Aktuellen Ticker für ein Symbol holen (Spot).

        Args:
            symbol: Trading-Paar (z.B. "BTC/EUR", "ETH/USDT")

        Returns:
            Ticker-Objekt mit Preisinformationen

        Raises:
            ValueError: Bei ungültigem Symbol
            Exception: Bei Netzwerkfehlern
        """
        ...

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        since: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        OHLCV-Daten als DataFrame zurückgeben.

        Args:
            symbol: Trading-Paar (z.B. "BTC/EUR")
            timeframe: Zeitintervall (z.B. "1m", "5m", "1h", "1d")
            since: Startzeit als Unix-Timestamp in Millisekunden (optional)
            limit: Maximale Anzahl Candles (optional, Exchange-abhängig)

        Returns:
            DataFrame mit Spalten: ['open', 'high', 'low', 'close', 'volume']
            Index: pd.DatetimeIndex (UTC)

        Raises:
            ValueError: Bei ungültigem Symbol oder Timeframe
            Exception: Bei Netzwerkfehlern
        """
        ...

    def fetch_balance(self) -> Balance:
        """
        Account-Balances für alle Assets (read-only).

        WICHTIG: Erfordert API-Key mit Lese-Rechten.
        Ohne API-Key schlägt diese Methode fehl!

        Returns:
            Balance-Objekt mit free/used/total pro Asset

        Raises:
            AuthenticationError: Bei fehlenden oder ungültigen Credentials
            Exception: Bei Netzwerkfehlern
        """
        ...

    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Offene Orders (Spot) als rohe Dicts zurückgeben (nur Lesen).

        WICHTIG: Erfordert API-Key mit Lese-Rechten.

        Args:
            symbol: Optional - filtert nach Symbol (z.B. "BTC/EUR")
                    Wenn None: alle offenen Orders

        Returns:
            Liste von Order-Dicts (Exchange-spezifisches Format)

        Raises:
            AuthenticationError: Bei fehlenden Credentials
            Exception: Bei Netzwerkfehlern
        """
        ...


# =============================================================================
# Phase 38: Trading Exchange Client (Order-fähig)
# =============================================================================

# Type aliases für Order-Attribute (vermeidet Zirkularimport zu src.orders.base)
TradingOrderSide = Literal["buy", "sell"]
TradingOrderType = Literal["market", "limit"]


class ExchangeOrderStatus(str, Enum):
    """
    Status einer Exchange-Order.

    Dieses Enum wird im Exchange-Layer verwendet und kann vom
    OrderExecutor auf die internen OrderStatus-Werte gemappt werden.
    """

    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"
    VALIDATED = "validated"  # Für validate_only Orders


@dataclass
class ExchangeOrderResult:
    """
    Ergebnis einer Exchange-Order-Platzierung.

    Attributes:
        exchange_order_id: ID der Order auf der Exchange
        status: Aktueller Status der Order
        filled_qty: Bisher gefüllte Menge
        avg_price: Durchschnittlicher Fill-Preis
        fee: Gebühr (falls bekannt)
        fee_currency: Währung der Gebühr
        raw: Rohe Exchange-Response (für Debugging)
    """

    exchange_order_id: str
    status: ExchangeOrderStatus
    filled_qty: float = 0.0
    avg_price: Optional[float] = None
    fee: Optional[float] = None
    fee_currency: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


@runtime_checkable
class TradingExchangeClient(Protocol):
    """
    Order-fähiger Exchange-Client für Testnet/Live-Trading (Phase 38).

    Dieses Protokoll erweitert die Basis-Exchange-Funktionalität um
    Order-Platzierung und -Verwaltung. Es ist absichtlich schlank gehalten
    für v0 und kann später erweitert werden.

    WICHTIG: Implementierungen sollten Safety-Guards und Environment-Checks
             NICHT selbst durchführen - das ist Aufgabe des OrderExecutors.

    Implementierungen:
    - `DummyExchangeClient`: In-Memory-Simulation für Tests
    - `KrakenTestnetClient`: Kraken Testnet/Demo-API

    Verwendung:
        >>> client: TradingExchangeClient = DummyExchangeClient(prices={"BTC/EUR": 50000})
        >>> order_id = client.place_order(
        ...     symbol="BTC/EUR",
        ...     side="buy",
        ...     quantity=0.01,
        ...     order_type="market",
        ... )
        >>> status = client.get_order_status(order_id)

    Note:
        Parameter sind bewusst primitiv (str, float) gehalten, um
        Zirkularimporte zu src.orders.base zu vermeiden.
    """

    def get_name(self) -> str:
        """
        Name/ID des Exchanges (z.B. 'dummy', 'kraken_testnet').

        Returns:
            Exchange-Name als String
        """
        ...

    def place_order(
        self,
        symbol: str,
        side: TradingOrderSide,
        quantity: float,
        order_type: TradingOrderType = "market",
        limit_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> str:
        """
        Platziert eine Order auf der Exchange.

        Args:
            symbol: Trading-Pair (z.B. "BTC/EUR")
            side: "buy" oder "sell"
            quantity: Menge (Stückzahl)
            order_type: "market" oder "limit"
            limit_price: Preis für Limit-Orders (erforderlich bei order_type="limit")
            client_order_id: Optionale Client-seitige ID für Tracking

        Returns:
            Exchange-Order-ID (String)

        Raises:
            ValueError: Bei ungültigen Parametern
            ExchangeAPIError: Bei Exchange-Fehlern
        """
        ...

    def cancel_order(self, exchange_order_id: str) -> bool:
        """
        Storniert eine offene Order.

        Args:
            exchange_order_id: Die Exchange-Order-ID

        Returns:
            True wenn erfolgreich storniert, False sonst

        Raises:
            ExchangeAPIError: Bei Exchange-Fehlern
        """
        ...

    def get_order_status(self, exchange_order_id: str) -> ExchangeOrderResult:
        """
        Fragt den Status einer Order ab.

        Args:
            exchange_order_id: Die Exchange-Order-ID

        Returns:
            ExchangeOrderResult mit aktuellem Status und Fill-Informationen

        Raises:
            ExchangeAPIError: Bei Exchange-Fehlern
        """
        ...
