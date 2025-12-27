"""
Tests for FileChannel.

Tests file writing, rotation, and health checks.
"""

import asyncio
import json
from pathlib import Path

from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.file_channel import FileChannel


class TestFileChannel:
    """Test FileChannel functionality."""

    def test_create_channel(self, file_config):
        """Test channel creation creates directory."""
        channel = FileChannel(file_config)

        assert channel.name == "file"
        assert channel.is_enabled()
        assert channel.path.exists()
        assert channel.path.is_dir()

    def test_create_with_custom_severity(self, file_config):
        """Test creating with custom min_severity."""
        channel = FileChannel(file_config, min_severity=AlertSeverity.WARNING)

        assert channel.min_severity == AlertSeverity.WARNING

    def test_send_creates_file(self, file_config, event_warning):
        """Test sending event creates log file."""
        channel = FileChannel(file_config)

        success = asyncio.run(channel.send(event_warning))

        assert success
        filepath = channel.get_current_filepath()
        assert filepath.exists()

    def test_send_writes_jsonl(self, file_config, event_error):
        """Test event is written as JSON line."""
        channel = FileChannel(file_config)

        asyncio.run(channel.send(event_error))

        filepath = channel.get_current_filepath()
        with open(filepath) as f:
            line = f.readline()

        data = json.loads(line)
        assert data["severity"] == "error"
        assert data["source"] == event_error.source
        assert data["message"] == event_error.message

    def test_send_multiple_appends(self, file_config, event_factory):
        """Test multiple sends append to same file."""
        channel = FileChannel(file_config)

        # Send 3 events
        for i in range(3):
            event = event_factory(message=f"Event {i}")
            asyncio.run(channel.send(event))

        filepath = channel.get_current_filepath()
        with open(filepath) as f:
            lines = f.readlines()

        assert len(lines) == 3
        assert all(line.strip() for line in lines)  # No empty lines

    def test_filename_includes_date(self, file_config):
        """Test log filename includes date for rotation."""
        channel = FileChannel(file_config)

        filepath = channel.get_current_filepath()

        assert "alerts_" in filepath.name
        assert filepath.suffix == ".jsonl"

    def test_list_log_files(self, file_config, event_info):
        """Test listing existing log files."""
        channel = FileChannel(file_config)

        # Create a log file
        asyncio.run(channel.send(event_info))

        files = channel.list_log_files()

        assert len(files) >= 1
        assert all(f.name.startswith("alerts_") for f in files)

    def test_health_check_when_writable(self, file_config):
        """Test health check when directory is writable."""
        channel = FileChannel(file_config)

        health = channel.health_check()

        assert health.status.value == "healthy"

    def test_health_check_when_disabled(self, file_config):
        """Test health check when channel disabled."""
        file_config["enabled"] = False
        channel = FileChannel(file_config)

        health = channel.health_check()

        assert health.status.value == "disabled"

    def test_context_data_preserved(self, file_config, event_critical):
        """Test that context data is preserved in log."""
        channel = FileChannel(file_config)

        asyncio.run(channel.send(event_critical))

        filepath = channel.get_current_filepath()
        with open(filepath) as f:
            data = json.loads(f.readline())

        assert "context" in data
        assert data["context"] == event_critical.context

    def test_severity_filtering(self, file_config, event_info, event_critical):
        """Test events below threshold are not written."""
        channel = FileChannel(file_config, min_severity=AlertSeverity.CRITICAL)

        assert not channel.should_send(event_info)
        assert channel.should_send(event_critical)


class TestFileChannelEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_directory_disables_channel(self):
        """Test that invalid path disables the channel."""
        config = {
            "enabled": True,
            "path": "/root/impossible/path/alerts",  # Usually not writable
        }

        channel = FileChannel(config)

        # Should be disabled due to failed directory creation
        assert not channel.is_enabled()

    def test_health_check_detects_missing_directory(self, file_config):
        """Test health check detects if directory disappears."""
        channel = FileChannel(file_config)

        # Remove the directory
        channel.path.rmdir()

        health = channel.health_check()

        assert health.status.value == "failed"
