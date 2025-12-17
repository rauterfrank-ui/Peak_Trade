# src/notifications/__init__.py
"""
Peak_Trade Notification Layer
=============================
Leichtgewichtiges Alerting-System für Forward-Signals, Risk-Events und Analytics.

Komponenten:
- Alert: Datenstruktur für Alerts mit Level, Source, Message, Context
- Notifier Protocol: Interface für Alert-Versand
- ConsoleNotifier: Ausgabe auf der CLI
- FileNotifier: Schreibt Alerts in Logdatei
- CombinedNotifier: Kombiniert mehrere Notifier

Usage:
    from peak_trade.notifications import Alert, ConsoleNotifier, FileNotifier

    notifier = ConsoleNotifier()
    alert = Alert(
        level="warning",
        source="forward_signal",
        message="BTC/EUR signal flip: LONG -> SHORT",
        timestamp=datetime.utcnow(),
        context={"symbol": "BTC/EUR", "strategy": "ma_crossover"},
    )
    notifier.send(alert)
"""
from __future__ import annotations

from src.notifications.base import Alert, AlertLevel, Notifier
from src.notifications.combined import CombinedNotifier
from src.notifications.console import ConsoleNotifier
from src.notifications.file import FileNotifier
from src.notifications.slack import SlackNotifier, send_test_health_slack_notification

__all__ = [
    "Alert",
    "AlertLevel",
    "CombinedNotifier",
    "ConsoleNotifier",
    "FileNotifier",
    "Notifier",
    "SlackNotifier",
    "send_test_health_slack_notification",
]
