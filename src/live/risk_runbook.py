# src/live/risk_runbook.py
"""
Peak_Trade: Risk-Severity Runbook (Operator-Handbuch)
======================================================

Dieses Modul enthält strukturierte Handlungsempfehlungen für Operatoren
basierend auf dem Risk-Severity-System.

Konzept:
--------
Das Risk-Severity-System unterscheidet drei Zustände:

1. **GREEN (OK)**
   - Alle Limits komfortabel eingehalten
   - Routine-Monitoring ausreichend
   - Trading kann normal fortgesetzt werden

2. **YELLOW (WARNING)**
   - Mindestens ein Limit im Warnbereich (80-99% des Limits)
   - Erhöhte Aufmerksamkeit erforderlich
   - Trading möglich, aber mit Vorsicht
   - Präventive Maßnahmen empfohlen

3. **RED (BREACH)**
   - Mindestens ein Limit verletzt (>= 100%)
   - Neue Orders werden automatisch blockiert
   - Sofortige Intervention erforderlich
   - Trading gestoppt bis zur Freigabe

Dieses Modul kann verwendet werden für:
- Generierung von Operator-Alerts
- Dashboard-Hinweistexte
- CLI-Ausgaben
- Automatisierte Postmortem-Vorbereitung

Usage:
    from src.live.risk_runbook import (
        get_runbook_for_status,
        RunbookEntry,
        format_runbook_for_operator,
    )

    entry = get_runbook_for_status("yellow")
    print(format_runbook_for_operator(entry))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

RiskStatus = Literal["green", "yellow", "red"]


@dataclass
class RunbookChecklist:
    """
    Checkliste für Operator-Aktionen.

    Attributes:
        item: Beschreibung der Aktion
        priority: Priorität (high, medium, low)
        estimated_time: Geschätzte Zeit für die Aktion
        responsible: Verantwortliche Rolle
    """

    item: str
    priority: Literal["high", "medium", "low"] = "medium"
    estimated_time: str = "< 5 min"
    responsible: str = "Operator"


@dataclass
class RunbookEntry:
    """
    Runbook-Eintrag für einen Risk-Status.

    Enthält alle relevanten Informationen und Handlungsanweisungen
    für einen bestimmten Risk-Status.

    Attributes:
        status: Risk-Status (green/yellow/red)
        severity: Severity-Level (ok/warning/breach)
        title: Titel für die Anzeige
        icon: Emoji/Icon
        summary: Kurze Zusammenfassung
        description: Ausführliche Beschreibung
        immediate_actions: Sofortige Aktionen (in Reihenfolge)
        monitoring_actions: Monitoring-Empfehlungen
        communication_actions: Kommunikations-Empfehlungen
        recovery_actions: Erholungs-/Normalisierungs-Aktionen
        escalation_threshold: Wann eskaliert werden sollte
        escalation_contacts: An wen eskaliert wird
        checklist: Detaillierte Checkliste
        monitoring_interval: Empfohlenes Monitoring-Intervall
        auto_actions: Automatische Aktionen des Systems
        documentation_required: Welche Dokumentation erforderlich ist
    """

    status: RiskStatus
    severity: str
    title: str
    icon: str
    summary: str
    description: str

    immediate_actions: List[str] = field(default_factory=list)
    monitoring_actions: List[str] = field(default_factory=list)
    communication_actions: List[str] = field(default_factory=list)
    recovery_actions: List[str] = field(default_factory=list)

    escalation_threshold: Optional[str] = None
    escalation_contacts: List[str] = field(default_factory=list)

    checklist: List[RunbookChecklist] = field(default_factory=list)
    monitoring_interval: str = "Standard"
    auto_actions: List[str] = field(default_factory=list)
    documentation_required: List[str] = field(default_factory=list)


# =============================================================================
# RUNBOOK DEFINITIONS
# =============================================================================

RUNBOOK_GREEN = RunbookEntry(
    status="green",
    severity="ok",
    title="Risk Status: OK",
    icon="✅",
    summary="Alle Risk-Limits komfortabel eingehalten. System läuft normal.",
    description="""
Das System befindet sich im normalen Betriebszustand. Alle konfigurierten
Risk-Limits sind mit ausreichendem Sicherheitsabstand eingehalten.

Es sind keine besonderen Maßnahmen erforderlich. Das reguläre Monitoring
kann im Standard-Intervall fortgesetzt werden.
    """.strip(),
    immediate_actions=[
        "Keine sofortigen Aktionen erforderlich",
    ],
    monitoring_actions=[
        "Routinemäßiges Monitoring fortsetzen",
        "Nächsten regulären Check-In abwarten",
        "Dashboard-Ampel beobachten",
    ],
    communication_actions=[
        "Keine Benachrichtigung erforderlich",
    ],
    recovery_actions=[],
    escalation_threshold="Bei Wechsel zu WARNING oder BREACH",
    escalation_contacts=[],
    checklist=[
        RunbookChecklist(
            item="Dashboard-Status prüfen",
            priority="low",
            estimated_time="< 1 min",
        ),
        RunbookChecklist(
            item="PnL-Trend beobachten",
            priority="low",
            estimated_time="< 1 min",
        ),
    ],
    monitoring_interval="Standard (5-15 min)",
    auto_actions=[
        "Normaler Trading-Betrieb",
        "Orders werden ausgeführt",
    ],
    documentation_required=[],
)

RUNBOOK_YELLOW = RunbookEntry(
    status="yellow",
    severity="warning",
    title="Risk Status: WARNING",
    icon="⚠️",
    summary="Mindestens ein Limit im Warnbereich. Erhöhte Aufmerksamkeit erforderlich.",
    description="""
Das System hat erkannt, dass mindestens ein Risk-Limit den Warnbereich
erreicht hat (typischerweise 80-99% des konfigurierten Limits).

WICHTIG: Orders werden noch ausgeführt, aber das System nähert sich
kritischen Grenzen. Präventive Maßnahmen sollten eingeleitet werden,
um einen BREACH zu vermeiden.

Der Warnbereich dient als Frühwarnsystem, um rechtzeitig reagieren
zu können, bevor harte Limits greifen und Orders blockiert werden.
    """.strip(),
    immediate_actions=[
        "Dashboard öffnen und betroffene Limits identifizieren",
        "Aktuelle Positionen und offene Orders überprüfen",
        "Exposure-Verteilung analysieren (Konzentration?)",
        "Daily-PnL-Entwicklung prüfen",
    ],
    monitoring_actions=[
        "Monitoring-Intervall auf 1-5 Minuten erhöhen",
        "Limit-Ratios kontinuierlich beobachten",
        "Alarme für weitere Verschlechterung aktivieren",
    ],
    communication_actions=[
        "Team über WARNING-Status informieren (Slack/Chat)",
        "Bei anhaltendem WARNING: Eskalationskontakt informieren",
    ],
    recovery_actions=[
        "Trading-Intensität reduzieren",
        "Auf defensive Strategien umschalten",
        "Ggf. Position-Sizing anpassen",
        "Stop-Loss-Orders prüfen/nachjustieren",
        "Bei Exposure-Warning: Positionen teilweise reduzieren",
        "Bei Daily-Loss-Warning: Risikoärmere Trades bevorzugen",
    ],
    escalation_threshold="Bei Trend Richtung BREACH oder nach 30 min ohne Verbesserung",
    escalation_contacts=[
        "Trading-Team-Lead",
        "Risk-Manager (bei anhaltendem WARNING)",
    ],
    checklist=[
        RunbookChecklist(
            item="Betroffene Limits im Dashboard identifizieren",
            priority="high",
            estimated_time="< 2 min",
        ),
        RunbookChecklist(
            item="Aktuelle Positionen auflisten",
            priority="high",
            estimated_time="< 3 min",
        ),
        RunbookChecklist(
            item="Exposure-Verteilung prüfen",
            priority="high",
            estimated_time="< 5 min",
        ),
        RunbookChecklist(
            item="Offene Orders prüfen",
            priority="medium",
            estimated_time="< 3 min",
        ),
        RunbookChecklist(
            item="Stop-Loss-Orders validieren",
            priority="medium",
            estimated_time="< 5 min",
        ),
        RunbookChecklist(
            item="Team informieren (Slack)",
            priority="medium",
            estimated_time="< 2 min",
        ),
        RunbookChecklist(
            item="Handlungsoptionen evaluieren",
            priority="medium",
            estimated_time="< 10 min",
        ),
    ],
    monitoring_interval="Erhöht (1-5 min)",
    auto_actions=[
        "Orders werden weiterhin ausgeführt",
        "WARNING-Alerts werden gesendet",
        "Logging auf WARNING-Level",
    ],
    documentation_required=[
        "Zeitpunkt des WARNING-Eintritts notieren",
        "Betroffene Limits dokumentieren",
        "Ergriffene Maßnahmen festhalten",
    ],
)

RUNBOOK_RED = RunbookEntry(
    status="red",
    severity="breach",
    title="Risk Status: BREACH",
    icon="⛔",
    summary="Limit(s) verletzt. Neue Orders werden blockiert. Sofortige Intervention erforderlich.",
    description="""
KRITISCHER ZUSTAND: Mindestens ein Risk-Limit wurde überschritten.

Das System hat automatisch folgende Schutzmaßnahmen aktiviert:
- Neue Orders werden BLOCKIERT
- Alerts werden auf CRITICAL-Level gesendet
- Trading ist effektiv gestoppt

ACHTUNG: Bestehende Positionen und offene Orders sind NICHT
automatisch betroffen. Diese müssen manuell evaluiert und
ggf. angepasst werden.

Ziel: Kontrollierte Stabilisierung, Ursachenanalyse, Dokumentation.
    """.strip(),
    immediate_actions=[
        "SOFORT: Alle Trading-Aktivitäten pausieren",
        "Dashboard öffnen: Welche Limits sind verletzt?",
        "Zeitpunkt und Kontext des BREACH notieren",
        "Bestehende Positionen auflisten",
        "Offene Orders identifizieren",
    ],
    monitoring_actions=[
        "Kontinuierliches Live-Monitoring aktivieren",
        "Positionen in Echtzeit beobachten",
        "Auf weitere Verschlechterung achten",
    ],
    communication_actions=[
        "Team-Lead SOFORT informieren",
        "Risk-Manager benachrichtigen",
        "Incident-Channel öffnen (falls vorhanden)",
        "Stakeholder bei signifikantem Verlust informieren",
    ],
    recovery_actions=[
        "Offene Orders prüfen und ggf. STORNIEREN",
        "Bestehende Positionen evaluieren",
        "Bei Over-Exposure: Kontrollierter Positionsabbau",
        "Bei Daily-Loss: Keine neuen Risiken eingehen",
        "Warten bis Limits wieder im grünen Bereich",
        "Nach Stabilisierung: Trading-Freigabe einholen",
    ],
    escalation_threshold="SOFORT bei BREACH",
    escalation_contacts=[
        "Trading-Team-Lead (sofort)",
        "Risk-Manager (sofort)",
        "Management (bei > 2% Verlust)",
    ],
    checklist=[
        RunbookChecklist(
            item="Trading pausieren",
            priority="high",
            estimated_time="sofort",
            responsible="Operator",
        ),
        RunbookChecklist(
            item="Verletzte Limits identifizieren",
            priority="high",
            estimated_time="< 2 min",
            responsible="Operator",
        ),
        RunbookChecklist(
            item="Incident-Log starten",
            priority="high",
            estimated_time="< 3 min",
            responsible="Operator",
        ),
        RunbookChecklist(
            item="Team-Lead informieren",
            priority="high",
            estimated_time="< 2 min",
            responsible="Operator",
        ),
        RunbookChecklist(
            item="Offene Orders listen",
            priority="high",
            estimated_time="< 5 min",
            responsible="Operator",
        ),
        RunbookChecklist(
            item="Positionen dokumentieren",
            priority="high",
            estimated_time="< 5 min",
            responsible="Operator",
        ),
        RunbookChecklist(
            item="Screenshots/Charts sichern",
            priority="medium",
            estimated_time="< 10 min",
            responsible="Operator",
        ),
        RunbookChecklist(
            item="Ursachenanalyse starten",
            priority="medium",
            estimated_time="15-30 min",
            responsible="Team-Lead",
        ),
        RunbookChecklist(
            item="Recovery-Plan erstellen",
            priority="medium",
            estimated_time="15-30 min",
            responsible="Team-Lead",
        ),
        RunbookChecklist(
            item="Positionen adjustieren (wenn nötig)",
            priority="medium",
            estimated_time="variabel",
            responsible="Operator + Team-Lead",
        ),
        RunbookChecklist(
            item="Postmortem vorbereiten",
            priority="low",
            estimated_time="30-60 min",
            responsible="Team",
        ),
    ],
    monitoring_interval="Kontinuierlich (Live-Watch)",
    auto_actions=[
        "Neue Orders werden BLOCKIERT",
        "CRITICAL-Alerts werden gesendet",
        "Logging auf ERROR-Level",
        "Metriken werden aufgezeichnet",
    ],
    documentation_required=[
        "Incident-Log mit Zeitstempel",
        "Liste der verletzten Limits mit Werten",
        "Snapshot aller Positionen",
        "Snapshot aller offenen Orders",
        "Screenshots von Dashboard/Charts",
        "Chronologie der Ereignisse",
        "Ergriffene Maßnahmen mit Zeitstempeln",
        "Root-Cause (sobald bekannt)",
        "Lessons Learned (für Postmortem)",
    ],
)

# Mapping
_RUNBOOK_MAP: Dict[RiskStatus, RunbookEntry] = {
    "green": RUNBOOK_GREEN,
    "yellow": RUNBOOK_YELLOW,
    "red": RUNBOOK_RED,
}


# =============================================================================
# PUBLIC API
# =============================================================================


def get_runbook_for_status(status: RiskStatus) -> RunbookEntry:
    """
    Gibt den Runbook-Eintrag für einen Risk-Status zurück.

    Args:
        status: "green", "yellow" oder "red"

    Returns:
        RunbookEntry mit allen Handlungsempfehlungen
    """
    return _RUNBOOK_MAP.get(status, RUNBOOK_GREEN)


def get_runbook_for_severity(severity: str) -> RunbookEntry:
    """
    Gibt den Runbook-Eintrag für eine Severity zurück.

    Args:
        severity: "ok", "warning" oder "breach"

    Returns:
        RunbookEntry mit allen Handlungsempfehlungen
    """
    mapping = {
        "ok": "green",
        "warning": "yellow",
        "breach": "red",
    }
    status = mapping.get(severity, "green")
    return get_runbook_for_status(status)


def format_runbook_for_operator(
    entry: RunbookEntry,
    *,
    include_checklist: bool = True,
    include_description: bool = True,
) -> str:
    """
    Formatiert einen Runbook-Eintrag als lesbaren Text.

    Args:
        entry: RunbookEntry
        include_checklist: Ob Checkliste inkludiert wird
        include_description: Ob ausführliche Beschreibung inkludiert wird

    Returns:
        Formatierter Text-String
    """
    lines = [
        f"{entry.icon} {entry.title}",
        "=" * 50,
        "",
        entry.summary,
        "",
    ]

    if include_description:
        lines.append(entry.description)
        lines.append("")

    # Sofortige Aktionen
    if entry.immediate_actions:
        lines.append("SOFORTIGE AKTIONEN:")
        for i, action in enumerate(entry.immediate_actions, 1):
            lines.append(f"  {i}. {action}")
        lines.append("")

    # Monitoring
    if entry.monitoring_actions:
        lines.append(f"MONITORING ({entry.monitoring_interval}):")
        for action in entry.monitoring_actions:
            lines.append(f"  • {action}")
        lines.append("")

    # Kommunikation
    if entry.communication_actions:
        lines.append("KOMMUNIKATION:")
        for action in entry.communication_actions:
            lines.append(f"  • {action}")
        lines.append("")

    # Recovery
    if entry.recovery_actions:
        lines.append("RECOVERY / STABILISIERUNG:")
        for action in entry.recovery_actions:
            lines.append(f"  • {action}")
        lines.append("")

    # Auto-Actions
    if entry.auto_actions:
        lines.append("AUTOMATISCHE SYSTEM-AKTIONEN:")
        for action in entry.auto_actions:
            lines.append(f"  ➤ {action}")
        lines.append("")

    # Checkliste
    if include_checklist and entry.checklist:
        lines.append("CHECKLISTE:")
        for item in entry.checklist:
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item.priority, "⚪")
            lines.append(
                f"  {priority_icon} [ ] {item.item} ({item.estimated_time}, {item.responsible})"
            )
        lines.append("")

    # Eskalation
    if entry.escalation_threshold:
        lines.append(f"ESKALATION: {entry.escalation_threshold}")
        if entry.escalation_contacts:
            lines.append("  Kontakte: " + ", ".join(entry.escalation_contacts))
        lines.append("")

    # Dokumentation
    if entry.documentation_required:
        lines.append("ERFORDERLICHE DOKUMENTATION:")
        for doc in entry.documentation_required:
            lines.append(f"  ☐ {doc}")

    return "\n".join(lines)


def format_runbook_compact(entry: RunbookEntry) -> str:
    """
    Formatiert einen Runbook-Eintrag als kompakten Einzeiler.

    Args:
        entry: RunbookEntry

    Returns:
        Kompakter String
    """
    actions_count = len(entry.immediate_actions)
    return (
        f"{entry.icon} {entry.status.upper()}: {entry.summary} "
        f"({actions_count} Aktionen, Monitoring: {entry.monitoring_interval})"
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RiskStatus",
    "RunbookChecklist",
    "RunbookEntry",
    "get_runbook_for_status",
    "get_runbook_for_severity",
    "format_runbook_for_operator",
    "format_runbook_compact",
    "RUNBOOK_GREEN",
    "RUNBOOK_YELLOW",
    "RUNBOOK_RED",
]
