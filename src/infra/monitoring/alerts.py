"""
Alert System
=============

Manages alerts for critical system events and conditions.

Usage:
    from src.infra.monitoring import AlertManager, AlertSeverity
    
    alerts = AlertManager()
    alerts.raise_alert(
        name="high_error_rate",
        severity=AlertSeverity.WARNING,
        message="Error rate above threshold",
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    """Represents an alert."""
    
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class AlertManager:
    """
    Manages system alerts.
    
    Tracks active alerts, alert history, and provides alerting functionality.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize alert manager.
        
        Args:
            max_history: Maximum number of alerts to keep in history
        """
        self.max_history = max_history
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._lock = Lock()
    
    def raise_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
    ) -> Alert:
        """
        Raise a new alert.
        
        Args:
            name: Unique name for this alert
            severity: Alert severity
            message: Alert message
            
        Returns:
            Created Alert instance
        """
        with self._lock:
            alert = Alert(
                name=name,
                severity=severity,
                message=message,
                timestamp=datetime.now(),
            )
            
            # Check if alert already active
            if name in self._active_alerts:
                existing = self._active_alerts[name]
                logger.info(
                    f"Alert '{name}' already active since "
                    f"{existing.timestamp.isoformat()}"
                )
                return existing
            
            # Add to active alerts
            self._active_alerts[name] = alert
            
            # Add to history
            self._alert_history.append(alert)
            
            # Trim history if needed
            if len(self._alert_history) > self.max_history:
                self._alert_history = self._alert_history[-self.max_history :]
            
            # Log alert
            log_level = {
                AlertSeverity.INFO: logging.INFO,
                AlertSeverity.WARNING: logging.WARNING,
                AlertSeverity.ERROR: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL,
            }[severity]
            
            logger.log(
                log_level,
                f"Alert raised: [{severity.value}] {name}: {message}",
            )
            
            return alert
    
    def resolve_alert(self, name: str) -> bool:
        """
        Resolve an active alert.
        
        Args:
            name: Name of the alert to resolve
            
        Returns:
            True if alert was resolved, False if not found
        """
        with self._lock:
            if name not in self._active_alerts:
                logger.warning(f"Cannot resolve alert '{name}': not found")
                return False
            
            alert = self._active_alerts[name]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            # Remove from active alerts
            del self._active_alerts[name]
            
            logger.info(f"Alert resolved: {name}")
            
            return True
    
    def get_active_alerts(self) -> List[Alert]:
        """
        Get all active alerts.
        
        Returns:
            List of active alerts
        """
        with self._lock:
            return list(self._active_alerts.values())
    
    def get_alert_history(
        self,
        limit: Optional[int] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> List[Alert]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity
            
        Returns:
            List of alerts from history
        """
        with self._lock:
            alerts = self._alert_history.copy()
            
            # Filter by severity if specified
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            # Apply limit
            if limit:
                alerts = alerts[-limit:]
            
            return alerts
    
    def clear_all_alerts(self) -> int:
        """
        Clear all active alerts.
        
        Returns:
            Number of alerts cleared
        """
        with self._lock:
            count = len(self._active_alerts)
            
            # Mark all as resolved
            for alert in self._active_alerts.values():
                alert.resolved = True
                alert.resolved_at = datetime.now()
            
            self._active_alerts.clear()
            
            logger.info(f"Cleared {count} active alerts")
            
            return count
    
    def get_summary(self) -> Dict:
        """
        Get alert summary.
        
        Returns:
            Dictionary with alert summary
        """
        with self._lock:
            active = list(self._active_alerts.values())
            
            severity_counts = {
                AlertSeverity.INFO: 0,
                AlertSeverity.WARNING: 0,
                AlertSeverity.ERROR: 0,
                AlertSeverity.CRITICAL: 0,
            }
            
            for alert in active:
                severity_counts[alert.severity] += 1
            
            return {
                "total_active": len(active),
                "by_severity": {
                    s.value: count for s, count in severity_counts.items()
                },
                "total_history": len(self._alert_history),
                "active_alerts": [a.to_dict() for a in active],
            }


# Global alert manager
_global_alerts = AlertManager()


def get_global_alert_manager() -> AlertManager:
    """
    Get the global alert manager.
    
    Returns:
        Global AlertManager instance
    """
    return _global_alerts
