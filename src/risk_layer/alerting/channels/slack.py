"""
Slack Notification Channel
===========================

Sends alerts to Slack via webhook (disabled by default).
"""

import json
import logging
import os
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from ..models import AlertEvent

logger = logging.getLogger(__name__)


class SlackChannel:
    """
    Slack notification channel (webhook).

    Features:
    - Sends alerts to Slack via webhook URL
    - Configurable via environment variable
    - Disabled by default (requires webhook_url)
    - Rich message formatting with color coding

    Environment Variables:
        RISK_ALERTS_SLACK_WEBHOOK: Slack webhook URL
    """

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack channel.

        Args:
            webhook_url: Slack webhook URL (default: read from env)
        """
        self.webhook_url = webhook_url or os.getenv("RISK_ALERTS_SLACK_WEBHOOK")

    @property
    def enabled(self) -> bool:
        """Slack channel is enabled only if webhook_url is configured."""
        return self.webhook_url is not None

    def send(self, alert: AlertEvent) -> bool:
        """Send alert to Slack."""
        if not self.enabled:
            logger.debug("Slack channel disabled (no webhook_url configured)")
            return False

        try:
            payload = self._format_slack_message(alert)
            
            req = Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

            with urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info("Alert sent to Slack")
                    return True
                else:
                    logger.error(f"Slack webhook returned status {response.status}")
                    return False

        except (URLError, HTTPError) as e:
            logger.error(f"Slack channel error: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Slack channel error: {e}", exc_info=True)
            return False

    def _format_slack_message(self, alert: AlertEvent) -> dict:
        """Format alert as Slack message payload."""
        # Color coding by severity
        color_map = {
            "info": "#17a2b8",
            "warn": "#ffc107",
            "critical": "#dc3545",
        }
        color = color_map.get(alert.severity.value, "#6c757d")

        # Emoji for severity
        emoji_map = {
            "info": ":information_source:",
            "warn": ":warning:",
            "critical": ":rotating_light:",
        }
        emoji = emoji_map.get(alert.severity.value, ":bell:")

        fields = [
            {
                "title": "Source",
                "value": alert.source,
                "short": True,
            },
            {
                "title": "Severity",
                "value": alert.severity.value.upper(),
                "short": True,
            },
            {
                "title": "Time",
                "value": alert.timestamp_utc.isoformat(),
                "short": False,
            },
        ]

        # Add labels as fields
        if alert.labels:
            for key, value in alert.labels.items():
                fields.append({
                    "title": key,
                    "value": value,
                    "short": True,
                })

        attachment = {
            "color": color,
            "title": f"{emoji} {alert.title}",
            "text": alert.body,
            "fields": fields,
            "footer": "Risk Layer Alerting",
            "ts": int(alert.timestamp_utc.timestamp()),
        }

        return {"attachments": [attachment]}
