"""
Risk Layer Alerting System
===========================

Multi-channel notification system for risk events with routing and failover.

Features:
- Multiple notification channels (console/file/email/slack/telegram/webhook)
- Severity-based routing matrix
- Failover to backup channels on failure
- Async dispatch support
- Safe defaults (external channels disabled by default)

Example Usage:
    >>> from src.risk_layer.alerting import (
    ...     AlertDispatcher, AlertEvent, AlertSeverity,
    ...     ConsoleChannel, FileChannel, SlackChannel
    ... )
    >>> 
    >>> # Create channels
    >>> channels = [
    ...     ConsoleChannel(),
    ...     FileChannel("/var/log/alerts.jsonl"),
    ...     SlackChannel(webhook_url="https://hooks.slack.com/...")
    ... ]
    >>> 
    >>> # Create dispatcher
    >>> dispatcher = AlertDispatcher(channels)
    >>> 
    >>> # Dispatch alert
    >>> alert = AlertEvent(
    ...     source="risk_gate",
    ...     severity=AlertSeverity.CRITICAL,
    ...     title="Position Limit Exceeded",
    ...     body="Portfolio exposure exceeds configured limit"
    ... )
    >>> results = dispatcher.dispatch(alert)
"""

from .channels import (
    ConsoleChannel,
    EmailChannel,
    FileChannel,
    NotificationChannel,
    SlackChannel,
    TelegramChannel,
    WebhookChannel,
)
from .dispatcher import AlertDispatcher
from .models import AlertEvent, AlertSeverity

__all__ = [
    # Models
    "AlertEvent",
    "AlertSeverity",
    # Dispatcher
    "AlertDispatcher",
    # Channels
    "NotificationChannel",
    "ConsoleChannel",
    "FileChannel",
    "EmailChannel",
    "SlackChannel",
    "TelegramChannel",
    "WebhookChannel",
]
