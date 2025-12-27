"""
Telegram Notification Channel
==============================

Sends alerts to Telegram via bot API (disabled by default).
"""

import json
import logging
import os
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from ..models import AlertEvent

logger = logging.getLogger(__name__)


class TelegramChannel:
    """
    Telegram notification channel (Bot API).

    Features:
    - Sends alerts to Telegram via Bot API
    - Configurable via environment variables
    - Disabled by default (requires bot_token and chat_id)
    - Markdown formatting support

    Environment Variables:
        RISK_ALERTS_TELEGRAM_BOT_TOKEN: Telegram bot token
        RISK_ALERTS_TELEGRAM_CHAT_ID: Telegram chat ID
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        """
        Initialize Telegram channel.

        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID
        """
        self.bot_token = bot_token or os.getenv("RISK_ALERTS_TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("RISK_ALERTS_TELEGRAM_CHAT_ID")

    @property
    def enabled(self) -> bool:
        """Telegram channel is enabled only if bot_token and chat_id are configured."""
        return self.bot_token is not None and self.chat_id is not None

    def send(self, alert: AlertEvent) -> bool:
        """Send alert to Telegram."""
        if not self.enabled:
            logger.debug("Telegram channel disabled (missing bot_token or chat_id)")
            return False

        try:
            message = self._format_telegram_message(alert)
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }

            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

            with urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info("Alert sent to Telegram")
                    return True
                else:
                    logger.error(f"Telegram API returned status {response.status}")
                    return False

        except (URLError, HTTPError) as e:
            logger.error(f"Telegram channel error: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Telegram channel error: {e}", exc_info=True)
            return False

    def _format_telegram_message(self, alert: AlertEvent) -> str:
        """Format alert as Telegram message with Markdown."""
        # Emoji for severity
        emoji_map = {
            "info": "ℹ️",
            "warn": "⚠️",
            "critical": "🚨",
        }
        emoji = emoji_map.get(alert.severity.value, "🔔")

        # Build message
        lines = [
            f"{emoji} *[{alert.severity.value.upper()}] {self._escape_markdown(alert.title)}*",
            "",
            f"*Source:* {self._escape_markdown(alert.source)}",
            f"*Time:* {alert.timestamp_utc.isoformat()}",
            "",
            f"*Message:*",
            self._escape_markdown(alert.body),
        ]

        # Add labels
        if alert.labels:
            lines.append("")
            lines.append("*Labels:*")
            for key, value in alert.labels.items():
                lines.append(f"  • {self._escape_markdown(key)}: {self._escape_markdown(value)}")

        return "\n".join(lines)

    def _escape_markdown(self, text: str) -> str:
        """Escape special characters for Telegram Markdown."""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text
