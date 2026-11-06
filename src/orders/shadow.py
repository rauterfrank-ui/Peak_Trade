# src/orders/shadow.py
"""
Peak_Trade: Shadow-Order-Executor (Phase 24)
============================================

Implementiert den ShadowOrderExecutor, der Orders nur simuliert und loggt,
ohne echte API-Calls an Exchanges zu senden.

Features:
- Nutzt die bestehende Execution-Pipeline-Infrastruktur
- Keine echten Exchange-API-Calls
- Konfigurierbare Fee- und Slippage-Simulation
- Integration mit der Experiments-Registry (run_type="shadow_run")
- Logging aller simulierten Orders/Fills

Use Cases:
- Shadow-Live: Strategien tun so, als würden sie live traden
- Dry-Run-Tests vor echtem Testnet/Live
- Quasi-realistische Ausführungssimulation

WICHTIG: Dieser Executor sendet NIEMALS echte Orders.
         Er ist zu 100% simulativ und dient nur zu Test-/Logging-Zwecken.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from .base import (
    OrderRequest,
    OrderFill,
    OrderExecutionResult,
    OrderStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Execution Mode Constants
# =============================================================================

EXECUTION_MODE_SHADOW = "shadow"
EXECUTION_MODE_SHADOW_RUN = "shadow_run"


# =============================================================================
# Shadow Order Log Entry
# =============================================================================


@dataclass
class ShadowOrderLog:
    """
    Log-Eintrag für eine Shadow-Order.

    Attributes:
        timestamp: Zeitpunkt der Shadow-Ausführung
        request: Die ursprüngliche OrderRequest
        result: Das simulierte OrderExecutionResult
        shadow_mode: Shadow-Modus ("shadow_run")
        notes: Zusätzliche Notizen
    """

    timestamp: datetime
    request: OrderRequest
    result: OrderExecutionResult
    shadow_mode: str = EXECUTION_MODE_SHADOW_RUN
    notes: Optional[str] = None


# =============================================================================
# Shadow Market Context
# =============================================================================


@dataclass
class ShadowMarketContext:
    """
    Marktkontext für Shadow-Trading.

    Stellt simulierte Preise, Fee- und Slippage-Einstellungen
    für den ShadowOrderExecutor bereit.

    Attributes:
        prices: Mapping von Symbol -> aktueller Preis
        fee_rate: Fee-Rate (z.B. 0.0005 = 5 bps = 0.05%)
        slippage_bps: Slippage in Basispunkten (z.B. 5 = 0.05%)
        base_currency: Basis-Währung für Fees (z.B. "EUR")
    """

    prices: Dict[str, float] = field(default_factory=dict)
    fee_rate: float = 0.0005  # 5 bps = 0.05%
    slippage_bps: float = 0.0
    base_currency: str = "EUR"

    def get_price(self, symbol: str) -> Optional[float]:
        """Gibt den aktuellen Preis für ein Symbol zurück."""
        return self.prices.get(symbol)

    def set_price(self, symbol: str, price: float) -> None:
        """Setzt den aktuellen Preis für ein Symbol."""
        if price <= 0:
            raise ValueError(f"Preis muss > 0 sein, erhalten: {price}")
        self.prices[symbol] = price

    def get_fee_bps(self) -> float:
        """Gibt die Fee in Basispunkten zurück."""
        return self.fee_rate * 10000.0


# =============================================================================
# ShadowOrderExecutor
# =============================================================================


class ShadowOrderExecutor:
    """
    Shadow-Order-Executor für Dry-Run/Shadow-Live-Modus.

    Simuliert Order-Ausführungen ohne echte API-Calls.
    Alle Orders werden geloggt und erzeugen simulierte Results.

    Dieser Executor ist ideal für:
    - Shadow-Live: Strategien parallel zum realen Markt simulieren
    - Dry-Run vor echtem Testnet/Live-Einsatz
    - Quasi-realistische Ausführungssimulation mit Fee/Slippage

    Verhalten:
    - Market-Orders: Werden sofort zum simulierten Preis ausgefüllt
    - Limit-Orders: Werden geprüft und ggf. zum Limit ausgefüllt
    - Unbekannte Symbole: Order wird rejected mit reason "no_price_for_symbol"
    - Alle Orders werden in order_log gespeichert

    WICHTIG: Dieser Executor sendet NIEMALS echte Orders an Börsen.
             Alles ist zu 100% simulativ.

    Example:
        >>> ctx = ShadowMarketContext(
        ...     prices={"BTC/EUR": 50000.0},
        ...     fee_rate=0.0005,  # 5 bps
        ...     slippage_bps=5.0,
        ... )
        >>> executor = ShadowOrderExecutor(market_context=ctx)
        >>> order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1)
        >>> result = executor.execute_order(order)
        >>> print(result.status)  # "filled"
        >>> print(result.metadata["mode"])  # "shadow_run"
    """

    def __init__(
        self,
        market_context: Optional[ShadowMarketContext] = None,
        fee_rate: Optional[float] = None,
        slippage_bps: Optional[float] = None,
    ) -> None:
        """
        Initialisiert den ShadowOrderExecutor.

        Args:
            market_context: Optionaler ShadowMarketContext.
                            Falls None, wird ein Default-Context erstellt.
            fee_rate: Optionale Fee-Rate (überschreibt Context-Wert)
            slippage_bps: Optionale Slippage in bps (überschreibt Context-Wert)
        """
        self._ctx = market_context or ShadowMarketContext()

        # Optionale Überschreibung von Fee/Slippage
        if fee_rate is not None:
            self._ctx.fee_rate = fee_rate
        if slippage_bps is not None:
            self._ctx.slippage_bps = slippage_bps

        self._execution_count = 0
        self._order_log: List[ShadowOrderLog] = []

        logger.info(
            f"[SHADOW EXECUTOR] Initialisiert mit fee_rate={self._ctx.fee_rate:.6f} "
            f"({self._ctx.get_fee_bps():.1f} bps), slippage_bps={self._ctx.slippage_bps:.1f}"
        )

    @property
    def context(self) -> ShadowMarketContext:
        """Zugriff auf den Marktkontext."""
        return self._ctx

    def set_price(self, symbol: str, price: float) -> None:
        """Setzt den aktuellen Preis für ein Symbol."""
        self._ctx.set_price(symbol, price)

    def get_price(self, symbol: str) -> Optional[float]:
        """Gibt den aktuellen Preis für ein Symbol zurück."""
        return self._ctx.get_price(symbol)

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
            # Bei Kauf: Slippage erhöht den Preis
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
        if self._ctx.fee_rate == 0.0:
            return 0.0
        return abs(notional) * self._ctx.fee_rate

    def _should_fill_limit_order(self, order: OrderRequest, market_price: float) -> bool:
        """
        Prüft ob eine Limit-Order ausgefüllt werden sollte.

        Eine Limit-Order wird ausgefüllt wenn:
        - BUY: market_price <= limit_price
        - SELL: market_price >= limit_price

        Args:
            order: Die Limit-Order
            market_price: Aktueller Marktpreis

        Returns:
            True wenn die Order ausgefüllt werden soll
        """
        if order.limit_price is None:
            return False

        if order.side == "buy":
            return market_price <= order.limit_price
        else:
            return market_price >= order.limit_price

    def execute_order(self, order: OrderRequest) -> OrderExecutionResult:
        """
        Führt eine Order im Shadow-Modus aus.

        In Phase 24 wird KEINE echte Order gesendet.
        Stattdessen wird ein simuliertes Ergebnis erzeugt.

        Args:
            order: Die auszuführende OrderRequest

        Returns:
            OrderExecutionResult mit status und metadata

        Note:
            Diese Methode wirft keine Exception für normale Orders,
            sondern erzeugt immer ein simuliertes Result.
        """
        self._execution_count += 1
        now = datetime.now(timezone.utc)

        # Log-Info
        logger.debug(
            f"[SHADOW] Order #{self._execution_count}: "
            f"{order.side.upper()} {order.quantity} {order.symbol} @ {order.order_type}"
        )

        # Preis aus Kontext holen
        market_price = self._ctx.get_price(order.symbol)

        # Kein Preis vorhanden -> rejected
        if market_price is None:
            result = OrderExecutionResult(
                status="rejected",
                request=order,
                fill=None,
                reason=f"no_price_for_symbol: {order.symbol}",
                metadata={
                    "execution_id": self._execution_count,
                    "mode": EXECUTION_MODE_SHADOW_RUN,
                    "shadow": True,
                    "note": "Setze einen Preis mit set_price() oder im market_context",
                },
            )
            self._log_order(order, result, now)
            return result

        # Limit-Order Logik
        if order.order_type == "limit":
            if not self._should_fill_limit_order(order, market_price):
                result = OrderExecutionResult(
                    status="rejected",
                    request=order,
                    fill=None,
                    reason=(
                        f"limit_not_met: market_price={market_price:.8f}, "
                        f"limit_price={order.limit_price:.8f}, side={order.side}"
                    ),
                    metadata={
                        "execution_id": self._execution_count,
                        "mode": EXECUTION_MODE_SHADOW_RUN,
                        "shadow": True,
                        "market_price": market_price,
                    },
                )
                self._log_order(order, result, now)
                return result

            # Bei Limit-Order: Fill zum Limit-Preis (günstigerer Fall)
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
        fill = OrderFill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            timestamp=now,
            fee=fee if fee > 0 else None,
            fee_currency=self._ctx.base_currency if fee > 0 else None,
        )

        result = OrderExecutionResult(
            status="filled",
            request=order,
            fill=fill,
            reason=None,
            metadata={
                "execution_id": self._execution_count,
                "mode": EXECUTION_MODE_SHADOW_RUN,
                "shadow": True,
                "market_price": market_price,
                "notional": notional,
                "fee": fee,
                "fee_rate": self._ctx.fee_rate,
                "slippage_bps": self._ctx.slippage_bps,
                "note": "SHADOW-EXECUTION - keine echte Order gesendet",
            },
        )

        self._log_order(order, result, now)
        return result

    def execute_orders(self, orders: Sequence[OrderRequest]) -> List[OrderExecutionResult]:
        """
        Führt mehrere Orders im Shadow-Modus aus.

        Args:
            orders: Liste von OrderRequest-Objekten

        Returns:
            Liste von OrderExecutionResult-Objekten (gleiche Reihenfolge)
        """
        return [self.execute_order(order) for order in orders]

    def _log_order(
        self,
        order: OrderRequest,
        result: OrderExecutionResult,
        timestamp: datetime,
    ) -> None:
        """Fügt einen Eintrag zum Order-Log hinzu."""
        log_entry = ShadowOrderLog(
            timestamp=timestamp,
            request=order,
            result=result,
            shadow_mode=EXECUTION_MODE_SHADOW_RUN,
            notes=f"Shadow execution #{self._execution_count}",
        )
        self._order_log.append(log_entry)

    def get_execution_count(self) -> int:
        """Gibt die Anzahl der ausgeführten Shadow-Orders zurück."""
        return self._execution_count

    def get_order_log(self) -> List[ShadowOrderLog]:
        """Gibt eine Kopie des Order-Logs zurück."""
        return list(self._order_log)

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Gibt eine Zusammenfassung aller Shadow-Ausführungen zurück.

        Returns:
            Dict mit Statistiken:
            - total_orders: Anzahl aller Orders
            - filled_orders: Anzahl gefüllter Orders
            - rejected_orders: Anzahl abgelehnter Orders
            - fill_rate: Anteil gefüllter Orders
            - total_notional: Summe aller Transaktionswerte
            - total_fees: Summe aller Fees
        """
        filled = [log for log in self._order_log if log.result.status == "filled"]
        rejected = [log for log in self._order_log if log.result.status == "rejected"]

        total_notional = 0.0
        total_fees = 0.0

        for log in filled:
            if log.result.fill:
                total_notional += log.result.fill.quantity * log.result.fill.price
                if log.result.fill.fee:
                    total_fees += log.result.fill.fee

        total_orders = len(self._order_log)

        return {
            "total_orders": total_orders,
            "filled_orders": len(filled),
            "rejected_orders": len(rejected),
            "fill_rate": len(filled) / total_orders if total_orders > 0 else 0.0,
            "total_notional": total_notional,
            "total_fees": total_fees,
            "mode": EXECUTION_MODE_SHADOW_RUN,
            "fee_rate": self._ctx.fee_rate,
            "slippage_bps": self._ctx.slippage_bps,
        }

    def clear_order_log(self) -> None:
        """Löscht das Order-Log."""
        self._order_log.clear()

    def reset(self) -> None:
        """Setzt den Executor zurück (Zähler und Log)."""
        self._execution_count = 0
        self._order_log.clear()
        logger.debug("[SHADOW EXECUTOR] Reset durchgeführt")


# =============================================================================
# Factory-Funktion
# =============================================================================


def create_shadow_executor(
    prices: Optional[Dict[str, float]] = None,
    fee_rate: float = 0.0005,
    slippage_bps: float = 0.0,
    base_currency: str = "EUR",
) -> ShadowOrderExecutor:
    """
    Factory-Funktion für einen ShadowOrderExecutor.

    Args:
        prices: Optionale initiale Preise (Symbol -> Preis)
        fee_rate: Fee-Rate (z.B. 0.0005 = 5 bps = 0.05%)
        slippage_bps: Slippage in Basispunkten (z.B. 5 = 0.05%)
        base_currency: Basis-Währung für Fees

    Returns:
        Konfigurierter ShadowOrderExecutor

    Example:
        >>> executor = create_shadow_executor(
        ...     prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
        ...     fee_rate=0.001,  # 10 bps
        ...     slippage_bps=5.0,
        ... )
    """
    ctx = ShadowMarketContext(
        prices=prices or {},
        fee_rate=fee_rate,
        slippage_bps=slippage_bps,
        base_currency=base_currency,
    )
    return ShadowOrderExecutor(market_context=ctx)
