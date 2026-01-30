# src/execution/live_session.py
"""
Peak_Trade: Strategy-to-Execution Bridge & Live Session Runner (Phase 80)
=========================================================================

Orchestriert den Flow von Strategy → Signals → Orders → ExecutionPipeline
für Shadow/Testnet-Sessions.

Features:
- Parametrisierbare Session-Konfiguration (LiveSessionConfig)
- Strategy-Laden über Registry
- Data-Feed über vorhandenen Data-Layer
- Order-Execution über ExecutionPipeline mit Safety-Checks
- Modi: "shadow" (Dummy/Paper), "testnet" (Testnet-API mit validate_only)
- LIVE-Mode ist HART BLOCKIERT (Phase 80: Safety-First)

WICHTIG: Es werden KEINE echten Orders an Börsen gesendet!
         Phase 80 ist rein für Shadow/Testnet-Dry-Runs konzipiert.

Example:
    >>> from src.execution.live_session import LiveSessionRunner, LiveSessionConfig
    >>>
    >>> config = LiveSessionConfig(
    ...     mode="shadow",
    ...     strategy_key="ma_crossover",
    ...     symbol="BTC/EUR",
    ...     timeframe="1m",
    ... )
    >>> runner = LiveSessionRunner.from_config(config, peak_config=cfg)
    >>> runner.warmup()
    >>> runner.run_n_steps(10)  # Führe 10 Steps aus
"""

from __future__ import annotations

import logging
import os
import signal
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, TYPE_CHECKING

import pandas as pd

from src.obs import strategy_risk_telemetry

from ..orders.base import OrderRequest, OrderExecutionResult
from .pipeline import ExecutionPipeline, ExecutionPipelineConfig, SignalEvent

if TYPE_CHECKING:
    from ..core.environment import (
        EnvironmentConfig,
        TradingEnvironment,
    )
    from ..live.safety import SafetyGuard, SafetyBlockedError
    from ..live.risk_limits import LiveRiskLimits
    from ..orders.paper import PaperMarketContext
    from ..orders.shadow import ShadowMarketContext, ShadowOrderExecutor
    from ..core.peak_config import PeakConfig
    from ..strategies.base import BaseStrategy
    from ..exchange.dummy_client import DummyExchangeClient
    from ..exchange.kraken_testnet import KrakenTestnetClient

logger = logging.getLogger(__name__)


# =============================================================================
# Session Mode Enum
# =============================================================================


class SessionMode(str, Enum):
    """
    Ausführungsmodus für LiveSessionRunner.

    Values:
        SHADOW: Shadow/Paper-Trading mit DummyExchangeClient (keine echten API-Calls)
        TESTNET: Testnet-Orders via KrakenTestnetClient (validate_only=True)
        LIVE: NICHT ERLAUBT in Phase 80 - wirft Exception!
    """

    SHADOW = "shadow"
    TESTNET = "testnet"
    LIVE = "live"  # NICHT ERLAUBT - nur zur Dokumentation


# =============================================================================
# Live Session Config
# =============================================================================


@dataclass
class LiveSessionConfig:
    """
    Konfiguration für eine LiveSessionRunner-Instanz.

    Ermöglicht parametrisierten Start von Shadow/Testnet-Sessions ohne Hardcoding.

    Attributes:
        mode: Ausführungsmodus ("shadow" oder "testnet")
        strategy_key: Strategie-Registry-Key (z.B. "ma_crossover", "rsi_reversion")
        symbol: Trading-Symbol (z.B. "BTC/EUR", "ETH/USDT")
        timeframe: Candle-Timeframe (z.B. "1m", "5m", "1h")
        config_path: Pfad zur TOML-Config (default: "config/config.toml")
        warmup_candles: Anzahl Warmup-Candles für Strategie-Indikatoren
        position_fraction: Position-Size als Anteil des Kapitals (0.0 - 1.0)
        poll_interval_seconds: Intervall zwischen Data-Polls in Sekunden
        fee_rate: Simulierte Fee-Rate (z.B. 0.001 = 0.1%)
        slippage_bps: Simulierte Slippage in Basispunkten
        start_balance: Simuliertes Startkapital
        enable_risk_limits: Ob Risk-Limits aktiviert werden sollen
        enable_logging: Ob Run-Logging aktiviert werden soll
        run_id: Optionale Run-ID (sonst automatisch generiert)

    Safety Notes:
        - mode="live" wirft eine Exception (Phase 80: nicht erlaubt)
        - Testnet-Mode nutzt validate_only=True (keine echten Testnet-Orders)
    """

    mode: Literal["shadow", "testnet"] = "shadow"
    strategy_key: str = "ma_crossover"
    symbol: str = "BTC/EUR"
    timeframe: str = "1m"
    config_path: str = "config/config.toml"
    warmup_candles: int = 200
    position_fraction: float = 0.1
    poll_interval_seconds: float = 60.0
    fee_rate: float = 0.001
    slippage_bps: float = 5.0
    start_balance: float = 10000.0
    enable_risk_limits: bool = True
    enable_logging: bool = True
    run_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validiert die Konfiguration nach Initialisierung."""
        # LIVE-Mode ist NICHT erlaubt in Phase 80
        if self.mode == "live":
            raise LiveModeNotAllowedError(
                "LIVE-Mode ist in Phase 80 NICHT erlaubt! "
                "Verwende mode='shadow' oder mode='testnet'. "
                "Echte Live-Orders werden erst in einer späteren Phase unterstützt."
            )

        # Validiere mode
        if self.mode not in ("shadow", "testnet"):
            raise ValueError(f"Ungültiger mode: '{self.mode}'. Erlaubt: 'shadow', 'testnet'")

        # Validiere strategy_key
        if not self.strategy_key:
            raise ValueError("strategy_key darf nicht leer sein")

        # Validiere symbol
        if not self.symbol or "/" not in self.symbol:
            raise ValueError(
                f"Ungültiges symbol: '{self.symbol}'. "
                f"Erwartet Format: 'BASE/QUOTE' (z.B. 'BTC/EUR')"
            )

        # Validiere numerische Parameter
        if self.warmup_candles < 0:
            raise ValueError(f"warmup_candles muss >= 0 sein: {self.warmup_candles}")
        if not 0.0 < self.position_fraction <= 1.0:
            raise ValueError(
                f"position_fraction muss im Bereich (0.0, 1.0] sein: {self.position_fraction}"
            )
        if self.poll_interval_seconds <= 0:
            raise ValueError(f"poll_interval_seconds muss > 0 sein: {self.poll_interval_seconds}")
        if self.start_balance <= 0:
            raise ValueError(f"start_balance muss > 0 sein: {self.start_balance}")

    def generate_run_id(self) -> str:
        """Generiert eine eindeutige Run-ID."""
        if self.run_id:
            return self.run_id
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        short_uuid = uuid.uuid4().hex[:8]
        return f"{self.mode}_{self.strategy_key}_{ts}_{short_uuid}"

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "mode": self.mode,
            "strategy_key": self.strategy_key,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "config_path": self.config_path,
            "warmup_candles": self.warmup_candles,
            "position_fraction": self.position_fraction,
            "poll_interval_seconds": self.poll_interval_seconds,
            "fee_rate": self.fee_rate,
            "slippage_bps": self.slippage_bps,
            "start_balance": self.start_balance,
            "enable_risk_limits": self.enable_risk_limits,
            "enable_logging": self.enable_logging,
            "run_id": self.run_id,
        }


# =============================================================================
# Custom Exceptions
# =============================================================================


class LiveModeNotAllowedError(Exception):
    """
    Exception wenn jemand versucht, LIVE-Mode zu aktivieren.

    Phase 80 erlaubt nur Shadow und Testnet. LIVE ist hart blockiert.
    """

    pass


class SessionSetupError(Exception):
    """Exception bei Fehlern während des Session-Setups."""

    pass


class SessionRuntimeError(Exception):
    """Exception bei Fehlern während der Session-Ausführung."""

    pass


# =============================================================================
# Session Metrics
# =============================================================================


@dataclass
class LiveSessionMetrics:
    """
    Metriken für eine LiveSession.

    Attributes:
        steps: Anzahl der ausgeführten Schritte
        start_time: Session-Startzeit
        last_bar_time: Zeitstempel der letzten verarbeiteten Bar
        total_orders_generated: Anzahl aller generierten Orders
        orders_executed: Anzahl erfolgreich ausgeführter Orders
        orders_rejected: Anzahl abgelehnter Orders
        orders_blocked_risk: Anzahl durch Risk-Limits blockierter Orders
        current_position: Aktuelle Position
        last_signal: Letztes Strategy-Signal
    """

    steps: int = 0
    start_time: Optional[datetime] = None
    last_bar_time: Optional[datetime] = None
    total_orders_generated: int = 0
    orders_executed: int = 0
    orders_rejected: int = 0
    orders_blocked_risk: int = 0
    current_position: float = 0.0
    last_signal: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Metriken zu Dictionary."""
        return {
            "steps": self.steps,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_bar_time": self.last_bar_time.isoformat() if self.last_bar_time else None,
            "total_orders_generated": self.total_orders_generated,
            "orders_executed": self.orders_executed,
            "orders_rejected": self.orders_rejected,
            "orders_blocked_risk": self.orders_blocked_risk,
            "fill_rate": (
                self.orders_executed / self.total_orders_generated
                if self.total_orders_generated > 0
                else 0.0
            ),
            "current_position": self.current_position,
            "last_signal": self.last_signal,
        }


# =============================================================================
# Live Session Runner
# =============================================================================


class LiveSessionRunner:
    """
    Strategy-to-Execution Bridge für Shadow/Testnet-Sessions (Phase 80).

    Orchestriert den kompletten Flow:
    1. Strategy über Registry laden
    2. Daten aus Data-Feed beziehen
    3. Strategie-Signale generieren
    4. Orders über ExecutionPipeline (mit Safety-Checks) ausführen
    5. Logging und Metriken

    Modi:
    - "shadow": Verwendet DummyExchangeClient / ShadowOrderExecutor (keine API-Calls)
    - "testnet": Verwendet KrakenTestnetClient mit validate_only=True

    WICHTIG:
    - LIVE-Mode ist NICHT erlaubt (Phase 80)
    - Keine echten Orders werden gesendet
    - Safety-Komponenten (SafetyGuard, LiveRiskLimits) werden integriert

    Example:
        >>> config = LiveSessionConfig(
        ...     mode="shadow",
        ...     strategy_key="ma_crossover",
        ...     symbol="BTC/EUR",
        ... )
        >>> runner = LiveSessionRunner.from_config(config, peak_config=cfg)
        >>> runner.warmup()
        >>> runner.run_n_steps(10)

    Attributes:
        config: LiveSessionConfig mit Session-Parametern
        metrics: LiveSessionMetrics mit Laufzeit-Metriken
        is_running: True wenn Session läuft
        is_warmup_done: True wenn Warmup abgeschlossen
    """

    def __init__(
        self,
        session_config: LiveSessionConfig,
        env_config: "EnvironmentConfig",
        strategy: "BaseStrategy",
        pipeline: ExecutionPipeline,
        data_source: Any,  # CandleSource oder kompatibel
        risk_limits: Optional["LiveRiskLimits"] = None,
        safety_guard: Optional["SafetyGuard"] = None,
        on_step_callback: Optional[Callable[[int, Any], None]] = None,
    ) -> None:
        """
        Initialisiert den LiveSessionRunner.

        Args:
            session_config: LiveSessionConfig mit Session-Parametern
            env_config: EnvironmentConfig für Safety-Checks
            strategy: Trading-Strategie (BaseStrategy)
            pipeline: ExecutionPipeline für Order-Ausführung
            data_source: Datenquelle (CandleSource oder kompatibel)
            risk_limits: Optionale LiveRiskLimits für Risk-Checks
            safety_guard: Optionaler SafetyGuard (sonst wird einer erstellt)
            on_step_callback: Optionaler Callback nach jedem Step

        Raises:
            LiveModeNotAllowedError: Wenn mode="live" (Phase 80)
        """
        # LIVE-Mode hart blockieren
        if session_config.mode == "live":
            raise LiveModeNotAllowedError(
                "LIVE-Mode ist in Phase 80 NICHT erlaubt! "
                "Verwende mode='shadow' oder mode='testnet'."
            )

        self._config = session_config
        self._env_config = env_config
        self._strategy = strategy
        self._pipeline = pipeline
        self._data_source = data_source
        self._risk_limits = risk_limits

        # Lazy import für SafetyGuard falls nicht übergeben
        if safety_guard is None:
            from ..live.safety import SafetyGuard

            safety_guard = SafetyGuard(env_config=env_config)
        self._safety_guard = safety_guard
        self._on_step_callback = on_step_callback

        # Metriken
        self._metrics = LiveSessionMetrics()

        # Session-State
        self._is_running = False
        self._is_warmup_done = False
        self._shutdown_requested = False
        self._last_signal = 0

        # Run-ID
        self._run_id = session_config.generate_run_id()

        # Signal Handler für Graceful Shutdown
        self._original_sigint_handler = None
        self._original_sigterm_handler = None

        logger.info(
            f"[LIVE SESSION] Initialisiert: "
            f"mode={session_config.mode}, "
            f"strategy={session_config.strategy_key}, "
            f"symbol={session_config.symbol}, "
            f"run_id={self._run_id}"
        )

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def config(self) -> LiveSessionConfig:
        """Zugriff auf Session-Config."""
        return self._config

    @property
    def metrics(self) -> LiveSessionMetrics:
        """Zugriff auf Session-Metriken."""
        return self._metrics

    @property
    def is_running(self) -> bool:
        """True wenn Session läuft."""
        return self._is_running

    @property
    def is_warmup_done(self) -> bool:
        """True wenn Warmup abgeschlossen."""
        return self._is_warmup_done

    @property
    def run_id(self) -> str:
        """Run-ID der Session."""
        return self._run_id

    @property
    def strategy(self) -> "BaseStrategy":
        """Zugriff auf die Strategie."""
        return self._strategy

    @property
    def pipeline(self) -> ExecutionPipeline:
        """Zugriff auf die ExecutionPipeline."""
        return self._pipeline

    # =========================================================================
    # Factory Methods
    # =========================================================================

    @classmethod
    def from_config(
        cls,
        session_config: LiveSessionConfig,
        peak_config: Optional["PeakConfig"] = None,
    ) -> "LiveSessionRunner":
        """
        Factory-Methode: Erstellt LiveSessionRunner aus Config.

        Lädt alle benötigten Komponenten (Strategy, Pipeline, Data-Source, etc.)
        basierend auf der LiveSessionConfig.

        Args:
            session_config: LiveSessionConfig mit Session-Parametern
            peak_config: Optionale PeakConfig (sonst wird aus config_path geladen)

        Returns:
            Konfigurierter LiveSessionRunner

        Raises:
            LiveModeNotAllowedError: Wenn mode="live"
            SessionSetupError: Bei Setup-Fehlern

        Example:
            >>> config = LiveSessionConfig(mode="shadow", strategy_key="ma_crossover")
            >>> runner = LiveSessionRunner.from_config(config)
        """
        # LIVE-Mode hart blockieren (redundant, aber explizit)
        if session_config.mode == "live":
            raise LiveModeNotAllowedError("LIVE-Mode ist in Phase 80 NICHT erlaubt!")

        logger.info(f"[LIVE SESSION] Baue Session aus Config: {session_config.mode}")

        try:
            # Lazy imports um Circular Imports zu vermeiden
            from ..core.environment import (
                EnvironmentConfig,
                TradingEnvironment,
            )
            from ..live.safety import SafetyGuard
            from ..live.risk_limits import LiveRiskLimits

            # 1. PeakConfig laden falls nicht übergeben
            if peak_config is None:
                from ..core.peak_config import load_config

                peak_config = load_config(session_config.config_path)

            # 2. EnvironmentConfig erstellen (Paper für Shadow, Testnet für Testnet)
            if session_config.mode == "shadow":
                env_config = EnvironmentConfig(
                    environment=TradingEnvironment.PAPER,
                    enable_live_trading=False,
                    testnet_dry_run=True,
                )
            else:  # testnet
                env_config = EnvironmentConfig(
                    environment=TradingEnvironment.TESTNET,
                    enable_live_trading=False,
                    testnet_dry_run=True,  # Immer True in Phase 80
                )

            # 3. Strategy laden über Registry
            from ..strategies.registry import create_strategy_from_config

            strategy = create_strategy_from_config(session_config.strategy_key, peak_config)
            logger.info(f"[LIVE SESSION] Strategy geladen: {strategy}")

            # 4. ExecutionPipeline erstellen
            pipeline = cls._build_pipeline(session_config, env_config)

            # 5. Data-Source erstellen
            data_source = cls._build_data_source(session_config)

            # 6. Risk-Limits erstellen (wenn aktiviert)
            risk_limits = None
            if session_config.enable_risk_limits:
                risk_limits = LiveRiskLimits.from_config(
                    peak_config, starting_cash=session_config.start_balance
                )

            # 7. SafetyGuard erstellen
            safety_guard = SafetyGuard(env_config=env_config)

            return cls(
                session_config=session_config,
                env_config=env_config,
                strategy=strategy,
                pipeline=pipeline,
                data_source=data_source,
                risk_limits=risk_limits,
                safety_guard=safety_guard,
            )

        except LiveModeNotAllowedError:
            raise
        except Exception as e:
            raise SessionSetupError(f"Session-Setup fehlgeschlagen: {e}") from e

    @classmethod
    def _build_pipeline(
        cls,
        session_config: LiveSessionConfig,
        env_config: "EnvironmentConfig",
    ) -> ExecutionPipeline:
        """
        Baut eine ExecutionPipeline basierend auf dem Session-Mode.

        Args:
            session_config: LiveSessionConfig
            env_config: EnvironmentConfig

        Returns:
            Konfigurierte ExecutionPipeline
        """
        # Lazy imports um Circular Imports zu vermeiden
        from ..orders.shadow import ShadowMarketContext
        from ..live.safety import SafetyGuard

        if session_config.mode == "shadow":
            # Shadow-Mode: ShadowOrderExecutor (keine echten API-Calls)
            market_context = ShadowMarketContext(
                fee_rate=session_config.fee_rate,
                slippage_bps=session_config.slippage_bps,
            )
            pipeline = ExecutionPipeline.for_shadow(
                market_context=market_context,
                fee_rate=session_config.fee_rate,
                slippage_bps=session_config.slippage_bps,
            )
        else:
            # Testnet-Mode: Auch ShadowOrderExecutor für Phase 80
            # (Echte Testnet-Integration kann später hinzugefügt werden)
            market_context = ShadowMarketContext(
                fee_rate=session_config.fee_rate,
                slippage_bps=session_config.slippage_bps,
            )
            pipeline = ExecutionPipeline.for_shadow(
                market_context=market_context,
                fee_rate=session_config.fee_rate,
                slippage_bps=session_config.slippage_bps,
            )
            logger.info("[LIVE SESSION] Testnet-Mode nutzt Shadow-Pipeline (Phase 80: Dry-Run)")

        # Safety-Komponenten zur Pipeline hinzufügen
        pipeline._env_config = env_config
        pipeline._safety_guard = SafetyGuard(env_config=env_config)

        return pipeline

    @classmethod
    def _build_data_source(cls, session_config: LiveSessionConfig) -> Any:
        """
        Baut eine Datenquelle basierend auf der Config.

        Args:
            session_config: LiveSessionConfig

        Returns:
            CandleSource oder kompatible Datenquelle
        """
        try:
            from ..data.kraken_live import (
                KrakenLiveCandleSource,
                ShadowPaperConfig,
                LiveExchangeConfig,
            )

            # Für Shadow-/Testnet-Mode: KrakenLiveCandleSource mit Public-API
            data_source = KrakenLiveCandleSource(
                symbol=session_config.symbol,
                timeframe=session_config.timeframe,
                warmup_candles=session_config.warmup_candles,
            )
            return data_source

        except ImportError:
            # Fallback: Einfache In-Memory-Source für Tests
            logger.warning(
                "[LIVE SESSION] KrakenLiveCandleSource nicht verfügbar, verwende Dummy-Source"
            )
            return _DummyCandleSource(
                symbol=session_config.symbol,
                timeframe=session_config.timeframe,
            )

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    def warmup(self) -> None:
        """
        Führt Warmup durch: Lädt historische Candles für Strategie-Indikatoren.

        Raises:
            SessionRuntimeError: Bei Warmup-Fehlern
        """
        logger.info(f"[LIVE SESSION] Starte Warmup: {self._config.warmup_candles} Candles...")

        try:
            if hasattr(self._data_source, "warmup"):
                candles = self._data_source.warmup()

                if candles:
                    logger.info(f"[LIVE SESSION] Warmup abgeschlossen: {len(candles)} Candles")
                    if hasattr(candles[-1], "timestamp"):
                        self._metrics.last_bar_time = candles[-1].timestamp
                else:
                    logger.warning("[LIVE SESSION] Warmup: Keine Candles erhalten")
            else:
                logger.info("[LIVE SESSION] Data-Source hat keine warmup()-Methode")

            self._is_warmup_done = True
            self._metrics.start_time = datetime.now(timezone.utc)

        except Exception as e:
            raise SessionRuntimeError(f"Warmup fehlgeschlagen: {e}") from e

    def step_once(self) -> Optional[List[OrderExecutionResult]]:
        """
        Führt einen einzelnen Session-Schritt durch.

        Workflow:
        1. Neue Candle von Data-Source holen
        2. Strategie-Signal generieren
        3. Bei Signal-Änderung: Orders erstellen
        4. Orders über ExecutionPipeline (mit Safety) ausführen
        5. Metriken aktualisieren

        Returns:
            Liste von OrderExecutionResults oder None wenn keine Orders
        """
        self._metrics.steps += 1
        step_num = self._metrics.steps

        # 1. Neue Candle holen
        candle = None
        if hasattr(self._data_source, "poll_latest"):
            candle = self._data_source.poll_latest()

        # Callback aufrufen
        if self._on_step_callback:
            self._on_step_callback(step_num, candle)

        if candle is None:
            logger.debug(f"[LIVE SESSION] Step {step_num}: Keine neue Candle")
            return None

        # Candle-Infos extrahieren
        if hasattr(candle, "timestamp"):
            self._metrics.last_bar_time = candle.timestamp
        if hasattr(candle, "close"):
            current_price = candle.close
        else:
            current_price = 0.0

        # 2. Preis im Pipeline-Executor aktualisieren
        if hasattr(self._pipeline.executor, "context"):
            self._pipeline.executor.context.set_price(self._config.symbol, current_price)

        # 3. Signal von Strategie generieren
        buffer_df = None
        if hasattr(self._data_source, "get_buffer"):
            buffer_df = self._data_source.get_buffer()

        if buffer_df is None or len(buffer_df) < 50:
            logger.debug(f"[LIVE SESSION] Step {step_num}: Zu wenig Daten für Signal")
            return None

        try:
            signals = self._strategy.generate_signals(buffer_df)
            current_signal = int(signals.iloc[-1]) if len(signals) > 0 else 0
        except Exception as e:
            logger.warning(f"[LIVE SESSION] Signal-Fehler: {e}")
            return None

        self._metrics.last_signal = current_signal

        # 4. Bei Signal-Änderung: Orders erstellen
        if current_signal == self._last_signal:
            logger.debug(f"[LIVE SESSION] Step {step_num}: Signal unverändert ({current_signal})")
            return None

        logger.info(
            f"[LIVE SESSION] Signal-Änderung: {self._last_signal} -> {current_signal} "
            f"@ price={current_price:.2f}"
        )

        # Telemetry: count final signal event once per change (watch-only safe)
        try:
            from ..obs import trade_flow_telemetry

            trade_flow_telemetry.inc_signal(
                strategy_id=self._config.strategy_key,
                symbol=self._config.symbol,
                signal=("buy" if current_signal > 0 else "sell" if current_signal < 0 else "flat"),
                n=1,
            )
        except Exception:
            pass

        # SignalEvent erstellen
        sig_event = SignalEvent(
            timestamp=datetime.now(timezone.utc),
            symbol=self._config.symbol,
            signal=current_signal,
            price=current_price,
            previous_signal=self._last_signal,
            metadata={
                "strategy": self._config.strategy_key,
                "mode": self._config.mode,
                "run_id": self._run_id,
            },
        )

        # Orders generieren
        orders = self._pipeline.signal_to_orders(
            event=sig_event,
            position_size=self._config.position_fraction,
            current_position=self._metrics.current_position,
        )

        if not orders:
            self._last_signal = current_signal
            return None

        self._metrics.total_orders_generated += len(orders)

        # 5. Orders über ExecutionPipeline (mit Safety) ausführen
        exec_result = self._pipeline.execute_with_safety(
            orders=orders,
            context={"current_price": current_price},
        )

        # Metriken aktualisieren
        if exec_result.rejected:
            self._metrics.orders_blocked_risk += len(orders)
            logger.warning(f"[LIVE SESSION] Orders blockiert: {exec_result.reason}")
        else:
            for result in exec_result.executed_orders:
                if result.is_filled:
                    self._metrics.orders_executed += 1
                    if result.fill:
                        if result.fill.side == "buy":
                            self._metrics.current_position += result.fill.quantity
                        else:
                            self._metrics.current_position -= result.fill.quantity
                elif result.is_rejected:
                    self._metrics.orders_rejected += 1

        self._last_signal = current_signal

        # SLICE4 telemetry (watch/paper/shadow safe): gross exposure gauge (no symbol label).
        try:
            from src.obs import strategy_risk_telemetry as _srt

            sym = str(self._config.symbol or "")
            ccy = sym.split("/", 1)[1] if "/" in sym else "NA"
            exposure = abs(float(self._metrics.current_position)) * float(current_price)
            _srt.set_strategy_position_gross_exposure(
                strategy_id=str(getattr(self._config, "strategy_key", None) or "na"),
                ccy=ccy,
                exposure=exposure,
            )
        except Exception:
            pass

        return exec_result.executed_orders if not exec_result.rejected else []

    def run_n_steps(self, n: int, sleep_between: bool = False) -> List[OrderExecutionResult]:
        """
        Führt n Schritte aus und stoppt dann.

        Args:
            n: Anzahl der Schritte
            sleep_between: Ob zwischen Steps gewartet werden soll

        Returns:
            Liste aller OrderExecutionResults
        """
        if not self._is_warmup_done:
            raise SessionRuntimeError("Warmup muss vor run_n_steps() aufgerufen werden.")

        strategy_risk_telemetry.ensure_registered()
        if (os.getenv("PEAKTRADE_METRICS_MODE", "") or "").strip().upper() != "B":
            from src.obs.metrics_server import ensure_metrics_server

            ensure_metrics_server()

        all_results: List[OrderExecutionResult] = []

        for i in range(n):
            if self._shutdown_requested:
                break

            results = self.step_once()
            if results:
                all_results.extend(results)

            if sleep_between and i < n - 1:
                time.sleep(self._config.poll_interval_seconds)

        return all_results

    def run_for_duration(self, minutes: int) -> List[OrderExecutionResult]:
        """
        Führt Session für eine bestimmte Dauer aus.

        Args:
            minutes: Laufzeit in Minuten

        Returns:
            Liste aller OrderExecutionResults
        """
        if not self._is_warmup_done:
            raise SessionRuntimeError("Warmup muss vor run_for_duration() aufgerufen werden.")

        strategy_risk_telemetry.ensure_registered()
        if (os.getenv("PEAKTRADE_METRICS_MODE", "") or "").strip().upper() != "B":
            from src.obs.metrics_server import ensure_metrics_server

            ensure_metrics_server()

        end_time = time.time() + (minutes * 60)
        all_results: List[OrderExecutionResult] = []

        logger.info(f"[LIVE SESSION] Starte für {minutes} Minuten...")

        while time.time() < end_time and not self._shutdown_requested:
            results = self.step_once()
            if results:
                all_results.extend(results)
            time.sleep(self._config.poll_interval_seconds)

        self._log_session_summary()
        return all_results

    def run_forever(self) -> None:
        """
        Startet den kontinuierlichen Session-Loop.

        Läuft bis KeyboardInterrupt (Ctrl+C) oder shutdown() aufgerufen wird.

        Raises:
            SessionRuntimeError: Wenn Warmup nicht durchgeführt wurde
        """
        if not self._is_warmup_done:
            raise SessionRuntimeError("Warmup muss vor run_forever() aufgerufen werden.")

        strategy_risk_telemetry.ensure_registered()
        if (os.getenv("PEAKTRADE_METRICS_MODE", "") or "").strip().upper() != "B":
            from src.obs.metrics_server import ensure_metrics_server

            ensure_metrics_server()

        self._is_running = True
        self._shutdown_requested = False
        self._setup_signal_handlers()

        logger.info(
            f"[LIVE SESSION] Starte Loop: poll_interval={self._config.poll_interval_seconds}s"
        )

        try:
            while not self._shutdown_requested:
                try:
                    self.step_once()
                except Exception as e:
                    logger.error(f"[LIVE SESSION] Fehler in step_once: {e}")

                time.sleep(self._config.poll_interval_seconds)

        except KeyboardInterrupt:
            logger.info("[LIVE SESSION] KeyboardInterrupt empfangen")

        finally:
            self._is_running = False
            self._restore_signal_handlers()
            self._log_session_summary()

    def shutdown(self) -> None:
        """Signalisiert der Session zu stoppen."""
        logger.info("[LIVE SESSION] Shutdown angefordert")
        self._shutdown_requested = True

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _setup_signal_handlers(self) -> None:
        """Installiert Signal-Handler für Graceful Shutdown."""

        def shutdown_handler(signum: int, frame: Any) -> None:
            logger.info(f"[LIVE SESSION] Shutdown-Signal empfangen (signal={signum})")
            self._shutdown_requested = True

        self._original_sigint_handler = signal.signal(signal.SIGINT, shutdown_handler)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, shutdown_handler)

    def _restore_signal_handlers(self) -> None:
        """Stellt ursprüngliche Signal-Handler wieder her."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)

    def _log_session_summary(self) -> None:
        """Loggt eine Zusammenfassung der Session."""
        metrics = self._metrics.to_dict()
        logger.info(
            f"[LIVE SESSION] === Session-Zusammenfassung ===\n"
            f"  Run-ID: {self._run_id}\n"
            f"  Mode: {self._config.mode}\n"
            f"  Strategy: {self._config.strategy_key}\n"
            f"  Steps: {metrics['steps']}\n"
            f"  Total Orders: {metrics['total_orders_generated']}\n"
            f"  Executed: {metrics['orders_executed']}\n"
            f"  Rejected: {metrics['orders_rejected']}\n"
            f"  Blocked (Risk): {metrics['orders_blocked_risk']}\n"
            f"  Fill Rate: {metrics['fill_rate']:.1%}\n"
            f"  Current Position: {metrics['current_position']:.6f}"
        )

    def get_summary(self) -> Dict[str, Any]:
        """
        Gibt eine Zusammenfassung der Session zurück.

        Returns:
            Dict mit Session-Infos und Metriken
        """
        return {
            "run_id": self._run_id,
            "config": self._config.to_dict(),
            "metrics": self._metrics.to_dict(),
            "pipeline_summary": self._pipeline.get_execution_summary(),
        }


# =============================================================================
# Dummy Candle Source (Fallback für Tests)
# =============================================================================


class _DummyCandleSource:
    """
    Minimale Dummy-Datenquelle für Tests wenn KrakenLiveCandleSource nicht verfügbar.

    ACHTUNG: Nur für Unit-Tests! Produziert keine echten Daten.
    """

    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe
        self._candles: List[Dict[str, Any]] = []
        self._step = 0

    def warmup(self) -> List[Dict[str, Any]]:
        """Simuliert Warmup mit Dummy-Daten."""
        import random

        base_price = 50000.0
        self._candles = []

        for i in range(100):
            price = base_price + random.uniform(-1000, 1000)
            candle = {
                "timestamp": datetime.now(timezone.utc),
                "open": price,
                "high": price + random.uniform(0, 100),
                "low": price - random.uniform(0, 100),
                "close": price + random.uniform(-50, 50),
                "volume": random.uniform(1, 100),
            }
            self._candles.append(candle)

        return self._candles

    def poll_latest(self) -> Optional[Dict[str, Any]]:
        """Gibt simulierte Candle zurück."""
        if not self._candles:
            return None

        self._step += 1
        # Rotiere durch existierende Candles
        return self._candles[self._step % len(self._candles)]

    def get_buffer(self) -> pd.DataFrame:
        """Gibt Candle-Buffer als DataFrame zurück."""
        if not self._candles:
            return pd.DataFrame()

        df = pd.DataFrame(self._candles)
        df.index = pd.to_datetime(df["timestamp"])
        return df


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SessionMode",
    "LiveSessionConfig",
    "LiveSessionRunner",
    "LiveSessionMetrics",
    "LiveModeNotAllowedError",
    "SessionSetupError",
    "SessionRuntimeError",
]
