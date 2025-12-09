# tests/test_alert_storage.py
"""
Tests für Alert-Storage (Phase 83)
==================================

Tests für:
- StoredAlert Dataclass
- AlertStorage (store, list, filter, stats)
- Integration mit AlertPipelineManager
- Convenience-Funktionen
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.live.alert_storage import (
    StoredAlert,
    AlertStorage,
    get_default_alert_storage,
    reset_default_storage,
    store_alert,
    list_recent_alerts,
    get_alert_stats,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_storage_dir(tmp_path: Path) -> Path:
    """Temporäres Verzeichnis für Alert-Storage."""
    storage_dir = tmp_path / "alerts"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def storage(temp_storage_dir: Path) -> AlertStorage:
    """AlertStorage-Instanz mit temporärem Verzeichnis."""
    return AlertStorage(temp_storage_dir)


@pytest.fixture
def sample_alert_dict() -> Dict[str, Any]:
    """Sample Alert als Dict."""
    return {
        "title": "Test Alert",
        "body": "This is a test alert body.",
        "severity": "WARN",
        "category": "RISK",
        "source": "test.source",
        "session_id": "test_session_123",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": {"key": "value", "number": 42.5},
    }


@pytest.fixture
def sample_alert_message():
    """Sample AlertMessage (lazy import)."""
    from src.live.alert_pipeline import AlertMessage, AlertSeverity, AlertCategory

    return AlertMessage(
        title="Test AlertMessage",
        body="This is a test AlertMessage body.",
        severity=AlertSeverity.WARN,
        category=AlertCategory.RISK,
        source="test.alert_message",
        session_id="test_session_456",
        context={"metric": 100.0},
    )


# =============================================================================
# STORED ALERT TESTS
# =============================================================================


class TestStoredAlert:
    """Tests für StoredAlert Dataclass."""

    def test_from_dict(self, sample_alert_dict: Dict[str, Any]):
        """Testet Erstellung aus Dict."""
        alert = StoredAlert.from_dict(sample_alert_dict)

        assert alert.title == "Test Alert"
        assert alert.body == "This is a test alert body."
        assert alert.severity == "WARN"
        assert alert.category == "RISK"
        assert alert.source == "test.source"
        assert alert.session_id == "test_session_123"
        assert "key" in alert.context

    def test_from_dict_defaults(self):
        """Testet Default-Werte bei fehlendenFeldern."""
        alert = StoredAlert.from_dict({"title": "Minimal"})

        assert alert.title == "Minimal"
        assert alert.severity == "INFO"
        assert alert.category == "SYSTEM"
        assert alert.context == {}

    def test_to_dict(self, sample_alert_dict: Dict[str, Any]):
        """Testet Serialisierung zu Dict."""
        alert = StoredAlert.from_dict(sample_alert_dict)
        alert.id = "test_id"
        result = alert.to_dict()

        assert result["id"] == "test_id"
        assert result["title"] == "Test Alert"
        assert result["severity"] == "WARN"
        assert "timestamp" in result

    def test_severity_level(self):
        """Testet severity_level Property."""
        info_alert = StoredAlert.from_dict({"severity": "INFO"})
        warn_alert = StoredAlert.from_dict({"severity": "WARN"})
        crit_alert = StoredAlert.from_dict({"severity": "CRITICAL"})

        assert info_alert.severity_level == 10
        assert warn_alert.severity_level == 20
        assert crit_alert.severity_level == 30


# =============================================================================
# ALERT STORAGE TESTS
# =============================================================================


class TestAlertStorage:
    """Tests für AlertStorage."""

    def test_init_creates_directory(self, tmp_path: Path):
        """Testet dass Storage-Verzeichnis erstellt wird."""
        storage_dir = tmp_path / "new_alerts"
        assert not storage_dir.exists()

        storage = AlertStorage(storage_dir)
        assert storage_dir.exists()
        assert storage.storage_dir == storage_dir

    def test_store_dict(self, storage: AlertStorage, sample_alert_dict: Dict[str, Any]):
        """Testet Speichern eines Dicts."""
        alert_id = storage.store(sample_alert_dict)

        assert alert_id is not None
        assert alert_id.startswith("alert_")

    def test_store_alert_message(self, storage: AlertStorage, sample_alert_message):
        """Testet Speichern eines AlertMessage-Objekts."""
        alert_id = storage.store(sample_alert_message)

        assert alert_id is not None
        assert alert_id.startswith("alert_")

    def test_store_creates_file(self, storage: AlertStorage, sample_alert_dict: Dict[str, Any]):
        """Testet dass Datei erstellt wird."""
        storage.store(sample_alert_dict)

        files = list(storage.storage_dir.glob("alerts_*.jsonl"))
        assert len(files) == 1

    def test_store_appends_to_file(self, storage: AlertStorage, sample_alert_dict: Dict[str, Any]):
        """Testet dass Alerts an Datei angehängt werden."""
        storage.store(sample_alert_dict)
        storage.store(sample_alert_dict)
        storage.store(sample_alert_dict)

        files = list(storage.storage_dir.glob("alerts_*.jsonl"))
        assert len(files) == 1

        # Prüfe Anzahl Zeilen
        with open(files[0], "r") as f:
            lines = f.readlines()
        assert len(lines) == 3

    def test_list_alerts_empty(self, storage: AlertStorage):
        """Testet leeres Storage."""
        alerts = storage.list_alerts()
        assert alerts == []

    def test_list_alerts_returns_stored(self, storage: AlertStorage, sample_alert_dict: Dict[str, Any]):
        """Testet dass gespeicherte Alerts zurückgegeben werden."""
        storage.store(sample_alert_dict)
        storage.store(sample_alert_dict)

        alerts = storage.list_alerts()
        assert len(alerts) == 2
        assert all(isinstance(a, StoredAlert) for a in alerts)

    def test_list_alerts_sorted_by_timestamp(self, storage: AlertStorage):
        """Testet Sortierung nach Timestamp (neueste zuerst)."""
        # Erstelle Alerts mit unterschiedlichen Timestamps
        now = datetime.now(timezone.utc)
        for i in range(3):
            alert = {
                "title": f"Alert {i}",
                "timestamp": (now - timedelta(hours=i)).isoformat(),
                "severity": "INFO",
            }
            storage.store(alert)

        alerts = storage.list_alerts()
        assert len(alerts) == 3
        assert alerts[0].title == "Alert 0"  # Neuester
        assert alerts[2].title == "Alert 2"  # Ältester

    def test_list_alerts_limit(self, storage: AlertStorage, sample_alert_dict: Dict[str, Any]):
        """Testet Limit-Parameter."""
        for _ in range(10):
            storage.store(sample_alert_dict)

        alerts = storage.list_alerts(limit=5)
        assert len(alerts) == 5

    def test_list_alerts_filter_severity(self, storage: AlertStorage):
        """Testet Severity-Filter."""
        storage.store({"title": "Info", "severity": "INFO"})
        storage.store({"title": "Warn", "severity": "WARN"})
        storage.store({"title": "Critical", "severity": "CRITICAL"})

        warn_alerts = storage.list_alerts(severity=["WARN"])
        assert len(warn_alerts) == 1
        assert warn_alerts[0].severity == "WARN"

        warn_crit = storage.list_alerts(severity=["WARN", "CRITICAL"])
        assert len(warn_crit) == 2

    def test_list_alerts_filter_category(self, storage: AlertStorage):
        """Testet Category-Filter."""
        storage.store({"title": "Risk", "category": "RISK"})
        storage.store({"title": "System", "category": "SYSTEM"})
        storage.store({"title": "Execution", "category": "EXECUTION"})

        risk_alerts = storage.list_alerts(category=["RISK"])
        assert len(risk_alerts) == 1
        assert risk_alerts[0].category == "RISK"

    def test_list_alerts_filter_session(self, storage: AlertStorage):
        """Testet Session-Filter."""
        storage.store({"title": "Session A", "session_id": "session_a"})
        storage.store({"title": "Session B", "session_id": "session_b"})
        storage.store({"title": "No Session"})

        session_a = storage.list_alerts(session_id="session_a")
        assert len(session_a) == 1
        assert session_a[0].session_id == "session_a"

    def test_list_alerts_filter_hours(self, storage: AlertStorage):
        """Testet Zeitfenster-Filter."""
        now = datetime.now(timezone.utc)

        # Alert vor 2 Stunden
        storage.store({
            "title": "Recent",
            "timestamp": (now - timedelta(hours=1)).isoformat(),
        })
        # Alert vor 48 Stunden
        storage.store({
            "title": "Old",
            "timestamp": (now - timedelta(hours=48)).isoformat(),
        })

        recent = storage.list_alerts(hours=24)
        assert len(recent) == 1
        assert recent[0].title == "Recent"

    def test_get_stats(self, storage: AlertStorage):
        """Testet Statistik-Berechnung."""
        storage.store({"severity": "INFO", "category": "SYSTEM"})
        storage.store({"severity": "WARN", "category": "RISK"})
        storage.store({"severity": "CRITICAL", "category": "RISK", "session_id": "s1"})
        storage.store({"severity": "WARN", "category": "SYSTEM", "session_id": "s2"})

        stats = storage.get_stats(hours=24)

        assert stats["total"] == 4
        assert stats["by_severity"]["INFO"] == 1
        assert stats["by_severity"]["WARN"] == 2
        assert stats["by_severity"]["CRITICAL"] == 1
        assert stats["by_category"]["RISK"] == 2
        assert stats["by_category"]["SYSTEM"] == 2
        assert stats["sessions_with_alerts"] == 2

    def test_get_stats_last_critical(self, storage: AlertStorage):
        """Testet dass letzter CRITICAL-Alert in Stats enthalten ist."""
        storage.store({"title": "Old Critical", "severity": "CRITICAL"})
        storage.store({"title": "New Critical", "severity": "CRITICAL"})

        stats = storage.get_stats(hours=24)

        assert stats["last_critical"] is not None
        assert stats["last_critical"]["title"] == "New Critical"

    def test_cleanup_old_files(self, storage: AlertStorage):
        """Testet Cleanup alter Dateien."""
        # Erstelle alte Datei
        old_date = datetime.now(timezone.utc) - timedelta(days=40)
        old_file = storage.storage_dir / f"alerts_{old_date.strftime('%Y-%m-%d')}.jsonl"
        old_file.write_text('{"title": "old"}')

        # Erstelle neue Datei
        storage.store({"title": "new"})

        # Cleanup
        storage._max_age_days = 30
        deleted = storage.cleanup_old_files()

        assert deleted == 1
        assert not old_file.exists()


# =============================================================================
# CONVENIENCE FUNCTIONS TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests für Convenience-Funktionen."""

    def test_store_alert_uses_default_storage(self, tmp_path: Path, monkeypatch):
        """Testet dass store_alert Default-Storage verwendet."""
        # Reset und setze neues Default-Verzeichnis
        reset_default_storage()

        # Patche den Default-Pfad
        import src.live.alert_storage as storage_module
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", tmp_path / "alerts")

        # Store Alert
        alert_id = store_alert({"title": "Test", "severity": "INFO"})

        assert alert_id is not None
        assert (tmp_path / "alerts").exists()

        # Cleanup
        reset_default_storage()

    def test_list_recent_alerts(self, tmp_path: Path, monkeypatch):
        """Testet list_recent_alerts."""
        reset_default_storage()

        import src.live.alert_storage as storage_module
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", tmp_path / "alerts")

        # Store some alerts
        store_alert({"title": "Alert 1", "severity": "WARN"})
        store_alert({"title": "Alert 2", "severity": "CRITICAL"})

        # List
        alerts = list_recent_alerts(limit=10, hours=24)
        assert len(alerts) == 2

        # Cleanup
        reset_default_storage()

    def test_get_alert_stats(self, tmp_path: Path, monkeypatch):
        """Testet get_alert_stats."""
        reset_default_storage()

        import src.live.alert_storage as storage_module
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", tmp_path / "alerts")

        # Store some alerts
        store_alert({"title": "A", "severity": "INFO"})
        store_alert({"title": "B", "severity": "WARN"})

        # Stats
        stats = get_alert_stats(hours=24)
        assert stats["total"] == 2

        # Cleanup
        reset_default_storage()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestPipelineIntegration:
    """Tests für Integration mit AlertPipelineManager."""

    def test_manager_persists_alerts(self, tmp_path: Path, monkeypatch):
        """Testet dass AlertPipelineManager Alerts persistiert."""
        from src.live.alert_pipeline import (
            AlertPipelineManager,
            AlertMessage,
            AlertSeverity,
            AlertCategory,
            NullAlertChannel,
        )
        import src.live.alert_storage as storage_module

        # Setup Storage
        reset_default_storage()
        storage_dir = tmp_path / "alerts"
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", storage_dir)

        # Manager mit persist_alerts=True (default)
        manager = AlertPipelineManager([NullAlertChannel()], persist_alerts=True)

        # Alert senden
        alert = AlertMessage(
            title="Test Persist",
            body="Body",
            severity=AlertSeverity.WARN,
            category=AlertCategory.RISK,
            source="test",
        )
        manager.send(alert)

        # Prüfen dass Alert gespeichert wurde
        storage = get_default_alert_storage()
        stored = storage.list_alerts(limit=10)
        assert len(stored) == 1
        assert stored[0].title == "Test Persist"

        # Cleanup
        reset_default_storage()

    def test_manager_persist_disabled(self, tmp_path: Path, monkeypatch):
        """Testet dass persist_alerts=False keine Alerts speichert."""
        from src.live.alert_pipeline import (
            AlertPipelineManager,
            AlertMessage,
            AlertSeverity,
            AlertCategory,
            NullAlertChannel,
        )
        import src.live.alert_storage as storage_module

        # Setup Storage
        reset_default_storage()
        storage_dir = tmp_path / "alerts"
        monkeypatch.setattr(storage_module, "_DEFAULT_ALERTS_DIR", storage_dir)

        # Manager mit persist_alerts=False
        manager = AlertPipelineManager([NullAlertChannel()], persist_alerts=False)

        # Alert senden
        alert = AlertMessage(
            title="Test No Persist",
            body="Body",
            severity=AlertSeverity.WARN,
            category=AlertCategory.RISK,
            source="test",
        )
        manager.send(alert)

        # Prüfen dass nichts gespeichert wurde
        assert not storage_dir.exists() or len(list(storage_dir.glob("*.jsonl"))) == 0

        # Cleanup
        reset_default_storage()


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests für Edge Cases."""

    def test_store_invalid_type(self, storage: AlertStorage):
        """Testet Fehlerbehandlung bei ungültigem Typ."""
        result = storage.store("invalid")
        assert result is None

    def test_list_from_nonexistent_dir(self, tmp_path: Path):
        """Testet Verhalten bei nicht-existierendem Verzeichnis."""
        storage = AlertStorage(tmp_path / "nonexistent")
        # Verzeichnis wird erstellt
        assert storage.storage_dir.exists()
        alerts = storage.list_alerts()
        assert alerts == []

    def test_invalid_json_line_skipped(self, storage: AlertStorage):
        """Testet dass ungültige JSON-Zeilen übersprungen werden."""
        # Erstelle Datei mit ungültiger Zeile
        today = datetime.now(timezone.utc)
        file_path = storage._get_file_path(today)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            f.write('{"title": "Valid"}\n')
            f.write('invalid json line\n')
            f.write('{"title": "Also Valid"}\n')

        alerts = storage.list_alerts()
        assert len(alerts) == 2

    def test_max_alerts_per_query_respected(self, storage: AlertStorage, sample_alert_dict: Dict[str, Any]):
        """Testet dass max_alerts_per_query nicht überschritten wird."""
        storage._max_alerts_per_query = 5

        for _ in range(10):
            storage.store(sample_alert_dict)

        # Selbst mit höherem Limit wird max begrenzt
        alerts = storage.list_alerts(limit=100)
        assert len(alerts) <= 5
