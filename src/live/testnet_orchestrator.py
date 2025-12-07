# src/live/testnet_orchestrator.py
"""
Peak_Trade: Testnet-Orchestrator v1 (Phase 64)
==============================================

Orchestrator für Shadow- & Testnet-Runs mit Lifecycle-Management.

Features:
- Start/Stop von Shadow- und Testnet-Runs
- Run-Status-Abfrage
- Event-Tailing aus Run-Logging
- Safety-Checks & Readiness-Validierung
- Integration mit LiveRunLogger, LiveRiskLimits, ShadowPaperSession

WICHTIG: Dieser Orchestrator sendet NIEMALS echte Orders!
         Nur Shadow- und Testnet-Modi sind erlaubt.
"""
from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.peak_config import PeakConfig
    from ..strategies.base import BaseStrategy
    from .shadow_session import ShadowPaperSession
    from .run_logging import LiveRunLogger, LiveRunEvent

logger = logging.getLogger(__name__)


# =============================================================================
# Run State
# =============================================================================


class RunState(str, Enum):
    """Zustand eines Runs."""
    PENDING = "pending"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


# =============================================================================
# Run Info
# =============================================================================


@dataclass
class RunInfo:
    """Informationen über einen aktiven Run."""
    run_id: str
    mode: str  # "shadow" oder "testnet"
    strategy_name: str
    symbol: str
    timeframe: str
    state: RunState
    started_at: datetime
    stopped_at: Optional[datetime] = None
    last_event_time: Optional[datetime] = None
    last_error: Optional[str] = None
    notes: str = ""
    session: Optional[Any] = None  # ShadowPaperSession oder Testnet-Session
    run_logger: Optional["LiveRunLogger"] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "state": self.state.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "last_event_time": self.last_event_time.isoformat() if self.last_event_time else None,
            "last_error": self.last_error,
            "notes": self.notes,
        }


# =============================================================================
# Orchestrator Exceptions
# =============================================================================


class OrchestratorError(Exception):
    """Basis-Exception für Orchestrator-Fehler."""
    pass


class ReadinessCheckFailedError(OrchestratorError):
    """Readiness-Check ist fehlgeschlagen."""
    pass


class RunNotFoundError(OrchestratorError):
    """Run-ID nicht gefunden."""
    pass


class InvalidModeError(OrchestratorError):
    """Ungültiger Mode (z.B. 'live' nicht erlaubt)."""
    pass


# =============================================================================
# Testnet Orchestrator
# =============================================================================


class TestnetOrchestrator:
    """
    Orchestrator für Shadow- & Testnet-Runs.

    Verwaltet den Lifecycle von Shadow- und Testnet-Runs:
    - Start/Stop von Runs
    - Status-Abfrage
    - Event-Tailing
    - Safety-Checks

    Example:
        >>> orchestrator = TestnetOrchestrator(cfg)
        >>> run_id = orchestrator.start_shadow_run(
        ...     strategy_name="ma_crossover",
        ...     symbol="BTC/EUR",
        ...     timeframe="1m",
        ... )
        >>> status = orchestrator.get_status(run_id)
        >>> orchestrator.stop_run(run_id)
    """

    def __init__(self, config: "PeakConfig") -> None:
        """
        Initialisiert den Orchestrator.

        Args:
            config: PeakConfig-Instanz
        """
        self._config = config
        self._runs: Dict[str, RunInfo] = {}
        self._lock = threading.RLock()

        logger.info("[ORCHESTRATOR] Initialisiert")

    def _ensure_readiness(self, mode: str) -> None:
        """
        Prüft Readiness für einen Run.

        Args:
            mode: "shadow" oder "testnet"

        Raises:
            ReadinessCheckFailedError: Wenn Readiness-Checks fehlschlagen
            InvalidModeError: Wenn Mode ungültig ist
        """
        from ..core.environment import get_environment_from_config, TradingEnvironment
        from .safety import SafetyGuard

        # Mode-Validierung
        if mode not in ("shadow", "testnet"):
            raise InvalidModeError(
                f"Ungültiger Mode: '{mode}'. Erlaubt: 'shadow', 'testnet'"
            )

        # Config-Validierung
        if self._config is None:
            raise ReadinessCheckFailedError("Config ist None")

        # Environment-Validierung
        env_config = get_environment_from_config(self._config)
        
        if mode == "shadow":
            # Shadow erfordert PAPER-Mode
            if env_config.environment != TradingEnvironment.PAPER:
                raise ReadinessCheckFailedError(
                    f"Shadow-Runs erfordern environment.mode='paper'. "
                    f"Aktuell: {env_config.environment.value}"
                )
        elif mode == "testnet":
            # Testnet erfordert TESTNET-Mode
            if env_config.environment != TradingEnvironment.TESTNET:
                raise ReadinessCheckFailedError(
                    f"Testnet-Runs erfordern environment.mode='testnet'. "
                    f"Aktuell: {env_config.environment.value}"
                )

        # Safety-Guard prüfen
        safety_guard = SafetyGuard(env_config=env_config)
        
        # Sicherstellen, dass kein Live-Mode aktiv ist
        if env_config.is_live:
            raise ReadinessCheckFailedError(
                "Live-Mode ist nicht erlaubt für Orchestrator-Runs. "
                "Nur 'shadow' und 'testnet' sind erlaubt."
            )

        # Risk-Limits prüfen (optional, aber empfohlen)
        try:
            from .risk_limits import LiveRiskLimits
            risk_limits = LiveRiskLimits.from_config(self._config)
            if not risk_limits.config.enabled:
                logger.warning("[ORCHESTRATOR] Live-Risk-Limits sind deaktiviert")
        except Exception as e:
            logger.warning(f"[ORCHESTRATOR] Risk-Limits-Check fehlgeschlagen: {e}")

        logger.info(f"[ORCHESTRATOR] Readiness-Check bestanden für Mode: {mode}")

    def _build_shadow_session(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        run_id: str,
        run_logger: Optional["LiveRunLogger"] = None,
    ) -> "ShadowPaperSession":
        """
        Baut eine ShadowPaperSession auf.

        Args:
            strategy_name: Name der Strategie
            symbol: Trading-Symbol
            timeframe: Timeframe
            run_id: Run-ID
            run_logger: Optionaler Run-Logger

        Returns:
            Konfigurierte ShadowPaperSession
        """
        from ..core.environment import get_environment_from_config
        from ..data.kraken_live import (
            ShadowPaperConfig,
            LiveExchangeConfig,
            create_kraken_source_from_config,
        )
        from ..strategies.registry import create_strategy_from_config
        from ..execution.pipeline import ExecutionPipeline
        from .risk_limits import LiveRiskLimits
        from .shadow_session import ShadowPaperSession

        # Environment-Config
        env_config = get_environment_from_config(self._config)

        # Shadow-Config
        shadow_cfg = ShadowPaperConfig(
            mode="shadow",
            symbol=symbol,
            timeframe=timeframe,
            position_fraction=0.1,  # Default, kann später konfigurierbar sein
            warmup_candles=200,
        )

        # Exchange-Config (keine symbol/timeframe Parameter - diese sind in shadow_cfg)
        exchange_cfg = LiveExchangeConfig()

        # Data-Source
        data_source = create_kraken_source_from_config(shadow_cfg, exchange_cfg)

        # Strategie
        strategy = create_strategy_from_config(strategy_name, self._config)

        # Execution-Pipeline mit Shadow-Executor
        pipeline = ExecutionPipeline.for_shadow(
            fee_rate=shadow_cfg.fee_rate,
            slippage_bps=shadow_cfg.slippage_bps,
        )

        # Risk-Limits
        starting_cash = float(self._config.get("general.starting_capital", 10000.0))
        risk_limits = LiveRiskLimits.from_config(
            self._config,
            starting_cash=starting_cash,
        )

        # Session erstellen
        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=data_source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
            run_logger=run_logger,
        )

        return session

    def start_shadow_run(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        notes: str = "",
    ) -> str:
        """
        Startet einen Shadow-Run.

        Args:
            strategy_name: Name der Strategie
            symbol: Trading-Symbol
            timeframe: Timeframe
            notes: Optionale Notizen

        Returns:
            Run-ID

        Raises:
            ReadinessCheckFailedError: Wenn Readiness-Checks fehlschlagen
            OrchestratorError: Bei anderen Fehlern
        """
        with self._lock:
            # Readiness-Check
            self._ensure_readiness("shadow")

            # Run-ID generieren
            run_id = f"shadow_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            try:
                # Run-Logger erstellen
                from .run_logging import create_run_logger_from_config
                run_logger = create_run_logger_from_config(
                    cfg=self._config,
                    mode="shadow",
                    strategy_name=strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    run_id=run_id,
                )

                # Session bauen
                session = self._build_shadow_session(
                    strategy_name=strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    run_id=run_id,
                    run_logger=run_logger,
                )

                # Run-Info erstellen
                run_info = RunInfo(
                    run_id=run_id,
                    mode="shadow",
                    strategy_name=strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    state=RunState.PENDING,
                    started_at=datetime.now(timezone.utc),
                    notes=notes,
                    session=session,
                    run_logger=run_logger,
                )

                # Run registrieren
                self._runs[run_id] = run_info

                # Session in separatem Thread starten (vereinfacht für v1)
                def run_session():
                    try:
                        run_info.state = RunState.RUNNING
                        logger.info(f"[ORCHESTRATOR] Starte Shadow-Run: {run_id}")
                        session.warmup()
                        session.run_forever()
                    except KeyboardInterrupt:
                        logger.info(f"[ORCHESTRATOR] Shadow-Run gestoppt (KeyboardInterrupt): {run_id}")
                        run_info.state = RunState.STOPPED
                        run_info.stopped_at = datetime.now(timezone.utc)
                    except Exception as e:
                        logger.error(f"[ORCHESTRATOR] Shadow-Run Fehler: {run_id}, {e}")
                        run_info.state = RunState.ERROR
                        run_info.last_error = str(e)
                        run_info.stopped_at = datetime.now(timezone.utc)
                    finally:
                        if run_info.run_logger:
                            run_info.run_logger.finalize()

                thread = threading.Thread(target=run_session, daemon=True)
                thread.start()

                logger.info(f"[ORCHESTRATOR] Shadow-Run gestartet: {run_id}")
                return run_id

            except Exception as e:
                logger.error(f"[ORCHESTRATOR] Fehler beim Starten des Shadow-Runs: {e}")
                raise OrchestratorError(f"Fehler beim Starten des Shadow-Runs: {e}") from e

    def start_testnet_run(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        notes: str = "",
    ) -> str:
        """
        Startet einen Testnet-Run.

        Args:
            strategy_name: Name der Strategie
            symbol: Trading-Symbol
            timeframe: Timeframe
            notes: Optionale Notizen

        Returns:
            Run-ID

        Raises:
            ReadinessCheckFailedError: Wenn Readiness-Checks fehlschlagen
            OrchestratorError: Bei anderen Fehlern

        Note:
            In v1 wird Testnet ähnlich wie Shadow behandelt (Dry-Run).
            Später kann hier echte Testnet-Integration erfolgen.
        """
        with self._lock:
            # Readiness-Check
            self._ensure_readiness("testnet")

            # Run-ID generieren
            run_id = f"testnet_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            try:
                # Run-Logger erstellen
                from .run_logging import create_run_logger_from_config
                run_logger = create_run_logger_from_config(
                    cfg=self._config,
                    mode="testnet",
                    strategy_name=strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    run_id=run_id,
                )

                # Für v1: Testnet-Runs nutzen ShadowPaperSession mit Testnet-Environment
                # Später kann hier echte Testnet-Session erstellt werden
                session = self._build_shadow_session(
                    strategy_name=strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    run_id=run_id,
                    run_logger=run_logger,
                )

                # Run-Info erstellen
                run_info = RunInfo(
                    run_id=run_id,
                    mode="testnet",
                    strategy_name=strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    state=RunState.PENDING,
                    started_at=datetime.now(timezone.utc),
                    notes=notes,
                    session=session,
                    run_logger=run_logger,
                )

                # Run registrieren
                self._runs[run_id] = run_info

                # Session in separatem Thread starten
                def run_session():
                    try:
                        run_info.state = RunState.RUNNING
                        logger.info(f"[ORCHESTRATOR] Starte Testnet-Run: {run_id}")
                        session.warmup()
                        session.run_forever()
                    except KeyboardInterrupt:
                        logger.info(f"[ORCHESTRATOR] Testnet-Run gestoppt (KeyboardInterrupt): {run_id}")
                        run_info.state = RunState.STOPPED
                        run_info.stopped_at = datetime.now(timezone.utc)
                    except Exception as e:
                        logger.error(f"[ORCHESTRATOR] Testnet-Run Fehler: {run_id}, {e}")
                        run_info.state = RunState.ERROR
                        run_info.last_error = str(e)
                        run_info.stopped_at = datetime.now(timezone.utc)
                    finally:
                        if run_info.run_logger:
                            run_info.run_logger.finalize()

                thread = threading.Thread(target=run_session, daemon=True)
                thread.start()

                logger.info(f"[ORCHESTRATOR] Testnet-Run gestartet: {run_id}")
                return run_id

            except Exception as e:
                logger.error(f"[ORCHESTRATOR] Fehler beim Starten des Testnet-Runs: {e}")
                raise OrchestratorError(f"Fehler beim Starten des Testnet-Runs: {e}") from e

    def stop_run(self, run_id: str) -> None:
        """
        Stoppt einen Run sauber.

        Args:
            run_id: Run-ID

        Raises:
            RunNotFoundError: Wenn Run-ID nicht gefunden
        """
        with self._lock:
            if run_id not in self._runs:
                raise RunNotFoundError(f"Run-ID nicht gefunden: {run_id}")

            run_info = self._runs[run_id]

            if run_info.state in (RunState.STOPPED, RunState.ERROR):
                logger.info(f"[ORCHESTRATOR] Run bereits gestoppt: {run_id}")
                return

            try:
                run_info.state = RunState.STOPPING

                # Session stoppen (wenn vorhanden)
                if run_info.session and hasattr(run_info.session, "stop"):
                    run_info.session.stop()
                elif run_info.session and hasattr(run_info.session, "_shutdown_requested"):
                    run_info.session._shutdown_requested = True

                # Run-Logger finalisieren
                if run_info.run_logger:
                    run_info.run_logger.finalize()

                run_info.state = RunState.STOPPED
                run_info.stopped_at = datetime.now(timezone.utc)

                logger.info(f"[ORCHESTRATOR] Run gestoppt: {run_id}")

            except Exception as e:
                logger.error(f"[ORCHESTRATOR] Fehler beim Stoppen des Runs: {run_id}, {e}")
                run_info.state = RunState.ERROR
                run_info.last_error = str(e)

    def get_status(self, run_id: Optional[str] = None) -> RunInfo | List[RunInfo]:
        """
        Gibt Status eines Runs oder aller Runs zurück.

        Args:
            run_id: Optional Run-ID (wenn None: alle Runs)

        Returns:
            RunInfo oder Liste von RunInfo

        Raises:
            RunNotFoundError: Wenn Run-ID nicht gefunden
        """
        with self._lock:
            if run_id is None:
                return list(self._runs.values())

            if run_id not in self._runs:
                raise RunNotFoundError(f"Run-ID nicht gefunden: {run_id}")

            return self._runs[run_id]

    def tail_events(
        self,
        run_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Gibt die letzten Events eines Runs zurück.

        Args:
            run_id: Run-ID
            limit: Maximale Anzahl Events

        Returns:
            Liste von Event-Dictionaries

        Raises:
            RunNotFoundError: Wenn Run-ID nicht gefunden
        """
        with self._lock:
            if run_id not in self._runs:
                raise RunNotFoundError(f"Run-ID nicht gefunden: {run_id}")

            run_info = self._runs[run_id]

            if not run_info.run_logger:
                return []

            try:
                from .run_logging import load_run_events
                events_df = load_run_events(run_info.run_logger.run_dir)

                # Sortiere nach Step (neueste zuerst) und limitiere
                if len(events_df) > 0:
                    events_df = events_df.sort_values("step", ascending=False).head(limit)
                    events_df = events_df.sort_values("step", ascending=True)  # Zurück sortieren für chronologische Reihenfolge
                    return events_df.to_dict("records")
                else:
                    return []

            except Exception as e:
                logger.error(f"[ORCHESTRATOR] Fehler beim Laden der Events: {run_id}, {e}")
                return []

