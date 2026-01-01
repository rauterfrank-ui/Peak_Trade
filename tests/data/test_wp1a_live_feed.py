"""
Tests for WP1A - Live Feed Client

Tests:
- Reconnection logic (deterministic)
- Backfill trigger on gap
- Latency tracking
- Message parsing
"""

import time
from unittest.mock import Mock

import pytest

from src.data.feeds.live_feed import (
    ConnectionState,
    FeedConfig,
    LiveFeedClient,
)
from src.observability.metrics import MetricsCollector


class TestLiveFeedClient:
    """Test suite for LiveFeedClient."""

    def test_connect_success(self):
        """Test successful connection."""
        config = FeedConfig(symbols=["BTC/EUR"])
        client = LiveFeedClient(config)

        assert client.state == ConnectionState.DISCONNECTED

        success = client.connect()

        assert success is True
        assert client.state == ConnectionState.CONNECTED
        assert client.is_connected() is True

    def test_disconnect(self):
        """Test disconnection."""
        config = FeedConfig(symbols=["BTC/EUR"])
        client = LiveFeedClient(config)

        client.connect()
        assert client.is_connected() is True

        client.disconnect()

        assert client.state == ConnectionState.DISCONNECTED
        assert client.is_connected() is False

    def test_reconnect_on_disconnect(self):
        """Test automatic reconnection after disconnect."""
        config = FeedConfig(
            symbols=["BTC/EUR"],
            reconnect_enabled=True,
            reconnect_max_attempts=3,
            reconnect_backoff_base=1.1,  # Low for fast tests
        )
        client = LiveFeedClient(config)

        client.connect()
        assert client.is_connected() is True
        assert client.stats.reconnect_count == 0

        # Simulate disconnect
        client.simulate_disconnect()

        # Should auto-reconnect
        assert client.is_connected() is True
        assert client.stats.reconnect_count == 1

    def test_reconnect_backoff_deterministic(self):
        """Test exponential backoff is deterministic."""
        config = FeedConfig(
            symbols=["BTC/EUR"],
            reconnect_enabled=True,
            reconnect_max_attempts=3,
            reconnect_backoff_base=2.0,
        )
        client = LiveFeedClient(config)

        client.connect()

        # First disconnect/reconnect
        client.simulate_disconnect()
        assert client.stats.reconnect_count == 1

        # Second disconnect/reconnect
        client.simulate_disconnect()
        assert client.stats.reconnect_count == 2

    def test_reconnect_max_attempts_reached(self):
        """Test failure after max reconnect attempts."""
        config = FeedConfig(
            symbols=["BTC/EUR"],
            reconnect_enabled=True,
            reconnect_max_attempts=0,  # Fail immediately
        )
        client = LiveFeedClient(config)

        # Patch connect to always fail
        def fail_connect():
            client._set_state(ConnectionState.DISCONNECTED)
            return False

        original_connect = client.connect
        client.connect = fail_connect

        client._set_state(ConnectionState.CONNECTED)
        client.simulate_disconnect()

        # Should fail after 0 attempts
        assert client.state == ConnectionState.FAILED

        # Restore
        client.connect = original_connect

    def test_backfill_triggered_on_reconnect(self):
        """Test backfill is triggered on reconnect."""
        config = FeedConfig(
            symbols=["BTC/EUR"],
            reconnect_enabled=True,
            backfill_enabled=True,
            backfill_lookback_ms=60_000,
        )
        client = LiveFeedClient(config)

        # Mock backfill callback
        backfill_calls = []

        def on_backfill(start_ms: int, end_ms: int):
            backfill_calls.append((start_ms, end_ms))

        client.on_backfill_requested = on_backfill

        client.connect()
        client.simulate_disconnect()

        # Backfill should have been triggered
        assert len(backfill_calls) == 1
        assert client.stats.backfill_count == 1

        start_ms, end_ms = backfill_calls[0]
        assert end_ms - start_ms == config.backfill_lookback_ms

    def test_backfill_not_triggered_when_disabled(self):
        """Test backfill is NOT triggered when disabled."""
        config = FeedConfig(
            symbols=["BTC/EUR"],
            reconnect_enabled=True,
            backfill_enabled=False,  # Disabled
        )
        client = LiveFeedClient(config)

        backfill_calls = []
        client.on_backfill_requested = lambda s, e: backfill_calls.append((s, e))

        client.connect()
        client.simulate_disconnect()

        assert len(backfill_calls) == 0
        assert client.stats.backfill_count == 0


class TestMessageParsing:
    """Test message parsing and tick processing."""

    def test_process_valid_kraken_message(self):
        """Test processing valid Kraken trade message."""
        config = FeedConfig(symbols=["BTC/EUR"])
        client = LiveFeedClient(config)

        # Valid Kraken trade message
        message = [
            123,  # channel_id
            [
                ["50000.0", "0.5", 1609459200.123, "b", "l", ""],  # trade 1
                ["50001.0", "0.3", 1609459200.456, "s", "l", ""],  # trade 2
            ],
            "trade",
            "BTC/EUR",
        ]

        ticks = client.process_message(message)

        assert len(ticks) == 2
        assert ticks[0].price == 50000.0
        assert ticks[0].volume == 0.5
        assert ticks[1].price == 50001.0
        assert client.stats.messages_received == 1
        assert client.stats.messages_parsed == 1
        assert client.stats.messages_failed == 0

    def test_process_invalid_message(self):
        """Test processing invalid message."""
        config = FeedConfig(symbols=["BTC/EUR"])
        client = LiveFeedClient(config)

        # Invalid message
        message = {"invalid": "structure"}

        ticks = client.process_message(message)

        assert len(ticks) == 0
        assert client.stats.messages_received == 1
        assert client.stats.messages_failed == 1

    def test_latency_tracking(self):
        """Test latency metrics are recorded."""
        metrics = MetricsCollector()
        config = FeedConfig(symbols=["BTC/EUR"])
        client = LiveFeedClient(config, metrics_collector=metrics)

        # Message with tick from 1 second ago
        past_ts = time.time() - 1.0
        message = [
            123,
            [["50000.0", "0.5", past_ts, "b", "l", ""]],
            "trade",
            "BTC/EUR",
        ]

        client.process_message(message)

        # Latency should be ~1000ms
        snapshot = metrics.get_snapshot()
        latency_values = snapshot["metrics"]["latency_ms"]["values"]

        assert len(latency_values) > 0
        # Should be around 1000ms (within tolerance)
        assert 900 <= latency_values[0]["value"] <= 1100

    def test_on_tick_callback(self):
        """Test on_tick callback is invoked."""
        config = FeedConfig(symbols=["BTC/EUR"])
        client = LiveFeedClient(config)

        received_ticks = []
        client.on_tick = lambda tick: received_ticks.append(tick)

        message = [
            123,
            [["50000.0", "0.5", time.time(), "b", "l", ""]],
            "trade",
            "BTC/EUR",
        ]

        client.process_message(message)

        assert len(received_ticks) == 1
        assert received_ticks[0].price == 50000.0


class TestConnectionStateCallbacks:
    """Test connection state change callbacks."""

    def test_state_change_callback(self):
        """Test state change callback is invoked."""
        config = FeedConfig(symbols=["BTC/EUR"])
        client = LiveFeedClient(config)

        state_changes = []

        def on_state_change(old, new):
            state_changes.append((old, new))

        client.on_connection_state_change = on_state_change

        client.connect()

        # Should have transitions: DISCONNECTED -> CONNECTING -> CONNECTED
        assert len(state_changes) == 2
        assert state_changes[0] == (
            ConnectionState.DISCONNECTED,
            ConnectionState.CONNECTING,
        )
        assert state_changes[1] == (
            ConnectionState.CONNECTING,
            ConnectionState.CONNECTED,
        )


class TestFeedStats:
    """Test feed statistics."""

    def test_stats_initial_state(self):
        """Test stats are initialized correctly."""
        config = FeedConfig()
        client = LiveFeedClient(config)

        stats = client.get_stats()

        assert stats.messages_received == 0
        assert stats.messages_parsed == 0
        assert stats.messages_failed == 0
        assert stats.reconnect_count == 0
        assert stats.backfill_count == 0

    def test_stats_updated_on_processing(self):
        """Test stats are updated correctly."""
        config = FeedConfig()
        client = LiveFeedClient(config)

        # Valid message
        message = [
            123,
            [["50000.0", "0.5", time.time(), "b", "l", ""]],
            "trade",
            "BTC/EUR",
        ]
        client.process_message(message)

        stats = client.get_stats()
        assert stats.messages_received == 1
        assert stats.messages_parsed == 1

        # Invalid message
        client.process_message({"invalid": "data"})

        stats = client.get_stats()
        assert stats.messages_received == 2
        assert stats.messages_failed == 1
