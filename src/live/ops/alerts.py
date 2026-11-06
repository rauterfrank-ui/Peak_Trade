"""
Operator Alerts - WP1D (Phase 1 Shadow Trading)

Minimal alert system with P1/P2 priorities and runbook links.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertPriority(str, Enum):
    """Alert priority levels."""

    P1 = "P1"  # Critical - immediate action required
    P2 = "P2"  # Warning - action required within hours
    P3 = "P3"  # Info - monitor but no immediate action


@dataclass
class Alert:
    """
    Operator alert.

    Attributes:
        alert_id: Unique alert ID
        priority: Alert priority (P1/P2/P3)
        code: Alert code
        message: Alert message
        runbook_link: Link to runbook
        timestamp: Alert timestamp
        metadata: Additional metadata
    """

    alert_id: str
    priority: AlertPriority
    code: str
    message: str
    runbook_link: str
    timestamp: datetime
    metadata: Dict

    def to_dict(self) -> Dict:
        """Convert to dict."""
        return {
            "alert_id": self.alert_id,
            "priority": self.priority.value,
            "code": self.code,
            "message": self.message,
            "runbook_link": self.runbook_link,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class OperatorAlerts:
    """
    Operator alert system with P1/P2 priorities.

    Provides minimal alert routing with runbook links.

    Usage:
        >>> alerts = OperatorAlerts()
        >>> alerts.raise_p1("DRIFT_CRITICAL", "Critical drift detected")
        >>> recent = alerts.get_recent_alerts(hours=24)
    """

    # Runbook mapping
    RUNBOOKS = {
        "DRIFT_CRITICAL": "docs/ops/runbooks/drift_critical.md",
        "DRIFT_HIGH": "docs/ops/runbooks/drift_high.md",
        "DATA_FEED_DOWN": "docs/ops/runbooks/data_feed_down.md",
        "EXECUTION_ERROR": "docs/ops/runbooks/execution_error.md",
        "RISK_LIMIT_BREACH": "docs/ops/runbooks/risk_limit_breach.md",
    }

    def __init__(self):
        """Initialize operator alerts."""
        self._alerts: List[Alert] = []
        self._alert_counter = 0

    def raise_alert(
        self,
        priority: AlertPriority,
        code: str,
        message: str,
        metadata: Optional[Dict] = None,
    ) -> Alert:
        """
        Raise an alert.

        Args:
            priority: Alert priority
            code: Alert code
            message: Alert message
            metadata: Optional metadata

        Returns:
            Alert
        """
        self._alert_counter += 1

        alert = Alert(
            alert_id=f"alert_{self._alert_counter:06d}",
            priority=priority,
            code=code,
            message=message,
            runbook_link=self.RUNBOOKS.get(code, "docs/ops/runbooks/general.md"),
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        self._alerts.append(alert)

        logger.log(
            logging.CRITICAL if priority == AlertPriority.P1 else logging.WARNING,
            f"[{priority.value}] {code}: {message}",
        )

        return alert

    def raise_p1(
        self,
        code: str,
        message: str,
        metadata: Optional[Dict] = None,
    ) -> Alert:
        """
        Raise P1 (critical) alert.

        Args:
            code: Alert code
            message: Alert message
            metadata: Optional metadata

        Returns:
            Alert
        """
        return self.raise_alert(AlertPriority.P1, code, message, metadata)

    def raise_p2(
        self,
        code: str,
        message: str,
        metadata: Optional[Dict] = None,
    ) -> Alert:
        """
        Raise P2 (warning) alert.

        Args:
            code: Alert code
            message: Alert message
            metadata: Optional metadata

        Returns:
            Alert
        """
        return self.raise_alert(AlertPriority.P2, code, message, metadata)

    def get_recent_alerts(
        self,
        hours: int = 24,
        priority_filter: Optional[AlertPriority] = None,
    ) -> List[Alert]:
        """
        Get recent alerts.

        Args:
            hours: Hours to look back
            priority_filter: Optional priority filter

        Returns:
            List of alerts
        """
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)
        alerts = [a for a in self._alerts if a.timestamp.timestamp() >= cutoff]

        if priority_filter:
            alerts = [a for a in alerts if a.priority == priority_filter]

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)

        return alerts

    def get_by_priority(self) -> Dict[str, int]:
        """
        Get alert count by priority.

        Returns:
            Dict mapping priority to count
        """
        counts = {p.value: 0 for p in AlertPriority}

        for alert in self._alerts:
            counts[alert.priority.value] += 1

        return counts
