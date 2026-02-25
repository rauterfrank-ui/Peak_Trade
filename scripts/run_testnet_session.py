#!/usr/bin/env python3
"""
Peak_Trade: Testnet Session CLI (Phase 35)
===========================================

Command-Line-Interface zum Starten einer Testnet-Trading-Session
mit echten Exchange-API-Calls (im Testnet/Demo-Modus).

Anders als run_shadow_paper_session.py sendet dieses Script
tatsaechliche Orders an die Exchange-API (im validate_only-Modus).

Usage:
    # Standard-Start mit MA-Crossover Strategie:
    python -m scripts.run_testnet_session --config config/config.toml

    # Mit anderer Strategie:
    python -m scripts.run_testnet_session --strategy rsi_strategy

    # Mit anderem Symbol:
    python -m scripts.run_testnet_session --symbol ETH/EUR

    # Fuer begrenzte Dauer (z.B. 30 Minuten):
    python -m scripts.run_testnet_session --duration 30

    # Ohne Run-Logging:
    python -m scripts.run_testnet_session --no-logging

Voraussetzungen:
    - Environment-Variablen KRAKEN_TESTNET_API_KEY und KRAKEN_TESTNET_API_SECRET
    - config/config.toml mit [environment] mode = "testnet"
    - config/config.toml mit [exchange.kraken_testnet] Block

WICHTIG:
    - Nur Testnet-Environment ist erlaubt!
    - Default: validate_only=true (Orders werden validiert, nicht ausgefuehrt)
    - Keine echten Live-Trades in Phase 35!

Zum Beenden: Ctrl+C (SIGINT) oder SIGTERM
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Projekt-Root zum Path hinzufuegen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import load_config, PeakConfig
from src.core.environment import (
    get_environment_from_config,
    TradingEnvironment,
    EnvironmentConfig,
)
from src.live.safety import SafetyGuard
from src.live.risk_limits import LiveRiskLimits, LiveRiskCheckResult
from src.live.orders import LiveOrderRequest
from src.live.run_logging import (
    LiveRunLogger,
    LiveRunMetadata,
    LiveRunEvent,
    ShadowPaperLoggingConfig,
    load_shadow_paper_logging_config,
    generate_run_id,
)
from src.orders.base import OrderRequest, OrderExecutionResult
from src.orders.testnet_executor import (
    TestnetExchangeOrderExecutor,
    EnvironmentNotTestnetError,
)
from src.exchange.kraken_testnet import (
    KrakenTestnetClient,
    KrakenTestnetConfig,
    create_kraken_testnet_client_from_config,
    ExchangeAPIError,
)
from src.strategies.base import BaseStrategy
from src.execution.pipeline import ExecutionPipeline, SignalEvent


def _emit_exec_event_safe(**kwargs: Any) -> None:
    """Emit execution event (no-op when PT_EXEC_EVENTS_ENABLED=false). Never raises."""
    try:
        from src.observability.execution_events import emit

        emit(**kwargs)
    except Exception:
        pass


# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Konfiguriert Logging fuer CLI."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Weniger Noise von requests/urllib3
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return logging.getLogger("testnet_session")


# =============================================================================
# Session Config
# =============================================================================


@dataclass
class TestnetSessionConfig:
    """
    Konfiguration fuer eine Testnet-Session.

    Attributes:
        symbol: Trading-Symbol (z.B. "BTC/EUR")
        timeframe: Candle-Timeframe (z.B. "1m", "5m", "1h")
        poll_interval_seconds: Polling-Intervall in Sekunden
        warmup_candles: Anzahl Candles fuer Warmup
        start_balance: Start-Balance fuer Tracking
        position_fraction: Position-Size als Anteil des Kapitals
        fee_rate: Fee-Rate fuer PnL-Berechnung
        slippage_bps: Slippage in Basispunkten
    """

    symbol: str = "BTC/EUR"
    timeframe: str = "1m"
    poll_interval_seconds: float = 60.0
    warmup_candles: int = 200
    start_balance: float = 10000.0
    position_fraction: float = 0.1
    fee_rate: float = 0.0026
    slippage_bps: float = 5.0


def load_testnet_session_config(cfg: PeakConfig) -> TestnetSessionConfig:
    """Laedt TestnetSessionConfig aus PeakConfig."""
    return TestnetSessionConfig(
        symbol=cfg.get("testnet_session.symbol", "BTC/EUR"),
        timeframe=cfg.get("testnet_session.timeframe", "1m"),
        poll_interval_seconds=float(cfg.get("testnet_session.poll_interval_seconds", 60.0)),
        warmup_candles=int(cfg.get("testnet_session.warmup_candles", 200)),
        start_balance=float(cfg.get("testnet_session.start_balance", 10000.0)),
        position_fraction=float(cfg.get("testnet_session.position_fraction", 0.1)),
        fee_rate=float(cfg.get("testnet_session.fee_rate", 0.0026)),
        slippage_bps=float(cfg.get("testnet_session.slippage_bps", 5.0)),
    )


# =============================================================================
# Session Metrics
# =============================================================================


@dataclass
class TestnetSessionMetrics:
    """Metriken fuer eine Testnet-Session."""

    steps: int = 0
    start_time: Optional[datetime] = None
    last_bar_time: Optional[datetime] = None
    total_orders: int = 0
    filled_orders: int = 0
    rejected_orders: int = 0
    risk_blocked_orders: int = 0
    total_pnl: float = 0.0
    current_position: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Metriken zu Dictionary."""
        return {
            "steps": self.steps,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_bar_time": self.last_bar_time.isoformat() if self.last_bar_time else None,
            "total_orders": self.total_orders,
            "filled_orders": self.filled_orders,
            "rejected_orders": self.rejected_orders,
            "risk_blocked_orders": self.risk_blocked_orders,
            "fill_rate": self.filled_orders / self.total_orders if self.total_orders > 0 else 0.0,
            "total_pnl": self.total_pnl,
            "current_position": self.current_position,
        }


# =============================================================================
# Strategy Factory
# =============================================================================


def create_strategy(strategy_name: str, cfg: PeakConfig) -> BaseStrategy:
    """
    Factory fuer Trading-Strategien.

    Args:
        strategy_name: Name der Strategie
        cfg: PeakConfig fuer Parameter

    Returns:
        Strategie-Instanz

    Raises:
        ValueError: Bei unbekannter Strategie
    """
    from src.strategies.ma_crossover import MACrossoverStrategy

    strategy_map = {
        "ma_crossover": lambda: MACrossoverStrategy.from_config(cfg, "strategy.ma_crossover"),
    }

    # Weitere Strategien dynamisch importieren
    try:
        from src.strategies.momentum import MomentumStrategy

        strategy_map["momentum_1h"] = lambda: MomentumStrategy.from_config(
            cfg, "strategy.momentum_1h"
        )
    except ImportError:
        pass

    try:
        from src.strategies.rsi_reversion import RSIStrategy

        strategy_map["rsi_strategy"] = lambda: RSIStrategy.from_config(cfg, "strategy.rsi_strategy")
    except ImportError:
        pass

    try:
        from src.strategies.macd import MACDStrategy

        strategy_map["macd"] = lambda: MACDStrategy.from_config(cfg, "strategy.macd")
    except ImportError:
        pass

    if strategy_name not in strategy_map:
        available = list(strategy_map.keys())
        raise ValueError(f"Unbekannte Strategie: '{strategy_name}'. Verfuegbar: {available}")

    return strategy_map[strategy_name]()


# =============================================================================
# Testnet Session
# =============================================================================


class TestnetSession:
    """
    Testnet-Trading-Session mit echten Exchange-API-Calls.

    Diese Session:
    1. Pollt Marktdaten von der Exchange
    2. Generiert Strategie-Signale
    3. Prueft Risk-Limits
    4. Sendet Orders an die Exchange (Testnet/validate_only)
    5. Loggt alle Aktivitaeten

    WICHTIG: Nur im Testnet-Environment erlaubt!
    """

    def __init__(
        self,
        env_config: EnvironmentConfig,
        session_config: TestnetSessionConfig,
        exchange_client: KrakenTestnetClient,
        executor: TestnetExchangeOrderExecutor,
        strategy: BaseStrategy,
        risk_limits: LiveRiskLimits,
        run_logger: Optional[LiveRunLogger] = None,
    ) -> None:
        """
        Initialisiert die Testnet-Session.

        Args:
            env_config: Environment-Konfiguration
            session_config: Session-Konfiguration
            exchange_client: Kraken Testnet Client
            executor: Testnet Order Executor
            strategy: Trading-Strategie
            risk_limits: Risk-Limits
            run_logger: Optionaler Run-Logger

        Raises:
            EnvironmentNotTestnetError: Wenn nicht im Testnet-Modus
        """
        if env_config.environment != TradingEnvironment.TESTNET:
            raise EnvironmentNotTestnetError(
                f"TestnetSession erfordert environment=TESTNET. "
                f"Aktuell: {env_config.environment.value}"
            )

        self._env_config = env_config
        self._session_config = session_config
        self._client = exchange_client
        self._executor = executor
        self._strategy = strategy
        self._risk_limits = risk_limits
        self._run_logger = run_logger

        self._metrics = TestnetSessionMetrics()
        self._is_running = False
        self._shutdown_requested = False
        self._last_signal: int = 0
        self._price_buffer: List[Dict[str, Any]] = []

        # Signal Handler
        self._original_sigint_handler = None
        self._original_sigterm_handler = None

        self._logger = logging.getLogger("testnet_session")
        self._logger.info(
            f"[TESTNET SESSION] Initialisiert: "
            f"symbol={session_config.symbol}, "
            f"timeframe={session_config.timeframe}, "
            f"executor_mode={executor.effective_mode}"
        )

    @property
    def metrics(self) -> TestnetSessionMetrics:
        """Zugriff auf Session-Metriken."""
        return self._metrics

    @property
    def is_running(self) -> bool:
        """True wenn Session laeuft."""
        return self._is_running

    def _setup_signal_handlers(self) -> None:
        """Installiert Signal-Handler fuer graceful shutdown."""

        def shutdown_handler(signum: int, frame: Any) -> None:
            self._logger.info(f"[TESTNET SESSION] Shutdown-Signal empfangen (signal={signum})")
            self._shutdown_requested = True

        self._original_sigint_handler = signal.signal(signal.SIGINT, shutdown_handler)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, shutdown_handler)

    def _restore_signal_handlers(self) -> None:
        """Stellt urspruengliche Signal-Handler wieder her."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)

    def warmup(self) -> None:
        """
        Fuehrt Warmup durch: Holt historische Daten fuer Strategie.
        """
        self._logger.info(
            f"[TESTNET SESSION] Starte Warmup: {self._session_config.warmup_candles} Candles..."
        )

        try:
            # Versuche Ticker zu holen als Verbindungstest
            ticker = self._client.fetch_ticker(self._session_config.symbol)
            self._logger.info(
                f"[TESTNET SESSION] Verbindung OK: "
                f"{self._session_config.symbol} @ {ticker.get('last', 'N/A')}"
            )

            self._metrics.start_time = datetime.now(timezone.utc)
            self._logger.info("[TESTNET SESSION] Warmup abgeschlossen")

        except ExchangeAPIError as e:
            self._logger.error(f"[TESTNET SESSION] Warmup fehlgeschlagen: {e}")
            raise RuntimeError(f"Warmup fehlgeschlagen: {e}") from e

    def step_once(self) -> Optional[List[OrderExecutionResult]]:
        """
        Fuehrt einen einzelnen Session-Schritt durch.

        1. Holt aktuellen Ticker
        2. Generiert Strategie-Signal (vereinfacht)
        3. Bei Signal-Aenderung: Order erstellen
        4. Risk-Check und Order-Ausfuehrung

        Returns:
            Liste von OrderExecutionResults oder None
        """
        self._metrics.steps += 1
        step_num = self._metrics.steps
        now = datetime.now(timezone.utc)

        # Event-Daten sammeln
        event_data: Dict[str, Any] = {
            "step": step_num,
            "ts_event": now,
            "signal": 0,
            "signal_changed": False,
            "orders_generated": 0,
            "orders_filled": 0,
            "orders_rejected": 0,
            "risk_allowed": True,
        }

        try:
            # 1. Ticker holen
            ticker = self._client.fetch_ticker(self._session_config.symbol)
            current_price = ticker.get("last")

            if current_price is None:
                self._logger.debug(f"[TESTNET SESSION] Step {step_num}: Kein Preis verfuegbar")
                return None

            event_data["price"] = current_price
            self._metrics.last_bar_time = now

            # Preis zum Buffer hinzufuegen (fuer Strategie)
            self._price_buffer.append(
                {
                    "timestamp": now,
                    "close": current_price,
                }
            )

            # Buffer begrenzen
            max_buffer = self._session_config.warmup_candles + 50
            if len(self._price_buffer) > max_buffer:
                self._price_buffer = self._price_buffer[-max_buffer:]

            # 2. Signal generieren (vereinfacht - basierend auf Preis-Momentum)
            # In einer echten Implementierung wuerde hier die Strategie aufgerufen
            current_signal = self._generate_simple_signal()
            event_data["signal"] = current_signal

            # 3. Bei Signal-Aenderung: Order erstellen
            if current_signal == self._last_signal:
                self._log_step_event(event_data)
                return None

            event_data["signal_changed"] = True
            self._logger.info(
                f"[TESTNET SESSION] Signal-Aenderung: {self._last_signal} -> {current_signal} "
                f"@ price={current_price:.2f}"
            )

            # Order erstellen
            if current_signal != 0:
                side = "buy" if current_signal > 0 else "sell"
                quantity = self._calculate_quantity(current_price)

                order = OrderRequest(
                    symbol=self._session_config.symbol,
                    side=side,
                    quantity=quantity,
                    order_type="market",
                    client_id=f"testnet_{step_num}_{int(time.time())}",
                    metadata={
                        "strategy": self._strategy.key,
                        "signal": current_signal,
                        "step": step_num,
                    },
                )

                event_data["orders_generated"] = 1

                # 4. Order ausfuehren
                result = self._executor.execute_order(order, current_price)

                # Metriken aktualisieren
                self._metrics.total_orders += 1
                if result.is_filled:
                    self._metrics.filled_orders += 1
                    event_data["orders_filled"] = 1
                    if result.fill:
                        if result.fill.side == "buy":
                            self._metrics.current_position += result.fill.quantity
                        else:
                            self._metrics.current_position -= result.fill.quantity
                elif result.is_rejected:
                    self._metrics.rejected_orders += 1
                    event_data["orders_rejected"] = 1
                    if "risk_limit" in (result.reason or ""):
                        self._metrics.risk_blocked_orders += 1
                        event_data["risk_allowed"] = False

                self._last_signal = current_signal
                self._log_step_event(event_data)
                return [result]

            self._last_signal = current_signal
            self._log_step_event(event_data)
            return None

        except Exception as e:
            self._logger.error(f"[TESTNET SESSION] Step {step_num} fehlgeschlagen: {e}")
            return None

    def _generate_simple_signal(self) -> int:
        """
        Generiert ein einfaches Signal basierend auf Preis-Momentum.

        In einer echten Implementierung wuerde hier die Strategie verwendet.

        Returns:
            1 (long), -1 (short), oder 0 (neutral)
        """
        if len(self._price_buffer) < 20:
            return 0

        # Einfaches Momentum: Vergleiche aktuellen Preis mit Durchschnitt der letzten 20
        recent_prices = [p["close"] for p in self._price_buffer[-20:]]
        avg_price = sum(recent_prices) / len(recent_prices)
        current_price = self._price_buffer[-1]["close"]

        if current_price > avg_price * 1.01:  # 1% ueber Durchschnitt -> Long
            return 1
        elif current_price < avg_price * 0.99:  # 1% unter Durchschnitt -> Short
            return -1
        return 0

    def _calculate_quantity(self, current_price: float) -> float:
        """Berechnet die Order-Quantity basierend auf Position-Sizing."""
        position_value = self._session_config.start_balance * self._session_config.position_fraction
        quantity = position_value / current_price
        return round(quantity, 8)  # Auf 8 Dezimalstellen runden

    def _log_step_event(self, event_data: Dict[str, Any]) -> None:
        """Loggt ein Step-Event."""
        if self._run_logger is None:
            return

        try:
            run_event = LiveRunEvent(
                step=event_data.get("step", 0),
                ts_bar=event_data.get("ts_bar"),
                ts_event=event_data.get("ts_event"),
                price=event_data.get("price"),
                position_size=self._metrics.current_position,
                signal=event_data.get("signal", 0),
                signal_changed=event_data.get("signal_changed", False),
                orders_generated=event_data.get("orders_generated", 0),
                orders_filled=event_data.get("orders_filled", 0),
                orders_rejected=event_data.get("orders_rejected", 0),
                orders_blocked=0,
                risk_allowed=event_data.get("risk_allowed", True),
                risk_reasons="",
            )
            self._run_logger.log_event(run_event)
        except Exception as e:
            self._logger.warning(f"[TESTNET SESSION] Event-Logging fehlgeschlagen: {e}")

    def run_forever(self) -> None:
        """
        Startet den kontinuierlichen Session-Loop.

        Laeuft bis KeyboardInterrupt (Ctrl+C) oder shutdown() aufgerufen wird.
        """
        self._is_running = True
        self._shutdown_requested = False
        self._setup_signal_handlers()

        _emit_exec_event_safe(
            event_type="session_start",
            level="info",
            msg=f"testnet session start symbol={self._session_config.symbol}",
        )

        self._logger.info(
            f"[TESTNET SESSION] Starte Loop: "
            f"poll_interval={self._session_config.poll_interval_seconds}s"
        )

        try:
            while not self._shutdown_requested:
                try:
                    self.step_once()
                except Exception as e:
                    self._logger.error(f"[TESTNET SESSION] Fehler in step_once: {e}")

                time.sleep(self._session_config.poll_interval_seconds)

        except KeyboardInterrupt:
            self._logger.info("[TESTNET SESSION] KeyboardInterrupt empfangen")

        finally:
            self._is_running = False
            self._restore_signal_handlers()
            self._finalize()

    def run_for_duration(self, minutes: int) -> List[OrderExecutionResult]:
        """
        Fuehrt Session fuer eine bestimmte Dauer aus.

        Args:
            minutes: Laufzeit in Minuten

        Returns:
            Liste aller OrderExecutionResults
        """
        end_time = time.time() + (minutes * 60)
        all_results: List[OrderExecutionResult] = []

        _emit_exec_event_safe(
            event_type="session_start",
            level="info",
            msg=f"testnet session start symbol={self._session_config.symbol} duration={minutes}min",
        )

        self._logger.info(f"[TESTNET SESSION] Starte fuer {minutes} Minuten...")

        try:
            while time.time() < end_time and not self._shutdown_requested:
                results = self.step_once()
                if results:
                    all_results.extend(results)
                time.sleep(self._session_config.poll_interval_seconds)
        finally:
            self._finalize()

        return all_results

    def shutdown(self) -> None:
        """Signalisiert der Session zu stoppen."""
        self._logger.info("[TESTNET SESSION] Shutdown angefordert")
        self._shutdown_requested = True

    def _finalize(self) -> None:
        """Finalisiert die Session."""
        _emit_exec_event_safe(
            event_type="session_end",
            level="info",
            msg=f"testnet session end symbol={self._session_config.symbol}",
        )
        self._log_session_summary()

        if self._run_logger:
            try:
                self._run_logger.finalize()
                self._logger.info(
                    f"[TESTNET SESSION] Run-Logger finalisiert: run_id={self._run_logger.run_id}"
                )
            except Exception as e:
                self._logger.warning(
                    f"[TESTNET SESSION] Run-Logger-Finalisierung fehlgeschlagen: {e}"
                )

    def _log_session_summary(self) -> None:
        """Loggt eine Zusammenfassung der Session."""
        metrics = self._metrics.to_dict()
        executor_summary = self._executor.get_execution_summary()

        self._logger.info(
            f"[TESTNET SESSION] === Session-Zusammenfassung ===\n"
            f"  Steps: {metrics['steps']}\n"
            f"  Total Orders: {metrics['total_orders']}\n"
            f"  Filled: {metrics['filled_orders']}\n"
            f"  Rejected: {metrics['rejected_orders']}\n"
            f"  Risk-Blocked: {metrics['risk_blocked_orders']}\n"
            f"  Fill Rate: {metrics['fill_rate']:.1%}\n"
            f"  Current Position: {metrics['current_position']:.8f}\n"
            f"  Executor Mode: {executor_summary['mode']}"
        )

    def get_execution_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung der Session zurueck."""
        return {
            "session_metrics": self._metrics.to_dict(),
            "executor_summary": self._executor.get_execution_summary(),
            "config": {
                "symbol": self._session_config.symbol,
                "timeframe": self._session_config.timeframe,
                "poll_interval": self._session_config.poll_interval_seconds,
            },
        }


# =============================================================================
# Session Builder
# =============================================================================


def build_testnet_session(
    cfg: PeakConfig,
    strategy_name: str,
    symbol_override: Optional[str] = None,
    timeframe_override: Optional[str] = None,
    run_id: Optional[str] = None,
    enable_logging: bool = True,
    log_dir_override: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> TestnetSession:
    """
    Baut eine komplett konfigurierte TestnetSession.

    Args:
        cfg: PeakConfig
        strategy_name: Name der Strategie
        symbol_override: Optionales Symbol-Override
        timeframe_override: Optionales Timeframe-Override
        run_id: Optionale Run-ID
        enable_logging: Run-Logging aktivieren
        log_dir_override: Optionales Log-Verzeichnis-Override
        logger: Logger-Instanz

    Returns:
        TestnetSession-Instanz

    Raises:
        EnvironmentNotTestnetError: Bei nicht erlaubtem Environment
    """
    logger = logger or logging.getLogger(__name__)

    # 1. Configs laden
    env_config = get_environment_from_config(cfg)
    session_config = load_testnet_session_config(cfg)
    logging_cfg = load_shadow_paper_logging_config(cfg)

    # Overrides anwenden
    if symbol_override:
        session_config.symbol = symbol_override
    if timeframe_override:
        session_config.timeframe = timeframe_override

    # 2. Environment-Check
    logger.info(f"Environment-Modus: {env_config.environment.value}")

    if env_config.environment != TradingEnvironment.TESTNET:
        raise EnvironmentNotTestnetError(
            f"Environment '{env_config.environment.value}' nicht erlaubt fuer Testnet-Session. "
            f"Setze [environment] mode = 'testnet' in config.toml"
        )

    # 3. Exchange-Client erstellen
    logger.info("Initialisiere Kraken Testnet Client...")
    exchange_client = create_kraken_testnet_client_from_config(cfg)

    if not exchange_client.has_credentials:
        logger.warning(
            "WARNUNG: Keine API-Credentials gefunden! "
            "Setze KRAKEN_TESTNET_API_KEY und KRAKEN_TESTNET_API_SECRET"
        )

    # 4. Risk-Limits
    logger.info("Initialisiere Risk-Limits...")
    risk_limits = LiveRiskLimits.from_config(cfg, starting_cash=session_config.start_balance)

    # 5. Safety-Guard
    safety_guard = SafetyGuard(env_config=env_config)

    # 6. Executor erstellen
    logger.info(f"Initialisiere Testnet-Executor (testnet_dry_run={env_config.testnet_dry_run})...")
    executor = TestnetExchangeOrderExecutor(
        exchange_client=exchange_client,
        safety_guard=safety_guard,
        risk_limits=risk_limits,
        env_config=env_config,
    )

    # 7. Strategie erstellen
    logger.info(f"Lade Strategie: {strategy_name}")
    strategy = create_strategy(strategy_name, cfg)

    # 8. Run-Logger erstellen
    run_logger: Optional[LiveRunLogger] = None
    if enable_logging and logging_cfg.enabled:
        effective_run_id = run_id or generate_run_id(
            mode="testnet",
            strategy_name=strategy_name,
            symbol=session_config.symbol,
            timeframe=session_config.timeframe,
        )

        config_snapshot = {
            "testnet_session": {
                "symbol": session_config.symbol,
                "timeframe": session_config.timeframe,
                "start_balance": session_config.start_balance,
                "position_fraction": session_config.position_fraction,
            },
            "strategy": {"key": strategy_name},
            "executor_mode": executor.effective_mode,
        }

        metadata = LiveRunMetadata(
            run_id=effective_run_id,
            mode="testnet",
            strategy_name=strategy_name,
            symbol=session_config.symbol,
            timeframe=session_config.timeframe,
            config_snapshot=config_snapshot,
        )

        run_logger = LiveRunLogger(
            logging_cfg=logging_cfg,
            metadata=metadata,
            base_dir_override=log_dir_override,
        )
        run_logger.initialize()

        logger.info(f"Run-Logging aktiviert: run_id={effective_run_id}")
        logger.info(f"Run-Verzeichnis: {run_logger.run_dir}")

    # 9. Session erstellen
    session = TestnetSession(
        env_config=env_config,
        session_config=session_config,
        exchange_client=exchange_client,
        executor=executor,
        strategy=strategy,
        risk_limits=risk_limits,
        run_logger=run_logger,
    )

    return session


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> int:
    """
    Haupteinstiegspunkt fuer Testnet Session CLI.

    Returns:
        Exit-Code (0 = Success, 1 = Error)
    """
    parser = argparse.ArgumentParser(
        description="Run Peak_Trade Testnet Session with exchange API calls.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Standard-Start:
  python -m scripts.run_testnet_session

  # Mit anderer Strategie:
  python -m scripts.run_testnet_session --strategy rsi_strategy

  # Mit anderem Symbol:
  python -m scripts.run_testnet_session --symbol ETH/EUR

  # Fuer begrenzte Zeit (30 Minuten):
  python -m scripts.run_testnet_session --duration 30

Voraussetzungen:
  - KRAKEN_TESTNET_API_KEY und KRAKEN_TESTNET_API_SECRET gesetzt
  - config.toml: [environment] mode = "testnet"

WICHTIG: Nur Testnet-Trading! Keine echten Live-Trades!
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (default: config/config.toml)",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="ma_crossover",
        help="Strategie-Name (default: ma_crossover)",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Trading-Symbol override (z.B. ETH/EUR)",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default=None,
        help="Timeframe override (z.B. 5m, 1h)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Laufzeit in Minuten (default: unbegrenzt)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log-Level (default: INFO)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Config laden und validieren, keine Session starten",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Spezifische Run-ID fuer Logging",
    )
    parser.add_argument(
        "--no-logging",
        action="store_true",
        help="Run-Logging deaktivieren",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Alternatives Verzeichnis fuer Run-Logs",
    )

    args = parser.parse_args()

    # Logging setup
    logger = setup_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("Peak_Trade Testnet Session (Phase 35)")
    logger.info("=" * 60)
    logger.info("WICHTIG: Nur Testnet-Trading! Keine echten Live-Trades!")
    logger.info("=" * 60)

    # API-Key-Check
    api_key = os.environ.get("KRAKEN_TESTNET_API_KEY")
    api_secret = os.environ.get("KRAKEN_TESTNET_API_SECRET")
    if not api_key or not api_secret:
        logger.warning(
            "WARNUNG: KRAKEN_TESTNET_API_KEY und/oder KRAKEN_TESTNET_API_SECRET nicht gesetzt!"
        )

    try:
        # Config laden
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Config-Datei nicht gefunden: {config_path}")
            return 1

        logger.info(f"Lade Config: {config_path}")
        cfg = load_config(config_path)

        # Session bauen
        session = build_testnet_session(
            cfg=cfg,
            strategy_name=args.strategy,
            symbol_override=args.symbol,
            timeframe_override=args.timeframe,
            run_id=args.run_id,
            enable_logging=not args.no_logging,
            log_dir_override=args.log_dir,
            logger=logger,
        )

        if args.dry_run:
            logger.info("Dry-Run: Session erfolgreich konfiguriert, keine Ausfuehrung.")
            return 0

        # Warmup
        logger.info("Starte Warmup...")
        session.warmup()

        # Session starten
        if args.duration:
            logger.info(f"Starte Session fuer {args.duration} Minuten...")
            results = session.run_for_duration(args.duration)
            logger.info(f"Session beendet. {len(results)} Orders ausgefuehrt.")
        else:
            logger.info("Starte Session (Ctrl+C zum Beenden)...")
            session.run_forever()

        # Zusammenfassung
        summary = session.get_execution_summary()
        logger.info(f"Session-Summary: {summary}")

        return 0

    except EnvironmentNotTestnetError as e:
        logger.error(f"Environment-Fehler: {e}")
        logger.error("Loesung: Setze [environment] mode = 'testnet' in config/config.toml")
        return 1

    except ExchangeAPIError as e:
        logger.error(f"Exchange-API-Fehler: {e}")
        return 1

    except ValueError as e:
        logger.error(f"Konfigurations-Fehler: {e}")
        return 1

    except KeyboardInterrupt:
        logger.info("Session durch Benutzer beendet (Ctrl+C)")
        return 0

    except Exception as e:
        logger.exception(f"Unerwarteter Fehler: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
