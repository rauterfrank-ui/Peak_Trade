"""
Console Alert Channel
=====================

Outputs alerts to stdout/stderr based on severity.
"""

import sys
from datetime import datetime
from typing import Any, Dict

from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.base_channel import (
    AlertChannel,
    ChannelHealth,
    ChannelStatus,
)


class ConsoleChannel(AlertChannel):
    """
    Console alert channel.

    Outputs alerts to stdout (INFO, DEBUG) or stderr (WARNING+).

    Formats:
    - simple: One-line format
    - structured: Multi-line with context
    - json: JSON-serialized (for log parsing)
    """

    def __init__(
        self,
        config: Dict[str, Any],
        min_severity: AlertSeverity = AlertSeverity.DEBUG,
    ):
        """
        Initialize console channel.

        Args:
            config: Channel configuration
            min_severity: Minimum severity (default: DEBUG - show everything)
        """
        super().__init__(name="console", config=config, min_severity=min_severity)
        self.format = config.get("format", "structured")  # simple | structured | json

    async def send(self, event: AlertEvent) -> bool:
        """
        Send alert to console.

        Args:
            event: AlertEvent to send

        Returns:
            True (console output always succeeds)
        """
        # Choose output stream based on severity
        stream = sys.stderr if event.severity >= AlertSeverity.WARNING else sys.stdout

        # Format message
        if self.format == "json":
            output = self._format_json(event)
        elif self.format == "simple":
            output = self._format_simple(event)
        else:  # structured
            output = self._format_structured(event)

        # Write to stream
        print(output, file=stream, flush=True)

        return True

    def _format_simple(self, event: AlertEvent) -> str:
        """Format as single line."""
        return f"[{event.severity.value.upper()}] {event.source}: {event.message}"

    def _format_structured(self, event: AlertEvent) -> str:
        """Format as structured multi-line."""
        lines = [
            f"\n{'=' * 60}",
            f"ALERT [{event.severity.value.upper()}]",
            f"{'=' * 60}",
            f"Source:    {event.source}",
            f"Category:  {event.category.value}",
            f"Time:      {event.timestamp.isoformat()}",
            f"Message:   {event.message}",
        ]

        if event.context:
            lines.append("Context:")
            for key, value in event.context.items():
                lines.append(f"  {key}: {value}")

        lines.append(f"Event ID:  {event.event_id}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _format_json(self, event: AlertEvent) -> str:
        """Format as JSON (one line per event)."""
        import json

        return json.dumps(event.to_dict())

    def health_check(self) -> ChannelHealth:
        """
        Check console health.

        Returns:
            ChannelHealth (always healthy if enabled)
        """
        self._health.last_check = datetime.utcnow()

        if not self._enabled:
            self._health.status = ChannelStatus.DISABLED
            self._health.message = "Channel disabled"
        else:
            # Console is always healthy if enabled
            self._health.status = ChannelStatus.HEALTHY
            self._health.message = "Console output available"

        return self._health
