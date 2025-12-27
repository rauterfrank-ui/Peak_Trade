"""
Tests for WebhookChannel.

Tests generic webhook integration with mocked HTTP calls.
"""

import asyncio
from unittest.mock import patch

from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.webhook_channel import WebhookChannel


class TestWebhookChannel:
    """Test WebhookChannel functionality."""

    def test_create_channel(self, webhook_config):
        """Test channel creation with config."""
        channel = WebhookChannel(webhook_config)

        assert channel.name == "webhook"
        assert channel.is_enabled()
        assert channel.url == webhook_config["url"]

    def test_create_without_url_disables(self):
        """Test channel disables if no URL."""
        config = {"enabled": True}  # Missing url
        channel = WebhookChannel(config)

        assert not channel.is_enabled()

    @patch("src.risk_layer.alerting.channels.webhook_channel.request.urlopen")
    def test_send_success(self, mock_urlopen, webhook_config, event_warning, mock_http_response):
        """Test successful webhook POST."""
        mock_urlopen.return_value = mock_http_response(status=200)

        channel = WebhookChannel(webhook_config)
        success = asyncio.run(channel.send(event_warning))

        assert success
        assert mock_urlopen.called

    @patch("src.risk_layer.alerting.channels.webhook_channel.request.urlopen")
    def test_send_failure(self, mock_urlopen, webhook_config, event_error):
        """Test handling of webhook failure."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Connection failed")

        channel = WebhookChannel(webhook_config)
        success = asyncio.run(channel.send(event_error))

        assert not success
        assert channel.get_health().last_error is not None

    @patch("src.risk_layer.alerting.channels.webhook_channel.request.urlopen")
    def test_send_includes_auth_token(self, mock_urlopen, event_warning, mock_http_response):
        """Test auth token is added to headers."""
        config = {
            "enabled": True,
            "url": "https://example.com/hook",
            "auth_token": "secret123",
        }
        mock_urlopen.return_value = mock_http_response(status=200)

        channel = WebhookChannel(config)
        asyncio.run(channel.send(event_warning))

        # Verify Authorization header was set
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert "Authorization" in request.headers
        assert "Bearer secret123" in request.headers["Authorization"]

    @patch("src.risk_layer.alerting.channels.webhook_channel.request.urlopen")
    def test_send_includes_custom_headers(self, mock_urlopen, webhook_config, event_info, mock_http_response):
        """Test custom headers are included."""
        mock_urlopen.return_value = mock_http_response(status=200)

        channel = WebhookChannel(webhook_config)
        asyncio.run(channel.send(event_info))

        # Verify custom header (case-insensitive)
        request = mock_urlopen.call_args[0][0]
        # Convert headers to lowercase for comparison
        headers_lower = {k.lower(): v for k, v in request.headers.items()}
        assert "x-test" in headers_lower
        assert headers_lower["x-test"] == "value"

    @patch("src.risk_layer.alerting.channels.webhook_channel.request.urlopen")
    def test_payload_is_json(self, mock_urlopen, webhook_config, event_critical, mock_http_response):
        """Test payload is sent as JSON."""
        mock_urlopen.return_value = mock_http_response(status=200)

        channel = WebhookChannel(webhook_config)
        asyncio.run(channel.send(event_critical))

        request = mock_urlopen.call_args[0][0]
        # HTTP headers are case-insensitive
        headers_lower = {k.lower(): v for k, v in request.headers.items()}
        assert "content-type" in headers_lower
        assert "json" in headers_lower["content-type"]

    def test_health_check_with_valid_url(self, webhook_config):
        """Test health check with valid URL."""
        channel = WebhookChannel(webhook_config)

        health = channel.health_check()

        assert health.status.value == "healthy"

    def test_health_check_without_url(self):
        """Test health check when URL missing."""
        config = {"enabled": True}
        channel = WebhookChannel(config)

        health = channel.health_check()

        assert health.status.value in ["disabled", "failed"]

    def test_health_check_invalid_url_format(self):
        """Test health check with malformed URL."""
        config = {
            "enabled": True,
            "url": "not-a-valid-url",
        }
        channel = WebhookChannel(config)

        health = channel.health_check()

        assert health.status.value == "failed"

    def test_get_url_redacts_credentials(self):
        """Test get_url() redacts auth in URL."""
        config = {
            "enabled": True,
            "url": "https://user:password@example.com/hook",
        }
        channel = WebhookChannel(config)

        url = channel.get_url()

        assert "password" not in url
        assert "***" in url

    def test_severity_filtering(self, webhook_config, event_debug, event_error):
        """Test channel respects min_severity."""
        channel = WebhookChannel(webhook_config, min_severity=AlertSeverity.ERROR)

        assert not channel.should_send(event_debug)
        assert channel.should_send(event_error)


class TestWebhookChannelEdgeCases:
    """Test edge cases and error handling."""

    @patch("src.risk_layer.alerting.channels.webhook_channel.request.urlopen")
    def test_http_non_2xx_is_failure(self, mock_urlopen, webhook_config, event_info, mock_http_response):
        """Test non-2xx status codes are treated as failures."""
        mock_urlopen.return_value = mock_http_response(status=500)

        channel = WebhookChannel(webhook_config)
        success = asyncio.run(channel.send(event_info))

        assert not success
