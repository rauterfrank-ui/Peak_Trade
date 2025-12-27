"""
Tests for Risk Layer Notification Channels
===========================================
"""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.risk_layer.alerting.models import AlertSeverity, AlertEvent
from src.risk_layer.alerting.channels import (
    ConsoleChannel,
    FileChannel,
    EmailChannel,
    SlackChannel,
    TelegramChannel,
    WebhookChannel,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_alert():
    """Create a sample alert for testing."""
    return AlertEvent(
        source="test_source",
        severity=AlertSeverity.WARN,
        title="Test Alert",
        body="This is a test alert",
        labels={"env": "test"},
    )


@pytest.fixture
def critical_alert():
    """Create a critical alert for testing."""
    return AlertEvent(
        source="risk_gate",
        severity=AlertSeverity.CRITICAL,
        title="Critical Risk Breach",
        body="Position limit exceeded",
        labels={"portfolio": "main"},
    )


# =============================================================================
# CONSOLE CHANNEL TESTS
# =============================================================================


def test_console_channel_enabled():
    """Test that console channel is always enabled."""
    channel = ConsoleChannel()
    assert channel.enabled is True


def test_console_channel_send(sample_alert, capsys):
    """Test console channel sends to stdout."""
    channel = ConsoleChannel(color=False)
    result = channel.send(sample_alert)

    assert result is True

    captured = capsys.readouterr()
    assert "Test Alert" in captured.out
    assert "test_source" in captured.out


def test_console_channel_with_color(sample_alert, capsys):
    """Test console channel with color enabled."""
    channel = ConsoleChannel(color=True)
    result = channel.send(sample_alert)

    assert result is True

    captured = capsys.readouterr()
    assert "Test Alert" in captured.out


# =============================================================================
# FILE CHANNEL TESTS
# =============================================================================


def test_file_channel_disabled_by_default():
    """Test that file channel is disabled without configuration."""
    channel = FileChannel()
    assert channel.enabled is False


def test_file_channel_enabled_with_path(tmp_path):
    """Test that file channel is enabled with path."""
    file_path = tmp_path / "alerts.jsonl"
    channel = FileChannel(file_path=str(file_path))
    assert channel.enabled is True


def test_file_channel_send(sample_alert, tmp_path):
    """Test file channel writes to JSONL file."""
    file_path = tmp_path / "alerts.jsonl"
    channel = FileChannel(file_path=str(file_path))

    result = channel.send(sample_alert)
    assert result is True
    assert file_path.exists()

    # Verify content
    with open(file_path) as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["title"] == "Test Alert"
        assert data["source"] == "test_source"


def test_file_channel_multiple_sends(sample_alert, critical_alert, tmp_path):
    """Test file channel appends multiple alerts."""
    file_path = tmp_path / "alerts.jsonl"
    channel = FileChannel(file_path=str(file_path))

    channel.send(sample_alert)
    channel.send(critical_alert)

    # Verify both alerts written
    with open(file_path) as f:
        lines = f.readlines()
        assert len(lines) == 2


def test_file_channel_creates_directory(sample_alert, tmp_path):
    """Test file channel creates parent directories."""
    file_path = tmp_path / "subdir" / "alerts.jsonl"
    channel = FileChannel(file_path=str(file_path))

    result = channel.send(sample_alert)
    assert result is True
    assert file_path.exists()
    assert file_path.parent.exists()


def test_file_channel_env_var(sample_alert, tmp_path, monkeypatch):
    """Test file channel reads from environment variable."""
    file_path = tmp_path / "alerts.jsonl"
    monkeypatch.setenv("RISK_ALERTS_FILE", str(file_path))

    channel = FileChannel()
    assert channel.enabled is True

    result = channel.send(sample_alert)
    assert result is True
    assert file_path.exists()


# =============================================================================
# EMAIL CHANNEL TESTS
# =============================================================================


def test_email_channel_disabled_by_default():
    """Test that email channel is disabled without configuration."""
    channel = EmailChannel()
    assert channel.enabled is False


def test_email_channel_enabled_with_config():
    """Test that email channel is enabled with full config."""
    channel = EmailChannel(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user@example.com",
        smtp_password="secret",
        from_email="alerts@example.com",
        to_emails=["admin@example.com"],
    )
    assert channel.enabled is True


def test_email_channel_partial_config():
    """Test that email channel is disabled with partial config."""
    channel = EmailChannel(
        smtp_host="smtp.example.com",
        smtp_user="user@example.com",
        # Missing password and from_email
    )
    assert channel.enabled is False


@patch("smtplib.SMTP")
def test_email_channel_send(mock_smtp, sample_alert):
    """Test email channel sends email."""
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    channel = EmailChannel(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user@example.com",
        smtp_password="secret",
        from_email="alerts@example.com",
        to_emails=["admin@example.com"],
    )

    result = channel.send(sample_alert)
    assert result is True

    # Verify SMTP calls
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "secret")
    mock_server.send_message.assert_called_once()


@patch("smtplib.SMTP")
def test_email_channel_smtp_error(mock_smtp, sample_alert):
    """Test email channel handles SMTP errors."""
    mock_smtp.side_effect = Exception("SMTP connection failed")

    channel = EmailChannel(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user@example.com",
        smtp_password="secret",
        from_email="alerts@example.com",
        to_emails=["admin@example.com"],
    )

    result = channel.send(sample_alert)
    assert result is False


def test_email_channel_env_vars(monkeypatch):
    """Test email channel reads from environment variables."""
    monkeypatch.setenv("RISK_ALERTS_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("RISK_ALERTS_SMTP_PORT", "587")
    monkeypatch.setenv("RISK_ALERTS_SMTP_USER", "user@example.com")
    monkeypatch.setenv("RISK_ALERTS_SMTP_PASSWORD", "secret")
    monkeypatch.setenv("RISK_ALERTS_EMAIL_FROM", "alerts@example.com")
    monkeypatch.setenv("RISK_ALERTS_EMAIL_TO", "admin1@example.com,admin2@example.com")

    channel = EmailChannel()
    assert channel.enabled is True
    assert len(channel.to_emails) == 2


# =============================================================================
# SLACK CHANNEL TESTS
# =============================================================================


def test_slack_channel_disabled_by_default():
    """Test that Slack channel is disabled without webhook URL."""
    channel = SlackChannel()
    assert channel.enabled is False


def test_slack_channel_enabled_with_webhook():
    """Test that Slack channel is enabled with webhook URL."""
    channel = SlackChannel(webhook_url="https://hooks.slack.com/services/xxx")
    assert channel.enabled is True


@patch("src.risk_layer.alerting.channels.slack.urlopen")
def test_slack_channel_send(mock_urlopen, sample_alert):
    """Test Slack channel sends webhook request."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    channel = SlackChannel(webhook_url="https://hooks.slack.com/services/xxx")
    result = channel.send(sample_alert)

    assert result is True
    mock_urlopen.assert_called_once()


@patch("src.risk_layer.alerting.channels.slack.urlopen")
def test_slack_channel_error(mock_urlopen, sample_alert):
    """Test Slack channel handles errors."""
    mock_urlopen.side_effect = Exception("Network error")

    channel = SlackChannel(webhook_url="https://hooks.slack.com/services/xxx")
    result = channel.send(sample_alert)

    assert result is False


def test_slack_channel_env_var(monkeypatch):
    """Test Slack channel reads from environment variable."""
    monkeypatch.setenv("RISK_ALERTS_SLACK_WEBHOOK", "https://hooks.slack.com/services/xxx")

    channel = SlackChannel()
    assert channel.enabled is True


# =============================================================================
# TELEGRAM CHANNEL TESTS
# =============================================================================


def test_telegram_channel_disabled_by_default():
    """Test that Telegram channel is disabled without configuration."""
    channel = TelegramChannel()
    assert channel.enabled is False


def test_telegram_channel_enabled_with_config():
    """Test that Telegram channel is enabled with bot token and chat ID."""
    channel = TelegramChannel(bot_token="123456:ABC", chat_id="123456789")
    assert channel.enabled is True


@patch("src.risk_layer.alerting.channels.telegram.urlopen")
def test_telegram_channel_send(mock_urlopen, sample_alert):
    """Test Telegram channel sends API request."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    channel = TelegramChannel(bot_token="123456:ABC", chat_id="123456789")
    result = channel.send(sample_alert)

    assert result is True
    mock_urlopen.assert_called_once()


@patch("src.risk_layer.alerting.channels.telegram.urlopen")
def test_telegram_channel_error(mock_urlopen, sample_alert):
    """Test Telegram channel handles errors."""
    mock_urlopen.side_effect = Exception("API error")

    channel = TelegramChannel(bot_token="123456:ABC", chat_id="123456789")
    result = channel.send(sample_alert)

    assert result is False


def test_telegram_channel_env_vars(monkeypatch):
    """Test Telegram channel reads from environment variables."""
    monkeypatch.setenv("RISK_ALERTS_TELEGRAM_BOT_TOKEN", "123456:ABC")
    monkeypatch.setenv("RISK_ALERTS_TELEGRAM_CHAT_ID", "123456789")

    channel = TelegramChannel()
    assert channel.enabled is True


# =============================================================================
# WEBHOOK CHANNEL TESTS
# =============================================================================


def test_webhook_channel_disabled_by_default():
    """Test that webhook channel is disabled without URL."""
    channel = WebhookChannel()
    assert channel.enabled is False


def test_webhook_channel_enabled_with_url():
    """Test that webhook channel is enabled with URL."""
    channel = WebhookChannel(webhook_url="https://example.com/webhook")
    assert channel.enabled is True


@patch("src.risk_layer.alerting.channels.webhook.urlopen")
def test_webhook_channel_send(mock_urlopen, sample_alert):
    """Test webhook channel sends POST request."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    channel = WebhookChannel(webhook_url="https://example.com/webhook")
    result = channel.send(sample_alert)

    assert result is True
    mock_urlopen.assert_called_once()


@patch("src.risk_layer.alerting.channels.webhook.urlopen")
def test_webhook_channel_error(mock_urlopen, sample_alert):
    """Test webhook channel handles errors."""
    mock_urlopen.side_effect = Exception("Connection refused")

    channel = WebhookChannel(webhook_url="https://example.com/webhook")
    result = channel.send(sample_alert)

    assert result is False


def test_webhook_channel_env_var(monkeypatch):
    """Test webhook channel reads from environment variable."""
    monkeypatch.setenv("RISK_ALERTS_WEBHOOK_URL", "https://example.com/webhook")

    channel = WebhookChannel()
    assert channel.enabled is True
