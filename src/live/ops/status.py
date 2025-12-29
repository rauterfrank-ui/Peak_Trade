"""
Status Overview - WP1D (Phase 1 Shadow Trading)

Read-only system status overview for operators.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class SystemStatus:
    """
    System status snapshot.

    Attributes:
        data_feed_uptime_s: Data feed uptime in seconds
        system_uptime_s: System uptime in seconds
        last_reconnect_ts: Last reconnect timestamp
        last_drift_report_ts: Last drift report timestamp
        metadata: Additional metadata
    """

    data_feed_uptime_s: float
    system_uptime_s: float
    last_reconnect_ts: Optional[datetime]
    last_drift_report_ts: Optional[datetime]
    metadata: Dict

    def to_dict(self) -> Dict:
        """Convert to dict."""
        return {
            "data_feed_uptime_s": self.data_feed_uptime_s,
            "system_uptime_s": self.system_uptime_s,
            "last_reconnect_ts": (
                self.last_reconnect_ts.isoformat() if self.last_reconnect_ts else None
            ),
            "last_drift_report_ts": (
                self.last_drift_report_ts.isoformat()
                if self.last_drift_report_ts
                else None
            ),
            "metadata": self.metadata,
        }


class StatusOverview:
    """
    Read-only system status overview.

    Provides high-level status for operator monitoring:
    - Data feed uptime
    - System uptime
    - Last reconnect
    - Last drift report

    Usage:
        >>> overview = StatusOverview()
        >>> overview.start()  # Start tracking
        >>> status = overview.get_status()
        >>> print(f"System uptime: {status.system_uptime_s}s")
    """

    def __init__(self):
        """Initialize status overview."""
        self._system_start_ts = None
        self._data_feed_start_ts = None
        self._last_reconnect_ts = None
        self._last_drift_report_ts = None
        self._metadata: Dict = {}

    def start(self):
        """Start tracking system status."""
        self._system_start_ts = time.monotonic()
        self._data_feed_start_ts = time.monotonic()
        logger.info("Status overview started")

    def record_reconnect(self):
        """Record data feed reconnect."""
        self._last_reconnect_ts = datetime.utcnow()
        self._data_feed_start_ts = time.monotonic()  # Reset feed uptime
        logger.info("Reconnect recorded")

    def record_drift_report(self):
        """Record drift report generation."""
        self._last_drift_report_ts = datetime.utcnow()
        logger.info("Drift report recorded")

    def update_metadata(self, key: str, value: any):
        """
        Update metadata.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value

    def get_status(self) -> SystemStatus:
        """
        Get current system status.

        Returns:
            SystemStatus snapshot
        """
        now = time.monotonic()

        system_uptime = (
            now - self._system_start_ts if self._system_start_ts else 0.0
        )

        data_feed_uptime = (
            now - self._data_feed_start_ts if self._data_feed_start_ts else 0.0
        )

        return SystemStatus(
            data_feed_uptime_s=data_feed_uptime,
            system_uptime_s=system_uptime,
            last_reconnect_ts=self._last_reconnect_ts,
            last_drift_report_ts=self._last_drift_report_ts,
            metadata=self._metadata.copy(),
        )
