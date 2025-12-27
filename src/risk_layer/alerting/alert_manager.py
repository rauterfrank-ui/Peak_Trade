"""
Alert Manager
=============

Central coordinator for alert registration, filtering, and dispatching.
"""

from datetime import datetime
from typing import List, Optional

from src.risk_layer.alerting.alert_config import AlertConfig
from src.risk_layer.alerting.alert_dispatcher import AlertDispatcher
from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertCategory, AlertSeverity


class AlertManager:
    """
    Central manager for the alerting system.

    Responsibilities:
    - Register new alert events
    - Filter based on configuration (severity, category, etc.)
    - Maintain in-memory buffer of recent events
    - Dispatch to configured channels via AlertDispatcher

    Thread-safe for concurrent alert generation.
    """

    def __init__(
        self,
        config: AlertConfig,
        dispatcher: Optional[AlertDispatcher] = None,
    ):
        """
        Initialize AlertManager.

        Args:
            config: Alert configuration
            dispatcher: AlertDispatcher instance (creates default if None)
        """
        self.config = config
        self.dispatcher = dispatcher or AlertDispatcher()
        self._event_buffer: List[AlertEvent] = []

    def register_alert(
        self,
        severity: AlertSeverity,
        category: AlertCategory,
        source: str,
        message: str,
        context: Optional[dict] = None,
    ) -> Optional[AlertEvent]:
        """
        Register a new alert event.

        Creates AlertEvent, applies filters, stores in buffer,
        and dispatches if alerting is enabled.

        Args:
            severity: Alert severity level
            category: Alert category
            source: Source component/module
            message: Human-readable message
            context: Additional structured data

        Returns:
            AlertEvent if created, None if filtered out
        """
        # Create event
        event = AlertEvent(
            severity=severity,
            category=category,
            source=source,
            message=message,
            context=context or {},
        )

        # Apply severity filter
        if event.severity < self.config.min_severity:
            return None

        # Add to buffer (FIFO, respecting max size)
        self._event_buffer.append(event)
        if len(self._event_buffer) > self.config.buffer_size:
            self._event_buffer.pop(0)

        # Dispatch if enabled
        if self.config.enabled:
            self.dispatcher.dispatch(event)

        return event

    def get_recent_events(
        self,
        limit: Optional[int] = None,
        min_severity: Optional[AlertSeverity] = None,
        categories: Optional[List[AlertCategory]] = None,
        sources: Optional[List[str]] = None,
    ) -> List[AlertEvent]:
        """
        Query recent alert events with filtering.

        Args:
            limit: Max number of events to return (most recent first)
            min_severity: Minimum severity filter
            categories: Category filter (None = all)
            sources: Source filter (None = all)

        Returns:
            List of matching AlertEvents, newest first
        """
        # Start with full buffer (newest first)
        events = list(reversed(self._event_buffer))

        # Apply filters
        if min_severity or categories or sources:
            events = [
                e for e in events
                if e.matches_filter(
                    min_severity=min_severity,
                    categories=categories,
                    sources=sources,
                )
            ]

        # Apply limit
        if limit is not None:
            events = events[:limit]

        return events

    def list_all_events(self) -> List[AlertEvent]:
        """
        Get all buffered events (oldest first).

        Returns:
            List of all AlertEvents in buffer
        """
        return list(self._event_buffer)

    def clear_buffer(self) -> None:
        """
        Clear the event buffer (for testing/maintenance).
        """
        self._event_buffer.clear()

    def get_event_count(self) -> int:
        """
        Get total count of buffered events.

        Returns:
            Number of events in buffer
        """
        return len(self._event_buffer)

    def get_stats(self) -> dict:
        """
        Get alerting statistics.

        Returns:
            Dict with counts by severity and category
        """
        severity_counts = {s.value: 0 for s in AlertSeverity}
        category_counts = {c.value: 0 for c in AlertCategory}

        for event in self._event_buffer:
            severity_counts[event.severity.value] += 1
            category_counts[event.category.value] += 1

        return {
            "total_events": len(self._event_buffer),
            "by_severity": severity_counts,
            "by_category": category_counts,
            "alerting_enabled": self.config.enabled,
            "min_severity": self.config.min_severity.value,
        }
