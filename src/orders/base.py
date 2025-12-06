# src/orders/base.py
"""
Peak_Trade: Grundlegende Order-Strukturen
=========================================

Definiert die Kern-Datenstrukturen fuer den Order-Layer:
- OrderRequest: Anfrage fuer eine Order
- OrderFill: Informationen ueber eine ausgefuehrte Order
- OrderExecutionResult: Ergebnis einer Order-Ausfuehrung
- OrderExecutor: Protocol fuer Order-Ausfuehrung

WICHTIG: Diese Strukturen sind unabhaengig vom konkreten Executor.
         Sie koennen sowohl fuer Paper-/Sandbox- als auch fuer
         zukuenftige Live-Executors verwendet werden.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Protocol, Sequence

# Type aliases fuer Order-Attribute
OrderSide = Literal["buy", "sell"]
OrderType = Literal["market", "limit"]
OrderStatus = Literal["pending", "filled", "partially_filled", "rejected", "cancelled"]


@dataclass
class OrderRequest:
    """
    Anfrage fuer eine Order.

    Attributes:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        side: Kauf- oder Verkaufsorder ("buy" oder "sell")
        quantity: Menge (Stueckzahl)
        order_type: Order-Typ ("market" oder "limit")
        limit_price: Limit-Preis (nur bei order_type="limit")
        client_id: Optionale Client-ID fuer Tracking
        metadata: Zusaetzliche Metadaten (strategy_key, signal_time, etc.)
    """

    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = "market"
    limit_price: Optional[float] = None
    client_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validierung nach Initialisierung."""
        if self.quantity <= 0:
            raise ValueError(f"quantity muss > 0 sein, erhalten: {self.quantity}")
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("limit_price ist erforderlich fuer order_type='limit'")
        if self.limit_price is not None and self.limit_price <= 0:
            raise ValueError(f"limit_price muss > 0 sein, erhalten: {self.limit_price}")


@dataclass
class OrderFill:
    """
    Informationen ueber eine ausgefuehrte Order (Fill).

    Attributes:
        symbol: Trading-Pair
        side: Kauf- oder Verkaufsorder
        quantity: Ausgefuehrte Menge
        price: Ausgefuehrter Preis
        timestamp: Zeitpunkt der Ausfuehrung
        fee: Gebuehr (optional)
        fee_currency: Waehrung der Gebuehr (optional)
    """

    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    fee: Optional[float] = None
    fee_currency: Optional[str] = None


@dataclass
class OrderExecutionResult:
    """
    Ergebnis einer Order-Ausfuehrung.

    Attributes:
        status: Status der Order (filled, rejected, etc.)
        request: Die urspruengliche OrderRequest
        fill: Fill-Informationen (wenn ausgefuehrt)
        reason: Grund bei Ablehnung/Fehler
        metadata: Zusaetzliche Metadaten (PnL, fees, etc.)
    """

    status: OrderStatus
    request: OrderRequest
    fill: Optional[OrderFill] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_filled(self) -> bool:
        """True wenn die Order vollstaendig ausgefuehrt wurde."""
        return self.status == "filled"

    @property
    def is_rejected(self) -> bool:
        """True wenn die Order abgelehnt wurde."""
        return self.status == "rejected"


class OrderExecutor(Protocol):
    """
    Protocol fuer Order-Executors.

    Implementierungen:
    - PaperOrderExecutor: Simulation ohne echte Orders
    - (Zukuenftig) TestnetOrderExecutor: Testnet-Orders
    - (Zukuenftig) LiveOrderExecutor: Echte Orders (NICHT in dieser Phase)

    WICHTIG: In Phase 15 gibt es NUR den PaperOrderExecutor.
             Keine echten Live-Orders werden unterstuetzt.
    """

    def execute_orders(
        self, orders: Sequence[OrderRequest]
    ) -> List[OrderExecutionResult]:
        """
        Fuehrt eine Liste von Orders aus.

        Args:
            orders: Liste von OrderRequest-Objekten

        Returns:
            Liste von OrderExecutionResult-Objekten (gleiche Reihenfolge wie Input)
        """
        ...

    def execute_order(self, order: OrderRequest) -> OrderExecutionResult:
        """
        Fuehrt eine einzelne Order aus.

        Args:
            order: OrderRequest-Objekt

        Returns:
            OrderExecutionResult-Objekt
        """
        ...
