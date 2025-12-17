"""
Alert System

Konfigurierbare Alerts für kritische System-Ereignisse.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AlertLevel(str, Enum):
    """Alert-Level"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert-Nachricht"""
    level: AlertLevel
    message: str
    timestamp: datetime
    source: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary"""
        return {
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "details": self.details or {},
        }


@dataclass
class AlertThreshold:
    """Alert-Schwellwert-Konfiguration"""
    metric_name: str
    threshold: float
    level: AlertLevel
    comparison: str = ">"  # ">", "<", ">=", "<=", "==", "!="
    message_template: str = "{metric_name} {comparison} {threshold}: {value}"


class AlertManager:
    """
    Alert-Manager für System-Monitoring.
    
    Beispiel:
        manager = AlertManager()
        
        # Alert-Threshold konfigurieren
        manager.add_threshold(AlertThreshold(
            metric_name="error_rate",
            threshold=0.05,
            level=AlertLevel.WARNING,
            comparison=">",
        ))
        
        # Prüfe Metrik
        manager.check_metric("error_rate", 0.08)
    """

    def __init__(self):
        self.thresholds: List[AlertThreshold] = []
        self.alerts: List[Alert] = []
        self.handlers: List[Callable[[Alert], None]] = []

    def add_threshold(self, threshold: AlertThreshold):
        """Füge Alert-Threshold hinzu"""
        self.thresholds.append(threshold)

    def add_handler(self, handler: Callable[[Alert], None]):
        """Füge Alert-Handler hinzu"""
        self.handlers.append(handler)

    def check_metric(self, metric_name: str, value: float) -> List[Alert]:
        """
        Prüfe Metrik gegen Thresholds.
        
        Args:
            metric_name: Name der Metrik
            value: Aktueller Wert
            
        Returns:
            Liste von ausgelösten Alerts
        """
        triggered_alerts = []
        
        for threshold in self.thresholds:
            if threshold.metric_name != metric_name:
                continue
            
            # Prüfe Threshold
            triggered = False
            if threshold.comparison == ">":
                triggered = value > threshold.threshold
            elif threshold.comparison == "<":
                triggered = value < threshold.threshold
            elif threshold.comparison == ">=":
                triggered = value >= threshold.threshold
            elif threshold.comparison == "<=":
                triggered = value <= threshold.threshold
            elif threshold.comparison == "==":
                triggered = value == threshold.threshold
            elif threshold.comparison == "!=":
                triggered = value != threshold.threshold
            
            if triggered:
                alert = Alert(
                    level=threshold.level,
                    message=threshold.message_template.format(
                        metric_name=metric_name,
                        comparison=threshold.comparison,
                        threshold=threshold.threshold,
                        value=value,
                    ),
                    timestamp=datetime.now(),
                    source="alert_manager",
                    details={
                        "metric_name": metric_name,
                        "value": value,
                        "threshold": threshold.threshold,
                        "comparison": threshold.comparison,
                    },
                )
                triggered_alerts.append(alert)
                self._trigger_alert(alert)
        
        return triggered_alerts

    def _trigger_alert(self, alert: Alert):
        """Löse Alert aus (rufe Handler auf)"""
        self.alerts.append(alert)
        
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception:
                # Handler-Fehler nicht durchreichen
                pass

    def get_recent_alerts(self, count: int = 10) -> List[Alert]:
        """Hole letzte N Alerts"""
        return self.alerts[-count:]

    def clear_alerts(self):
        """Lösche alle Alerts"""
        self.alerts.clear()


# Global Alert Manager
_global_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Hole globalen Alert Manager"""
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = AlertManager()
    return _global_alert_manager
