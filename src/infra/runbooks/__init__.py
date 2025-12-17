# src/infra/runbooks/__init__.py
"""
Peak_Trade: Runbook Registry (Phase 84)
=======================================

Zentrale Verwaltung von Incident-Runbooks für Alert-Verlinkung.

Features:
- RunbookLink Dataclass für Runbook-Metadaten
- Statisches Mapping: Alert (category, source) → Runbooks
- resolve_runbooks_for_alert() für automatische Zuordnung

Usage:
    from src.infra.runbooks import resolve_runbooks_for_alert, RunbookLink

    # Runbooks für einen Alert ermitteln
    runbooks = resolve_runbooks_for_alert(alert)
    for rb in runbooks:
        print(f"{rb.title}: {rb.url}")
"""
from .models import RunbookLink
from .registry import RUNBOOK_REGISTRY, get_all_runbooks, resolve_runbooks_for_alert

__all__ = [
    "RUNBOOK_REGISTRY",
    "RunbookLink",
    "get_all_runbooks",
    "resolve_runbooks_for_alert",
]
