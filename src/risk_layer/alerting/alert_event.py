"""
Alert Event Dataclass
=====================

Core data structure for alert events in the Risk-Layer alerting system.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from src.risk_layer.alerting.alert_types import AlertCategory, AlertSeverity


@dataclass(frozen=True)
class AlertEvent:
    """
    Immutable alert event with all required metadata.

    Represents a single alert occurrence with full context for
    routing, filtering, and auditing.

    Attributes:
        event_id: Unique identifier for this alert event
        timestamp: When the alert was created (UTC)
        severity: Severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        category: Functional category for routing
        source: Module/component that generated the alert
        message: Human-readable alert message
        context: Additional structured data (positions, limits, etc.)
    """

    severity: AlertSeverity
    category: AlertCategory
    source: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.utcnow())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields."""
        if not self.source:
            raise ValueError("AlertEvent.source cannot be empty")
        if not self.message:
            raise ValueError("AlertEvent.message cannot be empty")
        if not isinstance(self.severity, AlertSeverity):
            raise TypeError(f"severity must be AlertSeverity, got {type(self.severity)}")
        if not isinstance(self.category, AlertCategory):
            raise TypeError(f"category must be AlertCategory, got {type(self.category)}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert alert to dictionary for serialization/logging.

        Returns:
            Dict with all alert fields, timestamp as ISO format
        """
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
            "source": self.source,
            "message": self.message,
            "context": self.context,
        }

    def matches_filter(
        self,
        min_severity: Optional[AlertSeverity] = None,
        categories: Optional[list[AlertCategory]] = None,
        sources: Optional[list[str]] = None,
    ) -> bool:
        """
        Check if this alert matches given filter criteria.

        Args:
            min_severity: Minimum severity level (inclusive)
            categories: List of allowed categories (None = all)
            sources: List of allowed sources (None = all)

        Returns:
            True if alert matches all provided filters
        """
        if min_severity is not None and self.severity < min_severity:
            return False
        if categories is not None and self.category not in categories:
            return False
        if sources is not None and self.source not in sources:
            return False
        return True
