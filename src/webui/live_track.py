# src/webui/live_track.py
"""
Peak_Trade: Live-Track Service Layer (Phase 82/85 Dashboard)
=============================================================

Service-Funktionen für das Live-Track Panel im Web-Dashboard.
Liest aus der Live-Session-Registry (Phase 81) und liefert
aufbereitete Daten für das Dashboard.

Features (Phase 82):
- LiveSessionSummary: Pydantic-Modell für API-Responses
- get_recent_live_sessions(): Lädt letzte N Sessions aus der Registry
- Robuste Fehlerbehandlung (leere Liste bei fehlender Registry)

Features (Phase 85 - Session Explorer):
- LiveSessionDetail: Erweitertes Modell mit Config/Metrics/CLI
- get_session_by_id(): Lädt einzelne Session nach ID
- get_filtered_sessions(): Sessions mit Mode/Status-Filter
- compute_session_duration(): Berechnet Session-Dauer

Usage:
    >>> from src.webui.live_track import get_recent_live_sessions, get_session_by_id
    >>> sessions = get_recent_live_sessions(limit=10)
    >>> detail = get_session_by_id("session_20251208_001")

See also:
    - src/experiments/live_session_registry.py (LiveSessionRecord)
    - docs/PHASE_81_LIVE_SESSION_REGISTRY.md
    - docs/PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Hilfsfunktionen (Phase 85)
# =============================================================================


def compute_duration_seconds(
    started_at: Optional[datetime],
    ended_at: Optional[datetime],
) -> Optional[int]:
    """Berechnet die Session-Dauer in Sekunden."""
    if started_at is None:
        return None
    if ended_at is None:
        return None
    delta = ended_at - started_at
    return int(delta.total_seconds())


# =============================================================================
# Pydantic Models für API-Responses
# =============================================================================


class LiveSessionSummary(BaseModel):
    """
    Response-Modell für eine Live-Session im Dashboard (Liste).

    Leichtgewichtiges Modell, das die wichtigsten Felder aus
    LiveSessionRecord für die UI aufbereitet.

    Attributes:
        session_id: Eindeutige Session-ID
        started_at: Start-Zeitpunkt der Session
        ended_at: Ende-Zeitpunkt (None falls noch laufend)
        mode: Session-Mode (shadow, testnet, paper, live)
        environment: Environment-Name (z.B. Exchange + Symbol)
        status: Session-Status (started, completed, failed, aborted)
        realized_pnl: Realisierter PnL (falls verfügbar)
        max_drawdown: Maximaler Drawdown (falls verfügbar)
        num_orders: Anzahl Orders (falls verfügbar)
        report_path: Pfad zum Report-File (falls verfügbar)
        notes: Fehler oder Notizen (falls vorhanden)
        duration_seconds: Berechnete Dauer in Sekunden (Phase 85)
        is_live_warning: True wenn mode=live (Safety-Warnung, Phase 85)
        risk_status: Risk-Ampel-Status (green/yellow/red, Phase 87 Severity)
        risk_severity: Severity-Level (ok/warning/breach, Phase 87)
    """

    session_id: str = Field(..., description="Eindeutige Session-ID")
    started_at: datetime = Field(..., description="Start-Zeitpunkt")
    ended_at: Optional[datetime] = Field(None, description="Ende-Zeitpunkt")
    mode: str = Field(..., description="shadow, testnet, paper, live")
    environment: str = Field("", description="Environment-Info (Exchange + Symbol)")
    status: Literal["started", "completed", "failed", "aborted"] = Field(
        ..., description="Session-Status"
    )
    realized_pnl: Optional[float] = Field(None, description="Realisierter PnL")
    max_drawdown: Optional[float] = Field(None, description="Max Drawdown")
    num_orders: Optional[int] = Field(None, description="Anzahl Orders")
    report_path: Optional[str] = Field(None, description="Pfad zum Report")
    notes: Optional[str] = Field(None, description="Fehler oder Notizen")
    # Phase 85: Zusätzliche Felder
    duration_seconds: Optional[int] = Field(None, description="Session-Dauer in Sekunden")
    is_live_warning: bool = Field(False, description="True wenn mode=live (Safety)")
    # Phase 87: Risk-Severity Integration
    risk_status: Literal["green", "yellow", "red"] = Field(
        "green", description="Risk-Ampel: green=OK, yellow=WARNING, red=BREACH"
    )
    risk_severity: Literal["ok", "warning", "breach"] = Field(
        "ok", description="Risk-Severity-Level"
    )


class LiveSessionDetail(BaseModel):
    """
    Erweitertes Response-Modell für Session-Detail-Ansicht (Phase 85).

    Enthält alle Felder von LiveSessionSummary plus:
    - Vollständige Config
    - Alle Metrics
    - CLI-Args
    - Run-Type und Run-ID
    - Risk-Status und Limit-Details (Phase 87)

    Für die Detail-Page /session/{session_id}
    """

    # Basis-Felder (wie Summary)
    session_id: str = Field(..., description="Eindeutige Session-ID")
    started_at: datetime = Field(..., description="Start-Zeitpunkt")
    ended_at: Optional[datetime] = Field(None, description="Ende-Zeitpunkt")
    mode: str = Field(..., description="shadow, testnet, paper, live")
    environment: str = Field("", description="Environment-Info")
    status: Literal["started", "completed", "failed", "aborted"] = Field(
        ..., description="Session-Status"
    )
    realized_pnl: Optional[float] = Field(None, description="Realisierter PnL")
    max_drawdown: Optional[float] = Field(None, description="Max Drawdown")
    num_orders: Optional[int] = Field(None, description="Anzahl Orders")
    notes: Optional[str] = Field(None, description="Fehler oder Notizen")
    duration_seconds: Optional[int] = Field(None, description="Session-Dauer")
    is_live_warning: bool = Field(False, description="Safety-Warnung für Live")

    # Phase 87: Risk-Severity Integration
    risk_status: Literal["green", "yellow", "red"] = Field(
        "green", description="Risk-Ampel: green=OK, yellow=WARNING, red=BREACH"
    )
    risk_severity: Literal["ok", "warning", "breach"] = Field(
        "ok", description="Risk-Severity-Level"
    )
    risk_limit_details: List[dict] = Field(
        default_factory=list,
        description="Limit-Check-Details [{name, value, limit, ratio, severity}]",
    )

    # Detail-Felder (Phase 85)
    run_id: Optional[str] = Field(None, description="Experiment/Run-ID")
    run_type: str = Field("", description="z.B. live_session_shadow")
    env_name: str = Field("", description="Environment-Name")
    symbol: str = Field("", description="Trading-Symbol")
    config: dict = Field(default_factory=dict, description="Session-Config")
    metrics: dict = Field(default_factory=dict, description="Alle Metrics")
    cli_args: List[str] = Field(default_factory=list, description="CLI-Aufruf")
    created_at: Optional[datetime] = Field(None, description="Record-Erstellung")


# =============================================================================
# Service-Funktion: get_recent_live_sessions
# =============================================================================


def get_recent_live_sessions(
    limit: int = 10,
    base_dir: Optional[Path] = None,
) -> List[LiveSessionSummary]:
    """
    Lädt die letzten N Live-Sessions aus der Registry.

    Liest aus der bestehenden Live-Session-Registry (Phase 81) und
    konvertiert die Records in das Dashboard-freundliche LiveSessionSummary-Format.

    Args:
        limit: Maximale Anzahl Sessions (default: 10)
        base_dir: Optionales Override für Registry-Verzeichnis

    Returns:
        Liste von LiveSessionSummary, sortiert nach ended_at/started_at (neueste zuerst).
        Leere Liste falls keine Sessions vorhanden oder Registry nicht erreichbar.

    Note:
        - Robuste Fehlerbehandlung: Bei Registry-Fehlern wird geloggt und
          leere Liste zurückgegeben.
        - Filtert nur relevante Session-Typen (shadow, testnet, paper, live)
        - Technical test sessions werden ggf. übersprungen

    Example:
        >>> sessions = get_recent_live_sessions(limit=5)
        >>> for s in sessions:
        ...     print(f"{s.session_id}: {s.status}")
    """
    try:
        from src.experiments.live_session_registry import (
            list_session_records,
            LiveSessionRecord,
        )
    except ImportError as e:
        logger.warning(
            "Could not import live_session_registry: %s - returning empty list",
            e,
        )
        return []

    try:
        # Lade Records aus der Registry
        # list_session_records sortiert bereits nach Timestamp (neueste zuerst)
        kwargs = {"limit": limit}
        if base_dir is not None:
            kwargs["base_dir"] = base_dir

        records: List[LiveSessionRecord] = list_session_records(**kwargs)

        # Konvertiere zu LiveSessionSummary
        summaries: List[LiveSessionSummary] = []
        for record in records:
            summary = _record_to_summary(record)
            if summary is not None:
                summaries.append(summary)

        # Sortiere nach ended_at (falls vorhanden), sonst started_at
        # Neueste zuerst
        summaries.sort(
            key=lambda s: s.ended_at or s.started_at,
            reverse=True,
        )

        return summaries[:limit]

    except Exception as e:
        logger.warning(
            "Error loading live sessions from registry: %s - returning empty list",
            e,
            exc_info=True,
        )
        return []


def _extract_risk_status_from_metrics(metrics: dict) -> tuple:
    """
    Extrahiert risk_status und risk_severity aus Metrics.

    Versucht verschiedene Quellen:
    1. Direkt in metrics["risk_status"] / metrics["risk_severity"]
    2. In metrics["risk_check"]["severity"]
    3. Default: green/ok

    Returns:
        Tuple (risk_status, risk_severity)
    """
    risk_status = "green"
    risk_severity = "ok"

    if not metrics:
        return risk_status, risk_severity

    # Direkte Felder
    if "risk_status" in metrics:
        rs = metrics["risk_status"]
        if rs in ("green", "yellow", "red"):
            risk_status = rs
            # Severity ableiten
            risk_severity = {"green": "ok", "yellow": "warning", "red": "breach"}.get(rs, "ok")

    if "risk_severity" in metrics:
        sev = metrics["risk_severity"]
        if sev in ("ok", "warning", "breach"):
            risk_severity = sev
            # Status ableiten falls nicht gesetzt
            if "risk_status" not in metrics:
                risk_status = {"ok": "green", "warning": "yellow", "breach": "red"}.get(
                    sev, "green"
                )

    # Aus risk_check Sub-Dict
    risk_check = metrics.get("risk_check", {})
    if isinstance(risk_check, dict):
        if "severity" in risk_check:
            sev = risk_check["severity"]
            if sev in ("ok", "warning", "breach"):
                risk_severity = sev
                risk_status = {"ok": "green", "warning": "yellow", "breach": "red"}.get(
                    sev, "green"
                )

    return risk_status, risk_severity


def _record_to_summary(record) -> Optional[LiveSessionSummary]:
    """
    Konvertiert einen LiveSessionRecord in ein LiveSessionSummary.

    Args:
        record: LiveSessionRecord aus der Registry

    Returns:
        LiveSessionSummary oder None bei Konvertierungsfehler
    """
    try:
        # Environment aus env_name + symbol zusammenbauen
        env_parts = []
        if record.env_name:
            env_parts.append(record.env_name)
        if record.symbol:
            env_parts.append(record.symbol)
        environment = " / ".join(env_parts) if env_parts else ""

        # Metrics extrahieren
        metrics = record.metrics or {}
        realized_pnl = metrics.get("realized_pnl")
        max_drawdown = metrics.get("max_drawdown")
        num_orders = metrics.get("num_orders") or metrics.get("num_trades")

        # num_orders als int wenn vorhanden
        if num_orders is not None:
            num_orders = int(num_orders)

        # Status normalisieren (auf erlaubte Werte)
        status = record.status
        if status not in ("started", "completed", "failed", "aborted"):
            status = "completed" if record.finished_at else "started"

        # Phase 85: Duration und Live-Warnung
        mode = record.mode or "unknown"
        duration = compute_duration_seconds(record.started_at, record.finished_at)
        is_live_warning = mode == "live"

        # Phase 87: Risk-Status aus Metrics extrahieren
        risk_status, risk_severity = _extract_risk_status_from_metrics(metrics)

        return LiveSessionSummary(
            session_id=record.session_id,
            started_at=record.started_at,
            ended_at=record.finished_at,
            mode=mode,
            environment=environment,
            status=status,
            realized_pnl=realized_pnl,
            max_drawdown=max_drawdown,
            num_orders=num_orders,
            report_path=None,
            notes=record.error,
            duration_seconds=duration,
            is_live_warning=is_live_warning,
            risk_status=risk_status,
            risk_severity=risk_severity,
        )
    except Exception as e:
        logger.warning(
            "Error converting record %s to summary: %s",
            getattr(record, "session_id", "unknown"),
            e,
        )
        return None


def _extract_limit_details_from_metrics(metrics: dict) -> List[dict]:
    """
    Extrahiert Limit-Check-Details aus Metrics.

    Sucht in metrics["risk_check"]["limit_details"] oder metrics["limit_details"].

    Returns:
        Liste von Dicts: [{name, value, limit, ratio, severity}]
    """
    details: List[dict] = []

    if not metrics:
        return details

    # Suche in verschiedenen Quellen
    limit_details = None

    if "limit_details" in metrics:
        limit_details = metrics["limit_details"]
    elif "risk_check" in metrics and isinstance(metrics["risk_check"], dict):
        limit_details = metrics["risk_check"].get("limit_details")

    if not limit_details or not isinstance(limit_details, list):
        return details

    for item in limit_details:
        if not isinstance(item, dict):
            continue

        detail = {
            "name": item.get("limit_name", item.get("name", "unknown")),
            "value": item.get("current_value", item.get("value", 0.0)),
            "limit": item.get("limit_value", item.get("limit", 0.0)),
            "ratio": item.get("ratio", 0.0),
            "severity": item.get("severity", "ok"),
        }
        details.append(detail)

    return details


def _record_to_detail(record) -> Optional[LiveSessionDetail]:
    """
    Konvertiert einen LiveSessionRecord in ein LiveSessionDetail (Phase 85).

    Args:
        record: LiveSessionRecord aus der Registry

    Returns:
        LiveSessionDetail oder None bei Konvertierungsfehler
    """
    try:
        # Environment aus env_name + symbol zusammenbauen
        env_parts = []
        if record.env_name:
            env_parts.append(record.env_name)
        if record.symbol:
            env_parts.append(record.symbol)
        environment = " / ".join(env_parts) if env_parts else ""

        # Metrics extrahieren
        metrics = dict(record.metrics) if record.metrics else {}
        realized_pnl = metrics.get("realized_pnl")
        max_drawdown = metrics.get("max_drawdown")
        num_orders = metrics.get("num_orders") or metrics.get("num_trades")

        if num_orders is not None:
            num_orders = int(num_orders)

        # Status normalisieren
        status = record.status
        if status not in ("started", "completed", "failed", "aborted"):
            status = "completed" if record.finished_at else "started"

        mode = record.mode or "unknown"
        duration = compute_duration_seconds(record.started_at, record.finished_at)
        is_live_warning = mode == "live"

        # Phase 87: Risk-Status und Limit-Details aus Metrics extrahieren
        risk_status, risk_severity = _extract_risk_status_from_metrics(metrics)
        risk_limit_details = _extract_limit_details_from_metrics(metrics)

        return LiveSessionDetail(
            session_id=record.session_id,
            started_at=record.started_at,
            ended_at=record.finished_at,
            mode=mode,
            environment=environment,
            status=status,
            realized_pnl=realized_pnl,
            max_drawdown=max_drawdown,
            num_orders=num_orders,
            notes=record.error,
            duration_seconds=duration,
            is_live_warning=is_live_warning,
            # Phase 87: Risk-Fields
            risk_status=risk_status,
            risk_severity=risk_severity,
            risk_limit_details=risk_limit_details,
            # Detail-Felder
            run_id=record.run_id,
            run_type=record.run_type or "",
            env_name=record.env_name or "",
            symbol=record.symbol or "",
            config=dict(record.config) if record.config else {},
            metrics=metrics,
            cli_args=list(record.cli_args) if record.cli_args else [],
            created_at=record.created_at,
        )
    except Exception as e:
        logger.warning(
            "Error converting record %s to detail: %s",
            getattr(record, "session_id", "unknown"),
            e,
        )
        return None


# =============================================================================
# Phase 85: get_filtered_sessions()
# =============================================================================


def get_filtered_sessions(
    limit: int = 20,
    mode_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> List[LiveSessionSummary]:
    """
    Lädt Sessions mit optionalen Filtern nach Mode und Status (Phase 85).

    Args:
        limit: Maximale Anzahl Sessions (default: 20)
        mode_filter: Filter nach Mode (shadow, testnet, paper, live) oder None für alle
        status_filter: Filter nach Status (completed, failed, aborted, started) oder None
        base_dir: Optionales Override für Registry-Verzeichnis

    Returns:
        Liste von LiveSessionSummary, gefiltert und sortiert (neueste zuerst).

    Example:
        >>> sessions = get_filtered_sessions(mode_filter="shadow", status_filter="completed")
    """
    try:
        from src.experiments.live_session_registry import (
            list_session_records,
            LiveSessionRecord,
        )
    except ImportError as e:
        logger.warning("Could not import live_session_registry: %s - returning empty list", e)
        return []

    try:
        kwargs: Dict[str, Any] = {"limit": limit * 3}  # Mehr laden für Filter
        if base_dir is not None:
            kwargs["base_dir"] = base_dir

        # Status-Filter auf Registry-Ebene wenn möglich
        if status_filter:
            kwargs["status"] = status_filter

        records: List[LiveSessionRecord] = list_session_records(**kwargs)

        # Mode-Filter nachträglich anwenden (nicht in Registry)
        if mode_filter:
            records = [r for r in records if r.mode == mode_filter]

        # Konvertiere zu Summary
        summaries: List[LiveSessionSummary] = []
        for record in records:
            summary = _record_to_summary(record)
            if summary is not None:
                summaries.append(summary)

        # Sortiere nach ended_at/started_at (neueste zuerst)
        summaries.sort(
            key=lambda s: s.ended_at or s.started_at,
            reverse=True,
        )

        return summaries[:limit]

    except Exception as e:
        logger.warning(
            "Error loading filtered sessions: %s - returning empty list",
            e,
            exc_info=True,
        )
        return []


# =============================================================================
# Phase 85: get_session_by_id()
# =============================================================================


def get_session_by_id(
    session_id: str,
    base_dir: Optional[Path] = None,
) -> Optional[LiveSessionDetail]:
    """
    Lädt eine einzelne Session nach ID (Phase 85).

    Args:
        session_id: Die Session-ID zum Suchen
        base_dir: Optionales Override für Registry-Verzeichnis

    Returns:
        LiveSessionDetail oder None wenn nicht gefunden.

    Example:
        >>> detail = get_session_by_id("session_20251208_001")
        >>> if detail:
        ...     print(f"PnL: {detail.realized_pnl}, Config: {detail.config}")
    """
    try:
        from src.experiments.live_session_registry import (
            list_session_records,
            LiveSessionRecord,
        )
    except ImportError as e:
        logger.warning("Could not import live_session_registry: %s", e)
        return None

    try:
        kwargs: Dict[str, Any] = {}
        if base_dir is not None:
            kwargs["base_dir"] = base_dir

        # Alle Records laden und nach ID suchen
        records: List[LiveSessionRecord] = list_session_records(**kwargs)

        for record in records:
            if record.session_id == session_id:
                return _record_to_detail(record)

        logger.info("Session not found: %s", session_id)
        return None

    except Exception as e:
        logger.warning(
            "Error loading session %s: %s",
            session_id,
            e,
            exc_info=True,
        )
        return None


# =============================================================================
# Phase 85: get_session_stats()
# =============================================================================


def get_session_stats(
    base_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Aggregierte Statistiken über alle Sessions (Phase 85).

    Returns:
        Dict mit:
        - total_sessions: Gesamtzahl
        - by_mode: Dict mit Mode-Verteilung
        - by_status: Dict mit Status-Verteilung
        - total_pnl: Summe aller realized_pnl
        - avg_drawdown: Durchschnittlicher max_drawdown

    Example:
        >>> stats = get_session_stats()
        >>> print(f"Total: {stats['total_sessions']}, Shadow: {stats['by_mode'].get('shadow', 0)}")
    """
    try:
        from src.experiments.live_session_registry import get_session_summary
    except ImportError:
        return {
            "total_sessions": 0,
            "by_mode": {},
            "by_status": {},
            "total_pnl": 0.0,
            "avg_drawdown": 0.0,
        }

    try:
        kwargs: Dict[str, Any] = {}
        if base_dir is not None:
            kwargs["base_dir"] = base_dir

        summary = get_session_summary(**kwargs)

        # Mode-Verteilung berechnen (nicht in get_session_summary enthalten)
        from src.experiments.live_session_registry import list_session_records

        records = list_session_records(**kwargs)
        mode_counts: Dict[str, int] = {}
        for r in records:
            mode = r.mode or "unknown"
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

        return {
            "total_sessions": summary.get("num_sessions", 0),
            "by_mode": mode_counts,
            "by_status": summary.get("by_status", {}),
            "total_pnl": summary.get("total_realized_pnl", 0.0),
            "avg_drawdown": summary.get("avg_max_drawdown", 0.0),
        }

    except Exception as e:
        logger.warning("Error getting session stats: %s", e)
        return {
            "total_sessions": 0,
            "by_mode": {},
            "by_status": {},
            "total_pnl": 0.0,
            "avg_drawdown": 0.0,
        }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "LiveSessionSummary",
    "LiveSessionDetail",
    "get_recent_live_sessions",
    "get_filtered_sessions",
    "get_session_by_id",
    "get_session_stats",
    "compute_duration_seconds",
]
