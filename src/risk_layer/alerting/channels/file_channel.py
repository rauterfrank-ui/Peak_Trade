"""
File Alert Channel
==================

Writes alerts to log files with rotation support.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.base_channel import (
    AlertChannel,
    ChannelHealth,
    ChannelStatus,
)


class FileChannel(AlertChannel):
    """
    File alert channel.

    Writes alerts to log files with:
    - JSON Lines format (one JSON object per line)
    - Daily rotation (filename includes date)
    - Configurable retention

    File naming: alerts_YYYY-MM-DD.jsonl
    """

    def __init__(
        self,
        config: Dict[str, Any],
        min_severity: AlertSeverity = AlertSeverity.INFO,
    ):
        """
        Initialize file channel.

        Args:
            config: Channel configuration with:
                - path: Directory for log files
                - format: "jsonl" (default)
                - rotation: "daily" | "hourly" (default: daily)
            min_severity: Minimum severity (default: INFO)
        """
        super().__init__(name="file", config=config, min_severity=min_severity)

        self.path = Path(config.get("path", "logs/alerts"))
        self.format = config.get("format", "jsonl")
        self.rotation = config.get("rotation", "daily")

        # Ensure directory exists
        if self._enabled:
            try:
                self.path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self._health.status = ChannelStatus.FAILED
                self._health.message = f"Failed to create directory: {e}"
                self._enabled = False

    async def send(self, event: AlertEvent) -> bool:
        """
        Send alert to file.

        Args:
            event: AlertEvent to send

        Returns:
            True if written successfully, False otherwise
        """
        try:
            filepath = self._get_filepath()

            # Format as JSON line
            line = json.dumps(event.to_dict()) + "\n"

            # Append to file
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()

            return True

        except Exception as e:
            self._health.last_error = str(e)
            return False

    def _get_filepath(self) -> Path:
        """
        Get filepath for current alert.

        Returns:
            Path to log file (includes rotation pattern)
        """
        now = datetime.utcnow()

        if self.rotation == "hourly":
            filename = f"alerts_{now.strftime('%Y-%m-%d_%H')}.jsonl"
        else:  # daily (default)
            filename = f"alerts_{now.strftime('%Y-%m-%d')}.jsonl"

        return self.path / filename

    def health_check(self) -> ChannelHealth:
        """
        Check file channel health.

        Returns:
            ChannelHealth with directory writability check
        """
        self._health.last_check = datetime.utcnow()

        if not self._enabled:
            self._health.status = ChannelStatus.DISABLED
            self._health.message = "Channel disabled"
            return self._health

        # Check if directory exists and is writable
        try:
            if not self.path.exists():
                self._health.status = ChannelStatus.FAILED
                self._health.message = f"Directory does not exist: {self.path}"
            elif not os.access(self.path, os.W_OK):
                self._health.status = ChannelStatus.FAILED
                self._health.message = f"Directory not writable: {self.path}"
            else:
                self._health.status = ChannelStatus.HEALTHY
                self._health.message = "File channel operational"
        except Exception as e:
            self._health.status = ChannelStatus.FAILED
            self._health.message = f"Health check failed: {e}"

        return self._health

    def get_current_filepath(self) -> Path:
        """
        Get current log file path (for testing/inspection).

        Returns:
            Path to current log file
        """
        return self._get_filepath()

    def list_log_files(self) -> list[Path]:
        """
        List all alert log files.

        Returns:
            List of log file paths
        """
        if not self.path.exists():
            return []

        return sorted(self.path.glob("alerts_*.jsonl"))
