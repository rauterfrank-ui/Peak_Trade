"""
InfoStream v1 – Collector-Modul.

Sammelt Daten aus verschiedenen Quellen und erzeugt normierte IntelEvent-Objekte.

Unterstützte Quellen (v1):
- TestHealth Reports (reports/test_health/<run_id>/summary.json)

Geplante Quellen (v2+):
- Trigger-Training Sessions
- Offline-Realtime Pipeline Runs
- Macro-Reports

Verwendung:
    from src.meta.infostream.collector import build_event_from_test_health_report, save_intel_event

    event = build_event_from_test_health_report(Path("reports/test_health/20251211_143920_daily_quick"))
    save_intel_event(event, Path("reports/infostream/events"))
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .models import IntelEvent, SeverityLevel

logger = logging.getLogger(__name__)


def build_event_from_test_health_report(report_dir: Path) -> IntelEvent:
    """
    Erzeugt ein IntelEvent aus einem TestHealth-Report-Verzeichnis.

    Parameters
    ----------
    report_dir : Path
        Pfad zum Report-Verzeichnis, z.B. reports/test_health/20251211_143920_daily_quick/
        Erwartet eine Datei summary.json (oder summary_stats.json) im Ordner.

    Returns
    -------
    IntelEvent
        Das generierte Event

    Raises
    ------
    FileNotFoundError
        Wenn keine summary.json gefunden wird
    ValueError
        Wenn das JSON nicht parsbar ist

    Notes
    -----
    Struktur von summary.json (TestHealthSummary):
        - health_score: float (0-100)
        - passed_checks: int
        - failed_checks: int
        - skipped_checks: int
        - profile_name: str
        - started_at: str (ISO)
        - finished_at: str (ISO)
        - trigger_violations: list (optional)
        - strategy_coverage: dict (optional)
        - switch_sanity: dict (optional)

    TODO: Falls Keys abweichen, defensive Defaults einsetzen.
    """
    # Versuche summary.json oder summary_stats.json zu finden
    summary_path = report_dir / "summary.json"
    if not summary_path.exists():
        summary_path = report_dir / "summary_stats.json"

    if not summary_path.exists():
        raise FileNotFoundError(
            f"Keine summary.json oder summary_stats.json gefunden in: {report_dir}"
        )

    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Fehler beim Parsen von {summary_path}: {e}")

    # Daten extrahieren mit defensiven Defaults
    health_score = data.get("health_score", 0.0)
    passed_checks = data.get("passed_checks", 0)
    failed_checks = data.get("failed_checks", 0)
    skipped_checks = data.get("skipped_checks", 0)
    total_checks = passed_checks + failed_checks + skipped_checks
    profile_name = data.get("profile_name", "unknown")

    # Exit-Code simulieren basierend auf failed_checks
    # (summary.json hat keinen expliziten exit_code)
    exit_code = 0 if failed_checks == 0 else 1

    # Trigger-Violations
    trigger_violations = data.get("trigger_violations", [])
    num_violations = len(trigger_violations) if isinstance(trigger_violations, list) else 0

    # Event-ID generieren
    event_id = f"INF-{report_dir.name}"

    # Severity-Heuristik
    severity: SeverityLevel = "info"
    if exit_code >= 2:
        severity = "error"
    elif exit_code == 1:
        severity = "warning"
    elif num_violations > 0:
        severity = "warning"

    # Summary-Text erstellen
    summary_parts = [f"Health-Score {health_score:.1f}/100"]
    if failed_checks == 0:
        summary_parts.append("alle Core-Checks bestanden")
    else:
        summary_parts.append(f"{failed_checks} Check(s) fehlgeschlagen")
    if num_violations > 0:
        summary_parts.append(f"{num_violations} Trigger-Violation(s)")

    summary_text = f"TestHealth-Run für Profil {profile_name}: " + ", ".join(summary_parts) + "."

    # Details als Liste
    details = [
        f"Profile: {profile_name}",
        f"Health-Score: {health_score:.1f}/100.0",
        f"Passed Checks: {passed_checks}",
        f"Failed Checks: {failed_checks}",
        f"Total Checks: {total_checks}",
    ]

    if num_violations > 0:
        details.append(f"Trigger-Violations: {num_violations}")

    # Strategy-Coverage info
    strategy_coverage = data.get("strategy_coverage", {})
    if strategy_coverage and strategy_coverage.get("enabled"):
        cov_healthy = strategy_coverage.get("is_healthy", True)
        details.append(f"Strategy-Coverage: {'OK' if cov_healthy else 'Violations'}")

    # Switch-Sanity info
    switch_sanity = data.get("switch_sanity", {})
    if switch_sanity and switch_sanity.get("enabled"):
        sanity_ok = switch_sanity.get("is_ok", True)
        details.append(f"Switch-Sanity: {'OK' if sanity_ok else 'Violations'}")

    # Links
    links = [str(report_dir)]

    # Tags
    tags = ["test_health", profile_name]
    if num_violations > 0:
        tags.append("violations")
    if failed_checks == 0 and num_violations == 0:
        tags.append("healthy")
    else:
        tags.append("degraded")

    # Created-At: Versuche aus Daten zu extrahieren, sonst jetzt
    created_at_str = data.get("started_at") or data.get("finished_at")
    if created_at_str:
        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = datetime.now()
    else:
        created_at = datetime.now()

    return IntelEvent(
        event_id=event_id,
        source="test_health_automation",
        category="test_automation",
        severity=severity,
        created_at=created_at,
        summary=summary_text,
        details=details,
        links=links,
        tags=tags,
        status="new",
        # Legacy-Felder
        topic=f"TestHealth: {profile_name}",
        importance=3 if severity == "info" else (4 if severity == "warning" else 5),
        payload={"health_score": health_score, "profile": profile_name, "raw_data": data},
    )


def save_intel_event(event: IntelEvent, base_dir: Path) -> Path:
    """
    Speichert ein IntelEvent als JSON unter base_dir/<event_id>.json.

    Parameters
    ----------
    event : IntelEvent
        Das zu speichernde Event
    base_dir : Path
        Basis-Verzeichnis, z.B. reports/infostream/events

    Returns
    -------
    Path
        Pfad zur gespeicherten JSON-Datei
    """
    base_dir.mkdir(parents=True, exist_ok=True)

    output_path = base_dir / f"{event.event_id}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(event.to_dict(), f, indent=2, ensure_ascii=False)

    logger.info(f"IntelEvent gespeichert: {output_path}")
    return output_path


def load_intel_event(event_path: Path) -> IntelEvent:
    """
    Lädt ein IntelEvent aus einer JSON-Datei.

    Parameters
    ----------
    event_path : Path
        Pfad zur JSON-Datei

    Returns
    -------
    IntelEvent
        Das geladene Event
    """
    with open(event_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return IntelEvent.from_dict(data)


def find_unprocessed_events(events_dir: Path) -> list[IntelEvent]:
    """
    Findet alle Events mit status="new" im Events-Verzeichnis.

    Parameters
    ----------
    events_dir : Path
        Verzeichnis mit Event-JSON-Dateien

    Returns
    -------
    list[IntelEvent]
        Liste der noch nicht verarbeiteten Events
    """
    if not events_dir.exists():
        return []

    unprocessed = []
    for event_file in events_dir.glob("*.json"):
        try:
            event = load_intel_event(event_file)
            if event.status == "new":
                unprocessed.append(event)
        except Exception as e:
            logger.warning(f"Fehler beim Laden von {event_file}: {e}")

    return unprocessed
