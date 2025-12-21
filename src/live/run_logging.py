# src/live/run_logging.py
"""
Peak_Trade: Live/Shadow Run Logging (Phase 32)
==============================================

Strukturiertes Logging für Shadow-/Paper-Runs.
Erzeugt persistente Run-Logs für späteres Reporting.

Features:
- Eindeutige Run-IDs
- Run-Metadaten (JSON)
- Time-Series Events (Parquet/CSV)
- Automatisches Flushing
- Kontext-Manager-Support

WICHTIG: Dieses Modul ist rein passiv und erzeugt keine Order-Requests.
         Es dient ausschließlich der Dokumentation/Analyse von Runs.

Example:
    >>> from src.live.run_logging import LiveRunLogger, LiveRunMetadata
    >>>
    >>> metadata = LiveRunMetadata(
    ...     run_id="20251204_180000_paper_ma_crossover_BTC-EUR_1m",
    ...     mode="paper",
    ...     strategy_name="ma_crossover",
    ...     symbol="BTC/EUR",
    ...     timeframe="1m",
    ... )
    >>>
    >>> with LiveRunLogger(logging_cfg, metadata) as logger:
    ...     for candle in data_source:
    ...         # ... process ...
    ...         logger.log_event(event)
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from ..orders.base import OrderExecutionResult

logger = logging.getLogger(__name__)


# =============================================================================
# Config Dataclass
# =============================================================================


@dataclass
class ShadowPaperLoggingConfig:
    """
    Konfiguration für Shadow-/Paper-Run-Logging.

    Attributes:
        enabled: Logging aktiviert
        base_dir: Basis-Verzeichnis für Run-Logs
        flush_interval_steps: Flush alle N Steps
        format: Format für Events ("parquet" oder "csv")
        write_markdown_report_on_finish: Report bei Beenden generieren
        log_ohlc_details: OHLC-Details pro Step loggen
        log_order_details: Order-Details loggen
        log_risk_details: Risk-Check-Details loggen
    """

    enabled: bool = True
    base_dir: str = "live_runs"
    flush_interval_steps: int = 50
    format: str = "parquet"
    write_markdown_report_on_finish: bool = False
    log_ohlc_details: bool = True
    log_order_details: bool = True
    log_risk_details: bool = True


def load_shadow_paper_logging_config(cfg: Any) -> ShadowPaperLoggingConfig:
    """
    Lädt ShadowPaperLoggingConfig aus PeakConfig.

    Args:
        cfg: PeakConfig-Objekt

    Returns:
        ShadowPaperLoggingConfig mit Werten aus Config
    """
    return ShadowPaperLoggingConfig(
        enabled=cfg.get("shadow_paper_logging.enabled", True),
        base_dir=cfg.get("shadow_paper_logging.base_dir", "live_runs"),
        flush_interval_steps=cfg.get("shadow_paper_logging.flush_interval_steps", 50),
        format=cfg.get("shadow_paper_logging.format", "parquet"),
        write_markdown_report_on_finish=cfg.get(
            "shadow_paper_logging.write_markdown_report_on_finish", False
        ),
        log_ohlc_details=cfg.get("shadow_paper_logging.log_ohlc_details", True),
        log_order_details=cfg.get("shadow_paper_logging.log_order_details", True),
        log_risk_details=cfg.get("shadow_paper_logging.log_risk_details", True),
    )


# =============================================================================
# Run Metadata
# =============================================================================


@dataclass
class LiveRunMetadata:
    """
    Metadaten für einen Live-/Shadow-Run.

    Attributes:
        run_id: Eindeutige Run-ID
        mode: Environment-Modus (paper, shadow, etc.)
        strategy_name: Name der Strategie
        symbol: Trading-Symbol
        timeframe: Candle-Timeframe
        started_at: Startzeit des Runs
        ended_at: Endzeit des Runs (nach Abschluss)
        config_snapshot: Relevante Config-Werte
        notes: Optionale Notizen
    """

    run_id: str
    mode: str
    strategy_name: str
    symbol: str
    timeframe: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary (JSON-serialisierbar)."""
        d = asdict(self)
        # Datetime zu ISO-String
        if d["started_at"]:
            d["started_at"] = d["started_at"].isoformat()
        if d["ended_at"]:
            d["ended_at"] = d["ended_at"].isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LiveRunMetadata":
        """Erstellt LiveRunMetadata aus Dictionary."""
        # ISO-String zu Datetime
        started_at = data.get("started_at")
        if started_at and isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        ended_at = data.get("ended_at")
        if ended_at and isinstance(ended_at, str):
            ended_at = datetime.fromisoformat(ended_at)

        return cls(
            run_id=data["run_id"],
            mode=data["mode"],
            strategy_name=data["strategy_name"],
            symbol=data["symbol"],
            timeframe=data["timeframe"],
            started_at=started_at,
            ended_at=ended_at,
            config_snapshot=data.get("config_snapshot", {}),
            notes=data.get("notes", ""),
        )


# =============================================================================
# Run Event
# =============================================================================


@dataclass
class LiveRunEvent:
    """
    Ein einzelnes Event während eines Runs.

    Attributes:
        step: Schritt-Nummer
        ts_bar: Zeitstempel der Bar/Candle
        ts_event: Zeitstempel des Events (Verarbeitung)

        # Preis-Daten
        price: Aktueller Preis (Close)
        open: Open-Preis
        high: High-Preis
        low: Low-Preis
        close: Close-Preis
        volume: Volumen

        # Portfolio-Status
        position_size: Aktuelle Positionsgröße
        cash: Verfügbares Cash
        equity: Gesamtwert (Cash + Positionen)
        realized_pnl: Realisierter PnL
        unrealized_pnl: Unrealisierter PnL

        # Signal-Info
        signal: Strategie-Signal (-1, 0, +1)
        signal_changed: Ob Signal sich geändert hat

        # Order-Info
        orders_generated: Anzahl generierter Orders
        orders_filled: Anzahl gefüllter Orders
        orders_rejected: Anzahl abgelehnter Orders
        orders_blocked: Anzahl durch Risk blockierter Orders

        # Risk-Info
        risk_allowed: Ob Risk-Check bestanden
        risk_reasons: Gründe für Risk-Block

        # Extra-Daten
        extra: Zusätzliche Key-Value-Paare
    """

    step: int
    ts_bar: Optional[datetime] = None
    ts_event: Optional[datetime] = None

    # Preis-Daten
    price: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None

    # Portfolio-Status
    position_size: float = 0.0
    cash: Optional[float] = None
    equity: Optional[float] = None
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    # Signal-Info
    signal: int = 0
    signal_changed: bool = False

    # Order-Info
    orders_generated: int = 0
    orders_filled: int = 0
    orders_rejected: int = 0
    orders_blocked: int = 0

    # Risk-Info
    risk_allowed: bool = True
    risk_reasons: str = ""

    # Extra
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary (für DataFrame)."""
        d = asdict(self)
        # Datetime zu ISO-String
        if d["ts_bar"]:
            d["ts_bar"] = d["ts_bar"].isoformat()
        if d["ts_event"]:
            d["ts_event"] = d["ts_event"].isoformat()
        # Extra-Dict flatten (optional)
        extra = d.pop("extra", {})
        for k, v in extra.items():
            d[f"extra_{k}"] = v
        return d


# =============================================================================
# Run ID Generator
# =============================================================================


def generate_run_id(
    mode: str,
    strategy_name: str,
    symbol: str,
    timeframe: str,
    timestamp: Optional[datetime] = None,
) -> str:
    """
    Generiert eine eindeutige Run-ID.

    Format: YYYYMMDD_HHMMSS_{mode}_{strategy}_{symbol}_{timeframe}

    Args:
        mode: Environment-Modus
        strategy_name: Strategie-Name
        symbol: Trading-Symbol
        timeframe: Timeframe
        timestamp: Optionaler Zeitstempel (default: jetzt)

    Returns:
        Eindeutige Run-ID
    """
    ts = timestamp or datetime.now(timezone.utc)
    ts_str = ts.strftime("%Y%m%d_%H%M%S")

    # Symbol aufräumen (z.B. BTC/EUR -> BTC-EUR)
    symbol_clean = symbol.replace("/", "-").replace(" ", "_")
    strategy_clean = strategy_name.replace(" ", "_").replace("/", "-")

    return f"{ts_str}_{mode}_{strategy_clean}_{symbol_clean}_{timeframe}"


# =============================================================================
# Live Run Logger
# =============================================================================


class LiveRunLogger:
    """
    Logger für Live-/Shadow-Runs.

    Verwaltet Run-Metadaten und Events, schreibt sie in strukturierte Dateien.

    Filesystem-Layout:
        {base_dir}/{run_id}/
            meta.json       - Run-Metadaten
            events.parquet  - Time-Series Events (oder events.csv)

    Features:
    - Automatisches Flushing nach N Steps
    - Kontext-Manager-Support (with-Statement)
    - Robustes Error-Handling (Logging-Fehler crashen nicht den Run)

    Example:
        >>> with LiveRunLogger(config, metadata) as logger:
        ...     for i in range(100):
        ...         event = LiveRunEvent(step=i, ...)
        ...         logger.log_event(event)
    """

    def __init__(
        self,
        logging_cfg: ShadowPaperLoggingConfig,
        metadata: LiveRunMetadata,
        base_dir_override: Optional[str] = None,
    ) -> None:
        """
        Initialisiert den LiveRunLogger.

        Args:
            logging_cfg: Logging-Konfiguration
            metadata: Run-Metadaten
            base_dir_override: Optionaler Override für base_dir
        """
        self._cfg = logging_cfg
        self._metadata = metadata
        self._base_dir = Path(base_dir_override or logging_cfg.base_dir)

        # Run-Directory
        self._run_dir = self._base_dir / metadata.run_id

        # Events-Buffer
        self._events_buffer: List[Dict[str, Any]] = []
        self._total_events_logged: int = 0

        # State
        self._initialized = False
        self._finalized = False
        self._logging_disabled_due_to_error = False

        logger.info(
            f"[RUN LOGGER] Initialisiert: run_id={metadata.run_id}, base_dir={self._base_dir}"
        )

    @property
    def run_dir(self) -> Path:
        """Pfad zum Run-Verzeichnis."""
        return self._run_dir

    @property
    def run_id(self) -> str:
        """Run-ID."""
        return self._metadata.run_id

    @property
    def metadata(self) -> LiveRunMetadata:
        """Run-Metadaten."""
        return self._metadata

    @property
    def total_events_logged(self) -> int:
        """Anzahl geloggter Events."""
        return self._total_events_logged

    @property
    def is_initialized(self) -> bool:
        """True wenn Logger initialisiert ist."""
        return self._initialized

    def initialize(self) -> None:
        """
        Initialisiert den Logger: Erstellt Verzeichnis und schreibt Metadaten.

        Wird automatisch beim ersten log_event() aufgerufen,
        kann aber auch manuell aufgerufen werden.
        """
        if self._initialized:
            return

        if not self._cfg.enabled:
            logger.info("[RUN LOGGER] Logging ist deaktiviert")
            return

        try:
            # Run-Verzeichnis anlegen
            self._run_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[RUN LOGGER] Run-Verzeichnis erstellt: {self._run_dir}")

            # Startzeit setzen
            if self._metadata.started_at is None:
                self._metadata.started_at = datetime.now(timezone.utc)

            # Metadaten schreiben
            self._write_metadata()

            self._initialized = True

        except Exception as e:
            logger.error(f"[RUN LOGGER] Initialisierung fehlgeschlagen: {e}")
            self._logging_disabled_due_to_error = True
            raise

    def _write_metadata(self) -> None:
        """Schreibt Metadaten nach meta.json."""
        meta_path = self._run_dir / "meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata.to_dict(), f, indent=2, ensure_ascii=False)
        logger.debug(f"[RUN LOGGER] Metadaten geschrieben: {meta_path}")

    def log_event(self, event: LiveRunEvent) -> None:
        """
        Loggt ein Event.

        Args:
            event: Das zu loggende Event
        """
        if not self._cfg.enabled or self._logging_disabled_due_to_error:
            return

        if self._finalized:
            logger.warning("[RUN LOGGER] Logger bereits finalisiert, Event ignoriert")
            return

        # Lazy Initialization
        if not self._initialized:
            self.initialize()

        try:
            # Event zu Buffer hinzufügen
            self._events_buffer.append(event.to_dict())
            self._total_events_logged += 1

            # Flush wenn nötig
            if len(self._events_buffer) >= self._cfg.flush_interval_steps:
                self._flush()

        except Exception as e:
            logger.error(f"[RUN LOGGER] Fehler beim Event-Logging: {e}")
            # Weiterlaufen, aber warnen
            self._logging_disabled_due_to_error = True

    def _flush(self) -> None:
        """Schreibt Buffer in Events-Datei."""
        if not self._events_buffer:
            return

        try:
            df = pd.DataFrame(self._events_buffer)
            events_path = self._run_dir / f"events.{self._cfg.format}"

            if self._cfg.format == "parquet":
                # Parquet: Append-Strategie
                if events_path.exists():
                    existing_df = pd.read_parquet(events_path)
                    df = pd.concat([existing_df, df], ignore_index=True)
                df.to_parquet(events_path, index=False)
            else:
                # CSV: Append-Modus
                write_header = not events_path.exists()
                df.to_csv(events_path, mode="a", header=write_header, index=False)

            logger.debug(f"[RUN LOGGER] Flush: {len(self._events_buffer)} Events geschrieben")
            self._events_buffer.clear()

        except Exception as e:
            logger.error(f"[RUN LOGGER] Flush fehlgeschlagen: {e}")

    def finalize(self) -> None:
        """
        Finalisiert den Logger: Schreibt letzte Events und aktualisiert Metadaten.
        """
        if self._finalized:
            return

        if not self._cfg.enabled:
            self._finalized = True
            return

        try:
            # Letzten Buffer flushen
            self._flush()

            # Endzeit setzen und Metadaten aktualisieren
            self._metadata.ended_at = datetime.now(timezone.utc)
            self._write_metadata()

            # Optional: Markdown-Report generieren
            if self._cfg.write_markdown_report_on_finish:
                self._generate_report()

            logger.info(
                f"[RUN LOGGER] Finalisiert: {self._total_events_logged} Events geloggt, "
                f"Run-Dir: {self._run_dir}"
            )

        except Exception as e:
            logger.error(f"[RUN LOGGER] Finalisierung fehlgeschlagen: {e}")

        finally:
            self._finalized = True

    def _generate_report(self) -> None:
        """Generiert Markdown-Report (wenn konfiguriert)."""
        try:
            # Import hier um zirkuläre Imports zu vermeiden
            from ..reporting.live_run_report import build_live_run_report

            meta_path = self._run_dir / "meta.json"
            events_path = self._run_dir / f"events.{self._cfg.format}"
            report_path = self._run_dir / "report.md"

            if not events_path.exists():
                logger.warning("[RUN LOGGER] Keine Events-Datei für Report")
                return

            report = build_live_run_report(
                meta_path=str(meta_path),
                events_path=str(events_path),
            )

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report.to_markdown())

            logger.info(f"[RUN LOGGER] Report generiert: {report_path}")

        except ImportError:
            logger.warning("[RUN LOGGER] Report-Modul nicht verfügbar")
        except Exception as e:
            logger.error(f"[RUN LOGGER] Report-Generierung fehlgeschlagen: {e}")

    def __enter__(self) -> "LiveRunLogger":
        """Kontext-Manager Entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Kontext-Manager Exit."""
        self.finalize()


# =============================================================================
# Helper Functions
# =============================================================================


def create_run_logger_from_config(
    cfg: Any,
    mode: str,
    strategy_name: str,
    symbol: str,
    timeframe: str,
    config_snapshot: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None,
    base_dir_override: Optional[str] = None,
) -> LiveRunLogger:
    """
    Factory-Funktion für LiveRunLogger aus PeakConfig.

    Args:
        cfg: PeakConfig-Objekt
        mode: Environment-Modus
        strategy_name: Strategie-Name
        symbol: Trading-Symbol
        timeframe: Timeframe
        config_snapshot: Optionale Config-Snapshot
        run_id: Optionale Run-ID (sonst generiert)
        base_dir_override: Optionaler Base-Dir-Override

    Returns:
        Konfigurierter LiveRunLogger
    """
    logging_cfg = load_shadow_paper_logging_config(cfg)

    if run_id is None:
        run_id = generate_run_id(mode, strategy_name, symbol, timeframe)

    metadata = LiveRunMetadata(
        run_id=run_id,
        mode=mode,
        strategy_name=strategy_name,
        symbol=symbol,
        timeframe=timeframe,
        config_snapshot=config_snapshot or {},
    )

    return LiveRunLogger(
        logging_cfg=logging_cfg,
        metadata=metadata,
        base_dir_override=base_dir_override,
    )


def load_run_metadata(run_dir: str | Path) -> LiveRunMetadata:
    """
    Lädt Run-Metadaten aus einem Run-Verzeichnis.

    Args:
        run_dir: Pfad zum Run-Verzeichnis

    Returns:
        LiveRunMetadata

    Raises:
        FileNotFoundError: Wenn meta.json nicht existiert
    """
    meta_path = Path(run_dir) / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"meta.json nicht gefunden: {meta_path}")

    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return LiveRunMetadata.from_dict(data)


def load_run_events(run_dir: str | Path) -> pd.DataFrame:
    """
    Lädt Run-Events aus einem Run-Verzeichnis.

    Args:
        run_dir: Pfad zum Run-Verzeichnis

    Returns:
        DataFrame mit Events

    Raises:
        FileNotFoundError: Wenn Events-Datei nicht existiert
    """
    run_dir = Path(run_dir)

    # Parquet zuerst probieren
    parquet_path = run_dir / "events.parquet"
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)

    # CSV als Fallback
    csv_path = run_dir / "events.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)

    raise FileNotFoundError(f"Keine Events-Datei gefunden in: {run_dir}")


def list_runs(base_dir: str | Path = "live_runs") -> List[str]:
    """
    Listet alle verfügbaren Run-IDs.

    Args:
        base_dir: Basis-Verzeichnis für Runs

    Returns:
        Liste von Run-IDs
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return []

    runs = []
    for item in base_dir.iterdir():
        if item.is_dir() and (item / "meta.json").exists():
            runs.append(item.name)

    return sorted(runs, reverse=True)  # Neueste zuerst
