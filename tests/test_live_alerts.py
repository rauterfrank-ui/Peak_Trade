# tests/test_live_alerts.py
"""
Tests für Live Alerts & Notifications (Phase 49 + 50)
=====================================================

Tests für:
- AlertLevel
- AlertEvent
- LoggingAlertSink
- StderrAlertSink
- WebhookAlertSink (Phase 50)
- SlackWebhookAlertSink (Phase 50)
- MultiAlertSink
- LiveAlertsConfig
- build_alert_sink_from_config
"""
from __future__ import annotations

import json
import logging
import urllib.request
from datetime import UTC, datetime

import pytest

from src.live.alerts import (
    AlertEvent,
    AlertLevel,
    LiveAlertsConfig,
    LoggingAlertSink,
    MultiAlertSink,
    SlackWebhookAlertSink,
    StderrAlertSink,
    WebhookAlertSink,
    build_alert_sink_from_config,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_alert_info() -> AlertEvent:
    """Erstellt Sample-INFO-Alert."""
    return AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.INFO,
        source="test.source",
        code="TEST_INFO",
        message="Test info message",
        context={"key": "value"},
    )


@pytest.fixture
def sample_alert_warning() -> AlertEvent:
    """Erstellt Sample-WARNING-Alert."""
    return AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test.source",
        code="TEST_WARNING",
        message="Test warning message",
        context={"key": "value"},
    )


@pytest.fixture
def sample_alert_critical() -> AlertEvent:
    """Erstellt Sample-CRITICAL-Alert."""
    return AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.CRITICAL,
        source="test.source",
        code="TEST_CRITICAL",
        message="Test critical message",
        context={"key": "value"},
    )


# =============================================================================
# ALERTLEVEL TESTS
# =============================================================================


def test_alert_level_ordering():
    """Testet dass AlertLevel-Ordering korrekt ist."""
    assert AlertLevel.INFO < AlertLevel.WARNING
    assert AlertLevel.WARNING < AlertLevel.CRITICAL
    assert AlertLevel.INFO < AlertLevel.CRITICAL


def test_alert_level_comparison():
    """Testet AlertLevel-Vergleiche."""
    assert AlertLevel.WARNING >= AlertLevel.INFO
    assert AlertLevel.CRITICAL >= AlertLevel.WARNING
    assert AlertLevel.CRITICAL > AlertLevel.INFO


# =============================================================================
# ALERTEVENT TESTS
# =============================================================================


def test_alert_event_creation(sample_alert_warning: AlertEvent):
    """Testet Erstellung eines AlertEvents."""
    assert sample_alert_warning.level == AlertLevel.WARNING
    assert sample_alert_warning.source == "test.source"
    assert sample_alert_warning.code == "TEST_WARNING"
    assert sample_alert_warning.message == "Test warning message"
    assert sample_alert_warning.context == {"key": "value"}


# =============================================================================
# LOGGINGALERTSINK TESTS
# =============================================================================


def test_logging_alert_sink_warning(caplog, sample_alert_warning: AlertEvent):
    """Testet LoggingAlertSink mit WARNING-Level."""
    logger = logging.getLogger("test_logger")
    sink = LoggingAlertSink(logger, min_level=AlertLevel.WARNING)

    with caplog.at_level(logging.WARNING):
        sink.send(sample_alert_warning)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert "TEST_WARNING" in caplog.records[0].message
    assert "Test warning message" in caplog.records[0].message


def test_logging_alert_sink_critical(caplog, sample_alert_critical: AlertEvent):
    """Testet LoggingAlertSink mit CRITICAL-Level."""
    logger = logging.getLogger("test_logger")
    sink = LoggingAlertSink(logger, min_level=AlertLevel.WARNING)

    with caplog.at_level(logging.ERROR):
        sink.send(sample_alert_critical)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert "TEST_CRITICAL" in caplog.records[0].message


def test_logging_alert_sink_info_filtered(caplog, sample_alert_info: AlertEvent):
    """Testet dass INFO-Alerts unterhalb min_level gefiltert werden."""
    logger = logging.getLogger("test_logger")
    sink = LoggingAlertSink(logger, min_level=AlertLevel.WARNING)

    with caplog.at_level(logging.INFO):
        sink.send(sample_alert_info)

    assert len(caplog.records) == 0


def test_logging_alert_sink_with_context(caplog, sample_alert_warning: AlertEvent):
    """Testet LoggingAlertSink mit Context."""
    logger = logging.getLogger("test_logger")
    sink = LoggingAlertSink(logger, min_level=AlertLevel.WARNING)

    with caplog.at_level(logging.WARNING):
        sink.send(sample_alert_warning)

    assert len(caplog.records) == 1
    assert "context=" in caplog.records[0].message


# =============================================================================
# STDERRALERTSINK TESTS
# =============================================================================


def test_stderr_alert_sink_warning(capfd, sample_alert_warning: AlertEvent):
    """Testet StderrAlertSink mit WARNING-Level."""
    sink = StderrAlertSink(min_level=AlertLevel.WARNING)

    sink.send(sample_alert_warning)

    captured = capfd.readouterr()
    assert "TEST_WARNING" in captured.err
    assert "Test warning message" in captured.err


def test_stderr_alert_sink_critical(capfd, sample_alert_critical: AlertEvent):
    """Testet StderrAlertSink mit CRITICAL-Level."""
    sink = StderrAlertSink(min_level=AlertLevel.WARNING)

    sink.send(sample_alert_critical)

    captured = capfd.readouterr()
    assert "CRITICAL" in captured.err
    assert "TEST_CRITICAL" in captured.err


def test_stderr_alert_sink_info_filtered(capfd, sample_alert_info: AlertEvent):
    """Testet dass INFO-Alerts unterhalb min_level gefiltert werden."""
    sink = StderrAlertSink(min_level=AlertLevel.WARNING)

    sink.send(sample_alert_info)

    captured = capfd.readouterr()
    assert "TEST_INFO" not in captured.err


# =============================================================================
# MULTIALERTSINK TESTS
# =============================================================================


def test_multi_alert_sink_forwards_to_all():
    """Testet dass MultiAlertSink an alle Sinks weiterleitet."""
    class CollectingSink:
        def __init__(self) -> None:
            self.events: list[AlertEvent] = []

        def send(self, alert: AlertEvent) -> None:
            self.events.append(alert)

    sink1 = CollectingSink()
    sink2 = CollectingSink()
    multi = MultiAlertSink([sink1, sink2])

    alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="Test",
    )

    multi.send(alert)

    assert len(sink1.events) == 1
    assert len(sink2.events) == 1
    assert sink1.events[0] == alert
    assert sink2.events[0] == alert


def test_multi_alert_sink_exception_handling(caplog):
    """Testet dass MultiAlertSink Exceptions in Sinks abfängt."""
    class FailingSink:
        def send(self, alert: AlertEvent) -> None:
            raise Exception("Test exception")

    class WorkingSink:
        def __init__(self) -> None:
            self.events: list[AlertEvent] = []

        def send(self, alert: AlertEvent) -> None:
            self.events.append(alert)

    failing = FailingSink()
    working = WorkingSink()
    multi = MultiAlertSink([failing, working])

    alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="Test",
    )

    # Sollte nicht crashen
    multi.send(alert)

    # Working-Sink sollte trotzdem aufgerufen worden sein
    assert len(working.events) == 1

    # Exception sollte geloggt worden sein
    assert any("Failed to send alert" in record.message for record in caplog.records)


# =============================================================================
# LIVEALERTSCONFIG TESTS
# =============================================================================


def test_live_alerts_config_from_dict_defaults():
    """Testet LiveAlertsConfig.from_dict mit Defaults."""
    config = LiveAlertsConfig.from_dict({})

    assert config.enabled is True
    assert config.min_level == AlertLevel.WARNING
    assert config.sinks == ["log"]
    assert config.log_logger_name == "peak_trade.live.alerts"


def test_live_alerts_config_from_dict_custom():
    """Testet LiveAlertsConfig.from_dict mit Custom-Werten."""
    config = LiveAlertsConfig.from_dict({
        "enabled": False,
        "min_level": "critical",
        "sinks": ["log", "stderr"],
        "log_logger_name": "custom.logger",
    })

    assert config.enabled is False
    assert config.min_level == AlertLevel.CRITICAL
    assert config.sinks == ["log", "stderr"]
    assert config.log_logger_name == "custom.logger"


def test_live_alerts_config_from_dict_level_info():
    """Testet LiveAlertsConfig.from_dict mit level='info'."""
    config = LiveAlertsConfig.from_dict({"min_level": "info"})

    assert config.min_level == AlertLevel.INFO


def test_live_alerts_config_from_dict_sinks_string():
    """Testet LiveAlertsConfig.from_dict mit sinks als String."""
    config = LiveAlertsConfig.from_dict({"sinks": "stderr"})

    assert config.sinks == ["stderr"]


# =============================================================================
# BUILD_ALERT_SINK_FROM_CONFIG TESTS
# =============================================================================


def test_build_alert_sink_from_config_disabled():
    """Testet build_alert_sink_from_config mit enabled=False."""
    config = LiveAlertsConfig(enabled=False)
    sink = build_alert_sink_from_config(config)

    assert sink is None


def test_build_alert_sink_from_config_log_sink():
    """Testet build_alert_sink_from_config mit 'log' Sink."""
    config = LiveAlertsConfig(enabled=True, sinks=["log"])
    sink = build_alert_sink_from_config(config)

    assert sink is not None
    assert isinstance(sink, LoggingAlertSink)


def test_build_alert_sink_from_config_stderr_sink():
    """Testet build_alert_sink_from_config mit 'stderr' Sink."""
    config = LiveAlertsConfig(enabled=True, sinks=["stderr"])
    sink = build_alert_sink_from_config(config)

    assert sink is not None
    assert isinstance(sink, StderrAlertSink)


def test_build_alert_sink_from_config_multi_sink():
    """Testet build_alert_sink_from_config mit mehreren Sinks."""
    config = LiveAlertsConfig(enabled=True, sinks=["log", "stderr"])
    sink = build_alert_sink_from_config(config)

    assert sink is not None
    assert isinstance(sink, MultiAlertSink)


def test_build_alert_sink_from_config_unknown_sink(caplog):
    """Testet build_alert_sink_from_config mit unbekanntem Sink."""
    config = LiveAlertsConfig(enabled=True, sinks=["unknown_sink"])
    sink = build_alert_sink_from_config(config)

    # Sollte None zurückgeben, da keine gültigen Sinks
    assert sink is None

    # Warnung sollte geloggt worden sein
    assert any("Unknown alert sink name" in record.message for record in caplog.records)


def test_build_alert_sink_from_config_empty_sinks():
    """Testet build_alert_sink_from_config mit leerer Sinks-Liste."""
    config = LiveAlertsConfig(enabled=True, sinks=[])
    sink = build_alert_sink_from_config(config)

    assert sink is None


# =============================================================================
# WEBHOOKALERTSINK TESTS (Phase 50)
# =============================================================================


def test_webhook_alert_sink_respects_min_level(monkeypatch):
    """Testet dass WebhookAlertSink min_level respektiert."""
    called = []

    def fake_urlopen(req, timeout=0):
        called.append((req.full_url, timeout, req.data))
        class DummyResp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    sink = WebhookAlertSink(
        urls=["https://example.com/hook"],
        timeout_seconds=1.5,
        min_level=AlertLevel.WARNING,
    )

    low_alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.INFO,
        source="test",
        code="TEST",
        message="info level",
        context={},
    )

    high_alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.CRITICAL,
        source="test",
        code="TEST",
        message="critical",
        context={"foo": "bar"},
    )

    sink.send(low_alert)
    sink.send(high_alert)

    assert len(called) == 1
    url, timeout, data = called[0]
    assert url == "https://example.com/hook"
    assert timeout == 1.5
    payload = json.loads(data.decode("utf-8"))
    assert payload["level"] == "CRITICAL"
    assert payload["code"] == "TEST"
    assert payload["context"] == {"foo": "bar"}


def test_webhook_alert_sink_empty_urls():
    """Testet dass WebhookAlertSink mit leeren URLs nichts tut."""
    sink = WebhookAlertSink(urls=[], min_level=AlertLevel.INFO)

    alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="test",
    )

    # Sollte nicht crashen
    sink.send(alert)


def test_webhook_alert_sink_multiple_urls(monkeypatch):
    """Testet dass WebhookAlertSink mehrere URLs ansteuert."""
    called_urls = []

    def fake_urlopen(req, timeout=0):
        called_urls.append(req.full_url)
        class DummyResp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    sink = WebhookAlertSink(
        urls=["https://example.com/hook1", "https://example.com/hook2"],
        min_level=AlertLevel.INFO,
    )

    alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="test",
    )

    sink.send(alert)

    assert len(called_urls) == 2
    assert "https://example.com/hook1" in called_urls
    assert "https://example.com/hook2" in called_urls


def test_webhook_alert_sink_exception_handling(monkeypatch, caplog):
    """Testet dass WebhookAlertSink Exceptions abfängt und loggt."""
    def fake_urlopen(req, timeout=0):
        raise Exception("Network error")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    sink = WebhookAlertSink(
        urls=["https://example.com/hook"],
        min_level=AlertLevel.INFO,
    )

    alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="test",
    )

    # Sollte nicht crashen
    sink.send(alert)

    # Exception sollte geloggt worden sein
    assert any("Failed to send alert to webhook" in record.message for record in caplog.records)


# =============================================================================
# SLACKWEBHOOKALERTSINK TESTS (Phase 50)
# =============================================================================


def test_slack_webhook_alert_sink_builds_text(monkeypatch):
    """Testet dass SlackWebhookAlertSink korrekten Text baut."""
    called = []

    def fake_urlopen(req, timeout=0):
        called.append(json.loads(req.data.decode("utf-8")))
        class DummyResp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    sink = SlackWebhookAlertSink(
        urls=["https://hooks.slack.com/services/AAA/BBB/CCC"],
        timeout_seconds=2.0,
        min_level=AlertLevel.INFO,
    )

    alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="live_risk.portfolio",
        code="RISK_LIMIT_VIOLATION_PORTFOLIO",
        message="Limit breached",
        context={"total_notional": 12345.0},
    )

    sink.send(alert)

    assert len(called) == 1
    payload = called[0]
    assert "text" in payload
    assert "RISK_LIMIT_VIOLATION_PORTFOLIO" in payload["text"]
    assert "total_notional" in payload["text"]


def test_slack_webhook_alert_sink_respects_min_level(monkeypatch):
    """Testet dass SlackWebhookAlertSink min_level respektiert."""
    called = []

    def fake_urlopen(req, timeout=0):
        called.append(req.data)
        class DummyResp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    sink = SlackWebhookAlertSink(
        urls=["https://hooks.slack.com/services/AAA/BBB/CCC"],
        min_level=AlertLevel.WARNING,
    )

    info_alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.INFO,
        source="test",
        code="TEST",
        message="info",
    )

    warning_alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="warning",
    )

    sink.send(info_alert)
    sink.send(warning_alert)

    assert len(called) == 1


def test_slack_webhook_alert_sink_empty_urls():
    """Testet dass SlackWebhookAlertSink mit leeren URLs nichts tut."""
    sink = SlackWebhookAlertSink(urls=[], min_level=AlertLevel.INFO)

    alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="test",
    )

    # Sollte nicht crashen
    sink.send(alert)


# =============================================================================
# BUILD_ALERT_SINK_FROM_CONFIG - WEBHOOK/SLACK TESTS (Phase 50)
# =============================================================================


def test_build_alert_sink_from_config_webhook(monkeypatch):
    """Testet build_alert_sink_from_config mit 'webhook' Sink."""
    called = []

    def fake_urlopen(req, timeout=0):
        called.append(req.full_url)
        class DummyResp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    config = LiveAlertsConfig(
        enabled=True,
        sinks=["webhook"],
        webhook_urls=["https://example.com/hook"],
    )
    sink = build_alert_sink_from_config(config)

    assert sink is not None
    assert isinstance(sink, WebhookAlertSink)

    alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="test",
    )

    sink.send(alert)

    assert len(called) == 1


def test_build_alert_sink_from_config_slack_webhook(monkeypatch):
    """Testet build_alert_sink_from_config mit 'slack_webhook' Sink."""
    called = []

    def fake_urlopen(req, timeout=0):
        called.append(req.full_url)
        class DummyResp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    config = LiveAlertsConfig(
        enabled=True,
        sinks=["slack_webhook"],
        slack_webhook_urls=["https://hooks.slack.com/services/AAA/BBB/CCC"],
    )
    sink = build_alert_sink_from_config(config)

    assert sink is not None
    assert isinstance(sink, SlackWebhookAlertSink)

    alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="test",
    )

    sink.send(alert)

    assert len(called) == 1


def test_build_alert_sink_from_config_webhook_no_urls(caplog):
    """Testet build_alert_sink_from_config mit 'webhook' aber ohne URLs."""
    config = LiveAlertsConfig(
        enabled=True,
        sinks=["webhook"],
        webhook_urls=[],
    )
    sink = build_alert_sink_from_config(config)

    # Sollte None zurückgeben, da keine URLs konfiguriert
    assert sink is None

    # Warnung sollte geloggt worden sein
    assert any("no webhook_urls are configured" in record.message for record in caplog.records)


def test_build_alert_sink_from_config_slack_webhook_no_urls(caplog):
    """Testet build_alert_sink_from_config mit 'slack_webhook' aber ohne URLs."""
    config = LiveAlertsConfig(
        enabled=True,
        sinks=["slack_webhook"],
        slack_webhook_urls=[],
    )
    sink = build_alert_sink_from_config(config)

    # Sollte None zurückgeben, da keine URLs konfiguriert
    assert sink is None

    # Warnung sollte geloggt worden sein
    assert any("no slack_webhook_urls are configured" in record.message for record in caplog.records)


def test_build_alert_sink_from_config_multi_with_webhook(monkeypatch):
    """Testet build_alert_sink_from_config mit mehreren Sinks inkl. Webhook."""
    called = []

    def fake_urlopen(req, timeout=0):
        called.append(req.full_url)
        class DummyResp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    config = LiveAlertsConfig(
        enabled=True,
        sinks=["log", "webhook"],
        webhook_urls=["https://example.com/hook"],
    )
    sink = build_alert_sink_from_config(config)

    assert sink is not None
    assert isinstance(sink, MultiAlertSink)

    alert = AlertEvent(
        ts=datetime.now(UTC),
        level=AlertLevel.WARNING,
        source="test",
        code="TEST",
        message="test",
    )

    sink.send(alert)

    # Webhook sollte aufgerufen worden sein
    assert len(called) == 1


def test_live_alerts_config_from_dict_webhook_fields():
    """Testet LiveAlertsConfig.from_dict mit Webhook-Feldern."""
    config = LiveAlertsConfig.from_dict({
        "webhook_urls": ["https://example.com/hook"],
        "slack_webhook_urls": ["https://hooks.slack.com/services/AAA/BBB/CCC"],
        "webhook_timeout_seconds": 5.0,
    })

    assert config.webhook_urls == ["https://example.com/hook"]
    assert config.slack_webhook_urls == ["https://hooks.slack.com/services/AAA/BBB/CCC"]
    assert config.webhook_timeout_seconds == 5.0


def test_live_alerts_config_from_dict_webhook_urls_string():
    """Testet LiveAlertsConfig.from_dict mit webhook_urls als String."""
    config = LiveAlertsConfig.from_dict({
        "webhook_urls": "https://example.com/hook",
    })

    assert config.webhook_urls == ["https://example.com/hook"]
