"""
Base Alert Channel
==================

Abstract base class for all alert channels.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertSeverity


class ChannelStatus(str, Enum):
    """Health status of a channel."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class ChannelHealth:
    """Health check result for a channel."""

    status: ChannelStatus
    last_check: datetime
    message: str
    success_count: int = 0
    failure_count: int = 0
    last_error: Optional[str] = None


class AlertChannel(ABC):
    """
    Abstract base class for alert channels.

    All channels must implement:
    - send(): Async method to deliver alert
    - health_check(): Synchronous health verification

    Features:
    - Severity filtering
    - Enable/disable toggle
    - Health tracking
    - Automatic error handling
    """

    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        min_severity: AlertSeverity = AlertSeverity.WARNING,
    ):
        """
        Initialize alert channel.

        Args:
            name: Channel identifier (e.g., "slack", "email")
            config: Channel configuration dict
            min_severity: Minimum severity to process (default: WARNING)
        """
        self.name = name
        self.config = config
        self.min_severity = min_severity
        self._enabled = config.get("enabled", False)  # Default: disabled

        # Health tracking
        self._health = ChannelHealth(
            status=ChannelStatus.HEALTHY if self._enabled else ChannelStatus.DISABLED,
            last_check=datetime.utcnow(),
            message="Initialized",
        )

    def is_enabled(self) -> bool:
        """Check if channel is enabled."""
        return self._enabled

    def should_send(self, event: AlertEvent) -> bool:
        """
        Determine if event should be sent to this channel.

        Args:
            event: Alert event to check

        Returns:
            True if event meets severity threshold and channel is enabled
        """
        if not self._enabled:
            return False
        return event.severity >= self.min_severity

    async def dispatch(self, event: AlertEvent) -> bool:
        """
        Dispatch alert to channel with error handling.

        Args:
            event: Alert event to send

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.should_send(event):
            return False

        try:
            success = await self.send(event)
            if success:
                self._health.success_count += 1
                if self._health.status == ChannelStatus.FAILED:
                    # Recovery from failure
                    self._health.status = ChannelStatus.HEALTHY
                    self._health.message = "Recovered"
            else:
                self._health.failure_count += 1
                self._health.status = ChannelStatus.DEGRADED
            return success
        except Exception as e:
            self._health.failure_count += 1
            self._health.last_error = str(e)
            self._health.status = ChannelStatus.FAILED
            self._health.message = f"Send failed: {e}"
            return False

    @abstractmethod
    async def send(self, event: AlertEvent) -> bool:
        """
        Send alert to channel (implemented by subclasses).

        Args:
            event: Alert event to send

        Returns:
            True if sent successfully, False otherwise

        Raises:
            Exception on critical errors (caught by dispatch())
        """
        pass

    @abstractmethod
    def health_check(self) -> ChannelHealth:
        """
        Check channel health (implemented by subclasses).

        Returns:
            ChannelHealth with current status
        """
        pass

    def get_health(self) -> ChannelHealth:
        """
        Get current health status.

        Returns:
            Current ChannelHealth
        """
        return self._health

    def __repr__(self) -> str:
        """String representation."""
        status = "enabled" if self._enabled else "disabled"
        return f"{self.__class__.__name__}(name={self.name}, {status}, min_severity={self.min_severity.value})"
