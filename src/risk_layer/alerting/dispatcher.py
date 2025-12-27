"""
Alert Dispatcher
================

Routes alerts to appropriate channels based on severity with failover support.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from .channels import NotificationChannel
from .models import AlertEvent, AlertSeverity

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """
    Alert dispatcher with severity-based routing and failover.

    Features:
    - Severity-based routing matrix
    - Failover to alternative channels on failure
    - Async dispatch support
    - Thread-safe execution
    """

    def __init__(
        self,
        channels: List[NotificationChannel],
        routing_matrix: Optional[Dict[AlertSeverity, List[str]]] = None,
        enable_failover: bool = True,
    ):
        """
        Initialize alert dispatcher.

        Args:
            channels: List of notification channels
            routing_matrix: Severity to channel names mapping
                          (default: route based on severity)
            enable_failover: Enable failover to other channels on failure
        """
        self.channels = {self._get_channel_name(ch): ch for ch in channels}
        self.enable_failover = enable_failover

        # Default routing matrix
        if routing_matrix is None:
            routing_matrix = {
                AlertSeverity.INFO: ["console", "file"],
                AlertSeverity.WARN: ["console", "file", "slack"],
                AlertSeverity.CRITICAL: ["console", "file", "email", "slack", "telegram"],
            }

        self.routing_matrix = routing_matrix

    def dispatch(self, alert: AlertEvent) -> Dict[str, bool]:
        """
        Dispatch alert to channels based on severity.

        Args:
            alert: Alert event to dispatch

        Returns:
            Dict mapping channel names to success status
        """
        channel_names = self.routing_matrix.get(alert.severity, ["console"])
        results = {}

        # Send to primary channels
        for channel_name in channel_names:
            channel = self.channels.get(channel_name)
            if channel and channel.enabled:
                try:
                    success = channel.send(alert)
                    results[channel_name] = success

                    if not success:
                        logger.warning(f"Channel {channel_name} failed to send alert")
                except Exception as e:
                    logger.error(f"Error dispatching to {channel_name}: {e}", exc_info=True)
                    results[channel_name] = False
            else:
                logger.debug(f"Channel {channel_name} not available or disabled")

        # Failover if all channels failed
        if self.enable_failover and all(not success for success in results.values()):
            logger.warning("All primary channels failed, attempting failover")
            results.update(self._failover(alert, set(channel_names)))

        return results

    def dispatch_async(self, alert: AlertEvent) -> Dict[str, bool]:
        """
        Dispatch alert asynchronously using thread pool.

        Args:
            alert: Alert event to dispatch

        Returns:
            Dict mapping channel names to success status
        """
        channel_names = self.routing_matrix.get(alert.severity, ["console"])
        results = {}

        with ThreadPoolExecutor(max_workers=len(channel_names)) as executor:
            futures = {}

            for channel_name in channel_names:
                channel = self.channels.get(channel_name)
                if channel and channel.enabled:
                    future = executor.submit(self._send_safe, channel, alert)
                    futures[channel_name] = future

            # Collect results
            for channel_name, future in futures.items():
                try:
                    results[channel_name] = future.result(timeout=30)
                except Exception as e:
                    logger.error(f"Async dispatch to {channel_name} failed: {e}")
                    results[channel_name] = False

        # Failover if all channels failed
        if self.enable_failover and all(not success for success in results.values()):
            logger.warning("All primary channels failed, attempting failover")
            results.update(self._failover(alert, set(channel_names)))

        return results

    def _send_safe(self, channel: NotificationChannel, alert: AlertEvent) -> bool:
        """Send alert with exception handling."""
        try:
            return channel.send(alert)
        except Exception as e:
            logger.error(f"Error sending alert: {e}", exc_info=True)
            return False

    def _failover(self, alert: AlertEvent, tried_channels: set) -> Dict[str, bool]:
        """
        Attempt to send alert to backup channels.

        Args:
            alert: Alert event to send
            tried_channels: Set of channel names already tried

        Returns:
            Dict mapping channel names to success status
        """
        results = {}
        fallback_order = ["console", "file", "slack", "email", "telegram", "webhook"]

        for channel_name in fallback_order:
            if channel_name in tried_channels:
                continue

            channel = self.channels.get(channel_name)
            if channel and channel.enabled:
                try:
                    success = channel.send(alert)
                    results[channel_name] = success

                    if success:
                        logger.info(f"Failover successful to {channel_name}")
                        break
                except Exception as e:
                    logger.error(f"Failover to {channel_name} failed: {e}")
                    results[channel_name] = False

        return results

    def _get_channel_name(self, channel: NotificationChannel) -> str:
        """Get standardized channel name from channel instance."""
        class_name = channel.__class__.__name__
        # Remove 'Channel' suffix if present
        if class_name.endswith("Channel"):
            return class_name[:-7].lower()
        return class_name.lower()

    def get_enabled_channels(self) -> List[str]:
        """Get list of enabled channel names."""
        return [name for name, ch in self.channels.items() if ch.enabled]

    def get_routing_for_severity(self, severity: AlertSeverity) -> List[str]:
        """Get channel names for given severity."""
        return self.routing_matrix.get(severity, ["console"])
