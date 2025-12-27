"""
Alert Types for Risk-Layer Production Alerting
===============================================

Defines core enums and constants for the alerting system.
"""

from enum import Enum


class AlertSeverity(str, Enum):
    """
    Severity levels for alerts.

    Higher severity indicates more critical issues requiring urgent attention.
    """
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    def __lt__(self, other: "AlertSeverity") -> bool:
        """Enable comparison for filtering."""
        if not isinstance(other, AlertSeverity):
            return NotImplemented
        severity_order = {
            AlertSeverity.DEBUG: 0,
            AlertSeverity.INFO: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.ERROR: 3,
            AlertSeverity.CRITICAL: 4,
        }
        return severity_order[self] < severity_order[other]

    def __le__(self, other: "AlertSeverity") -> bool:
        """Enable comparison for filtering."""
        return self == other or self < other

    def __gt__(self, other: "AlertSeverity") -> bool:
        """Enable comparison for filtering."""
        if not isinstance(other, AlertSeverity):
            return NotImplemented
        return not self <= other

    def __ge__(self, other: "AlertSeverity") -> bool:
        """Enable comparison for filtering."""
        return self == other or self > other


class AlertCategory(str, Enum):
    """
    Categories for grouping and routing alerts.

    Categories help organize alerts by functional domain
    and enable targeted routing to appropriate channels.
    """
    RISK_LIMIT = "risk_limit"
    POSITION_VIOLATION = "position_violation"
    EXECUTION_ERROR = "execution_error"
    DATA_QUALITY = "data_quality"
    SYSTEM_HEALTH = "system_health"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    OTHER = "other"
