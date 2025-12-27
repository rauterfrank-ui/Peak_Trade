"""
Webhook Notification Channel
=============================

Sends alerts to a generic webhook endpoint (disabled by default).
"""

import json
import logging
import os
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from ..models import AlertEvent

logger = logging.getLogger(__name__)


class WebhookChannel:
    """
    Generic webhook notification channel.

    Features:
    - Sends alerts as JSON POST to webhook URL
    - Configurable via environment variable
    - Disabled by default (requires webhook_url)
    - Timeout protection

    Environment Variables:
        RISK_ALERTS_WEBHOOK_URL: Webhook URL for generic alerts
    """

    def __init__(self, webhook_url: Optional[str] = None, timeout: int = 10):
        """
        Initialize webhook channel.

        Args:
            webhook_url: Webhook URL (default: read from env)
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url or os.getenv("RISK_ALERTS_WEBHOOK_URL")
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        """Webhook channel is enabled only if webhook_url is configured."""
        return self.webhook_url is not None

    def send(self, alert: AlertEvent) -> bool:
        """Send alert to webhook endpoint."""
        if not self.enabled:
            logger.debug("Webhook channel disabled (no webhook_url configured)")
            return False

        try:
            payload = alert.to_dict()
            
            req = Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

            with urlopen(req, timeout=self.timeout) as response:
                if 200 <= response.status < 300:
                    logger.info(f"Alert sent to webhook (status: {response.status})")
                    return True
                else:
                    logger.error(f"Webhook returned status {response.status}")
                    return False

        except (URLError, HTTPError) as e:
            logger.error(f"Webhook channel error: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Webhook channel error: {e}", exc_info=True)
            return False
