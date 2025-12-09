# tests/test_runbook_registry.py
"""
Tests für Runbook-Registry (Phase 84)
=====================================

Tests für:
- RunbookLink Dataclass
- Runbook-Registry
- resolve_runbooks_for_alert() Funktion
"""
from __future__ import annotations

import pytest

from src.infra.runbooks import RunbookLink, resolve_runbooks_for_alert, get_all_runbooks, RUNBOOK_REGISTRY
from src.infra.runbooks.registry import get_runbook_by_id


# =============================================================================
# RUNBOOK LINK TESTS
# =============================================================================


class TestRunbookLink:
    """Tests für RunbookLink Dataclass."""

    def test_creation(self):
        """Testet Erstellung eines RunbookLink."""
        link = RunbookLink(
            id="test_runbook",
            title="Test Runbook",
            url="https://example.com/runbook",
            description="Test description",
        )

        assert link.id == "test_runbook"
        assert link.title == "Test Runbook"
        assert link.url == "https://example.com/runbook"
        assert link.description == "Test description"

    def test_creation_without_description(self):
        """Testet Erstellung ohne optionale Felder."""
        link = RunbookLink(
            id="minimal",
            title="Minimal Runbook",
            url="https://example.com",
        )

        assert link.id == "minimal"
        assert link.description is None

    def test_to_dict(self):
        """Testet Serialisierung zu Dict."""
        link = RunbookLink(
            id="test",
            title="Test",
            url="https://example.com",
            description="Description",
        )

        result = link.to_dict()

        assert result["id"] == "test"
        assert result["title"] == "Test"
        assert result["url"] == "https://example.com"
        assert result["description"] == "Description"

    def test_from_dict(self):
        """Testet Deserialisierung aus Dict."""
        data = {
            "id": "from_dict",
            "title": "From Dict",
            "url": "https://example.com",
            "description": "Test",
        }

        link = RunbookLink.from_dict(data)

        assert link.id == "from_dict"
        assert link.title == "From Dict"

    def test_frozen(self):
        """Testet dass RunbookLink immutable ist."""
        link = RunbookLink(id="test", title="Test", url="https://example.com")

        with pytest.raises(AttributeError):
            link.id = "modified"


# =============================================================================
# REGISTRY TESTS
# =============================================================================


class TestRunbookRegistry:
    """Tests für Runbook-Registry."""

    def test_registry_not_empty(self):
        """Testet dass die Registry Einträge hat."""
        assert len(RUNBOOK_REGISTRY) > 0

    def test_get_all_runbooks(self):
        """Testet get_all_runbooks()."""
        runbooks = get_all_runbooks()

        assert len(runbooks) > 0
        assert all(isinstance(rb, RunbookLink) for rb in runbooks)

    def test_get_runbook_by_id_existing(self):
        """Testet Abruf eines existierenden Runbooks."""
        runbook = get_runbook_by_id("live_alert_pipeline")

        assert runbook is not None
        assert runbook.id == "live_alert_pipeline"
        assert "Alert" in runbook.title or "alert" in runbook.title.lower()

    def test_get_runbook_by_id_nonexistent(self):
        """Testet Abruf eines nicht-existierenden Runbooks."""
        runbook = get_runbook_by_id("nonexistent_runbook")

        assert runbook is None

    def test_registry_contains_required_runbooks(self):
        """Testet dass erforderliche Runbooks vorhanden sind."""
        required = [
            "live_alert_pipeline",
            "live_risk_severity",
            "live_risk_limits",
        ]

        for runbook_id in required:
            assert runbook_id in RUNBOOK_REGISTRY, f"Missing required runbook: {runbook_id}"


# =============================================================================
# RESOLVER TESTS
# =============================================================================


class TestResolveRunbooks:
    """Tests für resolve_runbooks_for_alert()."""

    def test_risk_severity_critical(self):
        """Testet Auflösung für RISK + live_risk_severity + CRITICAL."""
        from src.live.alert_pipeline import AlertMessage, AlertSeverity, AlertCategory

        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.RISK,
            source="live_risk_severity",
        )

        runbooks = resolve_runbooks_for_alert(alert)

        assert len(runbooks) >= 2
        runbook_ids = [rb.id for rb in runbooks]
        assert "live_risk_severity" in runbook_ids
        assert "live_alert_pipeline" in runbook_ids

    def test_risk_severity_warn(self):
        """Testet Auflösung für RISK + live_risk_severity + WARN."""
        from src.live.alert_pipeline import AlertMessage, AlertSeverity, AlertCategory

        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.WARN,
            category=AlertCategory.RISK,
            source="live_risk_severity",
        )

        runbooks = resolve_runbooks_for_alert(alert)

        assert len(runbooks) >= 2
        runbook_ids = [rb.id for rb in runbooks]
        assert "live_risk_severity" in runbook_ids

    def test_risk_limits_critical(self):
        """Testet Auflösung für RISK + live_risk_limits + CRITICAL."""
        from src.live.alert_pipeline import AlertMessage, AlertSeverity, AlertCategory

        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.RISK,
            source="live_risk_limits",
        )

        runbooks = resolve_runbooks_for_alert(alert)

        assert len(runbooks) >= 2
        runbook_ids = [rb.id for rb in runbooks]
        assert "live_risk_limits" in runbook_ids
        assert "live_alert_pipeline" in runbook_ids

    def test_execution_alert(self):
        """Testet Auflösung für EXECUTION-Alerts."""
        from src.live.alert_pipeline import AlertMessage, AlertSeverity, AlertCategory

        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.WARN,
            category=AlertCategory.EXECUTION,
            source="order_execution",
        )

        runbooks = resolve_runbooks_for_alert(alert)

        assert len(runbooks) >= 1
        runbook_ids = [rb.id for rb in runbooks]
        assert "live_deployment" in runbook_ids or "live_alert_pipeline" in runbook_ids

    def test_system_alert(self):
        """Testet Auflösung für SYSTEM-Alerts."""
        from src.live.alert_pipeline import AlertMessage, AlertSeverity, AlertCategory

        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.WARN,
            category=AlertCategory.SYSTEM,
            source="heartbeat",
        )

        runbooks = resolve_runbooks_for_alert(alert)

        assert len(runbooks) >= 1
        runbook_ids = [rb.id for rb in runbooks]
        assert "live_alert_pipeline" in runbook_ids

    def test_unknown_source_fallback(self):
        """Testet Fallback für unbekannte Source."""
        from src.live.alert_pipeline import AlertMessage, AlertSeverity, AlertCategory

        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.WARN,
            category=AlertCategory.RISK,
            source="completely_unknown_source",
        )

        runbooks = resolve_runbooks_for_alert(alert)

        # Sollte auf Category-Fallback zurückfallen
        assert len(runbooks) >= 1

    def test_dict_input(self):
        """Testet Auflösung mit Dict-Input."""
        alert_dict = {
            "category": "RISK",
            "source": "live_risk_severity",
            "severity": "CRITICAL",
        }

        runbooks = resolve_runbooks_for_alert(alert_dict)

        assert len(runbooks) >= 2
        runbook_ids = [rb.id for rb in runbooks]
        assert "live_risk_severity" in runbook_ids

    def test_case_insensitive(self):
        """Testet Case-Insensitive Lookup."""
        alert_dict = {
            "category": "risk",  # lowercase
            "source": "live_risk_severity",
            "severity": "critical",  # lowercase
        }

        runbooks = resolve_runbooks_for_alert(alert_dict)

        assert len(runbooks) >= 2

    def test_invalid_input_returns_empty(self):
        """Testet dass ungültiger Input leere Liste zurückgibt."""
        runbooks = resolve_runbooks_for_alert("invalid")

        assert runbooks == []

    def test_critical_includes_incident_drills(self):
        """Testet dass CRITICAL-Alerts Incident Drills enthalten."""
        from src.live.alert_pipeline import AlertMessage, AlertSeverity, AlertCategory

        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.RISK,
            source="live_risk_severity",
        )

        runbooks = resolve_runbooks_for_alert(alert)

        runbook_ids = [rb.id for rb in runbooks]
        assert "incident_drills" in runbook_ids


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestRunbookIntegration:
    """Integrationstests für Runbook-System."""

    def test_runbook_urls_valid_format(self):
        """Testet dass alle Runbook-URLs gültiges Format haben."""
        for runbook in get_all_runbooks():
            assert runbook.url.startswith("http"), f"Invalid URL for {runbook.id}: {runbook.url}"
            assert "/docs/" in runbook.url or "/runbooks/" in runbook.url

    def test_runbook_ids_unique(self):
        """Testet dass alle Runbook-IDs eindeutig sind."""
        ids = [rb.id for rb in get_all_runbooks()]
        assert len(ids) == len(set(ids)), "Duplicate runbook IDs found"

    def test_runbook_titles_not_empty(self):
        """Testet dass alle Runbooks Titel haben."""
        for runbook in get_all_runbooks():
            assert runbook.title, f"Empty title for runbook: {runbook.id}"
            assert len(runbook.title) > 5, f"Title too short for: {runbook.id}"
