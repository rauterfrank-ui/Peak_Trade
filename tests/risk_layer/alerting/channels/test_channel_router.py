"""
Tests for ChannelRouter.

Tests routing, failover, and multi-channel dispatch.
"""

import asyncio

import pytest

from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.channel_router import ChannelRouter
from src.risk_layer.alerting.channels.console_channel import ConsoleChannel
from src.risk_layer.alerting.channels.file_channel import FileChannel


class TestChannelRouter:
    """Test ChannelRouter functionality."""

    def test_create_empty_router(self):
        """Test creating router without channels."""
        router = ChannelRouter()

        assert router.list_channels() == []
        assert router.get_enabled_channels() == []

    def test_add_channel(self, console_config):
        """Test adding channel to router."""
        router = ChannelRouter()
        channel = ConsoleChannel(console_config)

        router.add_channel(channel)

        assert len(router.list_channels()) == 1
        assert "console" in router.list_channels()

    def test_get_channel_by_name(self, console_config, file_config):
        """Test retrieving channel by name."""
        console = ConsoleChannel(console_config)
        file_ch = FileChannel(file_config)
        router = ChannelRouter(channels=[console, file_ch])

        assert router.get_channel("console") == console
        assert router.get_channel("file") == file_ch
        assert router.get_channel("nonexistent") is None

    def test_get_enabled_channels_only(self, console_config, file_config):
        """Test filtering enabled channels."""
        enabled = ConsoleChannel(console_config)

        disabled_config = file_config.copy()
        disabled_config["enabled"] = False
        disabled = FileChannel(disabled_config)

        router = ChannelRouter(channels=[enabled, disabled])
        enabled_list = router.get_enabled_channels()

        assert len(enabled_list) == 1
        assert enabled_list[0].name == "console"

    def test_route_single_event(self, console_config, event_warning):
        """Test routing event to single channel."""
        channel = ConsoleChannel(console_config)
        router = ChannelRouter(channels=[channel])

        results = asyncio.run(router.route_event(event_warning))

        assert "console" in results
        assert results["console"] is True

    def test_route_to_multiple_channels(self, console_config, file_config, event_error):
        """Test parallel routing to multiple channels."""
        console = ConsoleChannel(console_config)
        file_ch = FileChannel(file_config)
        router = ChannelRouter(channels=[console, file_ch])

        results = asyncio.run(router.route_event(event_error))

        assert len(results) == 2
        assert results["console"] is True
        assert results["file"] is True

    def test_severity_filtering(self, console_config, event_info, event_error):
        """Test that channels respect severity thresholds."""
        # Channel only accepts ERROR+
        channel = ConsoleChannel(console_config, min_severity=AlertSeverity.ERROR)
        router = ChannelRouter(channels=[channel])

        # INFO should be filtered out
        results_info = asyncio.run(router.route_event(event_info))
        assert results_info == {}

        # ERROR should pass through
        results_error = asyncio.run(router.route_event(event_error))
        assert "console" in results_error

    def test_fallback_chain(self, console_config, event_warning):
        """Test fallback when primary channel fails."""
        # Create failing channel
        failing_config = {"enabled": True, "path": "/nonexistent/impossible"}
        failing = FileChannel(failing_config)

        # Console as fallback
        fallback = ConsoleChannel(console_config)

        router = ChannelRouter(
            channels=[failing, fallback],
            fallback_chain={"file": "console"}
        )

        results = asyncio.run(router.route_event(event_warning))

        # Console should succeed via fallback
        assert "console" in results

    def test_route_with_no_enabled_channels(self, event_warning):
        """Test routing when all channels disabled."""
        disabled = ConsoleChannel({"enabled": False})
        router = ChannelRouter(channels=[disabled])

        results = asyncio.run(router.route_event(event_warning))

        assert results == {}

    def test_routing_statistics(self, console_config, event_info):
        """Test that router tracks dispatch stats."""
        channel = ConsoleChannel(console_config)
        router = ChannelRouter(channels=[channel])

        # Dispatch multiple events
        for _ in range(3):
            asyncio.run(router.route_event(event_info))

        stats = router.get_stats()

        assert stats["total_dispatches"] == 3
        assert stats["successful"] == 3
        assert stats["channels_registered"] == 1
        assert stats["channels_enabled"] == 1

    def test_health_check_all_channels(self, console_config, file_config):
        """Test health check across all channels."""
        console = ConsoleChannel(console_config)
        file_ch = FileChannel(file_config)
        router = ChannelRouter(channels=[console, file_ch])

        health = router.health_check_all()

        assert "console" in health
        assert "file" in health
        assert health["console"]["status"] == "healthy"
        assert health["file"]["status"] == "healthy"

    def test_synchronous_routing_wrapper(self, console_config, event_warning):
        """Test sync wrapper for async routing."""
        channel = ConsoleChannel(console_config)
        router = ChannelRouter(channels=[channel])

        # Should work from sync context
        results = router.route_event_sync(event_warning)

        assert isinstance(results, dict)


class TestChannelRouterEdgeCases:
    """Test edge cases and error handling."""

    def test_add_duplicate_channel_name(self, console_config):
        """Test that duplicate names overwrite."""
        router = ChannelRouter()
        channel1 = ConsoleChannel(console_config)
        channel2 = ConsoleChannel(console_config)

        router.add_channel(channel1)
        router.add_channel(channel2)

        # Should only have one (latest)
        assert len(router.list_channels()) == 1
        assert router.get_channel("console") == channel2

    def test_fallback_to_nonexistent_channel(self, file_config, event_warning):
        """Test fallback to channel that doesn't exist."""
        channel = FileChannel(file_config)
        router = ChannelRouter(
            channels=[channel],
            fallback_chain={"file": "nonexistent"}
        )

        # Should handle gracefully (no crash)
        results = asyncio.run(router.route_event(event_warning))
        assert isinstance(results, dict)
