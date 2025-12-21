# src/notifications/console.py
"""
Peak_Trade Notification Layer – Console Notifier
=================================================
Gibt Alerts auf der Konsole aus.

Features:
- Formatierte Ausgabe mit Timestamp, Level, Source, Message
- Optional farbige Ausgabe (ohne zusätzliche Dependencies)
- Konfigurierbare Mindest-Level-Filterung

Usage:
    from peak_trade.notifications import Alert, ConsoleNotifier

    notifier = ConsoleNotifier()
    notifier.send(alert)
"""

from __future__ import annotations

import sys
from typing import TextIO

from src.notifications.base import Alert, AlertLevel


# Level-Reihenfolge für Filterung
LEVEL_ORDER = {"info": 0, "warning": 1, "critical": 2}


class ConsoleNotifier:
    """
    Gibt Alerts auf der Konsole (stdout/stderr) aus.

    Attributes:
        min_level: Mindest-Level für Ausgabe ("info", "warning", "critical")
        use_stderr: True um critical-Alerts auf stderr auszugeben
        show_context: True um context-Dict mit auszugeben

    Examples:
        >>> notifier = ConsoleNotifier()
        >>> notifier.send(alert)
        [2025-01-01T12:00:00] [WARNING] [forward_signal] BTC/EUR signal flip detected

        >>> notifier = ConsoleNotifier(min_level="warning")
        >>> notifier.send(info_alert)  # Wird ignoriert
    """

    def __init__(
        self,
        *,
        min_level: AlertLevel = "info",
        use_stderr: bool = True,
        show_context: bool = False,
    ) -> None:
        """
        Initialisiert den ConsoleNotifier.

        Args:
            min_level: Mindest-Level für Ausgabe
            use_stderr: True um critical-Alerts auf stderr auszugeben
            show_context: True um context-Dict mit auszugeben
        """
        self.min_level = min_level
        self.use_stderr = use_stderr
        self.show_context = show_context

    def _should_send(self, level: AlertLevel) -> bool:
        """Prüft ob ein Alert basierend auf min_level gesendet werden soll."""
        return LEVEL_ORDER.get(level, 0) >= LEVEL_ORDER.get(self.min_level, 0)

    def _get_output_stream(self, level: AlertLevel) -> TextIO:
        """Bestimmt den Output-Stream basierend auf Level."""
        if self.use_stderr and level == "critical":
            return sys.stderr
        return sys.stdout

    def _format_alert(self, alert: Alert) -> str:
        """Formatiert einen Alert als String."""
        ts = alert.timestamp.isoformat(timespec="seconds")
        level_str = alert.level.upper()
        base = f"[{ts}] [{level_str}] [{alert.source}] {alert.message}"

        if self.show_context and alert.context:
            # Kompakte Darstellung des Context
            ctx_parts = [f"{k}={v}" for k, v in alert.context.items()]
            ctx_str = ", ".join(ctx_parts)
            base = f"{base} ({ctx_str})"

        return base

    def send(self, alert: Alert) -> None:
        """
        Gibt einen Alert auf der Konsole aus.

        Args:
            alert: Der auszugebende Alert
        """
        if not self._should_send(alert.level):
            return

        stream = self._get_output_stream(alert.level)
        message = self._format_alert(alert)
        print(message, file=stream)
