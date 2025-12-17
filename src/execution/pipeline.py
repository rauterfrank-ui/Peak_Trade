# src/execution/pipeline.py
"""
Peak_Trade: Execution-Pipeline (Phase 16A V2 - Governance-aware)
================================================================

Kapselt die Transformations- und Ausfuehrungslogik von Strategie-Signalen
zu OrderRequests und OrderExecutionResults.

Workflow:
    Strategy → OrderIntent → ExecutionPipeline → Risk → Governance → Executor → Result

Die Pipeline ist bewusst leichtgewichtig gehalten und konzentriert sich auf:
- Signale → gewuenschter Ziel-Exposure
- Differenz zur aktuellen Position → OrderRequest(s)
- OrderExecutor (Paper/Shadow/Testnet) fuehrt aus → Fills/Results

Phase 16A V2 Erweiterung (Governance-aware):
- Environment- und Safety-Checks vor Order-Ausfuehrung
- Integration mit SafetyGuard und LiveRiskLimits
- Governance-Check via get_governance_status("live_order_execution")
- Environment-Executor-Mapping (paper/shadow/testnet/live)
- Live-Execution ist governance-seitig gesperrt (status="locked")
- Optionales Run-Logging ueber LiveRunLogger

WICHTIG: Es werden KEINE echten Live-Orders an Boersen gesendet!
         live_order_execution ist governance-seitig gesperrt (locked).
         Bei env="live" wird GovernanceViolationError geworfen.
"""
from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

import pandas as pd

from ..governance.go_no_go import GovernanceStatus, get_governance_status
from ..orders.base import (
    OrderExecutionResult,
    OrderExecutor,
    OrderRequest,
    OrderSide,
)
from ..orders.paper import PaperMarketContext, PaperOrderExecutor
from ..orders.shadow import ShadowMarketContext, ShadowOrderExecutor

if TYPE_CHECKING:
    from ..core.environment import EnvironmentConfig
    from ..live.risk_limits import LiveRiskCheckResult, LiveRiskLimits
    from ..live.run_logging import LiveRunLogger
    from ..live.safety import SafetyGuard

logger = logging.getLogger(__name__)


# =============================================================================
# Phase 16A V2: Custom Exceptions
# =============================================================================


class ExecutionPipelineError(Exception):
    """Basisklasse fuer ExecutionPipeline-Fehler."""
    pass


class GovernanceViolationError(ExecutionPipelineError):
    """
    Governance-Verletzung: Eine Operation ist governance-seitig gesperrt.

    Wird geworfen wenn:
    - env="live" und get_governance_status("live_order_execution") == "locked"
    - Zukuenftige Governance-Regeln verletzt werden

    Attributes:
        feature_key: Der Governance-Feature-Key (z.B. "live_order_execution")
        status: Der aktuelle Governance-Status (z.B. "locked")
        message: Beschreibende Fehlermeldung
    """

    def __init__(
        self,
        message: str,
        feature_key: str = "live_order_execution",
        status: GovernanceStatus = "locked",
    ):
        super().__init__(message)
        self.feature_key = feature_key
        self.status = status
        self.message = message


class LiveExecutionLockedError(GovernanceViolationError):
    """
    Live-Execution ist governance-seitig gesperrt.

    Spezialisierte Exception fuer den Fall:
    - get_governance_status("live_order_execution") == "locked"

    In Phase 16A ist dies der Normalfall - Live-Orders sind nicht erlaubt.
    """

    def __init__(self, message: str | None = None):
        default_msg = (
            "Live-Order-Execution ist governance-seitig gesperrt (status='locked'). "
            "Governance-Feature: 'live_order_execution'. "
            "Es werden keine echten Live-Orders ausgefuehrt. "
            "Nutze paper/shadow/testnet Environments fuer Simulation."
        )
        super().__init__(
            message=message or default_msg,
            feature_key="live_order_execution",
            status="locked",
        )


class RiskCheckFailedError(ExecutionPipelineError):
    """
    Risk-Check fehlgeschlagen: Orders wurden durch Risk-Limits blockiert.

    Attributes:
        reasons: Liste der Gruende fuer die Blockierung
        metrics: Risk-Metriken zum Zeitpunkt der Blockierung
    """

    def __init__(self, message: str, reasons: list[str], metrics: dict[str, Any]):
        super().__init__(message)
        self.reasons = reasons
        self.metrics = metrics


# =============================================================================
# Phase 16A V2: OrderIntent & Environment Types
# =============================================================================


class ExecutionEnvironment(str, Enum):
    """
    Execution-Environment fuer die Pipeline.

    Values:
        PAPER: Paper-Trading / Backtest (PaperOrderExecutor)
        SHADOW: Shadow-Mode / Dry-Run (ShadowOrderExecutor)
        TESTNET: Testnet-Orders (TestnetExchangeOrderExecutor)
        LIVE: Echte Orders (GESPERRT - GovernanceViolationError)
    """
    PAPER = "paper"
    SHADOW = "shadow"
    TESTNET = "testnet"
    LIVE = "live"


@dataclass
class OrderIntent:
    """
    Order-Absicht (Intent) fuer die ExecutionPipeline.

    Repraesentiert eine gewuenschte Order, bevor sie durch Risk/Governance
    geprueft und an einen Executor delegiert wird.

    Attributes:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        side: Kauf- oder Verkaufsorder ("buy" oder "sell")
        quantity: Menge (Stueckzahl)
        order_type: Order-Typ ("market" oder "limit")
        limit_price: Limit-Preis (nur bei order_type="limit")
        strategy_key: Optional Strategy-Identifier
        current_price: Aktueller Preis (fuer Risk-Berechnung)
        metadata: Zusaetzliche Metadaten

    Example:
        >>> intent = OrderIntent(
        ...     symbol="BTC/EUR",
        ...     side="buy",
        ...     quantity=0.01,
        ...     order_type="market",
        ...     strategy_key="ma_crossover",
        ...     current_price=50000.0,
        ... )
        >>> result = pipeline.submit_order(intent)
    """
    symbol: str
    side: OrderSide
    quantity: float
    order_type: Literal["market", "limit"] = "market"
    limit_price: float | None = None
    strategy_key: str | None = None
    current_price: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_order_request(self, client_id: str | None = None) -> OrderRequest:
        """Konvertiert den OrderIntent zu einer OrderRequest."""
        meta = dict(self.metadata)
        if self.strategy_key:
            meta["strategy_key"] = self.strategy_key
        if self.current_price:
            meta["current_price"] = self.current_price

        return OrderRequest(
            symbol=self.symbol,
            side=self.side,
            quantity=self.quantity,
            order_type=self.order_type,
            limit_price=self.limit_price,
            client_id=client_id,
            metadata=meta,
        )


# =============================================================================
# Phase 16A V2: ExecutionResult Status
# =============================================================================


class ExecutionStatus(str, Enum):
    """
    Status einer Order-Ausfuehrung.

    Values:
        SUCCESS: Order erfolgreich ausgefuehrt
        BLOCKED_BY_RISK: Durch Risk-Limits blockiert
        BLOCKED_BY_GOVERNANCE: Durch Governance blockiert (z.B. live_order_execution=locked)
        BLOCKED_BY_SAFETY: Durch SafetyGuard blockiert
        BLOCKED_BY_ENVIRONMENT: Durch Environment-Check blockiert
        REJECTED: Vom Executor abgelehnt
        ERROR: Fehler bei der Ausfuehrung
        INVALID: Ungueltiger Input (z.B. quantity <= 0)
    """
    SUCCESS = "success"
    BLOCKED_BY_RISK = "blocked_by_risk"
    BLOCKED_BY_GOVERNANCE = "blocked_by_governance"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    BLOCKED_BY_ENVIRONMENT = "blocked_by_environment"
    REJECTED = "rejected"
    ERROR = "error"
    INVALID = "invalid"

# Typ-Alias fuer Signal-Serien
SignalSeries = pd.Series


@dataclass
class ExecutionResult:
    """
    Ergebnis einer Order-Ausfuehrung durch die ExecutionPipeline mit Safety-Checks.

    Phase 16A V2: Wird von execute_with_safety() und submit_order() zurueckgegeben.

    Attributes:
        risk_check: Ergebnis des Risk-Checks (falls durchgefuehrt)
        executed_orders: Liste der ausgeführten Orders (kann leer sein bei Blockierung)
        rejected: True wenn die Ausfuehrung durch Environment/Safety/Risk/Governance blockiert wurde
        reason: Grund fuer Blockierung (falls rejected=True)
        execution_results: Liste der OrderExecutionResults vom Executor
        status: Phase 16A V2: Detaillierter Execution-Status
        environment: Phase 16A V2: Environment in dem ausgefuehrt wurde
        governance_status: Phase 16A V2: Governance-Status zum Zeitpunkt der Ausfuehrung
    """
    risk_check: LiveRiskCheckResult | None = None
    executed_orders: list[OrderExecutionResult] = field(default_factory=list)
    rejected: bool = False
    reason: str | None = None
    execution_results: list[OrderExecutionResult] = field(default_factory=list)
    # Phase 16A V2 Erweiterungen
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    environment: str | None = None
    governance_status: GovernanceStatus | None = None

    @property
    def is_success(self) -> bool:
        """True wenn die Order erfolgreich ausgefuehrt wurde."""
        return self.status == ExecutionStatus.SUCCESS and not self.rejected

    @property
    def is_blocked_by_governance(self) -> bool:
        """True wenn durch Governance blockiert."""
        return self.status == ExecutionStatus.BLOCKED_BY_GOVERNANCE

    @property
    def is_blocked_by_risk(self) -> bool:
        """True wenn durch Risk-Limits blockiert."""
        return self.status == ExecutionStatus.BLOCKED_BY_RISK


@dataclass
class SignalEvent:
    """
    Ein Signal-Event, das einen Order-Trigger repraesentiert.

    Wird von der Backtest-Engine verwendet, um Signal-Wechsel zu erkennen
    und entsprechende Orders zu generieren.

    Attributes:
        timestamp: Zeitpunkt des Signals
        symbol: Trading-Pair (z.B. "BTC/EUR")
        signal: Signal-Wert (-1=Short, 0=Neutral, +1=Long)
        price: Referenz-Preis zum Zeitpunkt des Signals
        previous_signal: Vorheriges Signal (fuer Wechsel-Erkennung)
        metadata: Zusaetzliche Metadaten (strategy_key, bar_index, etc.)
    """

    timestamp: datetime
    symbol: str
    signal: int  # -1, 0, +1
    price: float
    previous_signal: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_entry_long(self) -> bool:
        """True bei Long-Entry (0 oder -1 → +1)."""
        return self.signal == 1 and self.previous_signal != 1

    @property
    def is_exit_long(self) -> bool:
        """True bei Long-Exit (+1 → 0 oder -1)."""
        return self.previous_signal == 1 and self.signal != 1

    @property
    def is_entry_short(self) -> bool:
        """True bei Short-Entry (0 oder +1 → -1)."""
        return self.signal == -1 and self.previous_signal != -1

    @property
    def is_exit_short(self) -> bool:
        """True bei Short-Exit (-1 → 0 oder +1)."""
        return self.previous_signal == -1 and self.signal != -1

    @property
    def is_flip_long_to_short(self) -> bool:
        """True bei Flip von Long zu Short (+1 → -1)."""
        return self.previous_signal == 1 and self.signal == -1

    @property
    def is_flip_short_to_long(self) -> bool:
        """True bei Flip von Short zu Long (-1 → +1)."""
        return self.previous_signal == -1 and self.signal == 1

    @property
    def has_signal_change(self) -> bool:
        """True wenn sich das Signal geaendert hat."""
        return self.signal != self.previous_signal


@dataclass
class ExecutionPipelineConfig:
    """
    Konfiguration fuer die ExecutionPipeline.

    Diese Klasse bietet eine zentrale Stelle fuer Order-bezogene Parameter,
    die in Backtests, Paper Trading und spaeteren Live-Simulationen
    konsistent verwendet werden koennen.

    Attributes:
        default_order_type: Standard-Order-Typ ("market" oder "limit")
        default_time_in_force: Standard-TimeInForce ("GTC", "IOC", "FOK")
        max_position_notional_pct: Anteil des verfuegbaren Kapitals pro Signal.
            1.0 = 100% des vorgesehenen Size-Budgets (nicht zwingend Gesamt-Equity).
        allow_partial_fills: Ob Teil-Fills erlaubt sind
        slippage_bps: Slippage in Basispunkten (dokumentarisch, Executor nutzt eigene Werte)
        fee_bps: Fees in Basispunkten (dokumentarisch, Executor nutzt eigene Werte)
        generate_client_ids: Ob automatisch Client-IDs generiert werden sollen
        log_executions: Ob Execution-Details geloggt werden sollen (Default: True)
    """

    default_order_type: str = "market"
    default_time_in_force: str = "GTC"
    max_position_notional_pct: float = 1.0
    allow_partial_fills: bool = True
    slippage_bps: float = 0.0
    fee_bps: float = 0.0
    generate_client_ids: bool = True
    log_executions: bool = True  # Fuer Backward-Kompatibilitaet mit BacktestEngine


class ExecutionPipeline:
    """
    Kapselt die Transformations- und Ausfuehrungslogik von Strategie-Signalen
    zu tatsaechlichen OrderRequests und OrderExecutionResults.

    Die Pipeline ist bewusst leichtgewichtig gehalten und konzentriert sich
    in dieser Phase auf ein einfaches, aber konsistentes Modell:
    - Signale → gewuenschter Ziel-Exposure
    - Differenz zur aktuellen Position → OrderRequest(s)
    - OrderExecutor (Paper) fuehrt aus → Fills/Results

    Beispiel-Usage:
        >>> from src.orders.paper import PaperMarketContext
        >>> from src.execution import ExecutionPipeline
        >>>
        >>> ctx = PaperMarketContext(prices={"BTC/EUR": 50000.0})
        >>> pipeline = ExecutionPipeline.for_paper(ctx)
        >>>
        >>> # Signale und Preise
        >>> signals = pd.Series([0, 1, 1, 0, -1, 0], index=pd.date_range("2024-01-01", periods=6, freq="h"))
        >>> prices = pd.Series([50000, 50100, 50200, 50150, 50000, 49900], index=signals.index)
        >>>
        >>> results = pipeline.execute_from_signals(
        ...     signals=signals,
        ...     prices=prices,
        ...     symbol="BTC/EUR",
        ...     base_currency="EUR",
        ...     quote_currency="BTC",
        ... )

    WICHTIG: Diese Pipeline schickt KEINE echten Orders an Boersen.
             Alles bleibt auf Paper-/Sandbox-Level.
    """

    def __init__(
        self,
        executor: OrderExecutor,
        config: ExecutionPipelineConfig | None = None,
        env_config: EnvironmentConfig | None = None,
        safety_guard: SafetyGuard | None = None,
        risk_limits: LiveRiskLimits | None = None,
        run_logger: LiveRunLogger | None = None,
    ) -> None:
        """
        Initialisiert die ExecutionPipeline.

        Args:
            executor: OrderExecutor-Instanz (z.B. PaperOrderExecutor).
                      WICHTIG: In dieser Phase nur PaperOrderExecutor verwenden.
            config: Optionale Konfiguration. Falls None, wird Default-Config verwendet.
            env_config: Optional EnvironmentConfig fuer Safety-Checks (Phase 16A)
            safety_guard: Optional SafetyGuard fuer Safety-Checks (Phase 16A)
            risk_limits: Optional LiveRiskLimits fuer Risk-Checks (Phase 16A)
            run_logger: Optional LiveRunLogger fuer Run-Logging (Phase 16A)
        """
        self._executor = executor
        self._config = config if config is not None else ExecutionPipelineConfig()
        self._execution_history: list[OrderExecutionResult] = []
        self._order_counter = 0

        # Phase 16A: Safety-Komponenten
        self._env_config = env_config
        self._safety_guard = safety_guard
        self._risk_limits = risk_limits
        self._run_logger = run_logger

    @property
    def config(self) -> ExecutionPipelineConfig:
        """Zugriff auf die Konfiguration."""
        return self._config

    @property
    def executor(self) -> OrderExecutor:
        """Zugriff auf den Executor."""
        return self._executor

    @property
    def execution_history(self) -> list[OrderExecutionResult]:
        """Gibt die Historie aller Ausfuehrungen zurueck (Kopie)."""
        return self._execution_history.copy()

    @classmethod
    def for_paper(
        cls,
        market_context: PaperMarketContext,
        config: ExecutionPipelineConfig | None = None,
    ) -> ExecutionPipeline:
        """
        Convenience-Konstruktor fuer eine reine Paper-/Sandbox-Pipeline
        auf Basis eines PaperMarketContext.

        Args:
            market_context: PaperMarketContext mit Preisen und Fee/Slippage-Einstellungen
            config: Optionale Pipeline-Konfiguration

        Returns:
            ExecutionPipeline-Instanz mit PaperOrderExecutor

        Beispiel:
            >>> ctx = PaperMarketContext(
            ...     prices={"BTC/EUR": 50000.0},
            ...     fee_bps=10.0,
            ...     slippage_bps=5.0,
            ... )
            >>> pipeline = ExecutionPipeline.for_paper(ctx)
        """
        executor = PaperOrderExecutor(market_context)
        return cls(executor=executor, config=config)

    @classmethod
    def for_shadow(
        cls,
        market_context: ShadowMarketContext | None = None,
        config: ExecutionPipelineConfig | None = None,
        fee_rate: float = 0.0005,
        slippage_bps: float = 0.0,
    ) -> ExecutionPipeline:
        """
        Convenience-Konstruktor fuer eine Shadow-/Dry-Run-Pipeline (Phase 24).

        Die Shadow-Pipeline nutzt den ShadowOrderExecutor, der:
        - Keine echten API-Calls an Exchanges macht
        - Orders nur simuliert und loggt
        - Sich wie eine quasi-realistische Execution verhaelt

        Args:
            market_context: Optionaler ShadowMarketContext.
                            Falls None, wird ein Default-Context erstellt.
            config: Optionale Pipeline-Konfiguration
            fee_rate: Fee-Rate (z.B. 0.0005 = 5 bps = 0.05%)
            slippage_bps: Slippage in Basispunkten (z.B. 5 = 0.05%)

        Returns:
            ExecutionPipeline-Instanz mit ShadowOrderExecutor

        Beispiel:
            >>> pipeline = ExecutionPipeline.for_shadow(
            ...     fee_rate=0.001,  # 10 bps
            ...     slippage_bps=5.0,
            ... )
            >>> # Oder mit explizitem Context:
            >>> ctx = ShadowMarketContext(
            ...     prices={"BTC/EUR": 50000.0},
            ...     fee_rate=0.0005,
            ... )
            >>> pipeline = ExecutionPipeline.for_shadow(market_context=ctx)

        WICHTIG: Diese Pipeline sendet NIEMALS echte Orders.
                 Alles ist zu 100% simulativ.
        """
        if market_context is None:
            market_context = ShadowMarketContext(
                fee_rate=fee_rate,
                slippage_bps=slippage_bps,
            )
        executor = ShadowOrderExecutor(market_context=market_context)
        return cls(executor=executor, config=config)

    def _generate_client_id(self, symbol: str) -> str:
        """
        Generiert eine eindeutige Client-ID fuer eine Order.

        Args:
            symbol: Trading-Symbol

        Returns:
            Eindeutige Client-ID
        """
        self._order_counter += 1
        symbol_clean = symbol.replace("/", "_")
        return f"exec_{symbol_clean}_{self._order_counter}_{uuid.uuid4().hex[:6]}"

    def execute_orders(
        self,
        orders: Iterable[OrderRequest],
    ) -> list[OrderExecutionResult]:
        """
        Fuehrt eine Liste von OrderRequests ueber den hinterlegten Executor aus
        und gibt die dazugehoerigen ExecutionResults zurueck.

        Args:
            orders: Iterable von OrderRequest-Objekten

        Returns:
            Liste von OrderExecutionResult-Objekten (gleiche Reihenfolge wie Input)

        Beispiel:
            >>> order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
            >>> results = pipeline.execute_orders([order])
            >>> print(results[0].status)  # "filled" oder "rejected"
        """
        orders_list = list(orders)

        if not orders_list:
            return []

        # Orders ueber Executor ausfuehren
        results = self._executor.execute_orders(orders_list)

        # Historie aktualisieren
        self._execution_history.extend(results)

        # Logging
        for result in results:
            if result.is_filled and result.fill:
                logger.debug(
                    f"[EXECUTION] FILLED {result.fill.side.upper()} {result.fill.symbol} "
                    f"qty={result.fill.quantity:.6f} @ {result.fill.price:.4f}"
                )
            elif result.is_rejected:
                logger.debug(
                    f"[EXECUTION] REJECTED {result.request.symbol}: {result.reason}"
                )

        return results

    def signal_to_orders(
        self,
        event: SignalEvent,
        position_size: float,
        current_position: float = 0.0,
    ) -> list[OrderRequest]:
        """
        Konvertiert ein SignalEvent in OrderRequests.

        Diese Methode erkennt Signal-Wechsel und generiert entsprechende Orders:
        - Entry Long: Kauforder
        - Exit Long: Verkauforder (Positionsgroesse)
        - Flip Long→Short: Verkauforder + Short-Order
        - etc.

        Wird von der BacktestEngine verwendet fuer bar-by-bar Order-Generierung.

        Args:
            event: SignalEvent mit Signal-Informationen
            position_size: Gewuenschte Positionsgroesse (in Stueck)
            current_position: Aktuelle Position (positiv=Long, negativ=Short, 0=Flat)

        Returns:
            Liste von OrderRequests (leer wenn kein Handel noetig)
        """
        orders: list[OrderRequest] = []
        metadata = {
            "signal": event.signal,
            "previous_signal": event.previous_signal,
            "signal_timestamp": event.timestamp.isoformat() if event.timestamp else None,
            **event.metadata,
        }

        # Kein Signal-Wechsel → keine Orders
        if not event.has_signal_change:
            return orders

        # Long Entry (0 oder -1 → +1)
        if event.is_entry_long:
            # Bei Flip von Short zu Long: Erst Short schliessen
            if current_position < 0:
                orders.append(
                    OrderRequest(
                        symbol=event.symbol,
                        side="buy",
                        quantity=abs(current_position),
                        order_type="market",
                        client_id=self._generate_client_id(event.symbol) if self._config.generate_client_ids else None,
                        metadata={**metadata, "order_reason": "close_short"},
                    )
                )

            # Long-Position eroeffnen
            if position_size > 0:
                orders.append(
                    OrderRequest(
                        symbol=event.symbol,
                        side="buy",
                        quantity=position_size,
                        order_type="market",
                        client_id=self._generate_client_id(event.symbol) if self._config.generate_client_ids else None,
                        metadata={**metadata, "order_reason": "entry_long"},
                    )
                )

        # Long Exit (+1 → 0)
        elif event.is_exit_long and not event.is_entry_short:
            if current_position > 0:
                orders.append(
                    OrderRequest(
                        symbol=event.symbol,
                        side="sell",
                        quantity=current_position,
                        order_type="market",
                        client_id=self._generate_client_id(event.symbol) if self._config.generate_client_ids else None,
                        metadata={**metadata, "order_reason": "exit_long"},
                    )
                )

        # Short Entry (0 oder +1 → -1)
        elif event.is_entry_short:
            # Bei Flip von Long zu Short: Erst Long schliessen
            if current_position > 0:
                orders.append(
                    OrderRequest(
                        symbol=event.symbol,
                        side="sell",
                        quantity=current_position,
                        order_type="market",
                        client_id=self._generate_client_id(event.symbol) if self._config.generate_client_ids else None,
                        metadata={**metadata, "order_reason": "close_long"},
                    )
                )

            # Short-Position eroeffnen (hier als Verkauf modelliert)
            if position_size > 0:
                orders.append(
                    OrderRequest(
                        symbol=event.symbol,
                        side="sell",
                        quantity=position_size,
                        order_type="market",
                        client_id=self._generate_client_id(event.symbol) if self._config.generate_client_ids else None,
                        metadata={**metadata, "order_reason": "entry_short"},
                    )
                )

        # Short Exit (-1 → 0)
        elif event.is_exit_short and not event.is_entry_long:
            if current_position < 0:
                orders.append(
                    OrderRequest(
                        symbol=event.symbol,
                        side="buy",
                        quantity=abs(current_position),
                        order_type="market",
                        client_id=self._generate_client_id(event.symbol) if self._config.generate_client_ids else None,
                        metadata={**metadata, "order_reason": "exit_short"},
                    )
                )

        return orders

    def execute_from_signals(
        self,
        signals: pd.Series,
        prices: pd.Series,
        symbol: str,
        base_currency: str = "EUR",
        quote_currency: str = "BTC",
        initial_position: float = 0.0,
    ) -> list[OrderExecutionResult]:
        """
        Nimmt eine Zeitreihe von Signalen (-1/0/+1 oder Ziel-Exposure)
        sowie die entsprechenden Preise entgegen und uebersetzt relevante
        Aenderungen in OrderRequests, die anschliessend ausgefuehrt werden.

        Signal-Interpretation:
        - +1 = Long (Ziel: position_size Units long)
        - 0 = Flat (Ziel: keine Position)
        - -1 = Short (Ziel: position_size Units short)

        Die Methode erkennt Signal-Wechsel (z.B. 0→+1, +1→0, +1→-1) und
        generiert entsprechende Orders, um die Position auf den Zielwert
        anzupassen.

        Args:
            signals: Signal-Serie (-1/0/+1) mit DatetimeIndex
            prices: Preis-Serie (Close-Preise) mit gleichem Index wie signals
            symbol: Trading-Symbol (z.B. "BTC/EUR")
            base_currency: Basiswaehrung (z.B. "EUR")
            quote_currency: Quote-Waehrung (z.B. "BTC")
            initial_position: Startposition in Units (Default: 0.0 = Flat)

        Returns:
            Liste von OrderExecutionResult in zeitlicher Reihenfolge

        Beispiel:
            >>> signals = pd.Series([0, 1, 1, 0], index=pd.date_range("2024-01-01", periods=4, freq="h"))
            >>> prices = pd.Series([50000, 50100, 50200, 50150], index=signals.index)
            >>> results = pipeline.execute_from_signals(
            ...     signals=signals,
            ...     prices=prices,
            ...     symbol="BTC/EUR",
            ...     base_currency="EUR",
            ...     quote_currency="BTC",
            ... )
            >>> # Ergibt 2 Trades: Entry bei Signal 0→1, Exit bei Signal 1→0

        Annahmen:
        - Signale sind -1, 0 oder +1 (werden auf diesen Bereich geclippt)
        - position_size = config.max_position_notional_pct (vereinfacht: 1.0 Unit)
        - Bei Signal-Wechsel wird die komplette Differenz gehandelt
        """
        all_results: list[OrderExecutionResult] = []

        if len(signals) == 0:
            return all_results

        # Sicherstellen dass Index uebereinstimmt
        signals = signals.reindex(prices.index, method="ffill").fillna(0)

        # Signale auf -1, 0, +1 beschraenken
        signals = signals.clip(-1, 1).astype(int)

        # Position-Sizing: Vereinfacht 1.0 Unit als Basis
        # (kann spaeter durch komplexere Logik ersetzt werden)
        base_position_size = self._config.max_position_notional_pct

        # Tracking-Variablen
        current_position = initial_position
        previous_signal = 0 if initial_position == 0 else (1 if initial_position > 0 else -1)

        for ts, signal in signals.items():
            signal = int(signal)
            price = float(prices.loc[ts])

            # Preis im Marktkontext aktualisieren (falls PaperOrderExecutor)
            if hasattr(self._executor, "context"):
                self._executor.context.set_price(symbol, price)

            # Nur bei Signal-Aenderung handeln
            if signal == previous_signal:
                previous_signal = signal
                continue

            # Ziel-Position berechnen (vereinfacht: Signal * base_position_size)
            # +1 = Long mit base_position_size Units
            # -1 = Short mit base_position_size Units (negative Position)
            # 0 = Flat
            target_position = signal * base_position_size

            # Differenz zur aktuellen Position berechnen
            position_delta = target_position - current_position

            if abs(position_delta) < 1e-10:
                # Keine nennenswerte Aenderung
                previous_signal = signal
                continue

            # Order-Side bestimmen
            side: OrderSide = "buy" if position_delta > 0 else "sell"
            quantity = abs(position_delta)

            # OrderRequest erstellen
            client_id = (
                self._generate_client_id(symbol)
                if self._config.generate_client_ids
                else None
            )

            order = OrderRequest(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=self._config.default_order_type,  # type: ignore
                limit_price=None,  # Market-Order
                client_id=client_id,
                metadata={
                    "signal": signal,
                    "previous_signal": previous_signal,
                    "target_position": target_position,
                    "position_delta": position_delta,
                    "signal_timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                    "base_currency": base_currency,
                    "quote_currency": quote_currency,
                    "time_in_force": self._config.default_time_in_force,
                },
            )

            # Order ausfuehren
            results = self.execute_orders([order])
            all_results.extend(results)

            # Position aktualisieren basierend auf Fill
            for result in results:
                if result.is_filled and result.fill:
                    fill = result.fill
                    if fill.side == "buy":
                        current_position += fill.quantity
                    else:
                        current_position -= fill.quantity

            previous_signal = signal

        return all_results

    def get_execution_summary(self) -> dict[str, Any]:
        """
        Gibt eine Zusammenfassung aller Ausfuehrungen zurueck.

        Returns:
            Dict mit Statistiken:
            - total_orders: Anzahl aller Orders
            - filled_orders: Anzahl gefuellter Orders
            - rejected_orders: Anzahl abgelehnter Orders
            - fill_rate: Anteil gefuellter Orders
            - total_notional: Summe aller Transaktionswerte
            - total_fees: Summe aller Fees
        """
        filled = [r for r in self._execution_history if r.is_filled]
        rejected = [r for r in self._execution_history if r.is_rejected]

        total_notional = 0.0
        total_fees = 0.0

        for result in filled:
            if result.fill:
                total_notional += result.fill.quantity * result.fill.price
                if result.fill.fee:
                    total_fees += result.fill.fee

        total_orders = len(self._execution_history)

        return {
            "total_orders": total_orders,
            "filled_orders": len(filled),
            "rejected_orders": len(rejected),
            "fill_rate": len(filled) / total_orders if total_orders > 0 else 0.0,
            "total_notional": total_notional,
            "total_fees": total_fees,
        }

    def reset(self) -> None:
        """Setzt die Pipeline zurueck (loescht Historie und Counter)."""
        self._execution_history.clear()
        self._order_counter = 0

    # =============================================================================
    # Phase 16A V2: submit_order() - Governance-aware Order Submission
    # =============================================================================

    def submit_order(
        self,
        intent: OrderIntent,
        *,
        raise_on_governance_violation: bool = True,
    ) -> ExecutionResult:
        """
        Zentrale Methode fuer Governance-aware Order-Submission (Phase 16A V2).

        Workflow:
        1. Input validieren/normalisieren
        2. Risk-Checks ausfuehren (bestehende Risk-Komponenten nutzen)
        3. Governance-Check ausfuehren (get_governance_status)
        4. Je nach Environment an passenden Executor delegieren

        Args:
            intent: OrderIntent mit allen Order-Details
            raise_on_governance_violation: Wenn True, wird LiveExecutionLockedError geworfen
                                          bei env="live". Wenn False, wird ExecutionResult
                                          mit status=BLOCKED_BY_GOVERNANCE zurueckgegeben.

        Returns:
            ExecutionResult mit Status, executed_orders, governance_status

        Raises:
            LiveExecutionLockedError: Wenn env="live" und raise_on_governance_violation=True
            GovernanceViolationError: Bei anderen Governance-Verletzungen
            RiskCheckFailedError: Optional bei Risk-Verletzung (nicht in v1)

        Example:
            >>> intent = OrderIntent(
            ...     symbol="BTC/EUR",
            ...     side="buy",
            ...     quantity=0.01,
            ...     strategy_key="ma_crossover",
            ...     current_price=50000.0,
            ... )
            >>> result = pipeline.submit_order(intent)
            >>> if result.is_blocked_by_governance:
            ...     print(f"Governance blockiert: {result.reason}")
        """
        # 1. Input validieren
        if intent.quantity <= 0:
            return ExecutionResult(
                rejected=True,
                reason="invalid_quantity: must be > 0",
                status=ExecutionStatus.INVALID,
            )

        # Bestimme Environment
        env_str = self._get_current_environment()

        # 2. Governance-Check fuer Live-Environment
        governance_status = get_governance_status("live_order_execution")

        if env_str == "live" and governance_status == "locked":
            reason = (
                f"live_order_execution is governance-locked (status='{governance_status}'). "
                f"Live-Orders sind nicht erlaubt."
            )
            logger.warning(
                f"[EXECUTION PIPELINE] Governance-Block: {reason}"
            )

            if raise_on_governance_violation:
                raise LiveExecutionLockedError()

            return ExecutionResult(
                rejected=True,
                reason=reason,
                status=ExecutionStatus.BLOCKED_BY_GOVERNANCE,
                environment=env_str,
                governance_status=governance_status,
            )

        # 3. OrderRequest erstellen
        client_id = self._generate_client_id(intent.symbol)
        order = intent.to_order_request(client_id=client_id)

        # 4. Kontext fuer Risk-Check
        context = {"current_price": intent.current_price} if intent.current_price else None

        # 5. Durch execute_with_safety() ausfuehren
        result = self.execute_with_safety([order], context=context)

        # 6. Result erweitern mit Phase 16A V2 Feldern
        result.environment = env_str
        result.governance_status = governance_status

        if result.rejected:
            if "risk_limits" in (result.reason or ""):
                result.status = ExecutionStatus.BLOCKED_BY_RISK
            elif "safety_guard" in (result.reason or ""):
                result.status = ExecutionStatus.BLOCKED_BY_SAFETY
            elif "live_mode" in (result.reason or ""):
                result.status = ExecutionStatus.BLOCKED_BY_ENVIRONMENT
        else:
            result.status = ExecutionStatus.SUCCESS

        return result

    def _get_current_environment(self) -> str:
        """
        Ermittelt das aktuelle Environment aus der Konfiguration.

        Returns:
            Environment-String: "paper", "shadow", "testnet", oder "live"
        """
        if self._env_config is None:
            return "paper"  # Default

        if self._env_config.is_live:
            return "live"
        if self._env_config.is_testnet:
            return "testnet"
        # Shadow wird durch Executor-Typ bestimmt
        if isinstance(self._executor, ShadowOrderExecutor):
            return "shadow"
        return "paper"

    def _check_governance(self, env: str) -> tuple[bool, GovernanceStatus, str | None]:
        """
        Prueft Governance-Regeln fuer das gegebene Environment.

        Args:
            env: Environment-String ("paper", "shadow", "testnet", "live")

        Returns:
            Tuple (allowed, governance_status, reason)
            - allowed: True wenn Ausfuehrung erlaubt
            - governance_status: Aktueller Governance-Status
            - reason: Grund bei Blockierung (None wenn erlaubt)
        """
        governance_status = get_governance_status("live_order_execution")

        if env == "live" and governance_status == "locked":
            # WICHTIG: Stabiler Reason-Code für Tests (Phase 16A Kompatibilität)
            return (
                False,
                governance_status,
                "live_mode_not_supported_in_phase_16a",
            )

        # Fuer paper/shadow/testnet: Governance v1 nicht blockierend
        # Code so gebaut, dass spaetere Governance-Regeln leicht ergaenzt werden koennen
        return (True, governance_status, None)

    # =============================================================================
    # Phase 16A V2: execute_with_safety() - Safety-Check-Wrapper (erweitert)
    # =============================================================================

    def execute_with_safety(
        self,
        orders: Sequence[OrderRequest],
        context: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """
        Fuehrt Orders mit vollstaendigen Safety-, Risk- und Governance-Checks aus.

        Phase 16A V2 Workflow:
        1. Environment-Check: Bestimme aktuelles Environment
        2. Governance-Check: Pruefe governance-seitige Freigabe (NEU in V2)
        3. SafetyGuard-Check: Prueft ob Order-Platzierung erlaubt ist
        4. Risk-Check: Optional LiveRiskLimits-Check (wenn konfiguriert)
        5. Executor: Fuehrt Orders aus (wenn alle Checks passiert)
        6. Run-Logging: Loggt Events (wenn run_logger konfiguriert)

        Args:
            orders: Liste von OrderRequests
            context: Optionaler Kontext-Dict (z.B. {"current_price": 50000.0})

        Returns:
            ExecutionResult mit Risk-Check-Ergebnis, executed_orders, rejected-Flag,
            sowie status, environment, governance_status (Phase 16A V2)

        Example:
            >>> from src.core.environment import EnvironmentConfig, TradingEnvironment
            >>> from src.live.safety import SafetyGuard
            >>> from src.orders.paper import PaperMarketContext, PaperOrderExecutor
            >>>
            >>> env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
            >>> safety_guard = SafetyGuard(env_config=env_config)
            >>> executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000}))
            >>>
            >>> pipeline = ExecutionPipeline(
            ...     executor=executor,
            ...     env_config=env_config,
            ...     safety_guard=safety_guard,
            ... )
            >>>
            >>> order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
            >>> result = pipeline.execute_with_safety([order])
            >>> print(f"Rejected: {result.rejected}, Status: {result.status.value}")
        """
        if not orders:
            return ExecutionResult(
                rejected=False,
                executed_orders=[],
                execution_results=[],
                reason=None,
                status=ExecutionStatus.SUCCESS,
            )

        orders_list = list(orders)
        env_str = self._get_current_environment()

        # 1. Governance-Check (Phase 16A V2)
        governance_allowed, governance_status, governance_reason = self._check_governance(env_str)

        if not governance_allowed:
            logger.warning(
                f"[EXECUTION PIPELINE] Governance-Block: {governance_reason}"
            )
            return ExecutionResult(
                rejected=True,
                executed_orders=[],
                execution_results=[],
                reason=governance_reason,
                status=ExecutionStatus.BLOCKED_BY_GOVERNANCE,
                environment=env_str,
                governance_status=governance_status,
            )

        # 2. Environment-Check: LIVE-Mode hart blockieren (Phase 16A)
        if self._env_config is not None and self._env_config.is_live:
            # WICHTIG: Reason-Code muss stabil bleiben für Tests
            # Governance-Check schlägt an, daher reason von Governance überschreiben
            reason = "live_mode_not_supported_in_phase_16a"
            logger.error(
                "[EXECUTION PIPELINE] LIVE-Mode blockiert in Phase 16A. "
                "Keine Orders werden ausgefuehrt."
            )
            return ExecutionResult(
                rejected=True,
                executed_orders=[],
                execution_results=[],
                reason=reason,
                status=ExecutionStatus.BLOCKED_BY_ENVIRONMENT,
                environment=env_str,
                governance_status=governance_status,
            )

        # 3. SafetyGuard-Check
        if self._safety_guard is not None:
            try:
                # SafetyGuard.ensure_may_place_order() wirft Exception bei Blockierung
                # Wir pruefen nur, ob wir im Testnet sind (fuer is_testnet Flag)
                is_testnet = (
                    self._env_config.is_testnet
                    if self._env_config is not None
                    else False
                )
                self._safety_guard.ensure_may_place_order(is_testnet=is_testnet)
            except Exception as e:
                reason = f"safety_guard_blocked: {e!s}"
                logger.warning(
                    f"[EXECUTION PIPELINE] SafetyGuard blockiert Orders: {reason}"
                )
                return ExecutionResult(
                    rejected=True,
                    executed_orders=[],
                    execution_results=[],
                    reason=reason,
                    status=ExecutionStatus.BLOCKED_BY_SAFETY,
                    environment=env_str,
                    governance_status=governance_status,
                )

        # 4. Risk-Check (optional, wenn LiveRiskLimits konfiguriert)
        risk_result: LiveRiskCheckResult | None = None
        if self._risk_limits is not None:
            # Konvertiere OrderRequest zu LiveOrderRequest fuer Risk-Check
            live_orders = self._convert_to_live_orders(orders_list, context)
            risk_result = self._risk_limits.check_orders(live_orders)

            if not risk_result.allowed:
                reason = f"risk_limits_violated: {', '.join(risk_result.reasons)}"
                logger.warning(
                    f"[EXECUTION PIPELINE] Risk-Limits blockieren Orders: {reason}"
                )
                # Optional: Run-Logger Event mit abgelehnter Ausfuehrung
                if self._run_logger is not None:
                    self._log_rejected_execution(orders_list, reason, risk_result)
                return ExecutionResult(
                    rejected=True,
                    executed_orders=[],
                    execution_results=[],
                    risk_check=risk_result,
                    reason=reason,
                    status=ExecutionStatus.BLOCKED_BY_RISK,
                    environment=env_str,
                    governance_status=governance_status,
                )

        # 5. Executor: Fuehre Orders aus
        execution_results = self._executor.execute_orders(orders_list)
        self._execution_history.extend(execution_results)

        # 6. Run-Logging (optional)
        if self._run_logger is not None:
            self._log_execution_results(execution_results, risk_result)

        # Erfolgreiche Ausfuehrung
        return ExecutionResult(
            rejected=False,
            executed_orders=execution_results,
            execution_results=execution_results,
            risk_check=risk_result,
            reason=None,
            status=ExecutionStatus.SUCCESS,
            environment=env_str,
            governance_status=governance_status,
        )

    def _convert_to_live_orders(
        self,
        orders: list[OrderRequest],
        context: dict[str, Any] | None = None,
    ) -> list[Any]:
        """
        Konvertiert OrderRequests zu LiveOrderRequests fuer Risk-Check.

        Args:
            orders: Liste von OrderRequests
            context: Optionaler Kontext (z.B. {"current_price": 50000.0})

        Returns:
            Liste von LiveOrderRequests
        """
        # Lazy import um zirkuläre Abhängigkeiten zu vermeiden
        from ..live.orders import LiveOrderRequest

        live_orders: list[LiveOrderRequest] = []
        current_price = (
            context.get("current_price") if context else None
        ) or 0.0  # Fallback

        for i, order in enumerate(orders):
            # Notional berechnen
            notional = order.quantity * current_price if current_price > 0 else None

            # Side konvertieren: "buy"/"sell" -> "BUY"/"SELL"
            side: Side = "BUY" if order.side == "buy" else "SELL"

            live_order = LiveOrderRequest(
                client_order_id=order.client_id
                or f"exec_{i}_{uuid.uuid4().hex[:8]}",
                symbol=order.symbol,
                side=side,
                order_type="MARKET" if order.order_type == "market" else "LIMIT",
                quantity=order.quantity,
                notional=notional,
                strategy_key=order.metadata.get("strategy_key"),
                extra=order.metadata,
            )
            live_orders.append(live_order)

        return live_orders

    def _log_execution_results(
        self,
        execution_results: list[OrderExecutionResult],
        risk_result: LiveRiskCheckResult | None,
    ) -> None:
        """
        Loggt Execution-Results ueber den Run-Logger (Phase 16A).

        Args:
            execution_results: Liste von OrderExecutionResults
            risk_result: Optionales Risk-Check-Ergebnis
        """
        if self._run_logger is None:
            return

        try:
            # Lazy import um zirkuläre Abhängigkeiten zu vermeiden

            from ..live.run_logging import LiveRunEvent

            now = datetime.now(UTC)

            for result in execution_results:
                # Erstelle Event fuer jede ausgeführte Order
                event = LiveRunEvent(
                    step=self._order_counter,
                    ts_event=now,
                    orders_generated=1,
                    orders_filled=1 if result.is_filled else 0,
                    orders_rejected=1 if result.is_rejected else 0,
                    risk_allowed=risk_result.allowed if risk_result else True,
                    risk_reasons="; ".join(risk_result.reasons) if risk_result and risk_result.reasons else "",
                    extra={
                        "order_symbol": result.request.symbol,
                        "order_side": result.request.side,
                        "order_quantity": result.request.quantity,
                        "execution_status": result.status,
                    },
                )

                if result.fill:
                    event.price = result.fill.price
                    event.extra["fill_price"] = result.fill.price
                    event.extra["fill_quantity"] = result.fill.quantity
                    if result.fill.fee:
                        event.extra["fill_fee"] = result.fill.fee

                self._run_logger.log_event(event)

        except Exception as e:
            logger.warning(
                f"[EXECUTION PIPELINE] Run-Logging fehlgeschlagen: {e}"
            )

    def _log_rejected_execution(
        self,
        orders: list[OrderRequest],
        reason: str,
        risk_result: LiveRiskCheckResult | None,
    ) -> None:
        """
        Loggt abgelehnte Ausfuehrung ueber den Run-Logger (Phase 16A).

        Args:
            orders: Liste von abgelehnten Orders
            reason: Grund fuer Ablehnung
            risk_result: Optionales Risk-Check-Ergebnis
        """
        if self._run_logger is None:
            return

        try:
            # Lazy import um zirkuläre Abhängigkeiten zu vermeiden

            from ..live.run_logging import LiveRunEvent

            now = datetime.now(UTC)

            event = LiveRunEvent(
                step=self._order_counter,
                ts_event=now,
                orders_generated=len(orders),
                orders_blocked=len(orders),
                risk_allowed=False,
                risk_reasons=reason,
                extra={
                    "rejection_reason": reason,
                    "n_orders": len(orders),
                },
            )

            self._run_logger.log_event(event)

        except Exception as e:
            logger.warning(
                f"[EXECUTION PIPELINE] Run-Logging (rejected) fehlgeschlagen: {e}"
            )
