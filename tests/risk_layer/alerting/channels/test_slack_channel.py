"""
Tests for SlackChannel.

Tests Slack webhook integration with mocked HTTP calls.
"""

import asyncio
from unittest.mock import patch

from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.slack_channel import SlackChannel


class TestSlackChannel:
    """Test SlackChannel functionality."""

    def test_create_channel(self, slack_config):
        """Test channel creation with config."""
        channel = SlackChannel(slack_config)

        assert channel.name == "slack"
        assert channel.is_enabled()
        assert channel.webhook_url == slack_config["webhook_url"]

    def test_create_without_webhook_disables(self):
        """Test channel disables if no webhook URL."""
        config = {"enabled": True}  # Missing webhook_url
        channel = SlackChannel(config)

        assert not channel.is_enabled()

    @patch("src.risk_layer.alerting.channels.slack_channel.request.urlopen")
    def test_send_success(self, mock_urlopen, slack_config, event_warning, mock_http_response):
        """Test successful send to Slack."""
        mock_urlopen.return_value = mock_http_response(status=200)

        channel = SlackChannel(slack_config)
        success = asyncio.run(channel.send(event_warning))

        assert success
        assert mock_urlopen.called

    @patch("src.risk_layer.alerting.channels.slack_channel.request.urlopen")
    def test_send_failure(self, mock_urlopen, slack_config, event_error):
        """Test handling of send failure."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Connection failed")

        channel = SlackChannel(slack_config)
        success = asyncio.run(channel.send(event_error))

        assert not success
        assert channel.get_health().last_error is not None

    def test_build_payload_structure(self, slack_config, event_critical):
        """Test Slack payload structure."""
        channel = SlackChannel(slack_config)
        payload = channel._build_payload(event_critical)

        assert "blocks" in payload
        assert "attachments" in payload
        assert "username" in payload
        assert payload["username"] == slack_config["username"]

    def test_payload_includes_severity(self, slack_config, event_error):
        """Test payload includes severity information."""
        channel = SlackChannel(slack_config)
        payload = channel._build_payload(event_error)

        # Check blocks contain severity
        blocks_str = str(payload["blocks"])
        assert "ERROR" in blocks_str.upper()

    def test_payload_includes_context(self, slack_config, event_critical):
        """Test payload includes event context."""
        channel = SlackChannel(slack_config)
        payload = channel._build_payload(event_critical)

        payload_str = str(payload)
        for key in event_critical.context:
            assert key in payload_str

    def test_severity_colors_mapped(self, slack_config):
        """Test severity to color mapping exists."""
        channel = SlackChannel(slack_config)

        assert AlertSeverity.INFO in SlackChannel.SEVERITY_COLORS
        assert AlertSeverity.CRITICAL in SlackChannel.SEVERITY_COLORS

        # All colors should be hex codes
        for color in SlackChannel.SEVERITY_COLORS.values():
            assert color.startswith("#")

    def test_mention_on_critical(self, slack_config, event_critical):
        """Test @mentions included for critical events."""
        channel = SlackChannel(slack_config)
        payload = channel._build_payload(event_critical)

        # Check mentions are in the message
        payload_str = str(payload)
        assert "@test" in payload_str

    def test_health_check_with_valid_webhook(self, slack_config):
        """Test health check with configured webhook."""
        channel = SlackChannel(slack_config)

        health = channel.health_check()

        assert health.status.value == "healthy"

    def test_health_check_without_webhook(self):
        """Test health check when webhook missing."""
        config = {"enabled": True}
        channel = SlackChannel(config)

        health = channel.health_check()

        assert health.status.value in ["disabled", "failed"]

    def test_severity_filtering(self, slack_config, event_info, event_warning):
        """Test channel respects min_severity."""
        channel = SlackChannel(slack_config, min_severity=AlertSeverity.WARNING)

        assert not channel.should_send(event_info)
        assert channel.should_send(event_warning)
