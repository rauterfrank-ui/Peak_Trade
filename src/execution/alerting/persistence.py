"""
Alert Persistence - Phase 16I

Lightweight alert storage (in-memory + optional JSONL).
"""

import json
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, List, Optional

from .models import AlertEvent

logger = logging.getLogger(__name__)


class AlertStore:
    """
    Alert storage (in-memory with optional JSONL persistence).

    Features:
    - In-memory cache with max size
    - Optional JSONL persistence
    - Thread-safe operations (no locking for now, single-process)
    """

    def __init__(
        self,
        max_size: int = 1000,
        persist_path: Optional[Path] = None,
    ):
        """
        Initialize alert store.

        Args:
            max_size: Maximum alerts to keep in memory
            persist_path: Optional JSONL file path for persistence
        """
        self.max_size = max_size
        self.persist_path = persist_path

        # In-memory cache (FIFO)
        self._alerts: Deque[AlertEvent] = deque(maxlen=max_size)

        # Load from file if exists
        if persist_path and persist_path.exists():
            self._load_from_file()

    def add(self, alert: AlertEvent):
        """Add alert to store."""
        self._alerts.append(alert)

        # Persist if configured
        if self.persist_path:
            self._append_to_file(alert)

    def add_many(self, alerts: List[AlertEvent]):
        """Add multiple alerts to store."""
        for alert in alerts:
            self.add(alert)

    def get_latest(self, limit: int = 50) -> List[AlertEvent]:
        """
        Get latest alerts.

        Args:
            limit: Maximum alerts to return

        Returns:
            List of AlertEvent objects (newest first)
        """
        # Convert deque to list and reverse (newest first)
        alerts = list(self._alerts)
        alerts.reverse()

        return alerts[:limit]

    def get_by_severity(self, severity: str, limit: int = 50) -> List[AlertEvent]:
        """Get alerts by severity."""
        filtered = [a for a in self._alerts if a.severity.value == severity]
        filtered.reverse()
        return filtered[:limit]

    def clear(self):
        """Clear all alerts from memory."""
        self._alerts.clear()

    def _load_from_file(self):
        """Load alerts from JSONL file."""
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        alert = AlertEvent.from_dict(data)
                        self._alerts.append(alert)
                    except Exception as e:
                        logger.warning(f"Failed to load alert at line {line_no}: {e}")

            logger.info(f"Loaded {len(self._alerts)} alerts from {self.persist_path}")

        except Exception as e:
            logger.error(f"Failed to load alerts from file: {e}")

    def _append_to_file(self, alert: AlertEvent):
        """Append alert to JSONL file."""
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.persist_path, "a", encoding="utf-8") as f:
                json.dump(alert.to_dict(), f)
                f.write("\n")

        except Exception as e:
            logger.error(f"Failed to persist alert: {e}")


# Global alert store (singleton)
_global_alert_store: Optional[AlertStore] = None


def get_global_alert_store() -> AlertStore:
    """Get or create global alert store."""
    global _global_alert_store

    if _global_alert_store is None:
        # Optional persistence path
        persist_path = Path("logs/telemetry_alerts.jsonl")

        # Only enable persistence if explicitly configured
        # (avoid creating file unless user wants it)
        persist_path = None  # Disabled by default

        _global_alert_store = AlertStore(max_size=1000, persist_path=persist_path)

    return _global_alert_store
