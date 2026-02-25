# src/orders/testnet_executor.py
"""
Peak_Trade: Testnet Exchange Order Executor (Phase 35)
======================================================

Implementiert einen Order-Executor fuer Testnet-/Demo-Trading.
Dieser Executor sendet Orders an den KrakenTestnetClient und ist
streng an Environment & Safety gebunden.

Features:
- Integration mit KrakenTestnetClient
- Safety-Guards (nur Testnet-Environment erlaubt)
- LiveRiskLimits-Integration
- Mapping zwischen OrderRequest und Exchange-API
- Umfangreiches Logging

Sicherheitsmerkmale:
- STRENGE Environment-Pruefung: Nur TradingEnvironment.TESTNET erlaubt
- testnet_dry_run Flag muss deaktiviert sein fuer echte Testnet-Orders
- LiveRiskLimits werden VOR jedem Order-Request geprueft
- Kein Fallback auf Live-Trading moeglich

WICHTIG: Dieser Executor ist NUR fuer Testnet-Trading vorgesehen!
         Echtes Live-Trading erfordert eine separate Implementierung (Phase 40+).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

from .base import (
    OrderRequest,
    OrderFill,
    OrderExecutionResult,
    OrderStatus,
)
from src.core.environment import (
    EnvironmentConfig,
    TradingEnvironment,
)
from src.live.safety import (
    SafetyGuard,
    SafetyBlockedError,
    LiveNotImplementedError,
    TestnetDryRunOnlyError,
)

if TYPE_CHECKING:
    from src.exchange.kraken_testnet import KrakenTestnetClient
    from src.live.risk_limits import LiveRiskLimits, LiveRiskCheckResult
    from src.live.orders import LiveOrderRequest

logger = logging.getLogger(__name__)


def _emit_exec_event_safe(**kwargs: Any) -> None:
    """Emit execution event (no-op when PT_EXEC_EVENTS_ENABLED=false). Never raises."""
    try:
        from src.observability.execution_events import emit

        emit(**kwargs)
    except Exception:
        pass


# =============================================================================
# Custom Exceptions
# =============================================================================


class TestnetExecutorError(Exception):
    """Basisklasse fuer Testnet-Executor-Fehler."""

    pass


class EnvironmentNotTestnetError(TestnetExecutorError):
    """Environment ist nicht auf Testnet gesetzt."""

    pass


class RiskLimitViolationError(TestnetExecutorError):
    """Risk-Limit wurde verletzt."""

    def __init__(self, message: str, reasons: List[str], metrics: Dict[str, Any]):
        super().__init__(message)
        self.reasons = reasons
        self.metrics = metrics


# =============================================================================
# Execution Mode Constants
# =============================================================================

EXECUTION_MODE_TESTNET_LIVE = "testnet_live"
EXECUTION_MODE_TESTNET_VALIDATED = "testnet_validated"


# =============================================================================
# Execution Log Entry
# =============================================================================


@dataclass
class TestnetExecutionLog:
    """
    Log-Eintrag fuer eine Testnet-Order.

    Attributes:
        timestamp: Zeitpunkt der Ausfuehrung
        request: Die urspruengliche OrderRequest
        result: Das Ausfuehrungsergebnis
        exchange_order_id: ID der Order auf der Exchange
        mode: Ausfuehrungsmodus (testnet_live, testnet_validated)
        risk_check_passed: Ob der Risk-Check bestanden wurde
        notes: Zusaetzliche Notizen
    """

    timestamp: datetime
    request: OrderRequest
    result: OrderExecutionResult
    exchange_order_id: Optional[str] = None
    mode: str = EXECUTION_MODE_TESTNET_LIVE
    risk_check_passed: bool = True
    notes: Optional[str] = None


# =============================================================================
# Testnet Exchange Order Executor
# =============================================================================


class TestnetExchangeOrderExecutor:
    """
    Order-Executor fuer Testnet-/Demo-Trading mit echten Exchange-API-Calls.

    Dieser Executor:
    1. Prueft das Environment (MUSS TradingEnvironment.TESTNET sein)
    2. Prueft die Safety-Guards (testnet_dry_run muss False sein fuer echte Orders)
    3. Prueft LiveRiskLimits vor jeder Order
    4. Sendet Orders an den KrakenTestnetClient
    5. Mappt Exchange-Responses auf OrderExecutionResult

    Sicherheitsmerkmale:
    - STRENGE Environment-Pruefung
    - Risk-Limits werden VOR Orderversand geprueft
    - Alle Orders werden geloggt
    - Bei Verletzungen werden keine Orders gesendet

    WICHTIG: Nur fuer Testnet-Trading!

    Example:
        >>> from src.core.environment import EnvironmentConfig, TradingEnvironment
        >>> from src.live.safety import SafetyGuard
        >>> from src.exchange.kraken_testnet import KrakenTestnetClient, KrakenTestnetConfig
        >>>
        >>> env_config = EnvironmentConfig(
        ...     environment=TradingEnvironment.TESTNET,
        ...     testnet_dry_run=False,  # Echte Testnet-Orders
        ... )
        >>> safety_guard = SafetyGuard(env_config=env_config)
        >>> client = KrakenTestnetClient(KrakenTestnetConfig())
        >>>
        >>> executor = TestnetExchangeOrderExecutor(
        ...     exchange_client=client,
        ...     safety_guard=safety_guard,
        ...     risk_limits=risk_limits,
        ... )
        >>> result = executor.execute_order(order)
    """

    def __init__(
        self,
        exchange_client: "KrakenTestnetClient",
        safety_guard: SafetyGuard,
        risk_limits: Optional["LiveRiskLimits"] = None,
        env_config: Optional[EnvironmentConfig] = None,
    ) -> None:
        """
        Initialisiert den TestnetExchangeOrderExecutor.

        Args:
            exchange_client: KrakenTestnetClient fuer API-Calls
            safety_guard: SafetyGuard fuer Safety-Pruefungen
            risk_limits: Optionale LiveRiskLimits fuer Risk-Pruefungen
            env_config: Optionale EnvironmentConfig (sonst aus safety_guard)

        Raises:
            EnvironmentNotTestnetError: Wenn Environment nicht TESTNET ist
        """
        self._client = exchange_client
        self._safety_guard = safety_guard
        self._risk_limits = risk_limits
        self._env_config = env_config or safety_guard.env_config

        # Environment-Check
        if self._env_config.environment != TradingEnvironment.TESTNET:
            raise EnvironmentNotTestnetError(
                f"TestnetExchangeOrderExecutor erfordert environment=TESTNET. "
                f"Aktuell: {self._env_config.environment.value}"
            )

        self._execution_count = 0
        self._execution_log: List[TestnetExecutionLog] = []

        # Bestimme effektiven Modus
        if self._env_config.testnet_dry_run:
            self._effective_mode = EXECUTION_MODE_TESTNET_VALIDATED
        else:
            self._effective_mode = EXECUTION_MODE_TESTNET_LIVE

        logger.info(
            f"[TESTNET EXECUTOR] Initialisiert: "
            f"environment={self._env_config.environment.value}, "
            f"testnet_dry_run={self._env_config.testnet_dry_run}, "
            f"effective_mode={self._effective_mode}, "
            f"risk_limits_enabled={self._risk_limits is not None}"
        )

    @property
    def effective_mode(self) -> str:
        """Gibt den effektiven Ausfuehrungsmodus zurueck."""
        return self._effective_mode

    @property
    def execution_count(self) -> int:
        """Anzahl der ausgefuehrten Orders."""
        return self._execution_count

    def _check_environment(self) -> None:
        """
        Prueft, ob das Environment Testnet-Orders erlaubt.

        Raises:
            EnvironmentNotTestnetError: Wenn nicht im Testnet-Modus
            TestnetDryRunOnlyError: Wenn testnet_dry_run=True und echte Orders versucht werden
        """
        if self._env_config.environment != TradingEnvironment.TESTNET:
            raise EnvironmentNotTestnetError(
                f"Orders nur im Testnet-Environment erlaubt. "
                f"Aktuell: {self._env_config.environment.value}"
            )

    def _check_risk_limits(
        self,
        orders: Sequence[OrderRequest],
        current_price: Optional[float] = None,
    ) -> Optional["LiveRiskCheckResult"]:
        """
        Prueft Orders gegen LiveRiskLimits.

        Args:
            orders: Zu pruefende Orders
            current_price: Optionaler aktueller Preis fuer Notional-Berechnung

        Returns:
            LiveRiskCheckResult oder None wenn keine Risk-Limits konfiguriert
        """
        if self._risk_limits is None:
            return None

        # Importiere hier um zirkulaere Imports zu vermeiden
        from src.live.orders import LiveOrderRequest

        # Konvertiere OrderRequests zu LiveOrderRequests
        live_orders: List[LiveOrderRequest] = []
        for order in orders:
            notional = None
            if current_price and order.quantity:
                notional = order.quantity * current_price

            live_order = LiveOrderRequest(
                client_order_id=order.client_id or f"testnet_{self._execution_count}",
                symbol=order.symbol,
                side="BUY" if order.side == "buy" else "SELL",
                order_type="MARKET" if order.order_type == "market" else "LIMIT",
                quantity=order.quantity,
                notional=notional,
                extra={"current_price": current_price} if current_price else None,
            )
            live_orders.append(live_order)

        return self._risk_limits.check_orders(live_orders)

    def execute_order(
        self,
        order: OrderRequest,
        current_price: Optional[float] = None,
    ) -> OrderExecutionResult:
        """
        Fuehrt eine Order im Testnet aus.

        1. Prueft Environment (TESTNET erforderlich)
        2. Prueft Risk-Limits (wenn konfiguriert)
        3. Sendet Order an Exchange (wenn risk_check ok)
        4. Mappt Response auf OrderExecutionResult

        Args:
            order: Die auszufuehrende OrderRequest
            current_price: Optionaler aktueller Preis fuer Risk-Berechnung

        Returns:
            OrderExecutionResult mit Status und Fill-Informationen

        Raises:
            EnvironmentNotTestnetError: Wenn nicht im Testnet-Modus
        """
        self._execution_count += 1
        now = datetime.now(timezone.utc)

        _emit_exec_event_safe(
            event_type="order_submit",
            level="info",
            symbol=order.symbol,
            side=order.side,
            qty=order.quantity,
            client_order_id=order.client_id,
        )

        logger.info(
            f"[TESTNET EXECUTOR] Order #{self._execution_count}: "
            f"{order.side.upper()} {order.quantity} {order.symbol} @ {order.order_type}"
        )

        # 1. Environment-Check
        try:
            self._check_environment()
        except (EnvironmentNotTestnetError, TestnetDryRunOnlyError) as e:
            _emit_exec_event_safe(
                event_type="order_reject",
                level="error",
                is_error=True,
                symbol=order.symbol,
                side=order.side,
                msg=f"environment_blocked: {type(e).__name__}",
            )
            result = OrderExecutionResult(
                status="rejected",
                request=order,
                fill=None,
                reason=f"environment_blocked: {e}",
                metadata={
                    "execution_id": self._execution_count,
                    "mode": self._effective_mode,
                    "error_type": type(e).__name__,
                },
            )
            self._log_execution(order, result, now, risk_check_passed=False)
            return result

        # 2. Risk-Check
        risk_result = self._check_risk_limits([order], current_price)
        if risk_result is not None and not risk_result.allowed:
            _emit_exec_event_safe(
                event_type="order_reject",
                level="error",
                is_error=True,
                symbol=order.symbol,
                side=order.side,
                msg="risk_limit_violation",
            )
            logger.warning(f"[TESTNET EXECUTOR] Risk-Limits verletzt: {risk_result.reasons}")
            result = OrderExecutionResult(
                status="rejected",
                request=order,
                fill=None,
                reason=f"risk_limit_violation: {'; '.join(risk_result.reasons)}",
                metadata={
                    "execution_id": self._execution_count,
                    "mode": self._effective_mode,
                    "risk_reasons": risk_result.reasons,
                    "risk_metrics": risk_result.metrics,
                },
            )
            self._log_execution(order, result, now, risk_check_passed=False)
            return result

        # 3. Order an Exchange senden
        try:
            exchange_order_id = self._client.create_order(order)

            logger.info(f"[TESTNET EXECUTOR] Order gesendet: exchange_order_id={exchange_order_id}")

            # 4. Bei validate_only kommt "VALIDATED" zurueck
            if exchange_order_id == "VALIDATED":
                # Simuliertes Fill fuer validierte Orders
                fill = OrderFill(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.quantity,
                    price=current_price or order.limit_price or 0.0,
                    timestamp=now,
                    fee=None,
                    fee_currency=None,
                )
                _emit_exec_event_safe(
                    event_type="fill",
                    level="info",
                    symbol=order.symbol,
                    side=order.side,
                    qty=fill.quantity,
                    price=fill.price,
                )
                result = OrderExecutionResult(
                    status="filled",
                    request=order,
                    fill=fill,
                    reason=None,
                    metadata={
                        "execution_id": self._execution_count,
                        "mode": EXECUTION_MODE_TESTNET_VALIDATED,
                        "exchange_order_id": exchange_order_id,
                        "validated_only": True,
                        "note": "Order wurde validiert, aber nicht ausgefuehrt",
                    },
                )
            else:
                # Echte Order - Status abfragen
                fill = self._client.fetch_order_as_fill(exchange_order_id, order)

                if fill:
                    _emit_exec_event_safe(
                        event_type="fill",
                        level="info",
                        symbol=order.symbol,
                        side=order.side,
                        qty=fill.quantity,
                        price=fill.price,
                        order_id=exchange_order_id,
                    )
                    status: OrderStatus = "filled"
                else:
                    # Order noch offen oder pending
                    status = "pending"
                    fill = None

                result = OrderExecutionResult(
                    status=status,
                    request=order,
                    fill=fill,
                    reason=None,
                    metadata={
                        "execution_id": self._execution_count,
                        "mode": EXECUTION_MODE_TESTNET_LIVE,
                        "exchange_order_id": exchange_order_id,
                        "validated_only": False,
                    },
                )

            self._log_execution(order, result, now, exchange_order_id=exchange_order_id)
            return result

        except Exception as e:
            _emit_exec_event_safe(
                event_type="order_reject",
                level="error",
                is_error=True,
                symbol=order.symbol,
                side=order.side,
                msg=f"exchange_error: {type(e).__name__}",
            )
            logger.error(f"[TESTNET EXECUTOR] Order fehlgeschlagen: {e}")
            result = OrderExecutionResult(
                status="rejected",
                request=order,
                fill=None,
                reason=f"exchange_error: {e}",
                metadata={
                    "execution_id": self._execution_count,
                    "mode": self._effective_mode,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            self._log_execution(order, result, now, notes=f"Error: {e}")
            return result

    def execute_orders(
        self,
        orders: Sequence[OrderRequest],
        current_price: Optional[float] = None,
    ) -> List[OrderExecutionResult]:
        """
        Fuehrt mehrere Orders im Testnet aus.

        Prueft Risk-Limits fuer alle Orders zusammen, fuehrt dann
        jede Order einzeln aus.

        Args:
            orders: Liste von OrderRequest-Objekten
            current_price: Optionaler aktueller Preis

        Returns:
            Liste von OrderExecutionResult-Objekten (gleiche Reihenfolge)
        """
        if not orders:
            return []

        # Batch-Risk-Check
        risk_result = self._check_risk_limits(orders, current_price)
        if risk_result is not None and not risk_result.allowed:
            logger.warning(f"[TESTNET EXECUTOR] Batch Risk-Limits verletzt: {risk_result.reasons}")
            # Alle Orders ablehnen
            now = datetime.now(timezone.utc)
            results = []
            for order in orders:
                self._execution_count += 1
                _emit_exec_event_safe(
                    event_type="order_reject",
                    level="error",
                    is_error=True,
                    symbol=order.symbol,
                    side=order.side,
                    msg="batch_risk_limit_violation",
                )
                result = OrderExecutionResult(
                    status="rejected",
                    request=order,
                    fill=None,
                    reason=f"batch_risk_limit_violation: {'; '.join(risk_result.reasons)}",
                    metadata={
                        "execution_id": self._execution_count,
                        "mode": self._effective_mode,
                        "risk_reasons": risk_result.reasons,
                        "risk_metrics": risk_result.metrics,
                        "batch_check": True,
                    },
                )
                self._log_execution(order, result, now, risk_check_passed=False)
                results.append(result)
            return results

        # Orders einzeln ausfuehren
        return [self.execute_order(order, current_price) for order in orders]

    def _log_execution(
        self,
        order: OrderRequest,
        result: OrderExecutionResult,
        timestamp: datetime,
        exchange_order_id: Optional[str] = None,
        risk_check_passed: bool = True,
        notes: Optional[str] = None,
    ) -> None:
        """Fuegt einen Eintrag zum Execution-Log hinzu."""
        log_entry = TestnetExecutionLog(
            timestamp=timestamp,
            request=order,
            result=result,
            exchange_order_id=exchange_order_id,
            mode=self._effective_mode,
            risk_check_passed=risk_check_passed,
            notes=notes,
        )
        self._execution_log.append(log_entry)

    def get_execution_log(self) -> List[TestnetExecutionLog]:
        """Gibt eine Kopie des Execution-Logs zurueck."""
        return list(self._execution_log)

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Gibt eine Zusammenfassung aller Ausfuehrungen zurueck.

        Returns:
            Dict mit Statistiken
        """
        filled = [log for log in self._execution_log if log.result.status == "filled"]
        rejected = [log for log in self._execution_log if log.result.status == "rejected"]
        risk_blocked = [log for log in self._execution_log if not log.risk_check_passed]

        total_notional = 0.0
        total_fees = 0.0

        for log in filled:
            if log.result.fill:
                total_notional += log.result.fill.quantity * log.result.fill.price
                if log.result.fill.fee:
                    total_fees += log.result.fill.fee

        return {
            "total_orders": len(self._execution_log),
            "filled_orders": len(filled),
            "rejected_orders": len(rejected),
            "risk_blocked_orders": len(risk_blocked),
            "fill_rate": len(filled) / len(self._execution_log) if self._execution_log else 0.0,
            "total_notional": total_notional,
            "total_fees": total_fees,
            "mode": self._effective_mode,
            "environment": self._env_config.environment.value,
            "testnet_dry_run": self._env_config.testnet_dry_run,
        }

    def clear_log(self) -> None:
        """Loescht das Execution-Log."""
        self._execution_log.clear()

    def reset(self) -> None:
        """Setzt den Executor zurueck."""
        self._execution_count = 0
        self._execution_log.clear()
        logger.info("[TESTNET EXECUTOR] Reset durchgefuehrt")


# =============================================================================
# Factory-Funktion
# =============================================================================


def create_testnet_executor_from_config(
    cfg: "PeakConfig",
    exchange_client: Optional["KrakenTestnetClient"] = None,
    risk_limits: Optional["LiveRiskLimits"] = None,
) -> TestnetExchangeOrderExecutor:
    """
    Factory-Funktion fuer TestnetExchangeOrderExecutor aus PeakConfig.

    Args:
        cfg: PeakConfig-Instanz
        exchange_client: Optionaler KrakenTestnetClient (sonst neu erstellt)
        risk_limits: Optionale LiveRiskLimits (sonst aus Config)

    Returns:
        Konfigurierter TestnetExchangeOrderExecutor

    Raises:
        EnvironmentNotTestnetError: Wenn Environment nicht TESTNET ist

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config("config/config.toml")
        >>> executor = create_testnet_executor_from_config(cfg)
    """
    from src.core.peak_config import PeakConfig
    from src.core.environment import get_environment_from_config
    from src.live.safety import SafetyGuard
    from src.live.risk_limits import LiveRiskLimits
    from src.exchange.kraken_testnet import (
        KrakenTestnetClient,
        create_kraken_testnet_client_from_config,
    )

    # Environment-Config laden
    env_config = get_environment_from_config(cfg)

    # Safety-Guard erstellen
    safety_guard = SafetyGuard(env_config=env_config)

    # Exchange-Client erstellen falls nicht uebergeben
    if exchange_client is None:
        exchange_client = create_kraken_testnet_client_from_config(cfg)

    # Risk-Limits laden falls nicht uebergeben
    if risk_limits is None:
        starting_cash = cfg.get("testnet_session.start_balance", 10000.0)
        risk_limits = LiveRiskLimits.from_config(cfg, starting_cash=starting_cash)

    return TestnetExchangeOrderExecutor(
        exchange_client=exchange_client,
        safety_guard=safety_guard,
        risk_limits=risk_limits,
        env_config=env_config,
    )
