# src/infra/runbooks/registry.py
"""
Peak_Trade: Runbook Registry (Phase 84)
=======================================

Statisches Mapping von Alert-Kombinationen zu Runbooks.

Das Mapping basiert auf:
- category: RISK, EXECUTION, SYSTEM
- source: z.B. "live_risk_severity", "live_risk_limits"
- severity (optional): WARN, CRITICAL

Lookup-Reihenfolge:
1. Exakter Match: (category, source, severity)
2. Ohne Severity: (category, source, None)
3. Nur Category: (category, None, None)
4. Default: Leere Liste
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from .models import RunbookLink

logger = logging.getLogger(__name__)

# =============================================================================
# KONFIGURATION
# =============================================================================

# Base-URL für GitHub-Docs (kann per Environment überschrieben werden)
BASE_DOCS_URL = "https://github.com/rauterfrank-ui/Peak_Trade/blob/main/docs"

# =============================================================================
# RUNBOOK DEFINITIONEN
# =============================================================================

# Alle verfügbaren Runbooks
RUNBOOK_REGISTRY: Dict[str, RunbookLink] = {
    "live_alert_pipeline": RunbookLink(
        id="live_alert_pipeline",
        title="Live Alert Pipeline Runbook",
        url=f"{BASE_DOCS_URL}/runbooks/LIVE_ALERT_PIPELINE_SLACK_EMAIL_RUNBOOK_V1.md",
        description="Alert-Pipeline Konfiguration, Slack/Email-Channels, Troubleshooting",
    ),
    "live_risk_severity": RunbookLink(
        id="live_risk_severity",
        title="Live Risk Severity Runbook",
        url=f"{BASE_DOCS_URL}/runbooks/LIVE_RISK_SEVERITY_INTEGRATION.md",
        description="Risk-Severity-Transitions (GREEN/YELLOW/RED), Alert-Handling",
    ),
    "live_risk_limits": RunbookLink(
        id="live_risk_limits",
        title="Live Risk Limits Runbook",
        url=f"{BASE_DOCS_URL}/LIVE_RISK_LIMITS.md",
        description="Hard/Soft Limits, Daily Loss, Drawdown, Position Sizing",
    ),
    "live_deployment": RunbookLink(
        id="live_deployment",
        title="Live Deployment Playbook",
        url=f"{BASE_DOCS_URL}/LIVE_DEPLOYMENT_PLAYBOOK.md",
        description="Deployment-Checkliste, Pre-Flight-Checks, Rollback-Verfahren",
    ),
    "incident_drills": RunbookLink(
        id="incident_drills",
        title="Incident Drills & Simulation",
        url=f"{BASE_DOCS_URL}/INCIDENT_SIMULATION_AND_DRILLS.md",
        description="Incident-Szenarien, Drill-Protokolle, Recovery-Verfahren",
    ),
}

# =============================================================================
# MAPPING: (category, source, severity) → List[runbook_id]
# =============================================================================

# Key: (category_name, source_pattern, severity_name_or_none)
# Value: Liste von Runbook-IDs
_ALERT_RUNBOOK_MAPPING: Dict[Tuple[str, Optional[str], Optional[str]], List[str]] = {
    # RISK + live_risk_severity
    ("RISK", "live_risk_severity", "CRITICAL"): [
        "live_risk_severity",
        "live_alert_pipeline",
        "incident_drills",
    ],
    ("RISK", "live_risk_severity", "WARN"): [
        "live_risk_severity",
        "live_alert_pipeline",
    ],
    ("RISK", "live_risk_severity", None): [
        "live_risk_severity",
        "live_alert_pipeline",
    ],
    # RISK + live_risk_limits
    ("RISK", "live_risk_limits", "CRITICAL"): [
        "live_risk_limits",
        "live_alert_pipeline",
        "incident_drills",
    ],
    ("RISK", "live_risk_limits", "WARN"): [
        "live_risk_limits",
        "live_alert_pipeline",
    ],
    ("RISK", "live_risk_limits", None): [
        "live_risk_limits",
        "live_alert_pipeline",
    ],
    # RISK Fallback (andere Sources)
    ("RISK", None, "CRITICAL"): [
        "live_risk_limits",
        "live_alert_pipeline",
        "incident_drills",
    ],
    ("RISK", None, "WARN"): [
        "live_risk_limits",
        "live_alert_pipeline",
    ],
    ("RISK", None, None): [
        "live_risk_limits",
        "live_alert_pipeline",
    ],
    # EXECUTION
    ("EXECUTION", None, "CRITICAL"): [
        "live_deployment",
        "live_alert_pipeline",
        "incident_drills",
    ],
    ("EXECUTION", None, "WARN"): [
        "live_deployment",
        "live_alert_pipeline",
    ],
    ("EXECUTION", None, None): [
        "live_deployment",
        "live_alert_pipeline",
    ],
    # SYSTEM
    ("SYSTEM", None, "CRITICAL"): [
        "live_deployment",
        "live_alert_pipeline",
        "incident_drills",
    ],
    ("SYSTEM", None, "WARN"): [
        "live_alert_pipeline",
    ],
    ("SYSTEM", None, None): [
        "live_alert_pipeline",
    ],
}


# =============================================================================
# RESOLVER FUNCTION
# =============================================================================


def resolve_runbooks_for_alert(alert: Any) -> List[RunbookLink]:
    """
    Bestimmt passende Runbooks basierend auf Alert-Attributen.

    Lookup-Reihenfolge:
    1. Exakter Match: (category, source, severity)
    2. Source-Match ohne Severity: (category, source, None)
    3. Category-Match mit Severity: (category, None, severity)
    4. Category-Fallback: (category, None, None)
    5. Default: Leere Liste

    Args:
        alert: AlertMessage-Objekt oder Dict mit category, source, severity

    Returns:
        Liste von RunbookLink-Objekten (kann leer sein)
    """
    # Alert-Attribute extrahieren
    if hasattr(alert, "category"):
        # AlertMessage-Objekt
        category = alert.category.value if hasattr(alert.category, "value") else str(alert.category)
        source = alert.source
        severity = alert.severity.name if hasattr(alert.severity, "name") else str(alert.severity)
    elif isinstance(alert, dict):
        # Dict
        category = alert.get("category", "")
        source = alert.get("source", "")
        severity = alert.get("severity", "")
    else:
        logger.warning(f"Cannot resolve runbooks for unknown alert type: {type(alert)}")
        return []

    # Normalisieren
    category = category.upper() if category else ""
    severity = severity.upper() if severity else None

    # Lookup-Reihenfolge
    lookup_keys = [
        (category, source, severity),      # Exakt
        (category, source, None),          # Ohne Severity
        (category, None, severity),        # Ohne Source
        (category, None, None),            # Nur Category
    ]

    runbook_ids: List[str] = []
    for key in lookup_keys:
        if key in _ALERT_RUNBOOK_MAPPING:
            runbook_ids = _ALERT_RUNBOOK_MAPPING[key]
            break

    # IDs zu RunbookLinks auflösen
    runbooks: List[RunbookLink] = []
    for rb_id in runbook_ids:
        if rb_id in RUNBOOK_REGISTRY:
            runbooks.append(RUNBOOK_REGISTRY[rb_id])
        else:
            logger.warning(f"Runbook ID '{rb_id}' not found in registry")

    return runbooks


def get_all_runbooks() -> List[RunbookLink]:
    """
    Gibt alle registrierten Runbooks zurück.

    Returns:
        Liste aller RunbookLink-Objekte
    """
    return list(RUNBOOK_REGISTRY.values())


def get_runbook_by_id(runbook_id: str) -> Optional[RunbookLink]:
    """
    Gibt ein Runbook nach ID zurück.

    Args:
        runbook_id: Runbook-ID

    Returns:
        RunbookLink oder None wenn nicht gefunden
    """
    return RUNBOOK_REGISTRY.get(runbook_id)
