"""
Alert Sink Base - Phase 16I

Base protocol for alert sinks (routing adapters).
"""

from typing import Protocol

from ..models import AlertEvent


class AlertSink(Protocol):
    """
    Alert sink protocol for routing alerts.
    
    Implementations:
    - ConsoleAlertSink: Print to stdout
    - WebhookAlertSink: POST to webhook URL
    - ... (future: SlackSink, PagerDutySink, etc.)
    """
    
    def send(self, alert: AlertEvent) -> bool:
        """
        Send alert to sink.
        
        Args:
            alert: Alert event to send
        
        Returns:
            True if send succeeded, False otherwise
        """
        ...
