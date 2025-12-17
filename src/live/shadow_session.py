# src/live/shadow_session.py
"""
Peak_Trade: Shadow/Paper Live Session (Phase 31)
================================================

Session-Klasse für Shadow-/Paper-Trading mit echten Exchange-Marktdaten.
Führt Live-Datenquelle, Strategie, ExecutionPipeline, OrderExecutor
und RiskLimits in einem kontinuierlichen Loop zusammen.

Features:
- Live-Marktdaten von Kraken (oder anderer Quelle)
- Strategie-Signalgenerierung auf Live-Daten
- Paper-Order-Execution (keine echten Orders)
- Live-Risk-Limit-Prüfung vor jeder Order
- Umfangreiches Logging und Metriken

WICHTIG: Diese Session sendet NIEMALS echte Orders!
         Nur Environment-Modi PAPER und SHADOW sind erlaubt.

Example:
    >>> from src.live.shadow_session import ShadowPaperSession
    >>> from src.data.kraken_live import KrakenLiveCandleSource
    >>>
    >>> source = KrakenLiveCandleSource(symbol="BTC/EUR", timeframe="1m")
    >>> session = ShadowPaperSession(
    ...     data_source=source,
    ...     strategy=my_strategy,
    ...     # ... weitere Parameter
    ... )
    >>> session.warmup()
    >>> session.run_forever()  # Ctrl+C zum Stoppen
"""
from __future__ import annotations

import logging
import signal
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ..core.environment import (
    EnvironmentConfig,
    TradingEnvironment,
    get_environment_from_config,
)
from ..data.kraken_live import (
    CandleSource,
    LiveCandle,
    LiveExchangeConfig,
    ShadowPaperConfig,
)
from ..execution.pipeline import ExecutionPipeline, SignalEvent
from ..live.orders import LiveOrderRequest
from ..live.risk_limits import LiveRiskLimits
from ..live.run_logging import (
    LiveRunEvent,
    LiveRunLogger,
    load_shadow_paper_logging_config,
)
from ..live.safety import SafetyGuard
from ..orders.base import OrderExecutionResult, OrderRequest
from ..orders.shadow import ShadowMarketContext

if TYPE_CHECKING:
    from ..core.peak_config import PeakConfig
    from ..strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


# =============================================================================
# Session Metrics
# =============================================================================


@dataclass
class ShadowPaperSessionMetrics:
    """
    Metriken für eine Shadow-/Paper-Session.

    Attributes:
        steps: Anzahl der ausgeführten Schritte
        start_time: Session-Startzeit
        last_bar_time: Zeitstempel der letzten verarbeiteten Bar
        last_risk_check: Zeitstempel des letzten Risk-Checks
        total_orders: Anzahl aller generierten Orders
        filled_orders: Anzahl erfolgreich ausgeführter Orders
        rejected_orders: Anzahl abgelehnter Orders
        blocked_orders_count: Anzahl durch Risk-Limits blockierter Orders
        total_pnl: Kumulierter PnL (nur für Tracking)
        current_position: Aktuelle Position
    """
    steps: int = 0
    start_time: datetime | None = None
    last_bar_time: datetime | None = None
    last_risk_check: datetime | None = None
    total_orders: int = 0
    filled_orders: int = 0
    rejected_orders: int = 0
    blocked_orders_count: int = 0
    total_pnl: float = 0.0
    current_position: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert Metriken zu Dictionary."""
        return {
            "steps": self.steps,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_bar_time": self.last_bar_time.isoformat() if self.last_bar_time else None,
            "last_risk_check": self.last_risk_check.isoformat() if self.last_risk_check else None,
            "total_orders": self.total_orders,
            "filled_orders": self.filled_orders,
            "rejected_orders": self.rejected_orders,
            "blocked_orders_count": self.blocked_orders_count,
            "fill_rate": self.filled_orders / self.total_orders if self.total_orders > 0 else 0.0,
            "total_pnl": self.total_pnl,
            "current_position": self.current_position,
        }


# =============================================================================
# Allowed Environment Modes
# =============================================================================

ALLOWED_ENVIRONMENT_MODES = {
    TradingEnvironment.PAPER,
    # TradingEnvironment.SHADOW,  # Kann später hinzugefügt werden
}


class EnvironmentNotAllowedError(Exception):
    """Wird geworfen wenn der Environment-Modus nicht erlaubt ist."""
    pass


# =============================================================================
# Shadow Paper Session
# =============================================================================


class ShadowPaperSession:
    """
    Shadow-/Paper-Live-Session mit echten Exchange-Marktdaten.

    Diese Klasse orchestriert den kompletten Shadow-/Paper-Trading-Loop:
    1. Polling von Live-Marktdaten
    2. Strategie-Signalgenerierung
    3. Order-Erstellung über ExecutionPipeline
    4. Risk-Check via LiveRiskLimits
    5. Paper-Order-Execution (keine echten Orders)
    6. Logging und Metriken

    Safety-Features:
    - Nur PAPER/SHADOW Environment-Modi erlaubt
    - Live-Risk-Limits werden vor jeder Order geprüft
    - SafetyGuard blockt echte Order-Versuche
    - Graceful Shutdown bei SIGINT/SIGTERM

    WICHTIG: Diese Session sendet NIEMALS echte Orders!

    Example:
        >>> session = ShadowPaperSession(
        ...     env_config=env_config,
        ...     shadow_cfg=shadow_cfg,
        ...     exchange_cfg=exchange_cfg,
        ...     data_source=kraken_source,
        ...     strategy=ma_strategy,
        ...     pipeline=pipeline,
        ...     risk_limits=risk_limits,
        ... )
        >>> session.warmup()
        >>> session.run_forever()
    """

    def __init__(
        self,
        env_config: EnvironmentConfig,
        shadow_cfg: ShadowPaperConfig,
        exchange_cfg: LiveExchangeConfig,
        data_source: CandleSource,
        strategy: BaseStrategy,
        pipeline: ExecutionPipeline,
        risk_limits: LiveRiskLimits,
        on_step_callback: Callable[[int, LiveCandle | None], None] | None = None,
        run_logger: LiveRunLogger | None = None,
    ) -> None:
        """
        Initialisiert die Shadow-/Paper-Session.

        Args:
            env_config: Environment-Konfiguration
            shadow_cfg: Shadow/Paper Session Config
            exchange_cfg: Exchange Config
            data_source: Live-Datenquelle (z.B. KrakenLiveCandleSource)
            strategy: Trading-Strategie
            pipeline: Execution-Pipeline
            risk_limits: Live-Risk-Limits
            on_step_callback: Optionaler Callback nach jedem Step
            run_logger: Optionaler LiveRunLogger für Logging (Phase 32)

        Raises:
            EnvironmentNotAllowedError: Wenn Environment-Modus nicht erlaubt
        """
        # Safety-Check: Nur erlaubte Environment-Modi
        if env_config.environment not in ALLOWED_ENVIRONMENT_MODES:
            raise EnvironmentNotAllowedError(
                f"Environment-Modus '{env_config.environment.value}' ist nicht erlaubt "
                f"für Shadow/Paper-Sessions. Erlaubt: {[m.value for m in ALLOWED_ENVIRONMENT_MODES]}"
            )

        self._env_config = env_config
        self._shadow_cfg = shadow_cfg
        self._exchange_cfg = exchange_cfg
        self._data_source = data_source
        self._strategy = strategy
        self._pipeline = pipeline
        self._risk_limits = risk_limits
        self._on_step_callback = on_step_callback
        self._run_logger = run_logger

        # Safety Guard
        self._safety_guard = SafetyGuard(env_config=env_config)

        # Metriken
        self._metrics = ShadowPaperSessionMetrics()

        # Session-State
        self._is_running = False
        self._is_warmup_done = False
        self._last_signal: int = 0
        self._shutdown_requested = False

        # Signal Handler für graceful shutdown
        self._original_sigint_handler = None
        self._original_sigterm_handler = None

        logger.info(
            f"[SHADOW SESSION] Initialisiert: "
            f"mode={shadow_cfg.mode}, "
            f"symbol={shadow_cfg.symbol}, "
            f"timeframe={shadow_cfg.timeframe}, "
            f"env={env_config.environment.value}"
        )

    @property
    def metrics(self) -> ShadowPaperSessionMetrics:
        """Zugriff auf Session-Metriken."""
        return self._metrics

    @property
    def is_running(self) -> bool:
        """True wenn Session läuft."""
        return self._is_running

    @property
    def is_warmup_done(self) -> bool:
        """True wenn Warmup abgeschlossen ist."""
        return self._is_warmup_done

    @property
    def run_logger(self) -> LiveRunLogger | None:
        """Zugriff auf den Run-Logger (falls gesetzt)."""
        return self._run_logger

    def _setup_signal_handlers(self) -> None:
        """Installiert Signal-Handler für graceful shutdown."""
        def shutdown_handler(signum: int, frame: Any) -> None:
            logger.info(f"[SHADOW SESSION] Shutdown-Signal empfangen (signal={signum})")
            self._shutdown_requested = True

        self._original_sigint_handler = signal.signal(signal.SIGINT, shutdown_handler)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, shutdown_handler)

    def _restore_signal_handlers(self) -> None:
        """Stellt ursprüngliche Signal-Handler wieder her."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)

    def warmup(self) -> None:
        """
        Führt Warmup durch: Holt initiale Candles für Strategie.

        Ruft die Datenquelle auf und lädt historische Candles,
        damit die Strategie genug Daten für Indikator-Berechnung hat.

        Raises:
            RuntimeError: Bei Warmup-Fehlern
        """
        logger.info(
            f"[SHADOW SESSION] Starte Warmup: {self._shadow_cfg.warmup_candles} Candles..."
        )

        try:
            candles = self._data_source.warmup()

            if not candles:
                logger.warning("[SHADOW SESSION] Warmup: Keine Candles erhalten")
                return

            logger.info(
                f"[SHADOW SESSION] Warmup abgeschlossen: {len(candles)} Candles geladen"
            )

            self._is_warmup_done = True
            self._metrics.start_time = datetime.now(UTC)

            if candles:
                self._metrics.last_bar_time = candles[-1].timestamp

        except Exception as e:
            logger.error(f"[SHADOW SESSION] Warmup fehlgeschlagen: {e}")
            raise RuntimeError(f"Warmup fehlgeschlagen: {e}") from e

    def step_once(self) -> list[OrderExecutionResult] | None:
        """
        Führt einen einzelnen Session-Schritt durch.

        1. Pollt neue Candle von Datenquelle
        2. Generiert Strategie-Signal
        3. Erstellt Orders bei Signal-Änderung
        4. Prüft Risk-Limits
        5. Führt Orders aus (Paper)
        6. Loggt Event (wenn run_logger gesetzt)

        Returns:
            Liste von OrderExecutionResults oder None wenn keine Orders
        """
        self._metrics.steps += 1
        step_num = self._metrics.steps
        ts_event = datetime.now(UTC)

        # Event-Daten sammeln (für Logging)
        event_data: dict[str, Any] = {
            "step": step_num,
            "ts_event": ts_event,
            "signal": 0,
            "signal_changed": False,
            "orders_generated": 0,
            "orders_filled": 0,
            "orders_rejected": 0,
            "orders_blocked": 0,
            "risk_allowed": True,
            "risk_reasons": "",
        }

        # 1. Neue Candle holen
        candle = self._data_source.poll_latest()

        # Callback aufrufen
        if self._on_step_callback:
            self._on_step_callback(step_num, candle)

        if candle is None:
            logger.debug(f"[SHADOW SESSION] Step {step_num}: Keine neue Candle")
            # Kein Event-Logging bei fehlender Candle
            return None

        self._metrics.last_bar_time = candle.timestamp

        # Event-Daten mit Candle-Infos ergänzen
        event_data.update({
            "ts_bar": candle.timestamp,
            "price": candle.close,
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "volume": candle.volume,
            "position_size": self._metrics.current_position,
        })

        # 2. Preis im Pipeline-Executor aktualisieren
        if hasattr(self._pipeline.executor, "context"):
            self._pipeline.executor.context.set_price(
                self._shadow_cfg.symbol, candle.close
            )

        # 3. Signal von Strategie generieren
        buffer_df = self._data_source.get_buffer()

        if len(buffer_df) < 50:  # Minimum für Strategie
            logger.debug(
                f"[SHADOW SESSION] Step {step_num}: "
                f"Zu wenig Daten für Signal ({len(buffer_df)} bars)"
            )
            self._log_step_event(event_data)
            return None

        try:
            signals = self._strategy.generate_signals(buffer_df)
            current_signal = int(signals.iloc[-1]) if len(signals) > 0 else 0
        except Exception as e:
            logger.warning(f"[SHADOW SESSION] Signal-Fehler: {e}")
            self._log_step_event(event_data)
            return None

        event_data["signal"] = current_signal

        # 4. Bei Signal-Änderung: Order erstellen
        if current_signal == self._last_signal:
            logger.debug(
                f"[SHADOW SESSION] Step {step_num}: "
                f"Signal unverändert ({current_signal})"
            )
            self._log_step_event(event_data)
            return None

        event_data["signal_changed"] = True

        logger.info(
            f"[SHADOW SESSION] Signal-Änderung: {self._last_signal} -> {current_signal} "
            f"@ {candle.timestamp}, close={candle.close:.2f}"
        )

        # Position-Size berechnen
        position_size = self._shadow_cfg.position_fraction

        # Signal-Event erstellen
        sig_event = SignalEvent(
            timestamp=candle.timestamp,
            symbol=self._shadow_cfg.symbol,
            signal=current_signal,
            price=candle.close,
            previous_signal=self._last_signal,
            metadata={"strategy": self._strategy.key, "mode": self._shadow_cfg.mode},
        )

        # Orders über Pipeline generieren
        orders = self._pipeline.signal_to_orders(
            event=sig_event,
            position_size=position_size,
            current_position=self._metrics.current_position,
        )

        if not orders:
            self._last_signal = current_signal
            self._log_step_event(event_data)
            return None

        event_data["orders_generated"] = len(orders)

        # 5. Risk-Check
        self._metrics.last_risk_check = datetime.now(UTC)

        # Konvertiere OrderRequests zu LiveOrderRequests für Risk-Check
        live_orders = self._convert_to_live_orders(orders, candle.close)

        risk_result = self._risk_limits.check_orders(live_orders)

        if not risk_result.allowed:
            self._metrics.blocked_orders_count += len(orders)
            event_data["orders_blocked"] = len(orders)
            event_data["risk_allowed"] = False
            event_data["risk_reasons"] = "; ".join(risk_result.reasons)
            logger.warning(
                f"[SHADOW SESSION] Orders blockiert durch Risk-Limits: "
                f"{risk_result.reasons}"
            )
            # Signal trotzdem aktualisieren, damit wir nicht in Loop geraten
            self._last_signal = current_signal
            self._log_step_event(event_data)
            return None

        # 6. Orders ausführen (Paper/Shadow)
        logger.info(f"[SHADOW SESSION] Führe {len(orders)} Order(s) aus...")

        results = self._pipeline.execute_orders(orders)

        # Metriken aktualisieren
        filled_count = 0
        rejected_count = 0
        for result in results:
            self._metrics.total_orders += 1
            if result.is_filled:
                self._metrics.filled_orders += 1
                filled_count += 1
                if result.fill:
                    # Position aktualisieren
                    if result.fill.side == "buy":
                        self._metrics.current_position += result.fill.quantity
                    else:
                        self._metrics.current_position -= result.fill.quantity
            elif result.is_rejected:
                self._metrics.rejected_orders += 1
                rejected_count += 1

        event_data["orders_filled"] = filled_count
        event_data["orders_rejected"] = rejected_count
        event_data["position_size"] = self._metrics.current_position

        self._last_signal = current_signal

        # 7. Event loggen
        self._log_step_event(event_data)

        return results

    def _log_step_event(self, event_data: dict[str, Any]) -> None:
        """
        Loggt ein Step-Event über den run_logger (falls gesetzt).

        Args:
            event_data: Dictionary mit Event-Daten
        """
        if self._run_logger is None:
            return

        try:
            run_event = LiveRunEvent(
                step=event_data.get("step", 0),
                ts_bar=event_data.get("ts_bar"),
                ts_event=event_data.get("ts_event"),
                price=event_data.get("price"),
                open=event_data.get("open"),
                high=event_data.get("high"),
                low=event_data.get("low"),
                close=event_data.get("close"),
                volume=event_data.get("volume"),
                position_size=event_data.get("position_size", 0.0),
                signal=event_data.get("signal", 0),
                signal_changed=event_data.get("signal_changed", False),
                orders_generated=event_data.get("orders_generated", 0),
                orders_filled=event_data.get("orders_filled", 0),
                orders_rejected=event_data.get("orders_rejected", 0),
                orders_blocked=event_data.get("orders_blocked", 0),
                risk_allowed=event_data.get("risk_allowed", True),
                risk_reasons=event_data.get("risk_reasons", ""),
            )
            self._run_logger.log_event(run_event)
        except Exception as e:
            logger.warning(f"[SHADOW SESSION] Event-Logging fehlgeschlagen: {e}")

    def _convert_to_live_orders(
        self, orders: list[OrderRequest], current_price: float
    ) -> list[LiveOrderRequest]:
        """
        Konvertiert OrderRequests zu LiveOrderRequests für Risk-Check.

        Args:
            orders: Liste von OrderRequests
            current_price: Aktueller Marktpreis

        Returns:
            Liste von LiveOrderRequests
        """
        live_orders: list[LiveOrderRequest] = []

        for i, order in enumerate(orders):
            notional = order.quantity * current_price
            side = "BUY" if order.side == "buy" else "SELL"

            live_order = LiveOrderRequest(
                client_order_id=order.client_id or f"shadow_{i}_{time.time_ns()}",
                symbol=order.symbol,
                side=side,  # type: ignore
                order_type="MARKET",
                quantity=order.quantity,
                notional=notional,
                strategy_key=self._strategy.key,
                extra={"current_price": current_price},
            )
            live_orders.append(live_order)

        return live_orders

    def run_forever(self) -> None:
        """
        Startet den kontinuierlichen Session-Loop.

        Läuft bis KeyboardInterrupt (Ctrl+C) oder shutdown() aufgerufen wird.
        Führt in jedem Durchlauf step_once() aus und wartet dann
        für das konfigurierte Poll-Intervall.

        Raises:
            RuntimeError: Wenn Warmup nicht durchgeführt wurde
        """
        if not self._is_warmup_done:
            raise RuntimeError(
                "Warmup muss vor run_forever() aufgerufen werden. "
                "Verwende session.warmup() zuerst."
            )

        self._is_running = True
        self._shutdown_requested = False
        self._setup_signal_handlers()

        logger.info(
            f"[SHADOW SESSION] Starte Loop: "
            f"poll_interval={self._shadow_cfg.poll_interval_seconds}s"
        )

        try:
            while not self._shutdown_requested:
                try:
                    self.step_once()
                except Exception as e:
                    logger.error(f"[SHADOW SESSION] Fehler in step_once: {e}")
                    # Weiterlaufen, nicht abbrechen

                # Warten bis zum nächsten Poll
                time.sleep(self._shadow_cfg.poll_interval_seconds)

        except KeyboardInterrupt:
            logger.info("[SHADOW SESSION] KeyboardInterrupt empfangen")

        finally:
            self._is_running = False
            self._restore_signal_handlers()
            self._finalize_run_logger()
            self._log_session_summary()

    def run_n_steps(self, n: int, sleep_between: bool = False) -> list[OrderExecutionResult]:
        """
        Führt n Schritte aus und stoppt dann.

        Nützlich für Tests und kontrollierte Ausführung.

        Args:
            n: Anzahl der Schritte
            sleep_between: Ob zwischen Steps gewartet werden soll

        Returns:
            Liste aller OrderExecutionResults
        """
        if not self._is_warmup_done:
            raise RuntimeError("Warmup muss vor run_n_steps() aufgerufen werden.")

        all_results: list[OrderExecutionResult] = []

        try:
            for i in range(n):
                results = self.step_once()
                if results:
                    all_results.extend(results)

                if sleep_between and i < n - 1:
                    time.sleep(self._shadow_cfg.poll_interval_seconds)
        finally:
            self._finalize_run_logger()

        return all_results

    def run_for_duration(self, minutes: int) -> list[OrderExecutionResult]:
        """
        Führt Session für eine bestimmte Dauer aus.

        Args:
            minutes: Laufzeit in Minuten

        Returns:
            Liste aller OrderExecutionResults
        """
        if not self._is_warmup_done:
            raise RuntimeError("Warmup muss vor run_for_duration() aufgerufen werden.")

        end_time = time.time() + (minutes * 60)
        all_results: list[OrderExecutionResult] = []

        logger.info(f"[SHADOW SESSION] Starte für {minutes} Minuten...")

        try:
            while time.time() < end_time and not self._shutdown_requested:
                results = self.step_once()
                if results:
                    all_results.extend(results)
                time.sleep(self._shadow_cfg.poll_interval_seconds)
        finally:
            self._finalize_run_logger()
            self._log_session_summary()

        return all_results

    def shutdown(self) -> None:
        """Signalisiert der Session zu stoppen."""
        logger.info("[SHADOW SESSION] Shutdown angefordert")
        self._shutdown_requested = True

    def _log_session_summary(self) -> None:
        """Loggt eine Zusammenfassung der Session."""
        metrics = self._metrics.to_dict()
        logger.info(
            f"[SHADOW SESSION] === Session-Zusammenfassung ===\n"
            f"  Steps: {metrics['steps']}\n"
            f"  Total Orders: {metrics['total_orders']}\n"
            f"  Filled: {metrics['filled_orders']}\n"
            f"  Rejected: {metrics['rejected_orders']}\n"
            f"  Blocked (Risk): {metrics['blocked_orders_count']}\n"
            f"  Fill Rate: {metrics['fill_rate']:.1%}\n"
            f"  Current Position: {metrics['current_position']:.6f}"
        )

    def _finalize_run_logger(self) -> None:
        """Finalisiert den Run-Logger (falls gesetzt)."""
        if self._run_logger is not None:
            try:
                self._run_logger.finalize()
                logger.info(
                    f"[SHADOW SESSION] Run-Logger finalisiert: "
                    f"run_id={self._run_logger.run_id}, "
                    f"events={self._run_logger.total_events_logged}"
                )
            except Exception as e:
                logger.warning(f"[SHADOW SESSION] Run-Logger-Finalisierung fehlgeschlagen: {e}")

    def get_execution_summary(self) -> dict[str, Any]:
        """
        Gibt eine Zusammenfassung der Session zurück.

        Returns:
            Dict mit Session-Metriken und Pipeline-Summary
        """
        pipeline_summary = self._pipeline.get_execution_summary()
        return {
            "session_metrics": self._metrics.to_dict(),
            "pipeline_summary": pipeline_summary,
            "config": {
                "mode": self._shadow_cfg.mode,
                "symbol": self._shadow_cfg.symbol,
                "timeframe": self._shadow_cfg.timeframe,
                "poll_interval": self._shadow_cfg.poll_interval_seconds,
            },
        }


# =============================================================================
# Factory Functions
# =============================================================================


def create_shadow_paper_session(
    cfg: PeakConfig,
    strategy: BaseStrategy,
    data_source: CandleSource | None = None,
    run_id: str | None = None,
    enable_logging: bool = True,
    log_dir_override: str | None = None,
) -> ShadowPaperSession:
    """
    Factory-Funktion für ShadowPaperSession aus PeakConfig.

    Erstellt alle benötigten Komponenten (Pipeline, Executor, RiskLimits, RunLogger)
    basierend auf der Konfiguration.

    Args:
        cfg: PeakConfig-Instanz
        strategy: Trading-Strategie
        data_source: Optionale Datenquelle (sonst KrakenLiveCandleSource)
        run_id: Optionale Run-ID (sonst automatisch generiert)
        enable_logging: Run-Logging aktivieren (default: True)
        log_dir_override: Optionales Override für Log-Verzeichnis

    Returns:
        Konfigurierte ShadowPaperSession

    Raises:
        EnvironmentNotAllowedError: Bei nicht erlaubtem Environment-Modus
    """
    from ..data.kraken_live import (
        create_kraken_source_from_config,
        load_live_exchange_config,
        load_shadow_paper_config,
    )
    from ..live.run_logging import (
        create_run_logger_from_config,
    )

    # Configs laden
    shadow_cfg = load_shadow_paper_config(cfg)
    exchange_cfg = load_live_exchange_config(cfg)
    env_config = get_environment_from_config(cfg)
    logging_cfg = load_shadow_paper_logging_config(cfg)

    # Datenquelle erstellen falls nicht übergeben
    if data_source is None:
        data_source = create_kraken_source_from_config(shadow_cfg, exchange_cfg)

    # Shadow-Executor erstellen
    market_context = ShadowMarketContext(
        fee_rate=shadow_cfg.fee_rate,
        slippage_bps=shadow_cfg.slippage_bps,
    )

    # Pipeline mit Shadow-Executor
    pipeline = ExecutionPipeline.for_shadow(
        market_context=market_context,
        fee_rate=shadow_cfg.fee_rate,
        slippage_bps=shadow_cfg.slippage_bps,
    )

    # Risk-Limits
    risk_limits = LiveRiskLimits.from_config(
        cfg, starting_cash=shadow_cfg.start_balance
    )

    # Run-Logger erstellen (wenn aktiviert)
    run_logger: LiveRunLogger | None = None
    if enable_logging and logging_cfg.enabled:
        # Config-Snapshot für Metadaten
        config_snapshot = {
            "shadow_paper": {
                "mode": shadow_cfg.mode,
                "symbol": shadow_cfg.symbol,
                "timeframe": shadow_cfg.timeframe,
                "start_balance": shadow_cfg.start_balance,
                "position_fraction": shadow_cfg.position_fraction,
                "fee_rate": shadow_cfg.fee_rate,
                "slippage_bps": shadow_cfg.slippage_bps,
            },
            "strategy": {
                "key": strategy.key,
            },
        }

        run_logger = create_run_logger_from_config(
            cfg=cfg,
            mode=shadow_cfg.mode,
            strategy_name=strategy.key,
            symbol=shadow_cfg.symbol,
            timeframe=shadow_cfg.timeframe,
            config_snapshot=config_snapshot,
            run_id=run_id,
            base_dir_override=log_dir_override,
        )

        # Logger initialisieren
        run_logger.initialize()

    return ShadowPaperSession(
        env_config=env_config,
        shadow_cfg=shadow_cfg,
        exchange_cfg=exchange_cfg,
        data_source=data_source,
        strategy=strategy,
        pipeline=pipeline,
        risk_limits=risk_limits,
        run_logger=run_logger,
    )
