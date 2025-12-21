# src/notifications/combined.py
"""
Peak_Trade Notification Layer – Combined Notifier
==================================================
Kombiniert mehrere Notifier für parallelen Alert-Versand.

Usage:
    from pathlib import Path
    from peak_trade.notifications import (
        Alert, ConsoleNotifier, FileNotifier, CombinedNotifier
    )

    notifier = CombinedNotifier([
        ConsoleNotifier(),
        FileNotifier(Path("logs/alerts.log")),
    ])
    notifier.send(alert)  # Sendet an Console und File
"""

from __future__ import annotations

from typing import Sequence

from src.notifications.base import Alert, Notifier


class CombinedNotifier:
    """
    Kombiniert mehrere Notifier für parallelen Alert-Versand.

    Wenn ein Notifier einen Fehler wirft, wird dieser geloggt aber nicht
    weitergereicht, damit andere Notifier weiterhin funktionieren.

    Attributes:
        notifiers: Liste der zu verwendenden Notifier

    Examples:
        >>> console = ConsoleNotifier()
        >>> file = FileNotifier(Path("logs/alerts.log"))
        >>> combined = CombinedNotifier([console, file])
        >>> combined.send(alert)
    """

    def __init__(self, notifiers: Sequence[Notifier]) -> None:
        """
        Initialisiert den CombinedNotifier.

        Args:
            notifiers: Liste von Notifier-Instanzen
        """
        self._notifiers = list(notifiers)

    @property
    def notifiers(self) -> list[Notifier]:
        """Liste der konfigurierten Notifier."""
        return self._notifiers.copy()

    def add(self, notifier: Notifier) -> None:
        """
        Fügt einen Notifier hinzu.

        Args:
            notifier: Notifier-Instanz zum Hinzufügen
        """
        self._notifiers.append(notifier)

    def send(self, alert: Alert) -> None:
        """
        Sendet einen Alert an alle konfigurierten Notifier.

        Fehler einzelner Notifier werden gefangen und auf stderr ausgegeben,
        damit andere Notifier weiterhin funktionieren.

        Args:
            alert: Der zu sendende Alert
        """
        for notifier in self._notifiers:
            try:
                notifier.send(alert)
            except Exception as e:
                # Fehler loggen aber nicht weitergeben
                import sys

                print(
                    f"[NOTIFIER ERROR] {type(notifier).__name__}: {e}",
                    file=sys.stderr,
                )
