# src/infra/escalation/models.py
"""
Peak_Trade: Escalation Models (Phase 85)
=========================================

Datenmodelle für die Eskalations-Integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class EscalationEvent:
    """
    Repräsentiert ein Ereignis, das potenziell eskaliert werden soll.

    Attributes:
        alert_id: Eindeutige ID des zugehörigen Alerts
        severity: Severity-String (z.B. "CRITICAL", "WARN", "INFO")
        alert_type: Kategorie des Alerts (z.B. "RISK", "EXECUTION", "SYSTEM")
        summary: Kurze Zusammenfassung / Titel
        details: Optionale zusätzliche Informationen
        symbol: Optionales Trading-Symbol (z.B. "BTC/EUR")
        session_id: Optionale Session-ID für Kontext
        created_at: Zeitstempel der Erstellung (UTC)
    """

    alert_id: str
    severity: str
    alert_type: str
    summary: str
    details: Optional[Dict[str, Any]] = None
    symbol: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert EscalationEvent zu Dict für Serialisierung."""
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "alert_type": self.alert_type,
            "summary": self.summary,
            "details": self.details or {},
            "symbol": self.symbol,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EscalationEvent":
        """Erstellt EscalationEvent aus Dict."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        return cls(
            alert_id=data.get("alert_id", ""),
            severity=data.get("severity", ""),
            alert_type=data.get("alert_type", ""),
            summary=data.get("summary", ""),
            details=data.get("details"),
            symbol=data.get("symbol"),
            session_id=data.get("session_id"),
            created_at=created_at,
        )

    def __repr__(self) -> str:
        return (
            f"EscalationEvent(alert_id={self.alert_id!r}, "
            f"severity={self.severity!r}, summary={self.summary!r})"
        )


@dataclass
class EscalationTarget:
    """
    Repräsentiert ein On-Call-Ziel für Eskalationen.

    Attributes:
        name: Lesbare Bezeichnung (z.B. "Primary Risk On-Call")
        provider: Provider-Typ (z.B. "null", "pagerduty_stub", "pagerduty")
        routing_key: Optionaler Routing-/Service-Key für den Provider
        min_severity: Minimale Severity für Eskalation an dieses Target
        enabled: Ob dieses Target aktiv ist
    """

    name: str
    provider: str = "null"
    routing_key: Optional[str] = None
    min_severity: str = "CRITICAL"
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert EscalationTarget zu Dict."""
        return {
            "name": self.name,
            "provider": self.provider,
            "routing_key": self.routing_key,
            "min_severity": self.min_severity,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EscalationTarget":
        """Erstellt EscalationTarget aus Dict."""
        return cls(
            name=data.get("name", "default"),
            provider=data.get("provider", "null"),
            routing_key=data.get("routing_key"),
            min_severity=data.get("min_severity", "CRITICAL"),
            enabled=data.get("enabled", True),
        )

    def __repr__(self) -> str:
        return (
            f"EscalationTarget(name={self.name!r}, "
            f"provider={self.provider!r}, min_severity={self.min_severity!r})"
        )
