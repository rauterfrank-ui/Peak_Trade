# tests/test_risk_runbook.py
"""
Tests für Risk-Runbook (Operator-Handbuch)
==========================================

Testet:
- RunbookEntry Datenstruktur
- get_runbook_for_status() für alle Status
- get_runbook_for_severity() Mapping
- format_runbook_for_operator() Formatierung
- format_runbook_compact() Kompakt-Format
"""
from __future__ import annotations

import pytest

from src.live.risk_runbook import (
    RiskStatus,
    RunbookChecklist,
    RunbookEntry,
    get_runbook_for_status,
    get_runbook_for_severity,
    format_runbook_for_operator,
    format_runbook_compact,
    RUNBOOK_GREEN,
    RUNBOOK_YELLOW,
    RUNBOOK_RED,
)


# =============================================================================
# TESTS: RUNBOOK ENTRIES
# =============================================================================


class TestRunbookEntries:
    """Tests für die vordefinierten Runbook-Einträge."""

    def test_runbook_green_structure(self):
        """RUNBOOK_GREEN hat korrekte Struktur."""
        entry = RUNBOOK_GREEN

        assert entry.status == "green"
        assert entry.severity == "ok"
        assert entry.icon == "✅"
        assert len(entry.immediate_actions) >= 1
        assert len(entry.monitoring_actions) >= 1
        assert entry.monitoring_interval is not None

    def test_runbook_yellow_structure(self):
        """RUNBOOK_YELLOW hat korrekte Struktur."""
        entry = RUNBOOK_YELLOW

        assert entry.status == "yellow"
        assert entry.severity == "warning"
        assert entry.icon == "⚠️"
        assert len(entry.immediate_actions) >= 3
        assert len(entry.recovery_actions) >= 3
        assert len(entry.checklist) >= 5
        assert entry.escalation_threshold is not None
        assert len(entry.escalation_contacts) >= 1

    def test_runbook_red_structure(self):
        """RUNBOOK_RED hat korrekte Struktur."""
        entry = RUNBOOK_RED

        assert entry.status == "red"
        assert entry.severity == "breach"
        assert entry.icon == "⛔"
        assert len(entry.immediate_actions) >= 5
        assert len(entry.recovery_actions) >= 5
        assert len(entry.checklist) >= 10
        assert entry.escalation_threshold is not None
        assert len(entry.escalation_contacts) >= 2
        assert len(entry.documentation_required) >= 5

    def test_checklist_items_have_priority(self):
        """Checklisten-Items haben Prioritäten."""
        for entry in [RUNBOOK_GREEN, RUNBOOK_YELLOW, RUNBOOK_RED]:
            for item in entry.checklist:
                assert item.priority in ("high", "medium", "low")
                assert item.estimated_time is not None
                assert item.responsible is not None


# =============================================================================
# TESTS: GET RUNBOOK FUNCTIONS
# =============================================================================


class TestGetRunbookFunctions:
    """Tests für Runbook-Lookup-Funktionen."""

    def test_get_runbook_for_status_green(self):
        """get_runbook_for_status('green') gibt RUNBOOK_GREEN."""
        entry = get_runbook_for_status("green")
        assert entry.status == "green"
        assert entry.severity == "ok"

    def test_get_runbook_for_status_yellow(self):
        """get_runbook_for_status('yellow') gibt RUNBOOK_YELLOW."""
        entry = get_runbook_for_status("yellow")
        assert entry.status == "yellow"
        assert entry.severity == "warning"

    def test_get_runbook_for_status_red(self):
        """get_runbook_for_status('red') gibt RUNBOOK_RED."""
        entry = get_runbook_for_status("red")
        assert entry.status == "red"
        assert entry.severity == "breach"

    def test_get_runbook_for_status_invalid(self):
        """Unbekannter Status gibt Green zurück."""
        entry = get_runbook_for_status("invalid")  # type: ignore
        assert entry.status == "green"

    def test_get_runbook_for_severity_ok(self):
        """get_runbook_for_severity('ok') gibt RUNBOOK_GREEN."""
        entry = get_runbook_for_severity("ok")
        assert entry.status == "green"

    def test_get_runbook_for_severity_warning(self):
        """get_runbook_for_severity('warning') gibt RUNBOOK_YELLOW."""
        entry = get_runbook_for_severity("warning")
        assert entry.status == "yellow"

    def test_get_runbook_for_severity_breach(self):
        """get_runbook_for_severity('breach') gibt RUNBOOK_RED."""
        entry = get_runbook_for_severity("breach")
        assert entry.status == "red"


# =============================================================================
# TESTS: FORMAT FUNCTIONS
# =============================================================================


class TestFormatFunctions:
    """Tests für Formatierungs-Funktionen."""

    def test_format_runbook_for_operator_green(self):
        """Formatiert Green-Runbook."""
        entry = RUNBOOK_GREEN
        output = format_runbook_for_operator(entry)

        assert "✅" in output
        assert "OK" in output
        assert "SOFORTIGE AKTIONEN" in output
        assert "MONITORING" in output

    def test_format_runbook_for_operator_yellow(self):
        """Formatiert Yellow-Runbook mit allen Sektionen."""
        entry = RUNBOOK_YELLOW
        output = format_runbook_for_operator(entry, include_checklist=True)

        assert "⚠️" in output
        assert "WARNING" in output
        assert "SOFORTIGE AKTIONEN" in output
        assert "RECOVERY" in output
        assert "CHECKLISTE" in output
        assert "ESKALATION" in output

    def test_format_runbook_for_operator_red(self):
        """Formatiert Red-Runbook mit Dokumentation."""
        entry = RUNBOOK_RED
        output = format_runbook_for_operator(entry)

        assert "⛔" in output
        assert "BREACH" in output
        assert "SOFORTIGE AKTIONEN" in output
        assert "ERFORDERLICHE DOKUMENTATION" in output
        assert "Incident-Log" in output

    def test_format_runbook_without_checklist(self):
        """Formatiert ohne Checkliste."""
        entry = RUNBOOK_YELLOW
        output = format_runbook_for_operator(entry, include_checklist=False)

        assert "CHECKLISTE" not in output

    def test_format_runbook_without_description(self):
        """Formatiert ohne ausführliche Beschreibung."""
        entry = RUNBOOK_YELLOW
        output_with = format_runbook_for_operator(entry, include_description=True)
        output_without = format_runbook_for_operator(entry, include_description=False)

        # Mit Beschreibung sollte länger sein
        assert len(output_with) > len(output_without)

    def test_format_runbook_compact_green(self):
        """Compact-Format für Green."""
        entry = RUNBOOK_GREEN
        output = format_runbook_compact(entry)

        assert "✅" in output
        assert "GREEN" in output
        assert "Monitoring:" in output

    def test_format_runbook_compact_yellow(self):
        """Compact-Format für Yellow."""
        entry = RUNBOOK_YELLOW
        output = format_runbook_compact(entry)

        assert "⚠️" in output
        assert "YELLOW" in output
        assert "Aktionen" in output

    def test_format_runbook_compact_red(self):
        """Compact-Format für Red."""
        entry = RUNBOOK_RED
        output = format_runbook_compact(entry)

        assert "⛔" in output
        assert "RED" in output


# =============================================================================
# TESTS: RUNBOOK CHECKLIST
# =============================================================================


class TestRunbookChecklist:
    """Tests für RunbookChecklist."""

    def test_checklist_item_defaults(self):
        """Checklisten-Item hat korrekte Defaults."""
        item = RunbookChecklist(item="Test item")

        assert item.item == "Test item"
        assert item.priority == "medium"
        assert item.estimated_time == "< 5 min"
        assert item.responsible == "Operator"

    def test_checklist_item_custom(self):
        """Checklisten-Item mit Custom-Werten."""
        item = RunbookChecklist(
            item="Critical task",
            priority="high",
            estimated_time="sofort",
            responsible="Team-Lead",
        )

        assert item.priority == "high"
        assert item.estimated_time == "sofort"
        assert item.responsible == "Team-Lead"


# =============================================================================
# TESTS: CONTENT VALIDATION
# =============================================================================


class TestContentValidation:
    """Tests für inhaltliche Korrektheit der Runbooks."""

    def test_green_has_no_escalation_contacts(self):
        """Green braucht keine Eskalationskontakte."""
        entry = RUNBOOK_GREEN
        assert len(entry.escalation_contacts) == 0

    def test_yellow_has_moderate_actions(self):
        """Yellow hat moderate Anzahl Aktionen."""
        entry = RUNBOOK_YELLOW
        assert 3 <= len(entry.immediate_actions) <= 10
        assert 3 <= len(entry.recovery_actions) <= 10

    def test_red_has_comprehensive_checklist(self):
        """Red hat umfassende Checkliste."""
        entry = RUNBOOK_RED
        assert len(entry.checklist) >= 10

        # Mindestens ein High-Priority Item
        high_priority = [i for i in entry.checklist if i.priority == "high"]
        assert len(high_priority) >= 3

    def test_red_auto_actions_include_blocking(self):
        """Red Auto-Actions enthalten Blocking-Info."""
        entry = RUNBOOK_RED
        auto_text = " ".join(entry.auto_actions).lower()
        assert "blockiert" in auto_text or "blocked" in auto_text

    def test_monitoring_intervals_appropriate(self):
        """Monitoring-Intervalle sind angemessen."""
        green = get_runbook_for_status("green")
        yellow = get_runbook_for_status("yellow")
        red = get_runbook_for_status("red")

        # Green sollte "standard" enthalten
        assert "standard" in green.monitoring_interval.lower()

        # Yellow sollte "erhöht" enthalten
        assert "erhöht" in yellow.monitoring_interval.lower()

        # Red sollte "kontinuierlich" oder "live" enthalten
        assert (
            "kontinuierlich" in red.monitoring_interval.lower()
            or "live" in red.monitoring_interval.lower()
        )
