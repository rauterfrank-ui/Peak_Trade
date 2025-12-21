# src/orders/paper.py
"""
Peak_Trade: Paper-/Sandbox-Order-Executor
=========================================

Implementiert den PaperOrderExecutor, der Orders simuliert ohne
echte Trades an Boersen zu senden.

Features:
- Market-Orders werden sofort zum aktuellen Preis ausgefuehrt
- Limit-Orders werden geprueft und ggf. ausgefuehrt
- Optionale Fee-Simulation
- Optionale Slippage-Simulation

WICHTIG: Dieser Executor schickt KEINE echten Orders.
         Er dient ausschliesslich zur Simulation/Paper-Trading.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from .base import (
    OrderRequest,
    OrderFill,
    OrderExecutionResult,
    OrderExecutor,
    OrderStatus,
)


@dataclass
class PaperMarketContext:
    """
    Minimaler Marktkontext fuer Paper-Trading.

    Stellt die aktuellen Preise fuer Symbole bereit,
    die der PaperOrderExecutor zum Fuellen von Orders verwendet.

    Attributes:
        prices: Mapping von Symbol -> aktueller Preis
        fee_bps: Fee in Basispunkten (0.1% = 10 bps)
        slippage_bps: Slippage in Basispunkten
        base_currency: Basis-Waehrung fuer Fees
    """

    prices: Dict[str, float] = field(default_factory=dict)
    fee_bps: float = 0.0
    slippage_bps: float = 0.0
    base_currency: str = "EUR"

    def get_price(self, symbol: str) -> Optional[float]:
        """Gibt den aktuellen Preis fuer ein Symbol zurueck."""
        return self.prices.get(symbol)

    def set_price(self, symbol: str, price: float) -> None:
        """Setzt den aktuellen Preis fuer ein Symbol."""
        if price <= 0:
            raise ValueError(f"Preis muss > 0 sein, erhalten: {price}")
        self.prices[symbol] = price


class PaperOrderExecutor:
    """
    Paper-/Sandbox-Order-Executor.

    Simuliert Order-Ausfuehrungen ohne echte Trades.

    Verhalten:
    - Market-Orders: Werden sofort zum Preis aus PaperMarketContext ausgefuehrt
    - Limit-Orders: Werden ausgefuehrt wenn der Limit-Preis guenstiger ist als der Marktpreis
    - Unbekannte Symbole: Order wird rejected mit reason "no_price_for_symbol"

    WICHTIG: Dieser Executor schickt KEINE echten Orders an Boersen.
    """

    def __init__(self, market_context: PaperMarketContext) -> None:
        """
        Initialisiert den PaperOrderExecutor.

        Args:
            market_context: Marktkontext mit aktuellen Preisen
        """
        self._ctx = market_context
        self._execution_count = 0

    @property
    def context(self) -> PaperMarketContext:
        """Zugriff auf den Marktkontext."""
        return self._ctx

    def _compute_fill_price(self, order: OrderRequest, market_price: float) -> float:
        """
        Berechnet den Fill-Preis inkl. Slippage.

        Args:
            order: Die Order
            market_price: Aktueller Marktpreis

        Returns:
            Fill-Preis nach Slippage
        """
        if self._ctx.slippage_bps == 0.0:
            return market_price

        slip_factor = self._ctx.slippage_bps / 10000.0

        if order.side == "buy":
            # Bei Kauf: Slippage erhoeht den Preis
            return market_price * (1.0 + slip_factor)
        else:
            # Bei Verkauf: Slippage reduziert den Preis
            return market_price * (1.0 - slip_factor)

    def _compute_fee(self, notional: float) -> float:
        """
        Berechnet die Fee basierend auf dem Notional.

        Args:
            notional: Transaktionswert (quantity * price)

        Returns:
            Fee-Betrag
        """
        if self._ctx.fee_bps == 0.0:
            return 0.0
        return abs(notional) * (self._ctx.fee_bps / 10000.0)

    def _should_fill_limit_order(self, order: OrderRequest, market_price: float) -> bool:
        """
        Prueft ob eine Limit-Order ausgefuehrt werden sollte.

        Eine Limit-Order wird ausgefuehrt wenn:
        - BUY: market_price <= limit_price
        - SELL: market_price >= limit_price

        Args:
            order: Die Limit-Order
            market_price: Aktueller Marktpreis

        Returns:
            True wenn die Order ausgefuehrt werden soll
        """
        if order.limit_price is None:
            return False

        if order.side == "buy":
            return market_price <= order.limit_price
        else:
            return market_price >= order.limit_price

    def execute_order(self, order: OrderRequest) -> OrderExecutionResult:
        """
        Fuehrt eine einzelne Order aus.

        Args:
            order: OrderRequest-Objekt

        Returns:
            OrderExecutionResult-Objekt
        """
        self._execution_count += 1

        # Preis aus Kontext holen
        market_price = self._ctx.get_price(order.symbol)

        # Kein Preis vorhanden -> rejected
        if market_price is None:
            return OrderExecutionResult(
                status="rejected",
                request=order,
                fill=None,
                reason=f"no_price_for_symbol: {order.symbol}",
                metadata={"execution_id": self._execution_count},
            )

        # Limit-Order Logik
        if order.order_type == "limit":
            if not self._should_fill_limit_order(order, market_price):
                return OrderExecutionResult(
                    status="rejected",
                    request=order,
                    fill=None,
                    reason=(
                        f"limit_not_met: market_price={market_price:.8f}, "
                        f"limit_price={order.limit_price:.8f}, side={order.side}"
                    ),
                    metadata={
                        "execution_id": self._execution_count,
                        "market_price": market_price,
                    },
                )
            # Bei Limit-Order: Fill zum Limit-Preis (guenstigerer Fall)
            if order.side == "buy":
                fill_price = min(market_price, order.limit_price)
            else:
                fill_price = max(market_price, order.limit_price)
        else:
            # Market-Order: Fill zum Marktpreis (mit Slippage)
            fill_price = self._compute_fill_price(order, market_price)

        # Fee berechnen
        notional = order.quantity * fill_price
        fee = self._compute_fee(notional)

        # Fill erstellen
        now = datetime.now(timezone.utc)
        fill = OrderFill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            timestamp=now,
            fee=fee if fee > 0 else None,
            fee_currency=self._ctx.base_currency if fee > 0 else None,
        )

        return OrderExecutionResult(
            status="filled",
            request=order,
            fill=fill,
            reason=None,
            metadata={
                "execution_id": self._execution_count,
                "market_price": market_price,
                "notional": notional,
                "fee": fee,
                "slippage_bps": self._ctx.slippage_bps,
                "mode": "paper",
            },
        )

    def execute_orders(self, orders: Sequence[OrderRequest]) -> List[OrderExecutionResult]:
        """
        Fuehrt eine Liste von Orders aus.

        Args:
            orders: Liste von OrderRequest-Objekten

        Returns:
            Liste von OrderExecutionResult-Objekten (gleiche Reihenfolge)
        """
        return [self.execute_order(order) for order in orders]

    def get_execution_count(self) -> int:
        """Gibt die Anzahl der ausgefuehrten Orders zurueck."""
        return self._execution_count

    def reset_execution_count(self) -> None:
        """Setzt den Ausfuehrungszaehler zurueck."""
        self._execution_count = 0


# -----------------------------------------------------------------------------
# Stub fuer zukuenftige Exchange-/Testnet-Executor (NICHT implementiert)
# -----------------------------------------------------------------------------


class ExchangeOrderExecutor:
    """
    Stub fuer einen echten Exchange-Order-Executor.

    WICHTIG: Diese Klasse ist NICHT implementiert und dient nur als
             Platzhalter fuer zukuenftige Testnet-/Live-Integrationen.

    In Phase 15 wird KEIN echter Order-Executor implementiert.
    Alle Order-Ausfuehrungen erfolgen ueber den PaperOrderExecutor.
    """

    def __init__(self) -> None:
        raise NotImplementedError(
            "ExchangeOrderExecutor ist in dieser Phase nicht implementiert. "
            "Verwende PaperOrderExecutor fuer Paper-/Sandbox-Trading."
        )

    def execute_orders(self, orders: Sequence[OrderRequest]) -> List[OrderExecutionResult]:
        raise NotImplementedError("Echte Order-Ausfuehrung ist in dieser Phase nicht verfuegbar.")

    def execute_order(self, order: OrderRequest) -> OrderExecutionResult:
        raise NotImplementedError("Echte Order-Ausfuehrung ist in dieser Phase nicht verfuegbar.")
