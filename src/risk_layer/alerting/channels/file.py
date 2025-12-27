"""
File Notification Channel
==========================

Appends alerts to a JSONL file for persistent logging.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from ..models import AlertEvent

logger = logging.getLogger(__name__)


class FileChannel:
    """
    File notification channel (JSONL format).

    Features:
    - Persistent storage of alerts
    - JSONL format (one alert per line)
    - Configurable via environment variable
    - Safe directory creation
    - Disabled by default (requires file_path)
    """

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize file channel.

        Args:
            file_path: Path to alerts file (default: read from env RISK_ALERTS_FILE)
        """
        self.file_path = file_path or os.getenv("RISK_ALERTS_FILE")

    @property
    def enabled(self) -> bool:
        """File channel is enabled only if file_path is configured."""
        return self.file_path is not None

    def send(self, alert: AlertEvent) -> bool:
        """Send alert to file (append as JSONL)."""
        if not self.enabled:
            logger.debug("File channel disabled (no file_path configured)")
            return False

        try:
            # Ensure directory exists
            file_path_obj = Path(self.file_path)
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Append alert as JSON line
            with open(self.file_path, "a") as f:
                json.dump(alert.to_dict(), f)
                f.write("\n")

            logger.debug(f"Alert written to file: {self.file_path}")
            return True

        except Exception as e:
            logger.error(f"File channel error: {e}", exc_info=True)
            return False
