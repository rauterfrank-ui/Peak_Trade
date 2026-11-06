# src/exchange/dummy_client.py
"""
Peak_Trade: Dummy Exchange Client (Phase 38)
============================================

In-Memory Exchange-Client für Unit- und Smoke-Tests.

Dieser Client simuliert eine Exchange ohne echte Netzwerkzugriffe:
- Deterministisches Verhalten für reproduzierbare Tests
- Sofortige Fills für Market-Orders
- Konfigurierbare Preise, Fees und Slippage
- Vollständiges Order-Tracking

WICHTIG: Nur für Tests gedacht! Keine echten Trades!

Verwendung:
    >>> client = DummyExchangeClient(
    ...     simulated_prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
    ...     fee_bps=10.0,
    ...     slippage_bps=5.0,
    ... )
    >>> order_id = client.place_order("BTC/EUR", "buy", 0.01, "market")
    >>> status = client.get_order_status(order_id)
    >>> print(status.status)  # ExchangeOrderStatus.FILLED
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import (
    ExchangeOrderStatus,
    ExchangeOrderResult,
    TradingOrderSide,
    TradingOrderType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Internal Order Tracking
# =============================================================================


@dataclass
class DummyOrderInfo:
    """
    Interner Order-Datensatz für den DummyExchangeClient.

    Attributes:
        order_id: Eindeutige Order-ID
        symbol: Trading-Pair
        side: "buy" oder "sell"
        quantity: Bestellte Menge
        order_type: "market" oder "limit"
        limit_price: Limit-Preis (nur bei Limit-Orders)
        client_order_id: Client-seitige ID
        status: Aktueller Status
        filled_qty: Gefüllte Menge
        avg_price: Durchschnittlicher Fill-Preis
        fee: Gebühr
        created_at: Erstellungszeitpunkt
        updated_at: Letzter Update-Zeitpunkt
    """

    order_id: str
    symbol: str
    side: TradingOrderSide
    quantity: float
    order_type: TradingOrderType
    limit_price: Optional[float] = None
    client_order_id: Optional[str] = None
    status: ExchangeOrderStatus = ExchangeOrderStatus.PENDING
    filled_qty: float = 0.0
    avg_price: Optional[float] = None
    fee: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# Dummy Exchange Client
# =============================================================================


class DummyExchangeClient:
    """
    In-Memory Exchange-Client für Tests (implementiert TradingExchangeClient).

    Simuliert eine Exchange mit:
    - Sofortigen Fills für Market-Orders
    - Konfigurierbaren Preisen pro Symbol
    - Simulierter Fee und Slippage
    - Order-Tracking mit Status-Abfragen
    - Deterministischem Verhalten für reproduzierbare Tests

    Attributes:
        simulated_prices: Dict von Symbol -> Preis
        fee_bps: Fee in Basispunkten (10 bps = 0.1%)
        slippage_bps: Slippage in Basispunkten (5 bps = 0.05%)

    Example:
        >>> client = DummyExchangeClient(
        ...     simulated_prices={"BTC/EUR": 50000.0},
        ...     fee_bps=10.0,
        ... )
        >>> order_id = client.place_order("BTC/EUR", "buy", 0.01, "market")
        >>> assert client.get_order_status(order_id).status == ExchangeOrderStatus.FILLED
    """

    def __init__(
        self,
        simulated_prices: Optional[Dict[str, float]] = None,
        fee_bps: float = 10.0,
        slippage_bps: float = 5.0,
        initial_balances: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Initialisiert den DummyExchangeClient.

        Args:
            simulated_prices: Dict von Symbol -> Preis (z.B. {"BTC/EUR": 50000})
            fee_bps: Fee in Basispunkten (Default: 10 = 0.1%)
            slippage_bps: Slippage in Basispunkten (Default: 5 = 0.05%)
            initial_balances: Optionale Start-Balances (z.B. {"EUR": 10000})
        """
        self._prices = simulated_prices or {}
        self._fee_bps = fee_bps
        self._slippage_bps = slippage_bps

        # Order-Storage
        self._orders: Dict[str, DummyOrderInfo] = {}
        self._order_counter = 0

        # Balance-Tracking (optional)
        self._balances = initial_balances or {"EUR": 10000.0}

        logger.info(
            f"[DUMMY EXCHANGE] Initialisiert: "
            f"prices={list(self._prices.keys())}, "
            f"fee_bps={self._fee_bps}, "
            f"slippage_bps={self._slippage_bps}"
        )

    # =========================================================================
    # TradingExchangeClient Protocol Implementation
    # =========================================================================

    def get_name(self) -> str:
        """Gibt den Namen des Exchange-Clients zurück."""
        return "dummy"

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
        Platziert eine Order (simuliert).

        Bei Market-Orders: Sofortiger Fill zum simulierten Preis + Slippage.
        Bei Limit-Orders: Order bleibt OPEN (wird nicht automatisch gefüllt).

        Args:
            symbol: Trading-Pair (z.B. "BTC/EUR")
            side: "buy" oder "sell"
            quantity: Menge
            order_type: "market" oder "limit"
            limit_price: Preis für Limit-Orders
            client_order_id: Optionale Client-ID

        Returns:
            Order-ID (String)

        Raises:
            ValueError: Bei ungültigen Parametern oder fehlendem Preis
        """
        # Validierung
        if quantity <= 0:
            raise ValueError(f"quantity muss > 0 sein: {quantity}")
        if order_type == "limit" and limit_price is None:
            raise ValueError("limit_price erforderlich für Limit-Orders")
        if limit_price is not None and limit_price <= 0:
            raise ValueError(f"limit_price muss > 0 sein: {limit_price}")

        # Order-ID generieren
        self._order_counter += 1
        order_id = f"DUMMY-{self._order_counter:06d}-{uuid.uuid4().hex[:8].upper()}"

        now = datetime.now(timezone.utc)

        # Order erstellen
        order = DummyOrderInfo(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            client_order_id=client_order_id,
            status=ExchangeOrderStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        logger.info(
            f"[DUMMY EXCHANGE] Order platziert: {order_id} - "
            f"{side.upper()} {quantity} {symbol} @ {order_type}"
        )

        # Bei Market-Orders: Sofort füllen
        if order_type == "market":
            self._fill_market_order(order)
        else:
            # Limit-Orders bleiben OPEN
            order.status = ExchangeOrderStatus.OPEN

        # Speichern
        self._orders[order_id] = order

        return order_id

    def cancel_order(self, exchange_order_id: str) -> bool:
        """
        Storniert eine offene Order.

        Args:
            exchange_order_id: Die Order-ID

        Returns:
            True wenn erfolgreich storniert, False wenn nicht möglich
        """
        order = self._orders.get(exchange_order_id)

        if order is None:
            logger.warning(f"[DUMMY EXCHANGE] Order nicht gefunden: {exchange_order_id}")
            return False

        # Nur offene Orders können storniert werden
        if order.status not in (ExchangeOrderStatus.PENDING, ExchangeOrderStatus.OPEN):
            logger.warning(
                f"[DUMMY EXCHANGE] Order kann nicht storniert werden: "
                f"{exchange_order_id} (Status: {order.status})"
            )
            return False

        order.status = ExchangeOrderStatus.CANCELLED
        order.updated_at = datetime.now(timezone.utc)

        logger.info(f"[DUMMY EXCHANGE] Order storniert: {exchange_order_id}")
        return True

    def get_order_status(self, exchange_order_id: str) -> ExchangeOrderResult:
        """
        Fragt den Status einer Order ab.

        Args:
            exchange_order_id: Die Order-ID

        Returns:
            ExchangeOrderResult mit aktuellem Status

        Raises:
            ValueError: Wenn Order nicht gefunden
        """
        order = self._orders.get(exchange_order_id)

        if order is None:
            raise ValueError(f"Order nicht gefunden: {exchange_order_id}")

        return ExchangeOrderResult(
            exchange_order_id=order.order_id,
            status=order.status,
            filled_qty=order.filled_qty,
            avg_price=order.avg_price,
            fee=order.fee,
            fee_currency="EUR" if order.fee else None,
            raw={
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
                "order_type": order.order_type,
                "limit_price": order.limit_price,
                "client_order_id": order.client_order_id,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
            },
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _fill_market_order(self, order: DummyOrderInfo) -> None:
        """
        Füllt eine Market-Order zum simulierten Preis.

        Args:
            order: Die zu füllende Order
        """
        base_price = self._prices.get(order.symbol)

        if base_price is None:
            # Kein Preis -> Order wird rejected
            order.status = ExchangeOrderStatus.REJECTED
            logger.warning(
                f"[DUMMY EXCHANGE] Order rejected - kein Preis für {order.symbol}. "
                f"Setze Preis mit set_price()"
            )
            return

        # Slippage berechnen
        slippage_factor = self._slippage_bps / 10000.0
        if order.side == "buy":
            fill_price = base_price * (1.0 + slippage_factor)
        else:
            fill_price = base_price * (1.0 - slippage_factor)

        # Fee berechnen
        notional = order.quantity * fill_price
        fee = notional * (self._fee_bps / 10000.0)

        # Order aktualisieren
        order.status = ExchangeOrderStatus.FILLED
        order.filled_qty = order.quantity
        order.avg_price = fill_price
        order.fee = fee if fee > 0 else None
        order.updated_at = datetime.now(timezone.utc)

        logger.info(
            f"[DUMMY EXCHANGE] Order filled: {order.order_id} - "
            f"{order.quantity} @ {fill_price:.2f} (fee: {fee:.4f})"
        )

    # =========================================================================
    # Configuration Methods
    # =========================================================================

    def set_price(self, symbol: str, price: float) -> None:
        """
        Setzt den simulierten Preis für ein Symbol.

        Args:
            symbol: Trading-Pair (z.B. "BTC/EUR")
            price: Simulierter Preis

        Raises:
            ValueError: Wenn Preis <= 0
        """
        if price <= 0:
            raise ValueError(f"Preis muss > 0 sein: {price}")
        self._prices[symbol] = price
        logger.debug(f"[DUMMY EXCHANGE] Preis gesetzt: {symbol} = {price}")

    def get_price(self, symbol: str) -> Optional[float]:
        """Gibt den simulierten Preis für ein Symbol zurück."""
        return self._prices.get(symbol)

    def get_all_prices(self) -> Dict[str, float]:
        """Gibt alle simulierten Preise zurück."""
        return dict(self._prices)

    def set_fee_bps(self, fee_bps: float) -> None:
        """Setzt die simulierte Fee in Basispunkten."""
        self._fee_bps = fee_bps

    def set_slippage_bps(self, slippage_bps: float) -> None:
        """Setzt die simulierte Slippage in Basispunkten."""
        self._slippage_bps = slippage_bps

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_all_orders(self) -> List[DummyOrderInfo]:
        """Gibt alle Orders zurück."""
        return list(self._orders.values())

    def get_open_orders(self) -> List[DummyOrderInfo]:
        """Gibt alle offenen Orders zurück."""
        return [
            o
            for o in self._orders.values()
            if o.status in (ExchangeOrderStatus.PENDING, ExchangeOrderStatus.OPEN)
        ]

    def get_filled_orders(self) -> List[DummyOrderInfo]:
        """Gibt alle gefüllten Orders zurück."""
        return [o for o in self._orders.values() if o.status == ExchangeOrderStatus.FILLED]

    def get_order_count(self) -> int:
        """Gibt die Gesamtzahl der Orders zurück."""
        return len(self._orders)

    def get_balances(self) -> Dict[str, float]:
        """Gibt die simulierten Balances zurück."""
        return dict(self._balances)

    # =========================================================================
    # Reset & Utility
    # =========================================================================

    def reset(self) -> None:
        """Setzt den Client zurück (löscht alle Orders)."""
        self._orders.clear()
        self._order_counter = 0
        logger.info("[DUMMY EXCHANGE] Reset durchgeführt")

    def clear_orders(self) -> None:
        """Löscht alle Orders (behält Preise und Einstellungen)."""
        self._orders.clear()
        self._order_counter = 0

    def __repr__(self) -> str:
        return (
            f"<DummyExchangeClient("
            f"prices={len(self._prices)}, "
            f"orders={len(self._orders)}, "
            f"fee_bps={self._fee_bps})>"
        )
