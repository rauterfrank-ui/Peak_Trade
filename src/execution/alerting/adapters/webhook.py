"""
Webhook Alert Sink - Phase 16I

POST alerts to webhook URL (safe by default).
"""

import json
import logging
from typing import Optional
from urllib import request
from urllib.error import HTTPError, URLError

from ..models import AlertEvent

logger = logging.getLogger(__name__)


class WebhookAlertSink:
    """
    Webhook alert sink (HTTP POST).
    
    Features:
    - POST JSON to webhook URL
    - Configurable timeout (default 10s)
    - Error handling (never crashes main process)
    - Disabled by default (must be explicitly enabled + URL provided)
    
    Safety:
    - Safe by default: disabled unless config enables and URL exists
    - Timeouts prevent hanging
    - Errors are logged but don't crash
    """
    
    def __init__(
        self,
        url: str,
        enabled: bool = False,
        timeout: int = 10,
        headers: Optional[dict] = None,
    ):
        """
        Initialize webhook sink.
        
        Args:
            url: Webhook URL (must be valid HTTP/HTTPS)
            enabled: Whether webhook is enabled
            timeout: Request timeout in seconds
            headers: Optional custom headers
        """
        self.url = url
        self.enabled = enabled
        self.timeout = timeout
        self.headers = headers or {
            "Content-Type": "application/json",
            "User-Agent": "Peak_Trade/Telemetry-Alerting",
        }
    
    def send(self, alert: AlertEvent) -> bool:
        """
        Send alert to webhook URL.
        
        Returns:
            True if send succeeded, False otherwise
        """
        if not self.enabled:
            logger.debug("Webhook sink disabled, skipping")
            return False
        
        if not self.url:
            logger.warning("Webhook sink enabled but URL not configured")
            return False
        
        try:
            # Serialize alert to JSON
            payload = alert.to_dict()
            data = json.dumps(payload).encode("utf-8")
            
            # Build request
            req = request.Request(
                self.url,
                data=data,
                headers=self.headers,
                method="POST",
            )
            
            # Send request
            with request.urlopen(req, timeout=self.timeout) as response:
                status = response.getcode()
                
                if 200 <= status < 300:
                    logger.info(f"Webhook sent successfully: {alert.title}")
                    return True
                else:
                    logger.warning(f"Webhook returned status {status}: {alert.title}")
                    return False
        
        except HTTPError as e:
            logger.error(
                f"Webhook HTTP error {e.code} for alert '{alert.title}': {e.reason}"
            )
            return False
        
        except URLError as e:
            logger.error(f"Webhook URL error for alert '{alert.title}': {e.reason}")
            return False
        
        except Exception as e:
            logger.error(
                f"Webhook send failed for alert '{alert.title}': {e}",
                exc_info=True,
            )
            return False
