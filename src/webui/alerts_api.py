# src/webui/alerts_api.py
"""
Peak_Trade: Alerts Web-API (Phase 83)
=====================================

Backend-Funktionen für die Alert-Historie im Web-Dashboard.

Features:
- Alert-Liste mit Filtern (Severity, Category, Zeitfenster)
- Status-Statistiken (Kacheln)
- Pagination-Support

Endpoints (registriert in app.py):
- GET /live/alerts → HTML-View
- GET /api/live/alerts → JSON-API
- GET /api/live/alerts/stats → Statistiken
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class RunbookSummary(BaseModel):
    """Zusammenfassung eines Runbook-Links für die API (Phase 84)."""

    id: str = Field(description="Eindeutige Runbook-ID")
    title: str = Field(description="Runbook-Titel")
    url: str = Field(description="URL zum Runbook")


class AlertSummary(BaseModel):
    """Zusammenfassung eines Alerts für die API."""

    id: str = Field(description="Eindeutige Alert-ID")
    title: str = Field(description="Alert-Titel")
    body: str = Field(description="Alert-Body (ggf. gekürzt)")
    severity: str = Field(description="Severity: INFO, WARN, CRITICAL")
    category: str = Field(description="Category: RISK, EXECUTION, SYSTEM")
    source: str = Field(description="Quelle des Alerts")
    session_id: str | None = Field(None, description="Session-ID falls vorhanden")
    timestamp: str = Field(description="ISO-Timestamp")
    timestamp_display: str = Field(description="Formatierter Timestamp für UI")
    runbooks: list[RunbookSummary] = Field(default_factory=list, description="Verlinkte Runbooks (Phase 84)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "alert_abc123",
                "title": "Risk Severity changed: GREEN → YELLOW",
                "body": "⚠️ WARNUNG: Risk-Status ist auf YELLOW gewechselt...",
                "severity": "WARN",
                "category": "RISK",
                "source": "live_risk_severity",
                "session_id": "shadow_2025-12-09_14-30-00",
                "timestamp": "2025-12-09T14:30:00+00:00",
                "timestamp_display": "09.12.2025 14:30:00",
                "runbooks": [
                    {"id": "live_risk_severity", "title": "Live Risk Severity Runbook", "url": "https://..."},
                ],
            }
        }


class AlertStats(BaseModel):
    """Statistiken über Alerts für Status-Kacheln."""

    total: int = Field(description="Gesamtzahl Alerts im Zeitfenster")
    by_severity: dict[str, int] = Field(description="Anzahl nach Severity")
    by_category: dict[str, int] = Field(description="Anzahl nach Category")
    sessions_with_alerts: int = Field(description="Anzahl Sessions mit Alerts")
    last_critical: dict[str, Any] | None = Field(
        None, description="Letzter CRITICAL Alert"
    )
    hours: int = Field(description="Betrachtetes Zeitfenster in Stunden")


class AlertListResponse(BaseModel):
    """Response für Alert-Liste."""

    alerts: list[AlertSummary]
    total: int = Field(description="Gesamtzahl (ungefiltert)")
    filtered: int = Field(description="Anzahl nach Filter")
    limit: int = Field(description="Angewandtes Limit")
    filters: dict[str, Any] = Field(description="Angewandte Filter")


# =============================================================================
# DATA FUNCTIONS
# =============================================================================


def _format_timestamp(dt: datetime) -> str:
    """Formatiert Datetime für UI-Anzeige."""
    return dt.strftime("%d.%m.%Y %H:%M:%S")


def _truncate_body(body: str, max_length: int = 200) -> str:
    """Kürzt Body-Text für Tabellenansicht."""
    if len(body) <= max_length:
        return body
    return body[:max_length].rsplit(" ", 1)[0] + "..."


def get_alerts_for_ui(
    limit: int = 100,
    hours: int | None = 24,
    severity: list[str] | None = None,
    category: list[str] | None = None,
    session_id: str | None = None,
) -> AlertListResponse:
    """
    Lädt Alerts für die UI mit Filtern.

    Args:
        limit: Maximale Anzahl Alerts
        hours: Zeitfenster in Stunden
        severity: Filter nach Severity (z.B. ["WARN", "CRITICAL"])
        category: Filter nach Category (z.B. ["RISK"])
        session_id: Filter nach Session-ID

    Returns:
        AlertListResponse mit formatierten Alerts
    """
    try:
        from src.live.alert_storage import get_alert_stats, list_recent_alerts
    except ImportError:
        # Fallback wenn Storage nicht verfügbar
        return AlertListResponse(
            alerts=[],
            total=0,
            filtered=0,
            limit=limit,
            filters={"hours": hours, "severity": severity, "category": category},
        )

    # Alerts laden
    stored_alerts = list_recent_alerts(
        limit=limit,
        hours=hours or 24,
        severity=severity,
        category=category,
    )

    # Session-Filter anwenden (falls Storage nicht unterstützt)
    if session_id:
        stored_alerts = [a for a in stored_alerts if a.session_id == session_id]

    # Zu UI-Modellen konvertieren
    alerts: list[AlertSummary] = []
    for alert in stored_alerts:
        # Phase 84: Runbooks aus Context extrahieren
        runbook_dicts = alert.context.get("runbooks", [])
        runbooks = [
            RunbookSummary(
                id=rb.get("id", ""),
                title=rb.get("title", ""),
                url=rb.get("url", ""),
            )
            for rb in runbook_dicts
            if isinstance(rb, dict)
        ]

        alerts.append(
            AlertSummary(
                id=alert.id,
                title=alert.title,
                body=_truncate_body(alert.body),
                severity=alert.severity,
                category=alert.category,
                source=alert.source,
                session_id=alert.session_id,
                timestamp=alert.timestamp.isoformat(),
                timestamp_display=_format_timestamp(alert.timestamp),
                runbooks=runbooks,
            )
        )

    # Stats für Total-Zählung
    stats = get_alert_stats(hours=hours or 24)

    return AlertListResponse(
        alerts=alerts,
        total=stats.get("total", len(alerts)),
        filtered=len(alerts),
        limit=limit,
        filters={
            "hours": hours,
            "severity": severity,
            "category": category,
            "session_id": session_id,
        },
    )


def get_alert_statistics(hours: int = 24) -> AlertStats:
    """
    Lädt Alert-Statistiken für Status-Kacheln.

    Args:
        hours: Zeitfenster in Stunden

    Returns:
        AlertStats mit aggregierten Daten
    """
    try:
        from src.live.alert_storage import get_alert_stats
    except ImportError:
        # Fallback wenn Storage nicht verfügbar
        return AlertStats(
            total=0,
            by_severity={"INFO": 0, "WARN": 0, "CRITICAL": 0},
            by_category={"RISK": 0, "EXECUTION": 0, "SYSTEM": 0},
            sessions_with_alerts=0,
            last_critical=None,
            hours=hours,
        )

    stats = get_alert_stats(hours=hours)

    return AlertStats(
        total=stats.get("total", 0),
        by_severity=stats.get("by_severity", {}),
        by_category=stats.get("by_category", {}),
        sessions_with_alerts=stats.get("sessions_with_alerts", 0),
        last_critical=stats.get("last_critical"),
        hours=stats.get("hours", hours),
    )


def get_alerts_template_context(
    limit: int = 100,
    hours: int | None = 24,
    severity: list[str] | None = None,
    category: list[str] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Baut Template-Context für die Alert-Historie-Seite.

    Returns:
        Dict für Jinja2-Template
    """
    # Alerts und Stats laden
    alert_response = get_alerts_for_ui(
        limit=limit,
        hours=hours,
        severity=severity,
        category=category,
        session_id=session_id,
    )
    stats = get_alert_statistics(hours=hours or 24)

    # UI-spezifische Berechnungen
    has_critical = stats.by_severity.get("CRITICAL", 0) > 0
    has_warn = stats.by_severity.get("WARN", 0) > 0

    return {
        "alerts": [a.model_dump() for a in alert_response.alerts],
        "stats": stats.model_dump(),
        "total": alert_response.total,
        "filtered": alert_response.filtered,
        "limit": limit,
        "filters": {
            "hours": hours,
            "severity": severity or [],
            "category": category or [],
            "session_id": session_id or "",
        },
        "has_alerts": len(alert_response.alerts) > 0,
        "has_critical": has_critical,
        "has_warn": has_warn,
        # Severity-Optionen für Filter-UI
        "severity_options": ["INFO", "WARN", "CRITICAL"],
        "category_options": ["RISK", "EXECUTION", "SYSTEM"],
        "hours_options": [2, 6, 24, 48, 168],  # 2h, 6h, 24h, 48h, 7d
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "AlertListResponse",
    "AlertStats",
    "AlertSummary",
    # Models
    "RunbookSummary",
    "get_alert_statistics",
    # Functions
    "get_alerts_for_ui",
    "get_alerts_template_context",
]
