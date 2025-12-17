# src/infra/escalation/__init__.py
"""
Peak_Trade: Escalation & On-Call Integration (Phase 85)
========================================================

Optionale Eskalations-Schicht für kritische Alerts.

Features:
- EscalationEvent / EscalationTarget Datenmodelle
- Provider-Abstraktion (Null, PagerDuty-like Stub)
- EscalationManager mit Config-Gating
- Sichere Integration: Fehler blockieren niemals Alerts

Usage:
    from src.infra.escalation import (
        EscalationEvent,
        EscalationTarget,
        EscalationManager,
        build_escalation_manager_from_config,
    )

    # Manager aus Config erstellen
    manager = build_escalation_manager_from_config(config, environment="live")

    # Event eskalieren (nur wenn kritisch + enabled)
    event = EscalationEvent(
        alert_id="alert_123",
        severity="CRITICAL",
        alert_type="RISK",
        summary="Risk Severity RED",
        details={"old_status": "yellow", "new_status": "red"},
    )
    manager.maybe_escalate(event)
"""
from .manager import EscalationManager, build_escalation_manager_from_config
from .models import EscalationEvent, EscalationTarget
from .providers import (
    EscalationProvider,
    NullEscalationProvider,
    PagerDutyLikeProviderStub,
)

__all__ = [
    # Models
    "EscalationEvent",
    # Manager
    "EscalationManager",
    # Providers
    "EscalationProvider",
    "EscalationTarget",
    "NullEscalationProvider",
    "PagerDutyLikeProviderStub",
    "build_escalation_manager_from_config",
]



