# src/orders/exchange.py
"""
Peak_Trade: Exchange-Order-Executors (Testnet/Live)
===================================================

Implementiert Order-Executors für Testnet- und Live-Trading.

Phase 17 Verhalten:
    - KEINE echten Orders werden gesendet
    - TestnetOrderExecutor: Dry-Run mit Logging
    - LiveOrderExecutor: Immer blockiert (nicht implementiert)

Alle Executors verwenden den SafetyGuard, um sicherzustellen,
dass keine unbeabsichtigten echten Orders gesendet werden.

WICHTIG: In Phase 17 werden KEINE echten API-Calls durchgeführt!
         Dies ist eine reine Architektur-Vorbereitung.
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

# Direkte Imports von safety.py (src/live/__init__.py verwendet lazy-loading)
from src.live.safety import (
    SafetyGuard,
    LiveNotImplementedError,
    TestnetDryRunOnlyError,
)
from src.core.environment import EnvironmentConfig, TradingEnvironment

logger = logging.getLogger(__name__)


# =============================================================================
# Execution Mode Constants
# =============================================================================

# Status-Werte für verschiedene Ausführungsmodi
EXECUTION_MODE_DRY_RUN = "dry_run"
EXECUTION_MODE_TESTNET_DRY_RUN = "testnet_dry_run"
EXECUTION_MODE_LIVE_BLOCKED = "live_blocked"
EXECUTION_MODE_SIMULATED = "simulated"


# =============================================================================
# Dry-Run Order Log Entry
# =============================================================================


@dataclass
class DryRunOrderLog:
    """
    Log-Eintrag für eine Dry-Run-Order.

    Attributes:
        timestamp: Zeitpunkt des Dry-Runs
        request: Die ursprüngliche OrderRequest
        simulated_result: Das simulierte Ergebnis
        environment: Die aktive Umgebung
        notes: Zusätzliche Notizen
    """

    timestamp: datetime
    request: OrderRequest
    simulated_result: OrderExecutionResult
    environment: TradingEnvironment
    notes: Optional[str] = None


# =============================================================================
# TestnetOrderExecutor (Dry-Run)
# =============================================================================


class TestnetOrderExecutor:
    """
    Testnet-Order-Executor im Dry-Run-Modus.

    Simuliert Testnet-Orders ohne echte API-Calls.
    Alle Orders werden geloggt und erzeugen simulierte Results.

    Phase 17 Verhalten:
        - KEINE echten Testnet-API-Calls
        - Orders werden nur simuliert/geloggt
        - OrderExecutionResult mit status "testnet_dry_run"

    Attributes:
        safety_guard: SafetyGuard für Safety-Checks
        simulated_prices: Optionale simulierte Preise für Fill-Berechnung
        fee_bps: Simulierte Fee in Basispunkten
        slippage_bps: Simulierte Slippage in Basispunkten

    Example:
        >>> env_config = EnvironmentConfig(environment=TradingEnvironment.TESTNET)
        >>> guard = SafetyGuard(env_config=env_config)
        >>> executor = TestnetOrderExecutor(safety_guard=guard)
        >>> result = executor.execute_order(order)  # Dry-Run
    """

    def __init__(
        self,
        safety_guard: SafetyGuard,
        simulated_prices: Optional[Dict[str, float]] = None,
        fee_bps: float = 10.0,
        slippage_bps: float = 5.0,
    ) -> None:
        """
        Initialisiert den TestnetOrderExecutor.

        Args:
            safety_guard: SafetyGuard für Safety-Prüfungen
            simulated_prices: Optionale Preise für Simulation
            fee_bps: Simulierte Fee in Basispunkten (Default: 10)
            slippage_bps: Simulierte Slippage in Basispunkten (Default: 5)
        """
        self._safety_guard = safety_guard
        self._simulated_prices = simulated_prices or {}
        self._fee_bps = fee_bps
        self._slippage_bps = slippage_bps
        self._execution_count = 0
        self._order_log: List[DryRunOrderLog] = []

    def set_simulated_price(self, symbol: str, price: float) -> None:
        """Setzt einen simulierten Preis für ein Symbol."""
        if price <= 0:
            raise ValueError(f"Preis muss > 0 sein: {price}")
        self._simulated_prices[symbol] = price

    def get_simulated_price(self, symbol: str) -> Optional[float]:
        """Gibt den simulierten Preis für ein Symbol zurück."""
        return self._simulated_prices.get(symbol)

    def _compute_simulated_fill_price(self, order: OrderRequest, base_price: float) -> float:
        """Berechnet den simulierten Fill-Preis mit Slippage."""
        if self._slippage_bps == 0.0:
            return base_price

        slip_factor = self._slippage_bps / 10000.0
        if order.side == "buy":
            return base_price * (1.0 + slip_factor)
        else:
            return base_price * (1.0 - slip_factor)

    def _compute_simulated_fee(self, notional: float) -> float:
        """Berechnet die simulierte Fee."""
        if self._fee_bps == 0.0:
            return 0.0
        return abs(notional) * (self._fee_bps / 10000.0)

    def execute_order(self, order: OrderRequest) -> OrderExecutionResult:
        """
        Führt eine Testnet-Order im Dry-Run-Modus aus.

        In Phase 17 wird KEINE echte Order gesendet.
        Stattdessen wird ein simuliertes Ergebnis erzeugt.

        Args:
            order: Die auszuführende OrderRequest

        Returns:
            OrderExecutionResult mit status und metadata

        Note:
            Diese Methode wirft keine Exception, sondern erzeugt
            ein simuliertes Result für Dry-Run-Zwecke.
        """
        self._execution_count += 1
        now = datetime.now(timezone.utc)

        # Log-Info
        logger.info(
            f"[TESTNET DRY-RUN] Order #{self._execution_count}: "
            f"{order.side.upper()} {order.quantity} {order.symbol} @ {order.order_type}"
        )

        # Prüfe ob wir einen Preis für das Symbol haben
        base_price = self._simulated_prices.get(order.symbol)

        if base_price is None:
            # Kein Preis -> simuliere Rejection
            result = OrderExecutionResult(
                status="rejected",
                request=order,
                fill=None,
                reason=f"no_simulated_price: {order.symbol}",
                metadata={
                    "execution_id": self._execution_count,
                    "mode": EXECUTION_MODE_TESTNET_DRY_RUN,
                    "environment": "testnet",
                    "dry_run": True,
                    "note": "Setze einen simulierten Preis mit set_simulated_price()",
                },
            )
        else:
            # Simuliere erfolgreichen Fill
            fill_price = self._compute_simulated_fill_price(order, base_price)
            notional = order.quantity * fill_price
            fee = self._compute_simulated_fee(notional)

            fill = OrderFill(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=fill_price,
                timestamp=now,
                fee=fee if fee > 0 else None,
                fee_currency="EUR" if fee > 0 else None,
            )

            result = OrderExecutionResult(
                status="filled",
                request=order,
                fill=fill,
                reason=None,
                metadata={
                    "execution_id": self._execution_count,
                    "mode": EXECUTION_MODE_TESTNET_DRY_RUN,
                    "environment": "testnet",
                    "dry_run": True,
                    "simulated_market_price": base_price,
                    "notional": notional,
                    "fee": fee,
                    "slippage_bps": self._slippage_bps,
                    "note": "KEIN echter API-Call - nur Dry-Run-Simulation",
                },
            )

        # Log Entry speichern
        log_entry = DryRunOrderLog(
            timestamp=now,
            request=order,
            simulated_result=result,
            environment=TradingEnvironment.TESTNET,
            notes="Phase 17 Dry-Run - keine echten Testnet-Orders",
        )
        self._order_log.append(log_entry)

        return result

    def execute_orders(self, orders: Sequence[OrderRequest]) -> List[OrderExecutionResult]:
        """Führt mehrere Orders im Dry-Run aus."""
        return [self.execute_order(order) for order in orders]

    def get_execution_count(self) -> int:
        """Gibt die Anzahl der ausgeführten Dry-Run-Orders zurück."""
        return self._execution_count

    def get_order_log(self) -> List[DryRunOrderLog]:
        """Gibt eine Kopie des Order-Logs zurück."""
        return list(self._order_log)

    def clear_order_log(self) -> None:
        """Löscht das Order-Log."""
        self._order_log.clear()

    def reset(self) -> None:
        """Setzt den Executor zurück."""
        self._execution_count = 0
        self._order_log.clear()


# =============================================================================
# LiveOrderExecutor (Stub - NOT IMPLEMENTED)
# =============================================================================


class LiveOrderExecutor:
    """
    Live-Order-Executor (Phase 71: Design & Dry-Run).

    Phase 71 Verhalten:
        - Live-Execution-Path existiert als Design
        - Im Dry-Run-Modus: Nur Logging, keine echten Orders
        - Echte Live-Orders sind weiterhin blockiert

    Dieser Executor demonstriert, wie ein Live-Execution-Path aussehen würde,
    aber er ist technisch auf "Dry-Run" verdrahtet.

    WICHTIG: In Phase 71 sendet diese Klasse KEINE echten Orders!
             Alle Live-Operationen sind als TODO/commented-out/NotImplemented
             gekennzeichnet.

    Attributes:
        safety_guard: SafetyGuard für Safety-Prüfungen
        simulated_prices: Optionale simulierte Preise für Dry-Run-Fill-Berechnung
        fee_bps: Simulierte Fee in Basispunkten
        slippage_bps: Simulierte Slippage in Basispunkten
        dry_run_mode: Ob im Dry-Run-Modus (Default: True in Phase 71)

    Example:
        >>> env_config = EnvironmentConfig(
        ...     environment=TradingEnvironment.LIVE,
        ...     live_dry_run_mode=True  # Phase 71: Immer True
        ... )
        >>> guard = SafetyGuard(env_config=env_config)
        >>> executor = LiveOrderExecutor(safety_guard=guard, dry_run_mode=True)
        >>> result = executor.execute_order(order)  # Dry-Run mit Logging
    """

    def __init__(
        self,
        safety_guard: SafetyGuard,
        simulated_prices: Optional[Dict[str, float]] = None,
        fee_bps: float = 10.0,
        slippage_bps: float = 5.0,
        dry_run_mode: bool = True,
        # Zukünftige Parameter (nicht verwendet in Phase 71):
        # exchange_client: Any = None,
        # api_key: str = "",
        # api_secret: str = "",
    ) -> None:
        """
        Initialisiert den LiveOrderExecutor.

        Args:
            safety_guard: SafetyGuard für Safety-Prüfungen
            simulated_prices: Optionale Preise für Dry-Run-Simulation
            fee_bps: Simulierte Fee in Basispunkten (Default: 10)
            slippage_bps: Simulierte Slippage in Basispunkten (Default: 5)
            dry_run_mode: Ob im Dry-Run-Modus (Default: True in Phase 71)

        Note:
            In Phase 71 ist dry_run_mode immer True.
            Echte Live-Orders werden erst in einer späteren Phase implementiert.
        """
        self._safety_guard = safety_guard
        self._simulated_prices = simulated_prices or {}
        self._fee_bps = fee_bps
        self._slippage_bps = slippage_bps
        self._dry_run_mode = dry_run_mode
        self._execution_count = 0
        self._order_log: List[DryRunOrderLog] = []

        # Phase 71: Immer Dry-Run
        if not self._dry_run_mode:
            logger.warning(
                "[LIVE EXECUTOR] dry_run_mode=False gesetzt, aber Phase 71 "
                "erlaubt nur Dry-Run. Setze auf True."
            )
            self._dry_run_mode = True

        logger.info(
            "[LIVE EXECUTOR] LiveOrderExecutor initialisiert im Dry-Run-Modus. "
            "Phase 71: Nur Design/Logging, keine echten Orders. "
            "[SAFETY] Live execution blocked – system is Phase 71 (design only, no real orders)."
        )

    def set_simulated_price(self, symbol: str, price: float) -> None:
        """Setzt einen simulierten Preis für ein Symbol."""
        if price <= 0:
            raise ValueError(f"Preis muss > 0 sein: {price}")
        self._simulated_prices[symbol] = price

    def get_simulated_price(self, symbol: str) -> Optional[float]:
        """Gibt den simulierten Preis für ein Symbol zurück."""
        return self._simulated_prices.get(symbol)

    def _compute_simulated_fill_price(self, order: OrderRequest, base_price: float) -> float:
        """Berechnet den simulierten Fill-Preis mit Slippage."""
        if self._slippage_bps == 0.0:
            return base_price

        slip_factor = self._slippage_bps / 10000.0
        if order.side == "buy":
            return base_price * (1.0 + slip_factor)
        else:
            return base_price * (1.0 - slip_factor)

    def _compute_simulated_fee(self, notional: float) -> float:
        """Berechnet die simulierte Fee."""
        if self._fee_bps == 0.0:
            return 0.0
        return abs(notional) * (self._fee_bps / 10000.0)

    def execute_order(self, order: OrderRequest) -> OrderExecutionResult:
        """
        Führt eine Live-Order im Dry-Run-Modus aus (Phase 71).

        In Phase 71 wird KEINE echte Order gesendet.
        Stattdessen wird ein simuliertes Ergebnis erzeugt und geloggt.

        Args:
            order: Die auszuführende OrderRequest

        Returns:
            OrderExecutionResult mit status und metadata

        Note:
            Diese Methode wirft keine Exception, sondern erzeugt
            ein simuliertes Result für Dry-Run-Zwecke.
            Echte Live-Orders sind weiterhin blockiert.
        """
        self._execution_count += 1
        now = datetime.now(timezone.utc)

        # Phase 71: Immer Dry-Run
        if not self._dry_run_mode:
            logger.warning(
                "[LIVE EXECUTOR] dry_run_mode=False, aber Phase 71 erlaubt nur Dry-Run. "
                "Führe Dry-Run aus."
            )

        # Log-Info - explizit als Dry-Run kennzeichnen
        logger.info(
            f"[LIVE-DRY-RUN] Would send LIVE order #{self._execution_count}: "
            f"{order.side.upper()} {order.quantity} {order.symbol} @ {order.order_type} "
            f"(Phase 71 – no real exchange call, design only)"
        )

        # Prüfe ob wir einen Preis für das Symbol haben
        base_price = self._simulated_prices.get(order.symbol)

        if base_price is None:
            # Kein Preis -> simuliere Rejection
            result = OrderExecutionResult(
                status="rejected",
                request=order,
                fill=None,
                reason=f"no_simulated_price: {order.symbol}",
                metadata={
                    "execution_id": self._execution_count,
                    "mode": "live_dry_run",
                    "environment": "live",
                    "dry_run": True,
                    "phase": "71",
                    "note": "Phase 71: Live-Execution-Design - nur Dry-Run, keine echten Orders. "
                    "Setze einen simulierten Preis mit set_simulated_price()",
                },
            )
        else:
            # Simuliere erfolgreichen Fill
            fill_price = self._compute_simulated_fill_price(order, base_price)
            notional = order.quantity * fill_price
            fee = self._compute_simulated_fee(notional)

            fill = OrderFill(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=fill_price,
                timestamp=now,
                fee=fee if fee > 0 else None,
                fee_currency="EUR" if fee > 0 else None,
            )

            result = OrderExecutionResult(
                status="filled",
                request=order,
                fill=fill,
                reason=None,
                metadata={
                    "execution_id": self._execution_count,
                    "mode": "live_dry_run",
                    "environment": "live",
                    "dry_run": True,
                    "phase": "71",
                    "simulated_market_price": base_price,
                    "notional": notional,
                    "fee": fee,
                    "slippage_bps": self._slippage_bps,
                    "note": "Phase 71: KEIN echter API-Call - nur Dry-Run-Simulation. "
                    "Live-Execution-Path existiert als Design, aber ist technisch "
                    "auf Dry-Run verdrahtet. Keine echten Orders werden gesendet.",
                },
            )

        # Log Entry speichern
        log_entry = DryRunOrderLog(
            timestamp=now,
            request=order,
            simulated_result=result,
            environment=TradingEnvironment.LIVE,
            notes="Phase 71: Live-Execution-Design - nur Dry-Run, keine echten Orders",
        )
        self._order_log.append(log_entry)

        return result

    def execute_orders(self, orders: Sequence[OrderRequest]) -> List[OrderExecutionResult]:
        """Führt mehrere Orders im Dry-Run aus."""
        return [self.execute_order(order) for order in orders]

    def get_execution_count(self) -> int:
        """Gibt die Anzahl der ausgeführten Dry-Run-Orders zurück."""
        return self._execution_count

    def get_order_log(self) -> List[DryRunOrderLog]:
        """Gibt eine Kopie des Order-Logs zurück."""
        return list(self._order_log)

    def clear_order_log(self) -> None:
        """Löscht das Order-Log."""
        self._order_log.clear()

    def reset(self) -> None:
        """Setzt den Executor zurück."""
        self._execution_count = 0
        self._order_log.clear()

    @property
    def is_dry_run(self) -> bool:
        """True wenn im Dry-Run-Modus (Phase 71: immer True)."""
        return self._dry_run_mode


# =============================================================================
# ExchangeOrderExecutor (Unified - mit Safety-Guard) - Phase 38 erweitert
# =============================================================================

# TYPE_CHECKING Import für TradingExchangeClient (vermeidet Zirkularimport)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.exchange.base import TradingExchangeClient, ExchangeOrderResult


class ExchangeOrderExecutor:
    """
    Unified Exchange-Order-Executor mit Safety-Guard.

    Phase 38 erweitert: Kann jetzt optional einen TradingExchangeClient nutzen.

    Modi:
    - Ohne TradingExchangeClient: Dry-Run via TestnetOrderExecutor (bisheriges Verhalten)
    - Mit TradingExchangeClient: Echte Aufrufe auf dem Client (z.B. DummyExchangeClient)

    Environment-Verhalten:
    - PAPER: Verwendet PaperOrderExecutor (nicht hier, separat)
    - TESTNET: Dry-Run oder TradingExchangeClient (je nach Konfiguration)
    - LIVE: Blockiert (nicht implementiert)

    Example (Dry-Run):
        >>> executor = ExchangeOrderExecutor(safety_guard=guard)
        >>> executor.execute_order(order)  # Dry-Run

    Example (mit TradingExchangeClient):
        >>> from src.exchange.dummy_client import DummyExchangeClient
        >>> client = DummyExchangeClient(simulated_prices={"BTC/EUR": 50000})
        >>> executor = ExchangeOrderExecutor(safety_guard=guard, trading_client=client)
        >>> executor.execute_order(order)  # Nutzt DummyExchangeClient
    """

    def __init__(
        self,
        safety_guard: SafetyGuard,
        simulated_prices: Optional[Dict[str, float]] = None,
        trading_client: Optional["TradingExchangeClient"] = None,
    ) -> None:
        """
        Initialisiert den ExchangeOrderExecutor.

        Args:
            safety_guard: SafetyGuard für Safety-Prüfungen
            simulated_prices: Optionale Preise für Dry-Run-Simulation
            trading_client: Optionaler TradingExchangeClient für echte Order-Aufrufe
                           (Phase 38: z.B. DummyExchangeClient, KrakenTestnetClient)
        """
        self._safety_guard = safety_guard
        self._simulated_prices = simulated_prices or {}
        self._trading_client = trading_client

        # Interner Testnet-Executor für Dry-Run (wenn kein Client)
        self._testnet_executor = TestnetOrderExecutor(
            safety_guard=safety_guard,
            simulated_prices=self._simulated_prices,
        )

        self._execution_count = 0
        self._use_trading_client = trading_client is not None

        env = safety_guard.env_config.environment
        mode_info = (
            f"TradingClient={trading_client.get_name()}" if self._use_trading_client else "Dry-Run"
        )
        logger.info(f"[EXCHANGE EXECUTOR] Initialisiert im {env.value}-Modus. Mode: {mode_info}")

    @property
    def is_dry_run(self) -> bool:
        """True wenn im Dry-Run-Modus (kein TradingExchangeClient)."""
        return not self._use_trading_client

    @property
    def trading_client(self) -> Optional["TradingExchangeClient"]:
        """Gibt den TradingExchangeClient zurück (oder None)."""
        return self._trading_client

    def set_simulated_price(self, symbol: str, price: float) -> None:
        """Setzt einen simulierten Preis für Dry-Run."""
        self._simulated_prices[symbol] = price
        self._testnet_executor.set_simulated_price(symbol, price)

    def execute_order(self, order: OrderRequest) -> OrderExecutionResult:
        """
        Führt eine Order aus.

        Bei TradingExchangeClient: Echte Aufrufe auf dem Client.
        Ohne TradingExchangeClient: Dry-Run-Simulation.

        Args:
            order: Die auszuführende OrderRequest

        Returns:
            OrderExecutionResult mit Status und Fill-Informationen

        Raises:
            SafetyBlockedError: Bei nicht erlaubten Operationen
            LiveNotImplementedError: Im Live-Modus (ohne Client)
        """
        self._execution_count += 1
        env = self._safety_guard.env_config.environment

        # Paper -> nicht über diesen Executor, sondern PaperOrderExecutor
        if env == TradingEnvironment.PAPER and not self._use_trading_client:
            logger.warning(
                f"[EXCHANGE EXECUTOR] Paper-Modus: Verwende PaperOrderExecutor stattdessen."
            )
            return OrderExecutionResult(
                status="rejected",
                request=order,
                fill=None,
                reason="use_paper_executor",
                metadata={
                    "execution_id": self._execution_count,
                    "mode": "paper_redirect",
                    "note": "Im Paper-Modus sollte PaperOrderExecutor verwendet werden",
                },
            )

        # Mit TradingExchangeClient: Echte Aufrufe (Phase 38)
        if self._use_trading_client and self._trading_client is not None:
            return self._execute_via_trading_client(order)

        # Testnet ohne Client -> Dry-Run
        if env == TradingEnvironment.TESTNET:
            logger.info(f"[EXCHANGE EXECUTOR] Testnet Dry-Run für {order.symbol}")
            return self._testnet_executor.execute_order(order)

        # Live ohne Client -> blockiert
        if env == TradingEnvironment.LIVE:
            # Safety-Check wirft Exception
            self._safety_guard.ensure_may_place_order(is_testnet=False)

            # Sollte nie erreicht werden
            raise LiveNotImplementedError("Live-Trading ist in Phase 17 nicht implementiert.")

        # Unbekannter Modus
        return OrderExecutionResult(
            status="rejected",
            request=order,
            fill=None,
            reason=f"unknown_environment: {env}",
            metadata={
                "execution_id": self._execution_count,
                "mode": "unknown",
            },
        )

    def _execute_via_trading_client(self, order: OrderRequest) -> OrderExecutionResult:
        """
        Führt eine Order über den TradingExchangeClient aus (Phase 38).

        Args:
            order: Die auszuführende OrderRequest

        Returns:
            OrderExecutionResult mit Status und Fill-Informationen
        """
        from src.exchange.base import ExchangeOrderStatus

        assert self._trading_client is not None

        now = datetime.now(timezone.utc)
        client_name = self._trading_client.get_name()

        logger.info(
            f"[EXCHANGE EXECUTOR] Order via {client_name}: "
            f"{order.side.upper()} {order.quantity} {order.symbol} @ {order.order_type}"
        )

        try:
            # Order über TradingExchangeClient platzieren
            exchange_order_id = self._trading_client.place_order(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                order_type=order.order_type,
                limit_price=order.limit_price,
                client_order_id=order.client_id,
            )

            # Status abfragen
            exchange_result = self._trading_client.get_order_status(exchange_order_id)

            # ExchangeOrderResult -> OrderExecutionResult mappen
            return self._map_exchange_result_to_execution_result(
                order=order,
                exchange_order_id=exchange_order_id,
                exchange_result=exchange_result,
                client_name=client_name,
                timestamp=now,
            )

        except Exception as e:
            logger.error(f"[EXCHANGE EXECUTOR] Order fehlgeschlagen via {client_name}: {e}")
            return OrderExecutionResult(
                status="rejected",
                request=order,
                fill=None,
                reason=f"trading_client_error: {e}",
                metadata={
                    "execution_id": self._execution_count,
                    "mode": f"trading_client_{client_name}",
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

    def _map_exchange_result_to_execution_result(
        self,
        order: OrderRequest,
        exchange_order_id: str,
        exchange_result: "ExchangeOrderResult",
        client_name: str,
        timestamp: datetime,
    ) -> OrderExecutionResult:
        """
        Mappt ExchangeOrderResult auf OrderExecutionResult.

        Args:
            order: Die ursprüngliche OrderRequest
            exchange_order_id: ID der Order auf der Exchange
            exchange_result: Ergebnis vom TradingExchangeClient
            client_name: Name des Clients
            timestamp: Zeitstempel

        Returns:
            OrderExecutionResult
        """
        from src.exchange.base import ExchangeOrderStatus

        # Status mappen
        status_mapping: Dict[ExchangeOrderStatus, OrderStatus] = {
            ExchangeOrderStatus.FILLED: "filled",
            ExchangeOrderStatus.PARTIALLY_FILLED: "partially_filled",
            ExchangeOrderStatus.PENDING: "pending",
            ExchangeOrderStatus.OPEN: "pending",
            ExchangeOrderStatus.CANCELLED: "cancelled",
            ExchangeOrderStatus.REJECTED: "rejected",
            ExchangeOrderStatus.EXPIRED: "rejected",
            ExchangeOrderStatus.VALIDATED: "filled",  # validate_only counts as success
        }

        mapped_status = status_mapping.get(exchange_result.status, "rejected")

        # Fill erstellen wenn gefüllt
        fill = None
        if exchange_result.filled_qty > 0 and exchange_result.avg_price is not None:
            fill = OrderFill(
                symbol=order.symbol,
                side=order.side,
                quantity=exchange_result.filled_qty,
                price=exchange_result.avg_price,
                timestamp=timestamp,
                fee=exchange_result.fee,
                fee_currency=exchange_result.fee_currency,
            )

        return OrderExecutionResult(
            status=mapped_status,
            request=order,
            fill=fill,
            reason=None
            if mapped_status in ("filled", "pending", "partially_filled")
            else f"status_{exchange_result.status.value}",
            metadata={
                "execution_id": self._execution_count,
                "mode": f"trading_client_{client_name}",
                "exchange_order_id": exchange_order_id,
                "exchange_status": exchange_result.status.value,
                "client_name": client_name,
            },
        )

    def execute_orders(self, orders: Sequence[OrderRequest]) -> List[OrderExecutionResult]:
        """Führt mehrere Orders aus."""
        return [self.execute_order(order) for order in orders]

    def get_execution_count(self) -> int:
        """Gibt die Anzahl der ausgeführten Orders zurück."""
        return self._execution_count

    def get_testnet_order_log(self) -> List[DryRunOrderLog]:
        """Gibt das Testnet-Dry-Run-Log zurück."""
        return self._testnet_executor.get_order_log()

    # =========================================================================
    # Factory Methods (Phase 38)
    # =========================================================================

    @classmethod
    def from_config(
        cls,
        cfg: "PeakConfig",
        safety_guard: Optional[SafetyGuard] = None,
    ) -> "ExchangeOrderExecutor":
        """
        Factory: Erstellt ExchangeOrderExecutor aus PeakConfig.

        Args:
            cfg: PeakConfig-Instanz
            safety_guard: Optionaler SafetyGuard (sonst aus Config erstellt)

        Returns:
            Konfigurierter ExchangeOrderExecutor

        Example:
            >>> from src.core.peak_config import load_config
            >>> cfg = load_config()
            >>> executor = ExchangeOrderExecutor.from_config(cfg)
        """
        from src.exchange import build_trading_client_from_config
        from src.core.environment import get_environment_from_config

        # Safety-Guard erstellen wenn nicht übergeben
        if safety_guard is None:
            env_config = get_environment_from_config(cfg)
            safety_guard = SafetyGuard(env_config=env_config)

        # TradingExchangeClient aus Config erstellen
        trading_client = build_trading_client_from_config(cfg)

        return cls(
            safety_guard=safety_guard,
            trading_client=trading_client,
        )


# Type alias für Rückwärtskompatibilität
PeakConfig = Any  # Vermeidet Import, wird nur für Type-Hints genutzt


# =============================================================================
# Factory-Funktion: create_order_executor (Phase 71)
# =============================================================================


def create_order_executor(
    env_config: EnvironmentConfig,
    simulated_prices: Optional[Dict[str, float]] = None,
    trading_client: Optional["TradingExchangeClient"] = None,
) -> OrderExecutor:
    """
    Factory-Funktion: Erstellt den passenden OrderExecutor basierend auf EnvironmentConfig.

    Phase 71: Live-Execution-Design
        - PAPER/Shadow: PaperOrderExecutor (oder ShadowOrderExecutor)
        - TESTNET: TestnetOrderExecutor (Dry-Run)
        - LIVE: LiveOrderExecutor (Dry-Run in Phase 71)

    Entscheidungslogik:
        1. env.mode == "paper" → PaperOrderExecutor (oder ShadowOrderExecutor)
        2. env.mode == "testnet" → TestnetOrderExecutor (Dry-Run)
        3. env.mode == "live" → LiveOrderExecutor (Dry-Run in Phase 71)
        4. Mit trading_client → ExchangeOrderExecutor (kann echte Calls machen)

    Args:
        env_config: EnvironmentConfig mit Mode und Flags
        simulated_prices: Optionale simulierte Preise für Dry-Run
        trading_client: Optionaler TradingExchangeClient für echte Order-Aufrufe

    Returns:
        OrderExecutor-Instanz (PaperOrderExecutor, TestnetOrderExecutor, LiveOrderExecutor, etc.)

    Example:
        >>> from src.core.environment import EnvironmentConfig, TradingEnvironment
        >>> from src.live.safety import SafetyGuard
        >>>
        >>> # Paper-Modus
        >>> env = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        >>> executor = create_order_executor(env)
        >>> # executor ist PaperOrderExecutor
        >>>
        >>> # Testnet-Modus
        >>> env = EnvironmentConfig(environment=TradingEnvironment.TESTNET)
        >>> guard = SafetyGuard(env_config=env)
        >>> executor = create_order_executor(env)
        >>> # executor ist TestnetOrderExecutor (Dry-Run)
        >>>
        >>> # Live-Modus (Phase 71: Dry-Run)
        >>> env = EnvironmentConfig(
        ...     environment=TradingEnvironment.LIVE,
        ...     live_dry_run_mode=True  # Phase 71: Immer True
        ... )
        >>> guard = SafetyGuard(env_config=env)
        >>> executor = create_order_executor(env)
        >>> # executor ist LiveOrderExecutor (Dry-Run)

    Note:
        In Phase 71 ist LiveOrderExecutor immer im Dry-Run-Modus.
        Echte Live-Orders werden erst in einer späteren Phase implementiert.
    """
    from .paper import PaperOrderExecutor, PaperMarketContext
    from src.live.safety import SafetyGuard

    env = env_config.environment
    guard = SafetyGuard(env_config=env_config)

    # Mit TradingExchangeClient: ExchangeOrderExecutor (kann echte Calls machen)
    if trading_client is not None:
        logger.info(
            f"[FACTORY] Erstelle ExchangeOrderExecutor mit TradingClient "
            f"({trading_client.get_name()}) für {env.value}-Modus"
        )
        return ExchangeOrderExecutor(
            safety_guard=guard,
            simulated_prices=simulated_prices,
            trading_client=trading_client,
        )

    # PAPER/Shadow: PaperOrderExecutor
    if env == TradingEnvironment.PAPER:
        logger.info("[FACTORY] Erstelle PaperOrderExecutor für Paper-Modus")
        market_ctx = PaperMarketContext(
            prices=simulated_prices or {},
            fee_bps=10.0,
            slippage_bps=5.0,
        )
        return PaperOrderExecutor(market_context=market_ctx)

    # TESTNET: TestnetOrderExecutor (Dry-Run)
    if env == TradingEnvironment.TESTNET:
        logger.info("[FACTORY] Erstelle TestnetOrderExecutor (Dry-Run) für Testnet-Modus")
        return TestnetOrderExecutor(
            safety_guard=guard,
            simulated_prices=simulated_prices,
            fee_bps=10.0,
            slippage_bps=5.0,
        )

    # LIVE: LiveOrderExecutor (Phase 71: Dry-Run)
    if env == TradingEnvironment.LIVE:
        # Phase 71: Immer Dry-Run
        dry_run = env_config.live_dry_run_mode
        if not dry_run:
            logger.warning(
                "[FACTORY] live_dry_run_mode=False, aber Phase 71 erlaubt nur Dry-Run. "
                "Setze auf True."
            )
            dry_run = True

        logger.info(
            "[FACTORY] Erstelle LiveOrderExecutor (Dry-Run) für Live-Modus "
            "(Phase 71: Nur Design/Logging, keine echten Orders)"
        )
        return LiveOrderExecutor(
            safety_guard=guard,
            simulated_prices=simulated_prices,
            fee_bps=10.0,
            slippage_bps=5.0,
            dry_run_mode=True,  # Phase 71: Immer True
        )

    # Unbekannter Modus -> Fallback auf Paper
    logger.warning(
        f"[FACTORY] Unbekannter Environment-Modus: {env}. Fallback auf PaperOrderExecutor"
    )
    market_ctx = PaperMarketContext(
        prices=simulated_prices or {},
        fee_bps=10.0,
        slippage_bps=5.0,
    )
    return PaperOrderExecutor(market_context=market_ctx)
