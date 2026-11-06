"""
Telegram Alert Channel
======================

Sends alerts via Telegram Bot API.
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


class TelegramChannel(AlertChannel):
    """
    Telegram alert channel via Bot API.

    Features:
    - Markdown formatting
    - Severity-based emojis
    - Silent notifications for low severity

    Config:
        bot_token: Telegram bot token (from env: ${TELEGRAM_BOT_TOKEN})
        chat_id: Target chat ID (from env: ${TELEGRAM_CHAT_ID})
        parse_mode: "Markdown" | "HTML" (default: Markdown)
        disable_notification: Disable sound for DEBUG/INFO (default: True)
    """

    def __init__(
        self,
        config: Dict[str, Any],
        min_severity: AlertSeverity = AlertSeverity.CRITICAL,
    ):
        """
        Initialize Telegram channel.

        Args:
            config: Channel configuration
            min_severity: Minimum severity (default: CRITICAL)
        """
        super().__init__(name="telegram", config=config, min_severity=min_severity)

        self.bot_token = config.get("bot_token", "")
        self.chat_id = config.get("chat_id", "")
        self.parse_mode = config.get("parse_mode", "Markdown")
        self.disable_notification = config.get("disable_notification", True)

        # Validate configuration
        if self._enabled and (not self.bot_token or not self.chat_id):
            self._health.status = ChannelStatus.FAILED
            self._health.message = "Missing bot_token or chat_id"
            self._enabled = False

    async def send(self, event: AlertEvent) -> bool:
        """
        Send alert via Telegram.

        Args:
            event: AlertEvent to send

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Build message
            text = self._format_message(event)

            # Build API request
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": self.parse_mode,
                "disable_notification": self.disable_notification
                and event.severity < AlertSeverity.WARNING,
            }

            # Send HTTP POST request
            req = request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

            with request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("ok", False)

        except URLError as e:
            self._health.last_error = str(e)
            return False
        except Exception as e:
            self._health.last_error = str(e)
            return False

    def _format_message(self, event: AlertEvent) -> str:
        """
        Format alert as Telegram message.

        Args:
            event: AlertEvent to format

        Returns:
            Formatted message string
        """
        # Severity emoji
        emoji = {
            AlertSeverity.DEBUG: "🔍",
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨",
        }.get(event.severity, "📢")

        # Build message (Markdown format)
        lines = [
            f"{emoji} *{event.severity.value.upper()} Alert*",
            "",
            f"*Source:* {event.source}",
            f"*Category:* {event.category.value}",
            f"*Time:* {event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            f"*Message:*",
            event.message,
        ]

        # Add context (limit to avoid message size limits)
        if event.context:
            lines.append("")
            lines.append("*Context:*")
            for i, (key, value) in enumerate(event.context.items()):
                if i >= 5:  # Limit to 5 items
                    lines.append(f"  ... ({len(event.context) - 5} more)")
                    break
                lines.append(f"  • {key}: `{value}`")

        lines.append("")
        lines.append(f"_Event ID: {event.event_id[:8]}_")

        return "\n".join(lines)

    def health_check(self) -> ChannelHealth:
        """
        Check Telegram channel health.

        Returns:
            ChannelHealth
        """
        self._health.last_check = datetime.utcnow()

        if not self._enabled:
            self._health.status = ChannelStatus.DISABLED
            self._health.message = "Channel disabled or misconfigured"
            return self._health

        # Basic validation
        if not self.bot_token or not self.chat_id:
            self._health.status = ChannelStatus.FAILED
            self._health.message = "Missing bot_token or chat_id"
        else:
            self._health.status = ChannelStatus.HEALTHY
            self._health.message = "Telegram bot configured"

        return self._health
