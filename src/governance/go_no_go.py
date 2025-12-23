"""
Go/No-Go Governance Module für Peak_Trade.

Dieses Modul verwaltet den Governance-Status für Features und ermöglicht
die programmgesteuerte Prüfung, ob ein Feature für ein bestimmtes Jahr
freigegeben ist.

Referenz: docs/GO_NO_GO_2026_LIVE_ALERTS_CLUSTER_82_85.md
"""

from __future__ import annotations

from typing import Literal, Mapping

GovernanceStatus = Literal["locked", "approved_2026", "approved_2027", "unknown"]

_FEATURE_STATUS_MAP: Mapping[str, GovernanceStatus] = {
    # Alerts & Incident-Handling Cluster 82–85:
    # Laut GO_NO_GO_2026_LIVE_ALERTS_CLUSTER_82_85.md für 2026 freigegeben.
    "live_alerts_cluster_82_85": "approved_2026",
    # Live-Order-Execution:
    # Laut demselben Dokument explizit gesperrt, separate Entscheidung nötig.
    "live_order_execution": "locked",
}


def get_governance_status(feature_key: str) -> GovernanceStatus:
    """
    Liefert den Governance-Status für ein Feature.

    Args:
        feature_key: Der eindeutige Schlüssel des Features.

    Returns:
        Der Governance-Status des Features.

    Status-Bedeutung (v1):
        - "locked":        Feature darf (noch) nicht live verwendet werden.
        - "approved_2026": Feature ist für das Ziel-Jahr 2026 freigegeben.
        - "approved_2027": Platzhalter für zukünftige Freigaben.
        - "unknown":       Feature ist (noch) nicht in der Governance hinterlegt.

    Example:
        >>> get_governance_status("live_alerts_cluster_82_85")
        'approved_2026'
        >>> get_governance_status("live_order_execution")
        'locked'
        >>> get_governance_status("unknown_feature")
        'unknown'
    """
    return _FEATURE_STATUS_MAP.get(feature_key, "unknown")


def is_feature_approved_for_year(feature_key: str, year: int) -> bool:
    """
    Gibt True zurück, wenn das Feature für das angefragte Jahr freigegeben ist.

    Args:
        feature_key: Der eindeutige Schlüssel des Features.
        year: Das Jahr, für das die Freigabe geprüft werden soll.

    Returns:
        True wenn das Feature für das angegebene Jahr freigegeben ist,
        False sonst.

    Aktuelle Regeln (v1):
        - "locked"  → immer False
        - "unknown" → immer False
        - "approved_<YYYY>" → True genau dann, wenn year == YYYY

    Example:
        >>> is_feature_approved_for_year("live_alerts_cluster_82_85", 2026)
        True
        >>> is_feature_approved_for_year("live_alerts_cluster_82_85", 2025)
        False
        >>> is_feature_approved_for_year("live_order_execution", 2026)
        False
    """
    status = get_governance_status(feature_key)
    if status in ("locked", "unknown"):
        return False

    if status.startswith("approved_"):
        try:
            approved_year = int(status.split("_", maxsplit=1)[1])
        except (IndexError, ValueError):
            return False
        return year == approved_year

    return False


# P0 Drill: CODEOWNERS+MergeQueue enforcement (2025-12-23T17:37:04)
