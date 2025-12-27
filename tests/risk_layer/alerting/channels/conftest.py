"""
Test fixtures and helpers for channel tests.

Provides:
- Event factories for different severities
- Mock helpers for network calls
- Temporary directory fixtures
- Channel introspection utilities
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertCategory, AlertSeverity


# ============================================================================
# Event Factories
# ============================================================================


@pytest.fixture
def event_factory():
    """Factory to create alert events with custom attributes."""

    def _factory(
        severity=AlertSeverity.INFO,
        category=AlertCategory.SYSTEM_HEALTH,
        source="test_source",
        message="Test message",
        context=None,
    ):
        return AlertEvent(
            severity=severity,
            category=category,
            source=source,
            message=message,
            context=context or {},
        )

    return _factory


@pytest.fixture
def event_debug(event_factory):
    """DEBUG level event."""
    return event_factory(
        severity=AlertSeverity.DEBUG,
        message="Debug message",
    )


@pytest.fixture
def event_info(event_factory):
    """INFO level event."""
    return event_factory(
        severity=AlertSeverity.INFO,
        message="Info message",
    )


@pytest.fixture
def event_warning(event_factory):
    """WARNING level event."""
    return event_factory(
        severity=AlertSeverity.WARNING,
        category=AlertCategory.RISK_LIMIT,
        source="var_gate",
        message="Warning: approaching limit",
        context={"current": 0.04, "limit": 0.05},
    )


@pytest.fixture
def event_error(event_factory):
    """ERROR level event."""
    return event_factory(
        severity=AlertSeverity.ERROR,
        category=AlertCategory.EXECUTION_ERROR,
        source="order_executor",
        message="Order failed",
        context={"order_id": "12345"},
    )


@pytest.fixture
def event_critical(event_factory):
    """CRITICAL level event."""
    return event_factory(
        severity=AlertSeverity.CRITICAL,
        category=AlertCategory.POSITION_VIOLATION,
        source="kill_switch",
        message="Kill switch activated",
        context={"reason": "emergency", "positions": 5},
    )


# ============================================================================
# Mock Helpers
# ============================================================================


@pytest.fixture
def mock_http_response():
    """Factory for mock HTTP responses."""

    def _factory(status=200, body=None):
        response = Mock()
        response.status = status
        if body:
            response.read.return_value = body.encode() if isinstance(body, str) else body
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        return response

    return _factory


@pytest.fixture
def mock_smtp_server():
    """Factory for mock SMTP servers."""

    def _factory():
        server = Mock()
        server.starttls = Mock()
        server.login = Mock()
        server.send_message = Mock()
        server.__enter__ = Mock(return_value=server)
        server.__exit__ = Mock(return_value=False)
        return server

    return _factory


# ============================================================================
# Channel Configs
# ============================================================================


@pytest.fixture
def console_config():
    """Console channel config."""
    return {
        "enabled": True,
        "format": "simple",
    }


@pytest.fixture
def file_config(tmp_path):
    """File channel config with temporary directory."""
    alerts_dir = tmp_path / "alerts"
    return {
        "enabled": True,
        "path": str(alerts_dir),
        "format": "jsonl",
        "rotation": "daily",
    }


@pytest.fixture
def slack_config():
    """Slack channel config (mocked)."""
    return {
        "enabled": True,
        "webhook_url": "https://hooks.slack.com/services/T/B/XXX",
        "channel": "#test",
        "username": "Test Bot",
        "mention_on_critical": ["@test"],
    }


@pytest.fixture
def webhook_config():
    """Webhook channel config (mocked)."""
    return {
        "enabled": True,
        "url": "https://example.com/webhook",
        "headers": {"X-Test": "value"},
        "timeout": 5,
    }


@pytest.fixture
def email_config():
    """Email channel config (mocked)."""
    return {
        "enabled": True,
        "smtp_host": "smtp.test.com",
        "smtp_port": 587,
        "smtp_user": "test@test.com",
        "smtp_password": "secret",
        "from_address": "alerts@test.com",
        "to_addresses": ["recipient@test.com"],
        "use_tls": True,
    }


@pytest.fixture
def telegram_config():
    """Telegram channel config (mocked)."""
    return {
        "enabled": True,
        "bot_token": "123456:ABC-DEF",
        "chat_id": "-1001234567890",
        "parse_mode": "Markdown",
    }


# ============================================================================
# Channel Introspection
# ============================================================================


def find_channel_class(module):
    """
    Find the AlertChannel subclass in a module.

    Resilient to naming changes - looks for any class
    that inherits from AlertChannel.
    """
    from src.risk_layer.alerting.channels.base_channel import AlertChannel

    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, AlertChannel) and obj is not AlertChannel:
            return obj
    raise ValueError(f"No AlertChannel subclass found in {module}")


@pytest.fixture
def channel_class_finder():
    """Fixture that provides channel class finder."""
    return find_channel_class
