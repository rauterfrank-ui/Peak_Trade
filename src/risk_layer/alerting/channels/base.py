"""
Base Channel Interface
=======================

Protocol for notification channel implementations.
"""

from typing import Protocol

from ..models import AlertEvent


class NotificationChannel(Protocol):
    """
    Protocol for notification channels.

    All channel implementations must provide:
    - send(alert): Send alert to the channel
    - enabled: Property indicating if channel is active
    """

    @property
    def enabled(self) -> bool:
        """Check if channel is enabled."""
        ...

    def send(self, alert: AlertEvent) -> bool:
        """
        Send alert to channel.

        Args:
            alert: Alert event to send

        Returns:
            True if send succeeded, False otherwise
        """
        ...
