"""
Slack Alert Channel
===================

Sends alerts to Slack via Incoming Webhooks.
"""

import json
from datetime import datetime
from typing import Any, Dict
from urllib import request
from urllib.error import URLError

from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.base_channel import (
    AlertChannel,
    ChannelHealth,
    ChannelStatus,
)


class SlackChannel(AlertChannel):
    """
    Slack alert channel via Incoming Webhooks.

    Features:
    - Structured message blocks
    - Severity-based colors
    - Optional @mentions for critical alerts
    - Configurable channel and username

    Config:
        webhook_url: Slack webhook URL (from env: ${SLACK_WEBHOOK_URL})
        channel: Override channel (optional, default: webhook default)
        username: Bot username (default: "Peak_Trade Alerts")
        mention_on_critical: List of mentions for CRITICAL+ (e.g., ["@channel"])
    """

    # Severity to color mapping
    SEVERITY_COLORS = {
        AlertSeverity.DEBUG: "#8B8B8B",  # Gray
        AlertSeverity.INFO: "#36A64F",  # Green
        AlertSeverity.WARNING: "#FFA500",  # Orange
        AlertSeverity.ERROR: "#E01E5A",  # Red
        AlertSeverity.CRITICAL: "#8B0000",  # Dark Red
    }

    def __init__(
        self,
        config: Dict[str, Any],
        min_severity: AlertSeverity = AlertSeverity.WARNING,
    ):
        """
        Initialize Slack channel.

        Args:
            config: Channel configuration
            min_severity: Minimum severity (default: WARNING)
        """
        super().__init__(name="slack", config=config, min_severity=min_severity)

        self.webhook_url = config.get("webhook_url", "")
        self.channel = config.get("channel")  # Optional override
        self.username = config.get("username", "Peak_Trade Alerts")
        self.mention_on_critical = config.get("mention_on_critical", [])

        if not self.webhook_url and self._enabled:
            self._health.status = ChannelStatus.FAILED
            self._health.message = "No webhook_url configured"
            self._enabled = False

    async def send(self, event: AlertEvent) -> bool:
        """
        Send alert to Slack.

        Args:
            event: AlertEvent to send

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            payload = self._build_payload(event)

            # Send HTTP POST request
            req = request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

            with request.urlopen(req, timeout=10) as response:
                return response.status == 200

        except URLError as e:
            self._health.last_error = str(e)
            return False
        except Exception as e:
            self._health.last_error = str(e)
            return False

    def _build_payload(self, event: AlertEvent) -> Dict[str, Any]:
        """
        Build Slack message payload.

        Args:
            event: AlertEvent to format

        Returns:
            Slack API payload dict
        """
        # Build mention prefix for critical alerts
        mention_text = ""
        if event.severity >= AlertSeverity.CRITICAL and self.mention_on_critical:
            mention_text = " ".join(self.mention_on_critical) + " "

        # Build blocks (structured message)
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {event.severity.value.upper()} Alert",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Source:*\n{event.source}"},
                    {"type": "mrkdwn", "text": f"*Category:*\n{event.category.value}"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{mention_text}*Message:*\n{event.message}"},
            },
        ]

        # Add context if present
        if event.context:
            context_lines = [f"• *{k}*: `{v}`" for k, v in event.context.items()]
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Context:*\n" + "\n".join(context_lines[:5]),  # Limit to 5 items
                    },
                }
            )

        # Add footer with timestamp and event ID
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"<!date^{int(event.timestamp.timestamp())}^{{date_short_pretty}} {{time}}|{event.timestamp.isoformat()}> | Event ID: `{event.event_id[:8]}`",
                    }
                ],
            }
        )

        payload = {
            "username": self.username,
            "blocks": blocks,
            "attachments": [
                {
                    "color": self.SEVERITY_COLORS.get(event.severity, "#CCCCCC"),
                    "fallback": f"[{event.severity.value.upper()}] {event.source}: {event.message}",
                }
            ],
        }

        # Override channel if configured
        if self.channel:
            payload["channel"] = self.channel

        return payload

    def health_check(self) -> ChannelHealth:
        """
        Check Slack channel health.

        Returns:
            ChannelHealth
        """
        self._health.last_check = datetime.utcnow()

        if not self._enabled:
            self._health.status = ChannelStatus.DISABLED
            self._health.message = "Channel disabled"
            return self._health

        if not self.webhook_url:
            self._health.status = ChannelStatus.FAILED
            self._health.message = "No webhook_url configured"
            return self._health

        # Basic validation: webhook URL format
        if not self.webhook_url.startswith("https://hooks.slack.com/"):
            self._health.status = ChannelStatus.DEGRADED
            self._health.message = "Suspicious webhook_url format"
        else:
            self._health.status = ChannelStatus.HEALTHY
            self._health.message = "Slack webhook configured"

        return self._health
