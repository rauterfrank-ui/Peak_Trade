"""
Channel Router
==============

Routes alerts to multiple channels based on severity and configuration.
Supports failover and async dispatch.
"""

import asyncio
from typing import Dict, List, Optional

from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.channels.base_channel import AlertChannel


class ChannelRouter:
    """
    Routes alert events to configured channels.

    Features:
    - Severity-based routing
    - Parallel async dispatch to multiple channels
    - Failover: if primary channel fails, try fallback
    - Non-blocking: never blocks main thread
    - Health monitoring
    """

    def __init__(
        self,
        channels: Optional[List[AlertChannel]] = None,
        fallback_chain: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize channel router.

        Args:
            channels: List of AlertChannel instances
            fallback_chain: Dict mapping channel_name -> fallback_channel_name
                           e.g., {"slack": "email", "email": "console"}
        """
        self._channels: Dict[str, AlertChannel] = {}
        if channels:
            for channel in channels:
                self.add_channel(channel)

        self._fallback_chain = fallback_chain or {}
        self._dispatch_count = 0
        self._success_count = 0
        self._failure_count = 0

    def add_channel(self, channel: AlertChannel) -> None:
        """
        Add a channel to the router.

        Args:
            channel: AlertChannel instance
        """
        self._channels[channel.name] = channel

    def get_channel(self, name: str) -> Optional[AlertChannel]:
        """
        Get channel by name.

        Args:
            name: Channel name

        Returns:
            AlertChannel or None if not found
        """
        return self._channels.get(name)

    def list_channels(self) -> List[str]:
        """
        List all registered channel names.

        Returns:
            List of channel names
        """
        return list(self._channels.keys())

    def get_enabled_channels(self) -> List[AlertChannel]:
        """
        Get all enabled channels.

        Returns:
            List of enabled AlertChannel instances
        """
        return [ch for ch in self._channels.values() if ch.is_enabled()]

    async def route_event(self, event: AlertEvent) -> Dict[str, bool]:
        """
        Route event to all applicable channels.

        Dispatches to all channels that:
        1. Are enabled
        2. Have min_severity <= event.severity

        Args:
            event: AlertEvent to route

        Returns:
            Dict mapping channel_name -> success (bool)
        """
        self._dispatch_count += 1

        # Find applicable channels
        applicable_channels = [
            ch for ch in self._channels.values()
            if ch.should_send(event)
        ]

        if not applicable_channels:
            return {}

        # Dispatch to all channels in parallel
        tasks = [
            self._dispatch_with_fallback(ch, event)
            for ch in applicable_channels
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dict
        result_dict = {}
        for channel, result in zip(applicable_channels, results):
            if isinstance(result, Exception):
                result_dict[channel.name] = False
                self._failure_count += 1
            else:
                result_dict[channel.name] = result
                if result:
                    self._success_count += 1
                else:
                    self._failure_count += 1

        return result_dict

    async def _dispatch_with_fallback(
        self,
        channel: AlertChannel,
        event: AlertEvent,
    ) -> bool:
        """
        Dispatch to channel with automatic fallback on failure.

        Args:
            channel: Primary channel
            event: Alert event

        Returns:
            True if sent (primary or fallback), False otherwise
        """
        # Try primary channel
        success = await channel.dispatch(event)
        if success:
            return True

        # Try fallback if configured
        fallback_name = self._fallback_chain.get(channel.name)
        if fallback_name:
            fallback_channel = self._channels.get(fallback_name)
            if fallback_channel and fallback_channel.is_enabled():
                return await fallback_channel.dispatch(event)

        return False

    def route_event_sync(self, event: AlertEvent) -> Dict[str, bool]:
        """
        Synchronous wrapper for route_event.

        Creates new event loop to dispatch asynchronously.
        Use this when calling from sync code.

        Args:
            event: AlertEvent to route

        Returns:
            Dict mapping channel_name -> success (bool)
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context - create task
                return {}  # Can't block in running loop
            else:
                return loop.run_until_complete(self.route_event(event))
        except RuntimeError:
            # No event loop - create new one
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.route_event(event))
            finally:
                loop.close()

    def get_stats(self) -> Dict[str, int]:
        """
        Get routing statistics.

        Returns:
            Dict with dispatch counts
        """
        return {
            "total_dispatches": self._dispatch_count,
            "successful": self._success_count,
            "failed": self._failure_count,
            "channels_registered": len(self._channels),
            "channels_enabled": len(self.get_enabled_channels()),
        }

    def health_check_all(self) -> Dict[str, Dict]:
        """
        Run health check on all channels.

        Returns:
            Dict mapping channel_name -> health status dict
        """
        results = {}
        for name, channel in self._channels.items():
            health = channel.health_check()
            results[name] = {
                "status": health.status.value,
                "message": health.message,
                "success_count": health.success_count,
                "failure_count": health.failure_count,
                "last_error": health.last_error,
            }
        return results
