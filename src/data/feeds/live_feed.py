"""
Live Feed Client - Phase 1 WP1A

WebSocket feed client with:
- Reconnection logic
- Backfill on gaps
- Latency tracking

For Phase 1 Shadow Trading, this is a STUB with simulated behavior.
Real WebSocket integration is Phase 2+.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from src.data.shadow.models import Tick
from src.data.shadow.tick_normalizer import parse_kraken_trade_message
from src.observability.metrics import MetricsCollector

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    """WebSocket connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class FeedConfig:
    """
    Configuration for LiveFeedClient.

    Attributes:
        exchange: Exchange name (e.g., "kraken")
        symbols: List of symbols to subscribe
        reconnect_enabled: Enable automatic reconnection
        reconnect_max_attempts: Maximum reconnection attempts
        reconnect_backoff_base: Backoff base in seconds
        backfill_enabled: Enable backfill on reconnect
        backfill_lookback_ms: Backfill lookback window (ms)
    """

    exchange: str = "kraken"
    symbols: list[str] = field(default_factory=lambda: ["BTC/EUR"])
    reconnect_enabled: bool = True
    reconnect_max_attempts: int = 5
    reconnect_backoff_base: float = 2.0
    backfill_enabled: bool = True
    backfill_lookback_ms: int = 60_000  # 1 minute


@dataclass
class FeedStats:
    """
    Feed statistics.

    Attributes:
        messages_received: Total messages received
        messages_parsed: Successfully parsed messages
        messages_failed: Failed to parse
        reconnect_count: Total reconnections
        backfill_count: Total backfills triggered
        last_message_ts_ms: Last message timestamp
    """

    messages_received: int = 0
    messages_parsed: int = 0
    messages_failed: int = 0
    reconnect_count: int = 0
    backfill_count: int = 0
    last_message_ts_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "messages_received": self.messages_received,
            "messages_parsed": self.messages_parsed,
            "messages_failed": self.messages_failed,
            "reconnect_count": self.reconnect_count,
            "backfill_count": self.backfill_count,
            "last_message_ts_ms": self.last_message_ts_ms,
        }


class LiveFeedClient:
    """
    Live Feed Client with reconnection and backfill logic.

    This is a STUB for Phase 1. Real WebSocket implementation in Phase 2+.

    Usage:
        >>> config = FeedConfig(symbols=["BTC/EUR"])
        >>> client = LiveFeedClient(config)
        >>> client.on_tick = lambda tick: print(f"Tick: {tick}")
        >>> client.connect()
        >>> # ... client.disconnect()
    """

    def __init__(
        self,
        config: FeedConfig,
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        self.config = config
        self.metrics = metrics_collector or MetricsCollector()

        self.state = ConnectionState.DISCONNECTED
        self.stats = FeedStats()

        # Callbacks
        self.on_tick: Optional[Callable[[Tick], None]] = None
        self.on_connection_state_change: Optional[
            Callable[[ConnectionState, ConnectionState], None]
        ] = None
        self.on_backfill_requested: Optional[Callable[[int, int], None]] = None

        # Internal state
        self._reconnect_attempts = 0
        self._last_connected_ts = 0.0

    def connect(self) -> bool:
        """
        Connect to the feed.

        Returns:
            True if connected, False otherwise
        """
        logger.info(
            f"Connecting to {self.config.exchange} feed (symbols: {self.config.symbols})"
        )
        self._set_state(ConnectionState.CONNECTING)

        # STUB: Simulate successful connection
        time.sleep(0.01)  # Simulate connection latency

        self._set_state(ConnectionState.CONNECTED)
        self._last_connected_ts = time.time()
        self._reconnect_attempts = 0

        logger.info("Feed connected successfully")
        return True

    def disconnect(self) -> None:
        """Disconnect from the feed."""
        if self.state == ConnectionState.DISCONNECTED:
            return

        logger.info("Disconnecting feed...")
        self._set_state(ConnectionState.DISCONNECTED)
        logger.info("Feed disconnected")

    def simulate_disconnect(self) -> None:
        """
        Simulate a disconnect (for testing reconnection logic).

        This is a test helper for Phase 1 validation.
        """
        if self.state != ConnectionState.CONNECTED:
            logger.warning("Cannot simulate disconnect: not connected")
            return

        logger.warning("Simulating disconnect...")
        self._set_state(ConnectionState.DISCONNECTED)

        if self.config.reconnect_enabled:
            self._attempt_reconnect()

    def _attempt_reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        if not self.config.reconnect_enabled:
            logger.info("Reconnection disabled")
            return

        if self._reconnect_attempts >= self.config.reconnect_max_attempts:
            logger.error(
                f"Max reconnect attempts ({self.config.reconnect_max_attempts}) reached"
            )
            self._set_state(ConnectionState.FAILED)
            self.metrics.record_error(error_type="reconnect_failed")
            return

        self._reconnect_attempts += 1
        backoff_delay = self.config.reconnect_backoff_base**self._reconnect_attempts

        logger.info(
            f"Reconnecting (attempt {self._reconnect_attempts}/{self.config.reconnect_max_attempts}, "
            f"backoff: {backoff_delay:.1f}s)..."
        )
        self._set_state(ConnectionState.RECONNECTING)

        # STUB: Simulate backoff
        time.sleep(min(backoff_delay, 0.1))  # Cap for testing

        # Try to reconnect
        success = self.connect()

        if success:
            self.stats.reconnect_count += 1
            self.metrics.record_reconnect(
                labels={"exchange": self.config.exchange}
            )

            # Trigger backfill
            if self.config.backfill_enabled:
                self._trigger_backfill()
        else:
            logger.error("Reconnection failed")
            self._set_state(ConnectionState.FAILED)

    def _trigger_backfill(self) -> None:
        """Trigger backfill for missed data."""
        if not self.config.backfill_enabled:
            return

        now_ms = int(time.time() * 1000)
        backfill_start_ms = now_ms - self.config.backfill_lookback_ms

        logger.info(
            f"Triggering backfill: {backfill_start_ms} -> {now_ms} "
            f"(lookback: {self.config.backfill_lookback_ms}ms)"
        )

        self.stats.backfill_count += 1

        # Callback to external backfill handler
        if self.on_backfill_requested:
            self.on_backfill_requested(backfill_start_ms, now_ms)

    def process_message(self, message: Any) -> list[Tick]:
        """
        Process a raw WebSocket message.

        Args:
            message: Raw message (typically list/dict from WS)

        Returns:
            List of parsed Ticks
        """
        self.stats.messages_received += 1

        # Measure latency (message arrival)
        arrival_ts_ms = int(time.time() * 1000)

        # Parse using existing normalizer
        ticks = parse_kraken_trade_message(message)

        if not ticks:
            self.stats.messages_failed += 1
            logger.debug(f"Failed to parse message: {message}")
            return []

        self.stats.messages_parsed += 1

        # Track latency for each tick
        for tick in ticks:
            latency_ms = arrival_ts_ms - tick.ts_ms
            if latency_ms >= 0:  # Only positive latencies (sanity check)
                self.metrics.record_latency(latency_ms, labels={"symbol": tick.symbol})

            self.stats.last_message_ts_ms = tick.ts_ms

            # Callback
            if self.on_tick:
                self.on_tick(tick)

        return ticks

    def _set_state(
        self,
        new_state: ConnectionState,
    ) -> None:
        """Set connection state and trigger callback."""
        old_state = self.state
        self.state = new_state

        if old_state != new_state:
            logger.debug(f"Connection state: {old_state.value} -> {new_state.value}")

            if self.on_connection_state_change:
                self.on_connection_state_change(old_state, new_state)

    def get_stats(self) -> FeedStats:
        """Get current feed statistics."""
        return self.stats

    def is_connected(self) -> bool:
        """Check if feed is connected."""
        return self.state == ConnectionState.CONNECTED
