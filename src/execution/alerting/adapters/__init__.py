"""
Alert Adapters - Phase 16I

Routing adapters for alert delivery.
"""

from .base import AlertSink
from .console import ConsoleAlertSink
from .webhook import WebhookAlertSink

__all__ = [
    "AlertSink",
    "ConsoleAlertSink",
    "WebhookAlertSink",
]
