# tests/test_notifications_smoke.py
"""
Smoke-Tests für den Peak_Trade Notification Layer.

Testet:
- Alert-Dataclass-Instanziierung
- ConsoleNotifier-Ausgabe
- FileNotifier-Schreiben
- CombinedNotifier-Kombination
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest


class TestAlert:
    """Tests für die Alert-Dataclass."""

    def test_alert_creation_basic(self):
        """Alert kann mit minimalen Parametern erstellt werden."""
        from src.notifications.base import Alert

        alert = Alert(
            level="info",
            source="test",
            message="Test message",
            timestamp=datetime.utcnow(),
            context={},
        )

        assert alert.level == "info"
        assert alert.source == "test"
        assert alert.message == "Test message"
        assert isinstance(alert.timestamp, datetime)
        assert alert.context == {}

    def test_alert_creation_with_context(self):
        """Alert kann mit Context erstellt werden."""
        from src.notifications.base import Alert

        ctx = {"strategy_key": "ma_crossover", "symbol": "BTC/EUR", "value": 42}
        alert = Alert(
            level="warning",
            source="forward_signal",
            message="Signal detected",
            timestamp=datetime.utcnow(),
            context=ctx,
        )

        assert alert.context == ctx
        assert alert.context["strategy_key"] == "ma_crossover"

    def test_alert_all_levels(self):
        """Alle gültigen Alert-Levels können erstellt werden."""
        from src.notifications.base import Alert

        for level in ["info", "warning", "critical"]:
            alert = Alert(
                level=level,
                source="test",
                message=f"Test {level}",
                timestamp=datetime.utcnow(),
                context={},
            )
            assert alert.level == level

    def test_alert_invalid_level_raises(self):
        """Ungültiges Level wirft ValueError."""
        from src.notifications.base import Alert

        with pytest.raises(ValueError, match="Invalid alert level"):
            Alert(
                level="invalid",  # type: ignore
                source="test",
                message="Test",
                timestamp=datetime.utcnow(),
                context={},
            )

    def test_alert_empty_source_raises(self):
        """Leerer Source wirft ValueError."""
        from src.notifications.base import Alert

        with pytest.raises(ValueError, match="source cannot be empty"):
            Alert(
                level="info",
                source="",
                message="Test",
                timestamp=datetime.utcnow(),
                context={},
            )

    def test_alert_empty_message_raises(self):
        """Leere Message wirft ValueError."""
        from src.notifications.base import Alert

        with pytest.raises(ValueError, match="message cannot be empty"):
            Alert(
                level="info",
                source="test",
                message="",
                timestamp=datetime.utcnow(),
                context={},
            )


class TestCreateAlert:
    """Tests für die create_alert Helper-Funktion."""

    def test_create_alert_sets_timestamp(self):
        """create_alert setzt automatisch den Timestamp."""
        from src.notifications.base import create_alert

        before = datetime.utcnow()
        alert = create_alert(
            level="info",
            source="test",
            message="Test message",
        )
        after = datetime.utcnow()

        assert before <= alert.timestamp <= after

    def test_create_alert_with_context(self):
        """create_alert kann Context übergeben werden."""
        from src.notifications.base import create_alert

        alert = create_alert(
            level="warning",
            source="test",
            message="Test",
            context={"foo": "bar"},
        )

        assert alert.context == {"foo": "bar"}


class TestSignalLevelFromValue:
    """Tests für signal_level_from_value Funktion."""

    def test_strong_positive_signal_is_warning(self):
        """Starkes positives Signal (>=1) ist WARNING."""
        from src.notifications.base import signal_level_from_value

        assert signal_level_from_value(1.0) == "warning"
        assert signal_level_from_value(1.5) == "warning"

    def test_strong_negative_signal_is_warning(self):
        """Starkes negatives Signal (<=-1) ist WARNING."""
        from src.notifications.base import signal_level_from_value

        assert signal_level_from_value(-1.0) == "warning"
        assert signal_level_from_value(-2.0) == "warning"

    def test_weak_signal_is_info(self):
        """Schwaches Signal (<1) ist INFO."""
        from src.notifications.base import signal_level_from_value

        assert signal_level_from_value(0.0) == "info"
        assert signal_level_from_value(0.5) == "info"
        assert signal_level_from_value(-0.5) == "info"


class TestConsoleNotifier:
    """Tests für ConsoleNotifier."""

    def test_console_notifier_send_captures_output(self, capsys):
        """ConsoleNotifier gibt Alert auf stdout aus."""
        from src.notifications.base import Alert
        from src.notifications.console import ConsoleNotifier

        notifier = ConsoleNotifier()
        alert = Alert(
            level="info",
            source="test",
            message="Hello console",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            context={},
        )

        notifier.send(alert)

        captured = capsys.readouterr()
        assert "[INFO]" in captured.out
        assert "[test]" in captured.out
        assert "Hello console" in captured.out

    def test_console_notifier_critical_on_stderr(self, capsys):
        """Critical-Alerts werden auf stderr ausgegeben."""
        from src.notifications.base import Alert
        from src.notifications.console import ConsoleNotifier

        notifier = ConsoleNotifier(use_stderr=True)
        alert = Alert(
            level="critical",
            source="test",
            message="Critical error",
            timestamp=datetime.utcnow(),
            context={},
        )

        notifier.send(alert)

        captured = capsys.readouterr()
        assert "[CRITICAL]" in captured.err
        assert "Critical error" in captured.err

    def test_console_notifier_min_level_filters(self, capsys):
        """min_level filtert niedrigere Levels aus."""
        from src.notifications.base import Alert
        from src.notifications.console import ConsoleNotifier

        notifier = ConsoleNotifier(min_level="warning")
        info_alert = Alert(
            level="info",
            source="test",
            message="Info message",
            timestamp=datetime.utcnow(),
            context={},
        )
        warning_alert = Alert(
            level="warning",
            source="test",
            message="Warning message",
            timestamp=datetime.utcnow(),
            context={},
        )

        notifier.send(info_alert)
        notifier.send(warning_alert)

        captured = capsys.readouterr()
        assert "Info message" not in captured.out
        assert "Warning message" in captured.out

    def test_console_notifier_show_context(self, capsys):
        """show_context=True zeigt Context an."""
        from src.notifications.base import Alert
        from src.notifications.console import ConsoleNotifier

        notifier = ConsoleNotifier(show_context=True)
        alert = Alert(
            level="info",
            source="test",
            message="Test",
            timestamp=datetime.utcnow(),
            context={"foo": "bar", "num": 42},
        )

        notifier.send(alert)

        captured = capsys.readouterr()
        assert "foo=bar" in captured.out
        assert "num=42" in captured.out


class TestFileNotifier:
    """Tests für FileNotifier."""

    def test_file_notifier_writes_to_file(self, tmp_path: Path):
        """FileNotifier schreibt Alert in Datei."""
        from src.notifications.base import Alert
        from src.notifications.file import FileNotifier

        log_path = tmp_path / "alerts.log"
        notifier = FileNotifier(log_path)

        alert = Alert(
            level="warning",
            source="test",
            message="Hello file",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            context={},
        )

        notifier.send(alert)

        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert "Hello file" in content
        assert "warning" in content
        assert "test" in content

    def test_file_notifier_appends(self, tmp_path: Path):
        """FileNotifier fügt mehrere Alerts an."""
        from src.notifications.base import Alert
        from src.notifications.file import FileNotifier

        log_path = tmp_path / "alerts.log"
        notifier = FileNotifier(log_path)

        for i in range(3):
            alert = Alert(
                level="info",
                source="test",
                message=f"Message {i}",
                timestamp=datetime.utcnow(),
                context={},
            )
            notifier.send(alert)

        content = log_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 3
        assert "Message 0" in lines[0]
        assert "Message 2" in lines[2]

    def test_file_notifier_creates_parent_dirs(self, tmp_path: Path):
        """FileNotifier erstellt Parent-Verzeichnisse."""
        from src.notifications.base import Alert
        from src.notifications.file import FileNotifier

        log_path = tmp_path / "deep" / "nested" / "alerts.log"
        notifier = FileNotifier(log_path)

        alert = Alert(
            level="info",
            source="test",
            message="Nested test",
            timestamp=datetime.utcnow(),
            context={},
        )

        notifier.send(alert)

        assert log_path.exists()

    def test_file_notifier_json_format(self, tmp_path: Path):
        """FileNotifier kann JSON-Format schreiben."""
        import json

        from src.notifications.base import Alert
        from src.notifications.file import FileNotifier

        log_path = tmp_path / "alerts.jsonl"
        notifier = FileNotifier(log_path, format="json")

        alert = Alert(
            level="warning",
            source="test",
            message="JSON test",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            context={"key": "value"},
        )

        notifier.send(alert)

        content = log_path.read_text(encoding="utf-8")
        data = json.loads(content.strip())

        assert data["level"] == "warning"
        assert data["source"] == "test"
        assert data["message"] == "JSON test"
        assert data["context"] == {"key": "value"}

    def test_file_notifier_min_level_filters(self, tmp_path: Path):
        """min_level filtert niedrigere Levels aus."""
        from src.notifications.base import Alert
        from src.notifications.file import FileNotifier

        log_path = tmp_path / "alerts.log"
        notifier = FileNotifier(log_path, min_level="warning")

        info_alert = Alert(
            level="info",
            source="test",
            message="Info should be filtered",
            timestamp=datetime.utcnow(),
            context={},
        )
        warning_alert = Alert(
            level="warning",
            source="test",
            message="Warning should appear",
            timestamp=datetime.utcnow(),
            context={},
        )

        notifier.send(info_alert)
        notifier.send(warning_alert)

        content = log_path.read_text(encoding="utf-8")
        assert "Info should be filtered" not in content
        assert "Warning should appear" in content


class TestCombinedNotifier:
    """Tests für CombinedNotifier."""

    def test_combined_notifier_sends_to_all(self, tmp_path: Path, capsys):
        """CombinedNotifier sendet an alle konfigurierten Notifier."""
        from src.notifications.base import Alert
        from src.notifications.combined import CombinedNotifier
        from src.notifications.console import ConsoleNotifier
        from src.notifications.file import FileNotifier

        log_path = tmp_path / "alerts.log"
        combined = CombinedNotifier([
            ConsoleNotifier(),
            FileNotifier(log_path),
        ])

        alert = Alert(
            level="warning",
            source="test",
            message="Combined test",
            timestamp=datetime.utcnow(),
            context={},
        )

        combined.send(alert)

        # Check console output
        captured = capsys.readouterr()
        assert "Combined test" in captured.out

        # Check file output
        content = log_path.read_text(encoding="utf-8")
        assert "Combined test" in content

    def test_combined_notifier_continues_on_error(self, tmp_path: Path, capsys):
        """CombinedNotifier setzt fort, auch wenn ein Notifier fehlschlägt."""
        from src.notifications.base import Alert
        from src.notifications.combined import CombinedNotifier
        from src.notifications.console import ConsoleNotifier

        class FailingNotifier:
            def send(self, alert: Alert) -> None:
                raise RuntimeError("Intentional failure")

        combined = CombinedNotifier([
            FailingNotifier(),
            ConsoleNotifier(),
        ])

        alert = Alert(
            level="info",
            source="test",
            message="Should still appear",
            timestamp=datetime.utcnow(),
            context={},
        )

        # Should not raise
        combined.send(alert)

        captured = capsys.readouterr()
        # Console output should appear despite first notifier failing
        assert "Should still appear" in captured.out
        # Error message should be on stderr
        assert "NOTIFIER ERROR" in captured.err

    def test_combined_notifier_add(self, capsys):
        """CombinedNotifier.add() fügt Notifier hinzu."""
        from src.notifications.base import Alert
        from src.notifications.combined import CombinedNotifier
        from src.notifications.console import ConsoleNotifier

        combined = CombinedNotifier([])
        combined.add(ConsoleNotifier())

        assert len(combined.notifiers) == 1

        alert = Alert(
            level="info",
            source="test",
            message="Added notifier test",
            timestamp=datetime.utcnow(),
            context={},
        )

        combined.send(alert)

        captured = capsys.readouterr()
        assert "Added notifier test" in captured.out


class TestNotifierProtocol:
    """Tests für das Notifier-Protocol."""

    def test_console_notifier_is_notifier(self):
        """ConsoleNotifier erfüllt das Notifier-Protocol."""
        from src.notifications.base import Notifier
        from src.notifications.console import ConsoleNotifier

        notifier = ConsoleNotifier()
        assert isinstance(notifier, Notifier)

    def test_file_notifier_is_notifier(self, tmp_path: Path):
        """FileNotifier erfüllt das Notifier-Protocol."""
        from src.notifications.base import Notifier
        from src.notifications.file import FileNotifier

        notifier = FileNotifier(tmp_path / "test.log")
        assert isinstance(notifier, Notifier)

    def test_custom_notifier_protocol(self):
        """Eigene Klassen können das Notifier-Protocol erfüllen."""
        from src.notifications.base import Alert, Notifier

        class MyNotifier:
            def __init__(self):
                self.alerts = []

            def send(self, alert: Alert) -> None:
                self.alerts.append(alert)

        notifier = MyNotifier()
        assert isinstance(notifier, Notifier)

        alert = Alert(
            level="info",
            source="test",
            message="Custom notifier",
            timestamp=datetime.utcnow(),
            context={},
        )

        notifier.send(alert)
        assert len(notifier.alerts) == 1
        assert notifier.alerts[0].message == "Custom notifier"
