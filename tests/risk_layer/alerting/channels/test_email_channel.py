"""
Tests for EmailChannel.

Tests SMTP email integration with mocked server.
"""

import asyncio
from unittest.mock import patch, Mock

from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.email_channel import EmailChannel


class TestEmailChannel:
    """Test EmailChannel functionality."""

    def test_create_channel(self, email_config):
        """Test channel creation with config."""
        channel = EmailChannel(email_config)

        assert channel.name == "email"
        assert channel.is_enabled()
        assert channel.smtp_host == email_config["smtp_host"]
        assert channel.smtp_port == email_config["smtp_port"]

    def test_create_without_smtp_host_disables(self):
        """Test channel disables if SMTP host missing."""
        config = {"enabled": True, "from_address": "test@test.com"}  # Missing smtp_host
        channel = EmailChannel(config)

        assert not channel.is_enabled()

    @patch("src.risk_layer.alerting.channels.email_channel.smtplib.SMTP")
    def test_send_success(self, mock_smtp_class, email_config, event_warning, mock_smtp_server):
        """Test successful email send."""
        mock_smtp_class.return_value = mock_smtp_server()

        channel = EmailChannel(email_config)
        success = asyncio.run(channel.send(event_warning))

        assert success
        assert mock_smtp_class.called

    @patch("src.risk_layer.alerting.channels.email_channel.smtplib.SMTP")
    def test_send_with_tls(self, mock_smtp_class, email_config, event_info, mock_smtp_server):
        """Test STARTTLS is called when use_tls=True."""
        mock_server = mock_smtp_server()
        mock_smtp_class.return_value = mock_server

        channel = EmailChannel(email_config)
        asyncio.run(channel.send(event_info))

        assert mock_server.starttls.called

    @patch("src.risk_layer.alerting.channels.email_channel.smtplib.SMTP")
    def test_send_with_auth(self, mock_smtp_class, email_config, event_error, mock_smtp_server):
        """Test authentication when credentials provided."""
        mock_server = mock_smtp_server()
        mock_smtp_class.return_value = mock_server

        channel = EmailChannel(email_config)
        asyncio.run(channel.send(event_error))

        assert mock_server.login.called

    @patch("src.risk_layer.alerting.channels.email_channel.smtplib.SMTP")
    def test_send_failure(self, mock_smtp_class, email_config, event_critical):
        """Test handling of SMTP failure."""
        from smtplib import SMTPException
        mock_server = Mock()
        mock_server.__enter__ = Mock(side_effect=SMTPException("Connection failed"))
        mock_smtp_class.return_value = mock_server

        channel = EmailChannel(email_config)
        success = asyncio.run(channel.send(event_critical))

        assert not success
        assert channel.get_health().last_error is not None

    @patch("src.risk_layer.alerting.channels.email_channel.smtplib.SMTP")
    def test_email_to_multiple_recipients(self, mock_smtp_class, event_info, mock_smtp_server):
        """Test sending to multiple recipients."""
        config = {
            "enabled": True,
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "from_address": "alerts@test.com",
            "to_addresses": ["user1@test.com", "user2@test.com"],
        }
        mock_smtp_class.return_value = mock_smtp_server()

        channel = EmailChannel(config)
        asyncio.run(channel.send(event_info))

        # Verify send_message was called
        mock_server = mock_smtp_class.return_value.__enter__.return_value
        assert mock_server.send_message.called

    def test_build_message_structure(self, email_config, event_warning):
        """Test email message structure."""
        channel = EmailChannel(email_config)
        msg = channel._build_message(event_warning)

        assert msg["From"] == email_config["from_address"]
        assert msg["To"] == ", ".join(email_config["to_addresses"])
        assert msg["Subject"] is not None

    def test_message_includes_severity(self, email_config, event_error):
        """Test email subject includes severity."""
        channel = EmailChannel(email_config)
        msg = channel._build_message(event_error)

        assert "ERROR" in msg["Subject"].upper()

    def test_message_includes_html_body(self, email_config, event_critical):
        """Test HTML body is included."""
        channel = EmailChannel(email_config)
        msg = channel._build_message(event_critical)

        # Should be multipart with HTML
        assert msg.is_multipart()
        parts = list(msg.walk())
        html_parts = [p for p in parts if p.get_content_type() == "text/html"]
        assert len(html_parts) > 0

    def test_health_check_with_config(self, email_config):
        """Test health check with valid config."""
        channel = EmailChannel(email_config)

        health = channel.health_check()

        assert health.status.value == "healthy"

    def test_health_check_without_smtp_host(self):
        """Test health check when SMTP host missing."""
        config = {"enabled": True}
        channel = EmailChannel(config)

        health = channel.health_check()

        assert health.status.value in ["disabled", "failed"]

    def test_severity_filtering(self, email_config, event_debug, event_critical):
        """Test channel respects min_severity."""
        channel = EmailChannel(email_config, min_severity=AlertSeverity.CRITICAL)

        assert not channel.should_send(event_debug)
        assert channel.should_send(event_critical)


class TestEmailChannelEdgeCases:
    """Test edge cases and error handling."""

    def test_no_recipients_disables_channel(self):
        """Test channel disables if no recipients."""
        config = {
            "enabled": True,
            "smtp_host": "smtp.test.com",
            "from_address": "test@test.com",
            "to_addresses": [],  # Empty
        }
        channel = EmailChannel(config)

        assert not channel.is_enabled()

    def test_password_not_logged(self, email_config):
        """Test password is not exposed in logs/repr."""
        channel = EmailChannel(email_config)

        # Get health or repr
        health = channel.health_check()
        health_str = str(health.__dict__)

        assert email_config["smtp_password"] not in health_str
