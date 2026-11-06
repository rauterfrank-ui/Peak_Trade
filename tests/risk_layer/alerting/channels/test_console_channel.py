"""
Tests for ConsoleChannel.

Tests stdout/stderr routing and formatting.
"""

import asyncio

from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.console_channel import ConsoleChannel


class TestConsoleChannel:
    """Test ConsoleChannel functionality."""

    def test_create_channel(self, console_config):
        """Test channel creation and defaults."""
        channel = ConsoleChannel(console_config)

        assert channel.name == "console"
        assert channel.is_enabled()
        assert channel.min_severity == AlertSeverity.DEBUG

    def test_create_with_custom_severity(self, console_config):
        """Test creating channel with custom min_severity."""
        channel = ConsoleChannel(console_config, min_severity=AlertSeverity.WARNING)

        assert channel.min_severity == AlertSeverity.WARNING

    def test_severity_filtering(self, console_config, event_info, event_warning):
        """Test should_send respects severity threshold."""
        channel = ConsoleChannel(console_config, min_severity=AlertSeverity.WARNING)

        assert not channel.should_send(event_info)  # INFO < WARNING
        assert channel.should_send(event_warning)  # WARNING >= WARNING

    def test_send_to_stdout(self, console_config, event_info, capsys):
        """Test INFO/DEBUG go to stdout."""
        channel = ConsoleChannel(console_config)

        success = asyncio.run(channel.send(event_info))

        assert success
        captured = capsys.readouterr()
        assert captured.out != ""  # Something in stdout
        assert "INFO" in captured.out or "info" in captured.out.lower()

    def test_send_to_stderr(self, console_config, event_warning, capsys):
        """Test WARNING+ go to stderr."""
        channel = ConsoleChannel(console_config)

        success = asyncio.run(channel.send(event_warning))

        assert success
        captured = capsys.readouterr()
        assert captured.err != ""  # Something in stderr

    def test_simple_format(self, console_config, event_error, capsys):
        """Test simple format output."""
        console_config["format"] = "simple"
        channel = ConsoleChannel(console_config)

        asyncio.run(channel.send(event_error))

        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR" in output or "error" in output
        assert event_error.source in output
        assert event_error.message in output

    def test_json_format(self, console_config, event_warning, capsys):
        """Test JSON format output."""
        console_config["format"] = "json"
        channel = ConsoleChannel(console_config)

        asyncio.run(channel.send(event_warning))

        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert '"severity"' in output
        assert '"source"' in output

    def test_structured_format(self, console_config, event_critical, capsys):
        """Test structured format with context."""
        console_config["format"] = "structured"
        channel = ConsoleChannel(console_config)

        asyncio.run(channel.send(event_critical))

        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "CRITICAL" in output or "critical" in output
        assert "Context" in output or "context" in output

    def test_health_check_when_enabled(self, console_config):
        """Test health check returns healthy when enabled."""
        channel = ConsoleChannel(console_config)

        health = channel.health_check()

        assert health.status.value == "healthy"

    def test_health_check_when_disabled(self):
        """Test health check when disabled."""
        channel = ConsoleChannel({"enabled": False})

        health = channel.health_check()

        assert health.status.value == "disabled"

    def test_channel_always_succeeds(self, console_config, event_factory):
        """Test console channel never fails (no network dependency)."""
        channel = ConsoleChannel(console_config)

        # Try various event types
        for severity in [AlertSeverity.DEBUG, AlertSeverity.CRITICAL]:
            event = event_factory(severity=severity)
            success = asyncio.run(channel.send(event))
            assert success
