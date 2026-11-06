"""
Tests for TelegramChannel.

Tests Telegram Bot API integration with mocked HTTP calls.
"""

import asyncio
from unittest.mock import patch

from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.telegram_channel import TelegramChannel


class TestTelegramChannel:
    """Test TelegramChannel functionality."""

    def test_create_channel(self, telegram_config):
        """Test channel creation with config."""
        channel = TelegramChannel(telegram_config)

        assert channel.name == "telegram"
        assert channel.is_enabled()
        assert channel.bot_token == telegram_config["bot_token"]
        assert channel.chat_id == telegram_config["chat_id"]

    def test_create_without_token_disables(self):
        """Test channel disables if bot token missing."""
        config = {"enabled": True, "chat_id": "-1001234"}  # Missing bot_token
        channel = TelegramChannel(config)

        assert not channel.is_enabled()

    def test_create_without_chat_id_disables(self):
        """Test channel disables if chat ID missing."""
        config = {"enabled": True, "bot_token": "123:ABC"}  # Missing chat_id
        channel = TelegramChannel(config)

        assert not channel.is_enabled()

    @patch("src.risk_layer.alerting.channels.telegram_channel.request.urlopen")
    def test_send_success(self, mock_urlopen, telegram_config, event_warning, mock_http_response):
        """Test successful send to Telegram."""
        mock_urlopen.return_value = mock_http_response(status=200, body='{"ok":true}')

        channel = TelegramChannel(telegram_config)
        success = asyncio.run(channel.send(event_warning))

        assert success
        assert mock_urlopen.called

    @patch("src.risk_layer.alerting.channels.telegram_channel.request.urlopen")
    def test_send_failure(self, mock_urlopen, telegram_config, event_error):
        """Test handling of send failure."""
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Connection failed")

        channel = TelegramChannel(telegram_config)
        success = asyncio.run(channel.send(event_error))

        assert not success
        assert channel.get_health().last_error is not None

    def test_format_message_structure(self, telegram_config, event_critical):
        """Test Telegram message formatting."""
        channel = TelegramChannel(telegram_config)
        text = channel._format_message(event_critical)

        assert "CRITICAL" in text.upper()
        assert event_critical.source in text
        assert event_critical.message in text
        assert event_critical.category.value in text

    def test_message_uses_markdown(self, telegram_config, event_error):
        """Test message uses Markdown formatting."""
        channel = TelegramChannel(telegram_config)
        text = channel._format_message(event_error)

        # Check for markdown bold/italic markers
        assert "*" in text or "_" in text or "`" in text

    def test_message_includes_severity(self, telegram_config, event_warning):
        """Test message includes severity."""
        channel = TelegramChannel(telegram_config)
        text = channel._format_message(event_warning)

        assert "WARNING" in text.upper() or "⚠" in text

    def test_format_includes_event_id(self, telegram_config, event_info):
        """Test formatted message includes event ID."""
        channel = TelegramChannel(telegram_config)
        text = channel._format_message(event_info)

        # Should include first 8 chars of event ID
        assert event_info.event_id[:8] in text

    def test_message_includes_context(self, telegram_config, event_critical):
        """Test message includes context data."""
        channel = TelegramChannel(telegram_config)
        text = channel._format_message(event_critical)

        # Should include context keys
        for key in event_critical.context:
            assert key in text

    def test_context_truncation_for_many_items(self, telegram_config, event_factory):
        """Test many context items are truncated."""
        # Create event with many context items
        huge_context = {f"key_{i}": f"value_{i}" for i in range(20)}
        event = event_factory(context=huge_context)

        channel = TelegramChannel(telegram_config)
        text = channel._format_message(event)

        # Should limit to 5 items and show "more" indicator
        assert "more" in text.lower()

    def test_health_check_with_valid_token(self, telegram_config):
        """Test health check with configured token."""
        channel = TelegramChannel(telegram_config)

        health = channel.health_check()

        assert health.status.value == "healthy"

    def test_health_check_without_token(self):
        """Test health check when token missing."""
        config = {"enabled": True}
        channel = TelegramChannel(config)

        health = channel.health_check()

        assert health.status.value in ["disabled", "failed"]

    def test_config_validation(self, telegram_config):
        """Test channel validates required config."""
        channel = TelegramChannel(telegram_config)

        assert channel.bot_token == telegram_config["bot_token"]
        assert channel.chat_id == telegram_config["chat_id"]
        assert channel.is_enabled()

    def test_severity_filtering(self, telegram_config, event_info, event_error):
        """Test channel respects min_severity."""
        channel = TelegramChannel(telegram_config, min_severity=AlertSeverity.ERROR)

        assert not channel.should_send(event_info)
        assert channel.should_send(event_error)


class TestTelegramChannelEdgeCases:
    """Test edge cases and error handling."""

    @patch("src.risk_layer.alerting.channels.telegram_channel.request.urlopen")
    def test_telegram_api_error_handled(
        self, mock_urlopen, telegram_config, event_warning, mock_http_response
    ):
        """Test Telegram API error response is handled."""
        mock_urlopen.return_value = mock_http_response(
            status=200, body='{"ok":false,"description":"Chat not found"}'
        )

        channel = TelegramChannel(telegram_config)
        success = asyncio.run(channel.send(event_warning))

        # Should be treated as failure even though HTTP 200
        assert not success
