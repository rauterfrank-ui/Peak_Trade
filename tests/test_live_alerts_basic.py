# tests/test_live_alerts_basic.py
"""
Tests für src/live/alert_manager.py und src/live/alert_rules.py (Phase 66)
===========================================================================

Tests für Alert-Manager, Notifier und Alert-Regeln.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Pfad-Setup
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.live.alert_manager import (
    AlertManager,
    ConsoleAlertNotifier,
    EmailAlertNotifier,
    TelegramAlertNotifier,
)
from src.live.alert_rules import (
    check_pnl_drop,
    check_no_events,
    check_error_spike,
    MonitoringAPI,
)
from src.live.alerts import AlertEvent, AlertLevel
from src.live.monitoring import RunMetricPoint, RunSnapshot


# =============================================================================
# Test Fixtures
# =============================================================================


class FakeAlertSink:
    """Fake Alert-Sink für Tests (sammelt Alerts in Liste)."""

    def __init__(self) -> None:
        self.alerts: list[AlertEvent] = []

    def send(self, alert: AlertEvent) -> None:
        """Sammelt Alert."""
        self.alerts.append(alert)


@pytest.fixture
def fake_sink() -> FakeAlertSink:
    """Erstellt einen Fake Alert-Sink."""
    return FakeAlertSink()


@pytest.fixture
def alert_manager(fake_sink: FakeAlertSink) -> AlertManager:
    """Erstellt einen AlertManager mit Fake-Sink."""
    return AlertManager(notifiers=[fake_sink])


@pytest.fixture
def monitoring_api(tmp_path: Path) -> MonitoringAPI:
    """Erstellt eine MonitoringAPI mit Temp-Verzeichnis."""
    return MonitoringAPI(base_dir=str(tmp_path / "live_runs"))


# =============================================================================
# AlertManager Tests
# =============================================================================


def test_alert_manager_raise_alert(alert_manager: AlertManager, fake_sink: FakeAlertSink) -> None:
    """Test: AlertManager.raise_alert ruft Notifier auf."""
    alert_manager.raise_alert(
        level=AlertLevel.WARNING,
        source="test",
        code="TEST_ALERT",
        message="Test message",
        run_id="test_run",
        details={"key": "value"},
    )

    assert len(fake_sink.alerts) == 1
    alert = fake_sink.alerts[0]
    assert alert.level == AlertLevel.WARNING
    assert alert.source == "test"
    assert alert.code == "TEST_ALERT"
    assert alert.message == "Test message"
    assert alert.context["run_id"] == "test_run"
    assert alert.context["key"] == "value"


def test_alert_manager_info(alert_manager: AlertManager, fake_sink: FakeAlertSink) -> None:
    """Test: AlertManager.info erstellt INFO-Alert."""
    alert_manager.info(
        source="test",
        code="INFO_TEST",
        message="Info message",
    )

    assert len(fake_sink.alerts) == 1
    assert fake_sink.alerts[0].level == AlertLevel.INFO


def test_alert_manager_warning(alert_manager: AlertManager, fake_sink: FakeAlertSink) -> None:
    """Test: AlertManager.warning erstellt WARNING-Alert."""
    alert_manager.warning(
        source="test",
        code="WARNING_TEST",
        message="Warning message",
    )

    assert len(fake_sink.alerts) == 1
    assert fake_sink.alerts[0].level == AlertLevel.WARNING


def test_alert_manager_critical(alert_manager: AlertManager, fake_sink: FakeAlertSink) -> None:
    """Test: AlertManager.critical erstellt CRITICAL-Alert."""
    alert_manager.critical(
        source="test",
        code="CRITICAL_TEST",
        message="Critical message",
    )

    assert len(fake_sink.alerts) == 1
    assert fake_sink.alerts[0].level == AlertLevel.CRITICAL


def test_alert_manager_multiple_notifiers() -> None:
    """Test: AlertManager mit mehreren Notifiers."""
    sink1 = FakeAlertSink()
    sink2 = FakeAlertSink()

    manager = AlertManager(notifiers=[sink1, sink2])
    manager.warning(source="test", code="TEST", message="Test")

    assert len(sink1.alerts) == 1
    assert len(sink2.alerts) == 1


def test_alert_manager_notifier_exception() -> None:
    """Test: Exception in einem Notifier crasht nicht die anderen."""
    sink1 = FakeAlertSink()
    sink2 = MagicMock()
    sink2.send.side_effect = Exception("Notifier error")

    manager = AlertManager(notifiers=[sink1, sink2])
    manager.warning(source="test", code="TEST", message="Test")

    # Sink1 sollte trotzdem den Alert erhalten
    assert len(sink1.alerts) == 1


# =============================================================================
# Stub Notifier Tests
# =============================================================================


def test_console_alert_notifier() -> None:
    """Test: ConsoleAlertNotifier implementiert AlertSink Protocol."""
    notifier = ConsoleAlertNotifier(min_level=AlertLevel.INFO)
    alert = AlertEvent(
        ts=datetime.now(timezone.utc),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="Test",
    )

    # Sollte keine Exception werfen
    notifier.send(alert)


def test_email_alert_notifier_stub() -> None:
    """Test: EmailAlertNotifier ist Stub."""
    notifier = EmailAlertNotifier(
        smtp_host="localhost",
        smtp_port=587,
        from_addr="test@example.com",
        to_addrs=["recipient@example.com"],
    )
    alert = AlertEvent(
        ts=datetime.now(timezone.utc),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="Test",
    )

    # Sollte loggen, aber nicht crashen
    with patch("src.live.alert_manager.logger") as mock_logger:
        notifier.send(alert)
        mock_logger.info.assert_called_once()


def test_telegram_alert_notifier_stub() -> None:
    """Test: TelegramAlertNotifier ist Stub."""
    notifier = TelegramAlertNotifier(
        bot_token="fake_token",
        chat_id="fake_chat_id",
    )
    alert = AlertEvent(
        ts=datetime.now(timezone.utc),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="Test",
    )

    # Sollte loggen, aber nicht crashen
    with patch("src.live.alert_manager.logger") as mock_logger:
        notifier.send(alert)
        mock_logger.info.assert_called_once()


# =============================================================================
# Alert Rules Tests
# =============================================================================


def test_check_pnl_drop_alert(alert_manager: AlertManager, fake_sink: FakeAlertSink, monitoring_api: MonitoringAPI) -> None:
    """Test: PnL-Drop-Rule löst Alert aus bei Drop > Threshold."""
    run_id = "test_run"

    # Mock Zeitreihe mit Drop
    # Verwende größere Zeitabstände um Race-Conditions zu vermeiden
    timeseries = [
        RunMetricPoint(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=3),
            equity=10000.0,
        ),
        RunMetricPoint(
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=30),
            equity=9500.0,  # Innerhalb des Fensters
        ),
        RunMetricPoint(
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=1),
            equity=8500.0,  # 15% Drop insgesamt, >10% vom window_start
        ),
    ]

    with patch.object(monitoring_api, "get_timeseries", return_value=timeseries):
        result = check_pnl_drop(
            run_id=run_id,
            threshold_pct=5.0,
            window=timedelta(hours=1),
            monitoring=monitoring_api,
            alert_manager=alert_manager,
        )

        assert result is True
        assert len(fake_sink.alerts) == 1
        assert fake_sink.alerts[0].level == AlertLevel.CRITICAL
        assert fake_sink.alerts[0].code == "PNL_DROP"


def test_check_pnl_drop_no_alert(alert_manager: AlertManager, fake_sink: FakeAlertSink, monitoring_api: MonitoringAPI) -> None:
    """Test: PnL-Drop-Rule löst keinen Alert aus bei Drop < Threshold."""
    run_id = "test_run"

    # Mock Zeitreihe ohne großen Drop
    timeseries = [
        RunMetricPoint(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
            equity=10000.0,
        ),
        RunMetricPoint(
            timestamp=datetime.now(timezone.utc),
            equity=9900.0,  # Nur 1% Drop
        ),
    ]

    with patch.object(monitoring_api, "get_timeseries", return_value=timeseries):
        result = check_pnl_drop(
            run_id=run_id,
            threshold_pct=5.0,
            window=timedelta(hours=1),
            monitoring=monitoring_api,
            alert_manager=alert_manager,
        )

        assert result is False
        assert len(fake_sink.alerts) == 0


def test_check_no_events_alert(alert_manager: AlertManager, fake_sink: FakeAlertSink, monitoring_api: MonitoringAPI) -> None:
    """Test: No-Events-Rule löst Alert aus bei zu langer Stille."""
    run_id = "test_run"

    # Mock Snapshot mit altem last_event_time
    snapshot = RunSnapshot(
        run_id=run_id,
        mode="shadow",
        last_event_time=datetime.now(timezone.utc) - timedelta(minutes=15),
        num_events=10,
    )

    with patch.object(monitoring_api, "get_snapshot", return_value=snapshot):
        result = check_no_events(
            run_id=run_id,
            max_silence=timedelta(minutes=10),
            monitoring=monitoring_api,
            alert_manager=alert_manager,
        )

        assert result is True
        assert len(fake_sink.alerts) == 1
        assert fake_sink.alerts[0].code in ("NO_EVENTS", "NO_EVENTS_CRITICAL")


def test_check_no_events_no_alert(alert_manager: AlertManager, fake_sink: FakeAlertSink, monitoring_api: MonitoringAPI) -> None:
    """Test: No-Events-Rule löst keinen Alert aus bei frischen Events."""
    run_id = "test_run"

    # Mock Snapshot mit frischem last_event_time
    snapshot = RunSnapshot(
        run_id=run_id,
        mode="shadow",
        last_event_time=datetime.now(timezone.utc) - timedelta(minutes=5),
        num_events=10,
    )

    with patch.object(monitoring_api, "get_snapshot", return_value=snapshot):
        result = check_no_events(
            run_id=run_id,
            max_silence=timedelta(minutes=10),
            monitoring=monitoring_api,
            alert_manager=alert_manager,
        )

        assert result is False
        assert len(fake_sink.alerts) == 0


def test_check_error_spike_alert(alert_manager: AlertManager, fake_sink: FakeAlertSink, monitoring_api: MonitoringAPI) -> None:
    """Test: Error-Spike-Rule löst Alert aus bei zu vielen Fehlern."""
    run_id = "test_run"

    # Mock Events mit vielen Fehlern
    now = datetime.now(timezone.utc)
    events = [
        {
            "step": i,
            "ts_event": (now - timedelta(minutes=10-i)).isoformat(),
            "risk_reasons": f"Risk violation {i}" if i % 2 == 0 else "",
            "orders_rejected": 1 if i % 2 == 1 else 0,
        }
        for i in range(10)
    ]

    with patch.object(monitoring_api, "get_events", return_value=events):
        result = check_error_spike(
            run_id=run_id,
            max_errors=5,
            window=timedelta(minutes=10),
            monitoring=monitoring_api,
            alert_manager=alert_manager,
        )

        assert result is True
        assert len(fake_sink.alerts) == 1
        assert fake_sink.alerts[0].code in ("ERROR_SPIKE", "ERROR_SPIKE_CRITICAL")


def test_check_error_spike_no_alert(alert_manager: AlertManager, fake_sink: FakeAlertSink, monitoring_api: MonitoringAPI) -> None:
    """Test: Error-Spike-Rule löst keinen Alert aus bei wenigen Fehlern."""
    run_id = "test_run"

    # Mock Events mit wenigen Fehlern
    now = datetime.now(timezone.utc)
    events = [
        {
            "step": i,
            "ts_event": (now - timedelta(minutes=10-i)).isoformat(),
            "risk_reasons": "",
            "orders_rejected": 0,
        }
        for i in range(10)
    ]

    with patch.object(monitoring_api, "get_events", return_value=events):
        result = check_error_spike(
            run_id=run_id,
            max_errors=5,
            window=timedelta(minutes=10),
            monitoring=monitoring_api,
            alert_manager=alert_manager,
        )

        assert result is False
        assert len(fake_sink.alerts) == 0







