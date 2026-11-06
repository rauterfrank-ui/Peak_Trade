# src/live/monitoring.py
"""
Peak_Trade: Live Monitoring & Dashboards v1 (Phase 65)
======================================================

Monitoring-Funktionen für Shadow- und Testnet-Runs.

Features:
- Run-Übersicht (list_runs)
- Run-Snapshots mit aggregierten Metriken
- Zeitreihen-Daten für Dashboards
- Event-Tailing

WICHTIG: Diese Library nutzt die bestehende Run-Logging-Struktur.
         Keine neue Persistenz wird erstellt.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .run_logging import (
    load_run_metadata,
    load_run_events,
    list_runs as list_run_ids,
    LiveRunMetadata,
)
from ..core.resilience_helpers import with_resilience

logger = logging.getLogger(__name__)


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class RunMetricPoint:
    """
    Ein einzelner Metrik-Punkt in einer Zeitreihe.

    Attributes:
        timestamp: Zeitstempel des Events
        equity: Aktuelles Equity
        pnl: Realisierter PnL
        unrealized_pnl: Unrealisierter PnL
        drawdown: Aktueller Drawdown (negativ)
        exposure: Gesamt-Exposure
    """

    timestamp: datetime
    equity: Optional[float] = None
    pnl: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    drawdown: Optional[float] = None
    exposure: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "equity": self.equity,
            "pnl": self.pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "drawdown": self.drawdown,
            "exposure": self.exposure,
        }


@dataclass
class RunSnapshot:
    """
    Snapshot eines Runs mit aggregierten Metriken.

    Attributes:
        run_id: Eindeutige Run-ID
        mode: Environment-Modus (shadow, testnet)
        strategy: Strategie-Name
        symbol: Trading-Symbol
        timeframe: Timeframe
        is_active: Ob der Run als aktiv gilt
        started_at: Start-Zeitpunkt
        ended_at: End-Zeitpunkt (falls beendet)
        last_event_time: Zeitstempel des letzten Events
        equity: Aktuelles Equity (aus letztem Event)
        pnl: Realisierter PnL (aus letztem Event)
        unrealized_pnl: Unrealisierter PnL (aus letztem Event)
        drawdown: Aktueller Drawdown (berechnet)
        num_events: Anzahl Events
        last_error: Letzter Fehler (falls vorhanden)
        run_dir: Pfad zum Run-Verzeichnis
    """

    run_id: str
    mode: str
    strategy: Optional[str] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    is_active: bool = False
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    last_event_time: Optional[datetime] = None
    equity: Optional[float] = None
    pnl: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    drawdown: Optional[float] = None
    num_events: int = 0
    last_error: Optional[str] = None
    run_dir: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "strategy": self.strategy,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "is_active": self.is_active,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "last_event_time": self.last_event_time.isoformat() if self.last_event_time else None,
            "equity": self.equity,
            "pnl": self.pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "drawdown": self.drawdown,
            "num_events": self.num_events,
            "last_error": self.last_error,
            "run_dir": str(self.run_dir) if self.run_dir else None,
        }


# =============================================================================
# Exceptions
# =============================================================================


class RunNotFoundError(Exception):
    """Wird geworfen wenn ein Run nicht gefunden wird."""

    pass


# =============================================================================
# Monitoring Functions
# =============================================================================


def _calculate_drawdown(equity_series: pd.Series) -> Optional[float]:
    """
    Berechnet den aktuellen Drawdown aus einer Equity-Serie.

    Args:
        equity_series: Serie von Equity-Werten

    Returns:
        Drawdown als negativer Prozentsatz (z.B. -0.05 für -5%)
    """
    if len(equity_series) == 0:
        return None

    # NaN-Werte entfernen
    equity_clean = equity_series.dropna()
    if len(equity_clean) == 0:
        return None

    # Running Maximum
    running_max = equity_clean.expanding().max()

    # Drawdown
    drawdown = (equity_clean - running_max) / running_max

    # Aktueller Drawdown (letzter Wert)
    current_dd = drawdown.iloc[-1]

    return float(current_dd) if not pd.isna(current_dd) else None


def _is_run_active(
    metadata: LiveRunMetadata,
    last_event_time: Optional[datetime],
    max_idle_minutes: int = 10,
) -> bool:
    """
    Bestimmt ob ein Run als aktiv gilt.

    Args:
        metadata: Run-Metadaten
        last_event_time: Zeitstempel des letzten Events
        max_idle_minutes: Max. Minuten ohne Event, bevor Run als inaktiv gilt

    Returns:
        True wenn Run aktiv ist
    """
    # Wenn Run beendet wurde, ist er nicht aktiv
    if metadata.ended_at is not None:
        return False

    # Wenn kein letztes Event, ist Run nicht aktiv
    if last_event_time is None:
        return False

    # Prüfe ob letztes Event zu alt ist
    now = datetime.now(timezone.utc)
    idle_minutes = (now - last_event_time).total_seconds() / 60.0

    return idle_minutes < max_idle_minutes


def list_runs(
    base_dir: str | Path = "live_runs",
    include_inactive: bool = False,
    max_age: Optional[timedelta] = None,
) -> List[RunSnapshot]:
    """
    Listet alle verfügbaren Runs und erstellt Snapshots.

    Args:
        base_dir: Basis-Verzeichnis für Runs
        include_inactive: Ob inaktive Runs eingeschlossen werden sollen
        max_age: Maximale Alter der Runs (z.B. timedelta(hours=24))

    Returns:
        Liste von RunSnapshots
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        logger.debug(f"Run-Verzeichnis existiert nicht: {base_dir}")
        return []

    run_ids = list_run_ids(base_dir=base_dir)
    snapshots: List[RunSnapshot] = []

    now = datetime.now(timezone.utc)

    for run_id in run_ids:
        try:
            run_dir = base_dir / run_id
            snapshot = get_run_snapshot(run_id, base_dir=base_dir)

            # Filter: max_age
            if max_age is not None and snapshot.started_at:
                age = now - snapshot.started_at
                if age > max_age:
                    continue

            # Filter: include_inactive
            if not include_inactive and not snapshot.is_active:
                continue

            snapshots.append(snapshot)

        except Exception as e:
            logger.warning(f"Fehler beim Laden von Run {run_id}: {e}")
            continue

    # Sortiere nach last_event_time (neueste zuerst)
    snapshots.sort(
        key=lambda s: s.last_event_time or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return snapshots


def get_run_snapshot(
    run_id: str,
    base_dir: str | Path = "live_runs",
) -> RunSnapshot:
    """
    Lädt einen Run-Snapshot mit aggregierten Metriken.

    Args:
        run_id: Run-ID
        base_dir: Basis-Verzeichnis für Runs

    Returns:
        RunSnapshot mit aggregierten Metriken

    Raises:
        RunNotFoundError: Wenn Run nicht gefunden wird
    """
    base_dir = Path(base_dir)
    run_dir = base_dir / run_id

    if not run_dir.exists():
        raise RunNotFoundError(f"Run-Verzeichnis nicht gefunden: {run_dir}")

    try:
        # Metadaten laden
        metadata = load_run_metadata(run_dir)

        # Events laden (falls vorhanden)
        try:
            events_df = load_run_events(run_dir)
        except FileNotFoundError:
            # Keine Events-Datei vorhanden (Run noch nicht gestartet)
            events_df = pd.DataFrame()

        # Letztes Event extrahieren
        last_event_time: Optional[datetime] = None
        equity: Optional[float] = None
        pnl: Optional[float] = None
        unrealized_pnl: Optional[float] = None
        drawdown: Optional[float] = None
        last_error: Optional[str] = None

        if len(events_df) > 0:
            # Letztes Event (höchster Step)
            last_event = events_df.iloc[-1]

            # Timestamp
            ts_str = last_event.get("ts_event") or last_event.get("ts_bar")
            if ts_str:
                if isinstance(ts_str, str):
                    try:
                        last_event_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except Exception:
                        pass
                elif isinstance(ts_str, pd.Timestamp):
                    last_event_time = ts_str.to_pydatetime()

            # Equity
            if "equity" in last_event and pd.notna(last_event["equity"]):
                equity = float(last_event["equity"])

            # PnL
            if "realized_pnl" in last_event and pd.notna(last_event["realized_pnl"]):
                pnl = float(last_event["realized_pnl"])
            elif "pnl" in last_event and pd.notna(last_event["pnl"]):
                pnl = float(last_event["pnl"])

            # Unrealized PnL
            if "unrealized_pnl" in last_event and pd.notna(last_event["unrealized_pnl"]):
                unrealized_pnl = float(last_event["unrealized_pnl"])

            # Drawdown berechnen
            if "equity" in events_df.columns:
                equity_series = events_df["equity"].dropna()
                if len(equity_series) > 0:
                    drawdown = _calculate_drawdown(equity_series)

            # Last Error
            if "risk_reasons" in last_event and pd.notna(last_event["risk_reasons"]):
                error_str = str(last_event["risk_reasons"]).strip()
                if error_str:
                    last_error = error_str

        # Active-Status bestimmen
        is_active = _is_run_active(metadata, last_event_time)

        # Snapshot erstellen
        snapshot = RunSnapshot(
            run_id=run_id,
            mode=metadata.mode,
            strategy=metadata.strategy_name,
            symbol=metadata.symbol,
            timeframe=metadata.timeframe,
            is_active=is_active,
            started_at=metadata.started_at,
            ended_at=metadata.ended_at,
            last_event_time=last_event_time,
            equity=equity,
            pnl=pnl,
            unrealized_pnl=unrealized_pnl,
            drawdown=drawdown,
            num_events=len(events_df),
            last_error=last_error,
            run_dir=run_dir,
        )

        return snapshot

    except FileNotFoundError as e:
        raise RunNotFoundError(f"Run nicht gefunden: {run_id}") from e
    except Exception as e:
        logger.error(f"Fehler beim Laden des Run-Snapshots {run_id}: {e}")
        raise RunNotFoundError(f"Fehler beim Laden des Run-Snapshots {run_id}: {e}") from e


def get_run_timeseries(
    run_id: str,
    metric: str = "equity",
    limit: int = 500,
    base_dir: str | Path = "live_runs",
) -> List[RunMetricPoint]:
    """
    Lädt eine Zeitreihe für einen Run.

    Args:
        run_id: Run-ID
        metric: Metrik-Name ("equity", "pnl", "drawdown")
        limit: Maximale Anzahl Events
        base_dir: Basis-Verzeichnis für Runs

    Returns:
        Liste von RunMetricPoints

    Raises:
        RunNotFoundError: Wenn Run nicht gefunden wird
    """
    base_dir = Path(base_dir)
    run_dir = base_dir / run_id

    if not run_dir.exists():
        raise RunNotFoundError(f"Run-Verzeichnis nicht gefunden: {run_dir}")

    try:
        events_df = load_run_events(run_dir)

        if len(events_df) == 0:
            return []

        # Limitieren
        if len(events_df) > limit:
            events_df = events_df.tail(limit)

        # Zeitreihe aufbauen
        points: List[RunMetricPoint] = []

        for _, row in events_df.iterrows():
            # Timestamp
            ts_str = row.get("ts_event") or row.get("ts_bar")
            timestamp: Optional[datetime] = None
            if ts_str:
                if isinstance(ts_str, str):
                    try:
                        timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except Exception:
                        pass
                elif isinstance(ts_str, pd.Timestamp):
                    timestamp = ts_str.to_pydatetime()

            if timestamp is None:
                continue

            # Equity
            equity = None
            if "equity" in row and pd.notna(row["equity"]):
                equity = float(row["equity"])

            # PnL
            pnl = None
            if "realized_pnl" in row and pd.notna(row["realized_pnl"]):
                pnl = float(row["realized_pnl"])
            elif "pnl" in row and pd.notna(row["pnl"]):
                pnl = float(row["pnl"])

            # Unrealized PnL
            unrealized_pnl = None
            if "unrealized_pnl" in row and pd.notna(row["unrealized_pnl"]):
                unrealized_pnl = float(row["unrealized_pnl"])

            # Drawdown (berechnen aus Equity-Serie bis zu diesem Punkt)
            drawdown = None
            if equity is not None and "equity" in events_df.columns:
                equity_series = events_df.loc[: row.name, "equity"].dropna()
                if len(equity_series) > 0:
                    drawdown = _calculate_drawdown(equity_series)

            # Exposure (optional)
            exposure = None
            if "position_size" in row and pd.notna(row["position_size"]):
                position_size = float(row["position_size"])
                price = row.get("price") or row.get("close")
                if price is not None and pd.notna(price):
                    exposure = abs(position_size * float(price))

            point = RunMetricPoint(
                timestamp=timestamp,
                equity=equity,
                pnl=pnl,
                unrealized_pnl=unrealized_pnl,
                drawdown=drawdown,
                exposure=exposure,
            )

            points.append(point)

        return points

    except FileNotFoundError as e:
        raise RunNotFoundError(f"Run nicht gefunden: {run_id}") from e
    except Exception as e:
        logger.error(f"Fehler beim Laden der Zeitreihe für Run {run_id}: {e}")
        raise RunNotFoundError(f"Fehler beim Laden der Zeitreihe für Run {run_id}: {e}") from e


def tail_events(
    run_id: str,
    limit: int = 100,
    base_dir: str | Path = "live_runs",
) -> List[Dict[str, Any]]:
    """
    Gibt die letzten Events eines Runs zurück.

    Args:
        run_id: Run-ID
        limit: Maximale Anzahl Events
        base_dir: Basis-Verzeichnis für Runs

    Returns:
        Liste von Event-Dictionaries

    Raises:
        RunNotFoundError: Wenn Run nicht gefunden wird
    """
    base_dir = Path(base_dir)
    run_dir = base_dir / run_id

    if not run_dir.exists():
        raise RunNotFoundError(f"Run-Verzeichnis nicht gefunden: {run_dir}")

    try:
        events_df = load_run_events(run_dir)

        if len(events_df) == 0:
            return []

        # Sortiere nach Step (neueste zuerst) und limitiere
        events_df = events_df.sort_values("step", ascending=False).head(limit)
        # Zurück sortieren für chronologische Reihenfolge
        events_df = events_df.sort_values("step", ascending=True)

        # Konvertiere zu Dict-Liste
        events = events_df.to_dict("records")

        # Konvertiere Timestamps zu ISO-Strings
        for event in events:
            for key in ["ts_event", "ts_bar"]:
                if key in event and pd.notna(event[key]):
                    if isinstance(event[key], pd.Timestamp):
                        event[key] = event[key].isoformat()
                    elif isinstance(event[key], datetime):
                        event[key] = event[key].isoformat()

        return events

    except FileNotFoundError as e:
        raise RunNotFoundError(f"Run nicht gefunden: {run_id}") from e
    except Exception as e:
        logger.error(f"Fehler beim Laden der Events für Run {run_id}: {e}")
        raise RunNotFoundError(f"Fehler beim Laden der Events für Run {run_id}: {e}") from e
