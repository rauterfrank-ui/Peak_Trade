# tests/test_alerts_api.py
"""
Tests für Alerts Web-API (Phase 83) mit Runbook-Integration (Phase 84).
======================================================================

Tests für:
- AlertSummary / RunbookSummary Pydantic-Models
- get_alerts_for_ui() mit Runbook-Anreicherung
- API-Endpoint /api/live/alerts (falls vorhanden)
- Runbook-Serialisierung im API-Response

Run:
    pytest tests/test_alerts_api.py -v
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_alerts_dir(tmp_path: Path) -> Path:
    """Temporäres Verzeichnis für Alert-Storage."""
    alerts_dir = tmp_path / "alerts"
    alerts_dir.mkdir(parents=True)
    return alerts_dir


@pytest.fixture
def sample_alert_with_runbooks() -> dict[str, Any]:
    """Sample-Alert mit Runbooks (Phase 84 Struktur)."""
    return {
        "title": "Risk Severity changed: GREEN → YELLOW",
        "body": "⚠️ WARNUNG: Risk-Status ist auf YELLOW gewechselt.",
        "severity": "WARN",
        "category": "RISK",
        "source": "live_risk_severity",
        "session_id": "test_session_001",
        "timestamp": datetime.now(UTC).isoformat(),
        "context": {
            "daily_loss": -250.0,
            "limit": 500.0,
            "runbooks": [
                {
                    "id": "live_risk_severity",
                    "title": "Live Risk Severity Runbook",
                    "url": "https://github.com/example/docs/runbooks/LIVE_RISK_SEVERITY.md",
                },
                {
                    "id": "live_alert_pipeline",
                    "title": "Live Alert Pipeline Runbook",
                    "url": "https://github.com/example/docs/runbooks/ALERT_PIPELINE.md",
                },
            ],
        },
    }


@pytest.fixture
def sample_alert_without_runbooks() -> dict[str, Any]:
    """Sample-Alert ohne Runbooks."""
    return {
        "title": "System Health Check Passed",
        "body": "All systems operational.",
        "severity": "INFO",
        "category": "SYSTEM",
        "source": "health_monitor",
        "session_id": None,
        "timestamp": datetime.now(UTC).isoformat(),
        "context": {},
    }


# =============================================================================
# TESTS: RunbookSummary Model
# =============================================================================


class TestRunbookSummaryModel:
    """Tests für das RunbookSummary Pydantic-Modell (Phase 84)."""

    def test_create_runbook_summary(self):
        """Testet Erstellung eines RunbookSummary."""
        from src.webui.alerts_api import RunbookSummary

        rb = RunbookSummary(
            id="live_risk_severity",
            title="Live Risk Severity Runbook",
            url="https://example.com/runbook",
        )

        assert rb.id == "live_risk_severity"
        assert rb.title == "Live Risk Severity Runbook"
        assert rb.url == "https://example.com/runbook"

    def test_runbook_summary_serialization(self):
        """Testet JSON-Serialisierung von RunbookSummary."""
        from src.webui.alerts_api import RunbookSummary

        rb = RunbookSummary(
            id="test_rb",
            title="Test Runbook",
            url="https://example.com/test",
        )

        data = rb.model_dump()
        assert data["id"] == "test_rb"
        assert data["title"] == "Test Runbook"
        assert data["url"] == "https://example.com/test"


# =============================================================================
# TESTS: AlertSummary Model mit Runbooks
# =============================================================================


class TestAlertSummaryWithRunbooks:
    """Tests für AlertSummary mit Runbook-Integration (Phase 84)."""

    def test_alert_summary_has_runbooks_field(self):
        """Testet dass AlertSummary ein runbooks-Feld hat."""
        from src.webui.alerts_api import AlertSummary, RunbookSummary

        summary = AlertSummary(
            id="alert_001",
            title="Test Alert",
            body="Test body",
            severity="WARN",
            category="RISK",
            source="test.source",
            timestamp="2025-12-09T10:00:00+00:00",
            timestamp_display="09.12.2025 10:00:00",
            runbooks=[
                RunbookSummary(
                    id="rb1",
                    title="Runbook 1",
                    url="https://example.com/rb1",
                ),
            ],
        )

        assert len(summary.runbooks) == 1
        assert summary.runbooks[0].id == "rb1"

    def test_alert_summary_runbooks_default_empty(self):
        """Testet dass runbooks standardmäßig leer ist."""
        from src.webui.alerts_api import AlertSummary

        summary = AlertSummary(
            id="alert_002",
            title="Test Alert",
            body="Test body",
            severity="INFO",
            category="SYSTEM",
            source="test.source",
            timestamp="2025-12-09T10:00:00+00:00",
            timestamp_display="09.12.2025 10:00:00",
        )

        assert summary.runbooks == []

    def test_alert_summary_json_includes_runbooks(self):
        """Testet dass JSON-Serialisierung Runbooks enthält."""
        from src.webui.alerts_api import AlertSummary, RunbookSummary

        summary = AlertSummary(
            id="alert_003",
            title="Test Alert",
            body="Test body",
            severity="CRITICAL",
            category="RISK",
            source="live_risk_limits",
            timestamp="2025-12-09T10:00:00+00:00",
            timestamp_display="09.12.2025 10:00:00",
            runbooks=[
                RunbookSummary(
                    id="live_risk_limits",
                    title="Live Risk Limits Runbook",
                    url="https://example.com/risk_limits",
                ),
                RunbookSummary(
                    id="incident_drills",
                    title="Incident Drills",
                    url="https://example.com/drills",
                ),
            ],
        )

        data = summary.model_dump()
        assert "runbooks" in data
        assert len(data["runbooks"]) == 2
        assert data["runbooks"][0]["id"] == "live_risk_limits"
        assert data["runbooks"][1]["id"] == "incident_drills"


# =============================================================================
# TESTS: get_alerts_for_ui mit Runbooks
# =============================================================================


class TestGetAlertsForUiWithRunbooks:
    """Tests für get_alerts_for_ui() mit Runbook-Anreicherung."""

    def test_alerts_include_runbooks_from_storage(
        self, temp_alerts_dir: Path, sample_alert_with_runbooks: dict[str, Any], monkeypatch
    ):
        """Testet dass Alerts aus Storage Runbooks enthalten."""
        import src.live.alert_storage as storage_module
        from src.live.alert_storage import AlertStorage, reset_default_storage
        from src.webui.alerts_api import get_alerts_for_ui

        # Setup Storage
        reset_default_storage()
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", temp_alerts_dir)

        # Alert speichern
        storage = AlertStorage(temp_alerts_dir)
        storage.store(sample_alert_with_runbooks)

        # Via API laden
        response = get_alerts_for_ui(limit=10, hours=24)

        # Assertions
        assert len(response.alerts) == 1
        alert = response.alerts[0]
        assert alert.source == "live_risk_severity"
        assert len(alert.runbooks) == 2
        assert alert.runbooks[0].id == "live_risk_severity"
        assert alert.runbooks[0].title == "Live Risk Severity Runbook"
        assert alert.runbooks[1].id == "live_alert_pipeline"

        # Cleanup
        reset_default_storage()

    def test_alerts_without_runbooks_have_empty_list(
        self, temp_alerts_dir: Path, sample_alert_without_runbooks: dict[str, Any], monkeypatch
    ):
        """Testet dass Alerts ohne Runbooks leere Liste haben."""
        import src.live.alert_storage as storage_module
        from src.live.alert_storage import AlertStorage, reset_default_storage
        from src.webui.alerts_api import get_alerts_for_ui

        # Setup Storage
        reset_default_storage()
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", temp_alerts_dir)

        # Alert ohne Runbooks speichern
        storage = AlertStorage(temp_alerts_dir)
        storage.store(sample_alert_without_runbooks)

        # Via API laden
        response = get_alerts_for_ui(limit=10, hours=24)

        # Assertions
        assert len(response.alerts) == 1
        assert response.alerts[0].runbooks == []

        # Cleanup
        reset_default_storage()

    def test_runbook_structure_matches_api_contract(
        self, temp_alerts_dir: Path, sample_alert_with_runbooks: dict[str, Any], monkeypatch
    ):
        """Testet dass Runbook-Struktur dem API-Contract entspricht (id, title, url)."""
        import src.live.alert_storage as storage_module
        from src.live.alert_storage import AlertStorage, reset_default_storage
        from src.webui.alerts_api import get_alerts_for_ui

        # Setup Storage
        reset_default_storage()
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", temp_alerts_dir)

        # Alert speichern
        storage = AlertStorage(temp_alerts_dir)
        storage.store(sample_alert_with_runbooks)

        # Via API laden
        response = get_alerts_for_ui(limit=10, hours=24)

        # Prüfe API-Contract
        for runbook in response.alerts[0].runbooks:
            assert hasattr(runbook, "id"), "Runbook muss id-Feld haben"
            assert hasattr(runbook, "title"), "Runbook muss title-Feld haben"
            assert hasattr(runbook, "url"), "Runbook muss url-Feld haben"
            assert isinstance(runbook.id, str)
            assert isinstance(runbook.title, str)
            assert isinstance(runbook.url, str)
            assert len(runbook.id) > 0
            assert len(runbook.title) > 0
            assert runbook.url.startswith("http")

        # Cleanup
        reset_default_storage()


# =============================================================================
# TESTS: API-Level Test für Alerts mit Runbooks (Kerntest für Phase 84)
# =============================================================================


class TestAlertsApiIncludesRunbooksForKnownAlertType:
    """
    API-Level Integration-Test: Alerts mit bekanntem Alert-Type enthalten Runbooks.

    Dieser Test validiert den vollständigen Flow:
    1. Alert mit kategorie/source wird erstellt und persistiert (wie Live-Stack)
    2. API-Endpoint wird abgefragt
    3. Response enthält Runbooks basierend auf Registry-Mapping
    """

    def test_alerts_api_includes_runbooks_for_known_alert_type(
        self, temp_alerts_dir: Path, monkeypatch
    ):
        """Testet dass API-Response Runbooks für bekannte Alert-Types enthält."""
        import src.live.alert_storage as storage_module
        from src.live.alert_pipeline import (
            AlertCategory,
            AlertMessage,
            AlertPipelineManager,
            AlertSeverity,
            NullAlertChannel,
        )
        from src.live.alert_storage import reset_default_storage
        from src.webui.alerts_api import get_alerts_for_ui

        # Setup Storage
        reset_default_storage()
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", temp_alerts_dir)

        # Arrange: Manager mit Persistierung erstellen
        manager = AlertPipelineManager([NullAlertChannel()], persist_alerts=True)

        # Alert erstellen der auf Runbooks mappen sollte (RISK + live_risk_severity)
        alert = AlertMessage(
            title="Risk Severity changed: GREEN → YELLOW",
            body="⚠️ WARNUNG: Risk-Status ist auf YELLOW gewechselt.",
            severity=AlertSeverity.WARN,
            category=AlertCategory.RISK,
            source="live_risk_severity",
            session_id="integration_test_session",
            context={"daily_loss": -250.0, "limit": 500.0},
        )

        # Act: Alert senden (wird automatisch mit Runbooks angereichert und persistiert)
        manager.send(alert)

        # Act: API abfragen
        response = get_alerts_for_ui(limit=10, hours=24)

        # Assert: Mindestens ein Alert vorhanden
        assert len(response.alerts) >= 1, "Response sollte mindestens einen Alert enthalten"

        # Assert: Alert hat Runbooks
        test_alert = response.alerts[0]
        assert len(test_alert.runbooks) > 0, "Alert sollte nicht-leere runbooks-Liste haben"

        # Assert: Runbook-Struktur korrekt
        for rb in test_alert.runbooks:
            assert rb.id, "Runbook muss id haben"
            assert rb.title, "Runbook muss title haben"
            assert rb.url, "Runbook muss url haben"
            assert rb.url.startswith("http"), "Runbook-URL muss mit http beginnen"

        # Assert: Erwartete Runbooks für RISK + live_risk_severity vorhanden
        runbook_ids = [rb.id for rb in test_alert.runbooks]
        assert "live_risk_severity" in runbook_ids, "live_risk_severity Runbook sollte enthalten sein"
        assert "live_alert_pipeline" in runbook_ids, "live_alert_pipeline Runbook sollte enthalten sein"

        # Cleanup
        reset_default_storage()

    def test_critical_risk_alert_includes_incident_drills_runbook(
        self, temp_alerts_dir: Path, monkeypatch
    ):
        """Testet dass CRITICAL Risk-Alerts das Incident-Drills-Runbook enthalten."""
        import src.live.alert_storage as storage_module
        from src.live.alert_pipeline import (
            AlertCategory,
            AlertMessage,
            AlertPipelineManager,
            AlertSeverity,
            NullAlertChannel,
        )
        from src.live.alert_storage import reset_default_storage
        from src.webui.alerts_api import get_alerts_for_ui

        # Setup
        reset_default_storage()
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", temp_alerts_dir)

        manager = AlertPipelineManager([NullAlertChannel()], persist_alerts=True)

        # CRITICAL Alert erstellen
        alert = AlertMessage(
            title="BREACH: Daily Loss Limit exceeded",
            body="⛔ KRITISCH: Hartes Limit überschritten",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.RISK,
            source="live_risk_limits",
            context={"breach_type": "max_daily_loss", "value": -600.0, "limit": 500.0},
        )

        manager.send(alert)

        # API abfragen
        response = get_alerts_for_ui(limit=10, hours=24)

        assert len(response.alerts) >= 1

        critical_alert = response.alerts[0]
        runbook_ids = [rb.id for rb in critical_alert.runbooks]

        # CRITICAL Alerts sollten Incident-Drills enthalten
        assert "incident_drills" in runbook_ids, (
            "CRITICAL Alerts sollten incident_drills Runbook enthalten"
        )
        assert "live_risk_limits" in runbook_ids, (
            "Risk-Limits Alerts sollten live_risk_limits Runbook enthalten"
        )

        # Cleanup
        reset_default_storage()


# =============================================================================
# TESTS: Edge Cases und Robustheit
# =============================================================================


class TestRunbookEdgeCases:
    """Tests für Edge Cases bei der Runbook-Verarbeitung."""

    def test_malformed_runbook_in_context_handled_gracefully(
        self, temp_alerts_dir: Path, monkeypatch
    ):
        """Testet dass fehlerhafte Runbook-Daten im Context behandelt werden."""
        import src.live.alert_storage as storage_module
        from src.live.alert_storage import AlertStorage, reset_default_storage
        from src.webui.alerts_api import get_alerts_for_ui

        reset_default_storage()
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", temp_alerts_dir)

        # Alert mit teilweise fehlerhaften Runbook-Daten
        alert_with_malformed_runbooks = {
            "title": "Test Alert",
            "body": "Test body",
            "severity": "WARN",
            "category": "RISK",
            "source": "test",
            "timestamp": datetime.now(UTC).isoformat(),
            "context": {
                "runbooks": [
                    {"id": "valid_rb", "title": "Valid Runbook", "url": "https://example.com"},
                    {"id": "", "title": "", "url": ""},  # Leere Werte
                    "not_a_dict",  # Kein Dict
                    None,  # None-Wert
                ],
            },
        }

        storage = AlertStorage(temp_alerts_dir)
        storage.store(alert_with_malformed_runbooks)

        # Sollte nicht crashen
        response = get_alerts_for_ui(limit=10, hours=24)

        assert len(response.alerts) == 1
        # Nur gültige Runbooks sollten übernommen werden
        # (die Implementation filtert ungültige ggf. raus)

        reset_default_storage()

    def test_runbooks_preserved_through_storage_roundtrip(
        self, temp_alerts_dir: Path, monkeypatch
    ):
        """Testet dass Runbooks nach Storage-Roundtrip erhalten bleiben."""
        import src.live.alert_storage as storage_module
        from src.live.alert_storage import AlertStorage, reset_default_storage
        from src.webui.alerts_api import get_alerts_for_ui

        reset_default_storage()
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", temp_alerts_dir)

        original_runbooks = [
            {"id": "rb_1", "title": "Runbook One", "url": "https://example.com/1"},
            {"id": "rb_2", "title": "Runbook Two", "url": "https://example.com/2"},
            {"id": "rb_3", "title": "Runbook Three", "url": "https://example.com/3"},
        ]

        alert = {
            "title": "Roundtrip Test",
            "body": "Testing roundtrip",
            "severity": "WARN",
            "category": "RISK",
            "source": "test",
            "timestamp": datetime.now(UTC).isoformat(),
            "context": {"runbooks": original_runbooks, "other_key": "preserved"},
        }

        storage = AlertStorage(temp_alerts_dir)
        storage.store(alert)

        response = get_alerts_for_ui(limit=10, hours=24)

        assert len(response.alerts) == 1
        loaded_runbooks = response.alerts[0].runbooks

        assert len(loaded_runbooks) == 3
        assert loaded_runbooks[0].id == "rb_1"
        assert loaded_runbooks[1].id == "rb_2"
        assert loaded_runbooks[2].id == "rb_3"

        reset_default_storage()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "TestAlertSummaryWithRunbooks",
    "TestAlertsApiIncludesRunbooksForKnownAlertType",
    "TestGetAlertsForUiWithRunbooks",
    "TestRunbookEdgeCases",
    "TestRunbookSummaryModel",
]



