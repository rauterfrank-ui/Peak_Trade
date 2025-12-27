"""
Generic Webhook Alert Channel
==============================

Sends alerts to custom HTTP webhooks.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional
from urllib import request
from urllib.error import URLError

from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.base_channel import (
    AlertChannel,
    ChannelHealth,
    ChannelStatus,
)


class WebhookChannel(AlertChannel):
    """
    Generic HTTP webhook channel.

    Sends alert as JSON POST request to configured URL.
    Supports custom headers and authentication.

    Config:
        url: Webhook URL (required)
        headers: Dict of custom headers (optional)
        auth_token: Bearer token for Authorization header (optional, from env)
        timeout: Request timeout in seconds (default: 10)
        verify_ssl: Verify SSL certificates (default: True)
    """

    def __init__(
        self,
        config: Dict[str, Any],
        min_severity: AlertSeverity = AlertSeverity.WARNING,
    ):
        """
        Initialize webhook channel.

        Args:
            config: Channel configuration
            min_severity: Minimum severity (default: WARNING)
        """
        super().__init__(name="webhook", config=config, min_severity=min_severity)

        self.url = config.get("url", "")
        self.headers = config.get("headers", {})
        self.auth_token = config.get("auth_token")
        self.timeout = config.get("timeout", 10)
        self.verify_ssl = config.get("verify_ssl", True)

        if not self.url and self._enabled:
            self._health.status = ChannelStatus.FAILED
            self._health.message = "No URL configured"
            self._enabled = False

    async def send(self, event: AlertEvent) -> bool:
        """
        Send alert to webhook.

        Args:
            event: AlertEvent to send

        Returns:
            True if sent successfully (2xx status), False otherwise
        """
        try:
            # Build payload (alert event as JSON)
            payload = event.to_dict()

            # Build headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Peak_Trade-Alerting/2.0",
                **self.headers
            }

            # Add auth token if configured
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            # Send HTTP POST request
            req = request.Request(
                self.url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
            )

            with request.urlopen(req, timeout=self.timeout) as response:
                # Success: 2xx status codes
                return 200 <= response.status < 300

        except URLError as e:
            self._health.last_error = str(e)
            return False
        except Exception as e:
            self._health.last_error = str(e)
            return False

    def health_check(self) -> ChannelHealth:
        """
        Check webhook channel health.

        Returns:
            ChannelHealth
        """
        self._health.last_check = datetime.utcnow()

        if not self._enabled:
            self._health.status = ChannelStatus.DISABLED
            self._health.message = "Channel disabled"
            return self._health

        if not self.url:
            self._health.status = ChannelStatus.FAILED
            self._health.message = "No URL configured"
            return self._health

        # Basic validation: URL format
        if not self.url.startswith(("http://", "https://")):
            self._health.status = ChannelStatus.FAILED
            self._health.message = "Invalid URL format"
        else:
            self._health.status = ChannelStatus.HEALTHY
            self._health.message = "Webhook configured"

        return self._health

    def get_url(self) -> str:
        """
        Get webhook URL (for testing/inspection).

        Returns:
            Webhook URL (redacted if contains auth)
        """
        # Redact credentials in URL
        if "@" in self.url:
            parts = self.url.split("@")
            return f"{parts[0].split('://')[0]}://***@{parts[1]}"
        return self.url
