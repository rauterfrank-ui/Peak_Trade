# src/live/alert_rules.py
"""
Peak_Trade: Alert Rules v1 (Phase 66)
=====================================

Regel-Engine für Monitoring-basierte Alerts.

Regeln:
- PnL-Drop: Erkennt starke Intraday-PnL-Drops
- No-Events: Erkennt ausbleibende Events (Data-Gaps)
- Error-Spike: Erkennt gehäufte Fehler/Order-Rejects
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from .alert_manager import AlertManager
from .alerts import AlertLevel
from .monitoring import (
    get_run_snapshot,
    get_run_timeseries,
    tail_events,
    RunNotFoundError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Monitoring API (Wrapper für einfachere Nutzung)
# =============================================================================


class MonitoringAPI:
    """
    Wrapper um Monitoring-Funktionen für einfachere Nutzung in Regeln.
    """

    def __init__(self, base_dir: str = "live_runs") -> None:
        """
        Initialisiert MonitoringAPI.

        Args:
            base_dir: Basis-Verzeichnis für Runs
        """
        self.base_dir = base_dir

    def get_snapshot(self, run_id: str) -> Any:
        """Lädt Run-Snapshot."""
        return get_run_snapshot(run_id, base_dir=self.base_dir)

    def get_timeseries(self, run_id: str, metric: str = "equity", limit: int = 500) -> Any:
        """Lädt Zeitreihen-Daten."""
        return get_run_timeseries(run_id, metric=metric, limit=limit, base_dir=self.base_dir)

    def get_events(self, run_id: str, limit: int = 100) -> Any:
        """Lädt Events."""
        return tail_events(run_id, limit=limit, base_dir=self.base_dir)


# =============================================================================
# Alert Rules
# =============================================================================


def check_pnl_drop(
    run_id: str,
    threshold_pct: float,
    window: timedelta,
    monitoring: MonitoringAPI,
    alert_manager: AlertManager,
) -> bool:
    """
    Prüft ob PnL im angegebenen Zeitfenster um mehr als threshold_pct gefallen ist.

    Args:
        run_id: Run-ID
        threshold_pct: Schwellenwert in Prozent (z.B. 5.0 für 5%)
        window: Zeitfenster (z.B. timedelta(hours=1))
        monitoring: MonitoringAPI-Instanz
        alert_manager: AlertManager-Instanz

    Returns:
        True wenn Alert ausgelöst wurde, sonst False
    """
    try:
        # Zeitreihe laden
        timeseries = monitoring.get_timeseries(run_id, metric="equity", limit=500)

        if len(timeseries) < 2:
            logger.debug(f"Zu wenige Datenpunkte für PnL-Drop-Check: {run_id}")
            return False

        # Aktueller Equity
        current_equity = timeseries[-1].equity
        if current_equity is None:
            logger.debug(f"Kein Equity-Wert für PnL-Drop-Check: {run_id}")
            return False

        # Zeitfenster-Beginn
        window_start = datetime.now(timezone.utc) - window

        # Equity am Zeitfenster-Beginn finden
        window_equity: Optional[float] = None
        for point in timeseries:
            if point.timestamp >= window_start and point.equity is not None:
                window_equity = point.equity
                break

        # Falls kein Punkt im Fenster, nimm den ältesten verfügbaren
        if window_equity is None:
            for point in timeseries:
                if point.equity is not None:
                    window_equity = point.equity
                    break

        if window_equity is None or window_equity <= 0:
            logger.debug(f"Kein gültiger Equity-Wert für PnL-Drop-Check: {run_id}")
            return False

        # Drop berechnen
        drop_pct = ((current_equity - window_equity) / window_equity) * 100.0

        if drop_pct < -threshold_pct:
            # Alert auslösen
            alert_manager.critical(
                source="monitoring.pnl_drop",
                code="PNL_DROP",
                message=f"PnL dropped by {abs(drop_pct):.2f}% in the last {window}",
                run_id=run_id,
                details={
                    "drop_pct": drop_pct,
                    "window_equity": window_equity,
                    "current_equity": current_equity,
                    "threshold_pct": threshold_pct,
                },
            )
            return True

        return False

    except RunNotFoundError:
        logger.warning(f"Run nicht gefunden für PnL-Drop-Check: {run_id}")
        return False
    except Exception as e:
        logger.error(f"Fehler beim PnL-Drop-Check für Run {run_id}: {e}", exc_info=True)
        return False


def check_no_events(
    run_id: str,
    max_silence: timedelta,
    monitoring: MonitoringAPI,
    alert_manager: AlertManager,
) -> bool:
    """
    Prüft ob ein Run zu lange keine Events produziert hat.

    Args:
        run_id: Run-ID
        max_silence: Maximale Stille-Zeit (z.B. timedelta(minutes=10))
        monitoring: MonitoringAPI-Instanz
        alert_manager: AlertManager-Instanz

    Returns:
        True wenn Alert ausgelöst wurde, sonst False
    """
    try:
        snapshot = monitoring.get_snapshot(run_id)

        if snapshot.last_event_time is None:
            # Kein Event bisher
            alert_manager.warning(
                source="monitoring.no_events",
                code="NO_EVENTS",
                message=f"Run has no events yet",
                run_id=run_id,
                details={"num_events": snapshot.num_events},
            )
            return True

        # Zeit seit letztem Event
        now = datetime.now(timezone.utc)
        silence_duration = now - snapshot.last_event_time

        if silence_duration > max_silence:
            # Alert auslösen
            severity = AlertLevel.CRITICAL if silence_duration > max_silence * 2 else AlertLevel.WARNING

            if severity == AlertLevel.CRITICAL:
                alert_manager.critical(
                    source="monitoring.no_events",
                    code="NO_EVENTS_CRITICAL",
                    message=f"No events for {silence_duration} (max: {max_silence})",
                    run_id=run_id,
                    details={
                        "silence_duration_seconds": silence_duration.total_seconds(),
                        "last_event_time": snapshot.last_event_time.isoformat(),
                        "num_events": snapshot.num_events,
                    },
                )
            else:
                alert_manager.warning(
                    source="monitoring.no_events",
                    code="NO_EVENTS",
                    message=f"No events for {silence_duration} (max: {max_silence})",
                    run_id=run_id,
                    details={
                        "silence_duration_seconds": silence_duration.total_seconds(),
                        "last_event_time": snapshot.last_event_time.isoformat(),
                        "num_events": snapshot.num_events,
                    },
                )
            return True

        return False

    except RunNotFoundError:
        logger.warning(f"Run nicht gefunden für No-Events-Check: {run_id}")
        return False
    except Exception as e:
        logger.error(f"Fehler beim No-Events-Check für Run {run_id}: {e}", exc_info=True)
        return False


def check_error_spike(
    run_id: str,
    max_errors: int,
    window: timedelta,
    monitoring: MonitoringAPI,
    alert_manager: AlertManager,
) -> bool:
    """
    Prüft ob zu viele Fehler im angegebenen Zeitfenster aufgetreten sind.

    Args:
        run_id: Run-ID
        max_errors: Maximale Anzahl Fehler im Zeitfenster
        window: Zeitfenster (z.B. timedelta(minutes=10))
        monitoring: MonitoringAPI-Instanz
        alert_manager: AlertManager-Instanz

    Returns:
        True wenn Alert ausgelöst wurde, sonst False
    """
    try:
        events = monitoring.get_events(run_id, limit=500)

        if len(events) == 0:
            return False

        # Zeitfenster-Beginn
        window_start = datetime.now(timezone.utc) - window

        # Fehler zählen
        error_count = 0
        error_details: list[Dict[str, Any]] = []

        for event in events:
            # Timestamp prüfen
            ts_str = event.get("ts_event") or event.get("ts_bar")
            if not ts_str:
                continue

            try:
                if isinstance(ts_str, str):
                    event_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                else:
                    continue
            except Exception:
                continue

            if event_time < window_start:
                continue

            # Fehler-Kriterien prüfen
            has_error = False
            error_reason = ""

            # Risk-Block
            if event.get("risk_reasons") and str(event.get("risk_reasons")).strip():
                has_error = True
                error_reason = f"Risk: {event.get('risk_reasons')}"

            # Order-Rejects
            if event.get("orders_rejected", 0) > 0:
                has_error = True
                error_reason = f"Order-Rejects: {event.get('orders_rejected')}"

            # Extra-Error-Feld (falls vorhanden)
            if event.get("extra_error") and str(event.get("extra_error")).strip():
                has_error = True
                error_reason = f"Error: {event.get('extra_error')}"

            if has_error:
                error_count += 1
                error_details.append({
                    "step": event.get("step"),
                    "ts": ts_str,
                    "reason": error_reason,
                })

        if error_count > max_errors:
            # Alert auslösen
            severity = AlertLevel.CRITICAL if error_count > max_errors * 2 else AlertLevel.WARNING

            if severity == AlertLevel.CRITICAL:
                alert_manager.critical(
                    source="monitoring.error_spike",
                    code="ERROR_SPIKE_CRITICAL",
                    message=f"{error_count} errors in the last {window} (max: {max_errors})",
                    run_id=run_id,
                    details={
                        "error_count": error_count,
                        "max_errors": max_errors,
                        "window_seconds": window.total_seconds(),
                        "error_details": error_details[:10],  # Nur erste 10
                    },
                )
            else:
                alert_manager.warning(
                    source="monitoring.error_spike",
                    code="ERROR_SPIKE",
                    message=f"{error_count} errors in the last {window} (max: {max_errors})",
                    run_id=run_id,
                    details={
                        "error_count": error_count,
                        "max_errors": max_errors,
                        "window_seconds": window.total_seconds(),
                        "error_details": error_details[:10],  # Nur erste 10
                    },
                )
            return True

        return False

    except RunNotFoundError:
        logger.warning(f"Run nicht gefunden für Error-Spike-Check: {run_id}")
        return False
    except Exception as e:
        logger.error(f"Fehler beim Error-Spike-Check für Run {run_id}: {e}", exc_info=True)
        return False







