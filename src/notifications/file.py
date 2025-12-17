# src/notifications/file.py
"""
Peak_Trade Notification Layer – File Notifier
==============================================
Schreibt Alerts in eine Logdatei.

Features:
- Append-Modus (fügt Alerts an bestehende Datei an)
- Automatisches Erstellen von Parent-Verzeichnissen
- Tab-separiertes Format für einfache Verarbeitung
- Optional JSON-Format für strukturierte Logs

Usage:
    from pathlib import Path
    from peak_trade.notifications import Alert, FileNotifier

    notifier = FileNotifier(Path("logs/alerts.log"))
    notifier.send(alert)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from src.notifications.base import Alert, AlertLevel

# Level-Reihenfolge für Filterung
LEVEL_ORDER = {"info": 0, "warning": 1, "critical": 2}


class FileNotifier:
    """
    Schreibt Alerts in eine Logdatei.

    Das Default-Format ist Tab-separiert (TSV):
        timestamp    level    source    message

    Optional kann JSON-Format verwendet werden für strukturierte Logs.

    Attributes:
        path: Pfad zur Logdatei
        min_level: Mindest-Level für Logging
        format: "tsv" oder "json"

    Examples:
        >>> notifier = FileNotifier(Path("logs/alerts.log"))
        >>> notifier.send(alert)
        # Schreibt: 2025-01-01T12:00:00    warning    forward_signal    BTC/EUR signal flip

        >>> notifier = FileNotifier(Path("logs/alerts.jsonl"), format="json")
        >>> notifier.send(alert)
        # Schreibt: {"timestamp": "2025-01-01T12:00:00", "level": "warning", ...}
    """

    def __init__(
        self,
        path: Path | str,
        *,
        min_level: AlertLevel = "info",
        format: Literal["tsv", "json"] = "tsv",
    ) -> None:
        """
        Initialisiert den FileNotifier.

        Args:
            path: Pfad zur Logdatei
            min_level: Mindest-Level für Logging
            format: Ausgabeformat ("tsv" oder "json")
        """
        self._path = Path(path)
        self.min_level = min_level
        self.format = format

    @property
    def path(self) -> Path:
        """Pfad zur Logdatei."""
        return self._path

    def _should_send(self, level: AlertLevel) -> bool:
        """Prüft ob ein Alert basierend auf min_level geloggt werden soll."""
        return LEVEL_ORDER.get(level, 0) >= LEVEL_ORDER.get(self.min_level, 0)

    def _format_tsv(self, alert: Alert) -> str:
        """Formatiert Alert als Tab-separierte Zeile."""
        ts = alert.timestamp.isoformat(timespec="seconds")
        # Newlines und Tabs in Message escapen
        message = alert.message.replace("\n", "\\n").replace("\t", "\\t")
        return f"{ts}\t{alert.level}\t{alert.source}\t{message}"

    def _format_json(self, alert: Alert) -> str:
        """Formatiert Alert als JSON-Zeile (JSONL)."""
        data = {
            "timestamp": alert.timestamp.isoformat(timespec="seconds"),
            "level": alert.level,
            "source": alert.source,
            "message": alert.message,
            "context": alert.context,
        }
        return json.dumps(data, ensure_ascii=False)

    def send(self, alert: Alert) -> None:
        """
        Schreibt einen Alert in die Logdatei.

        Args:
            alert: Der zu loggende Alert
        """
        if not self._should_send(alert.level):
            return

        # Parent-Verzeichnis erstellen falls nötig
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Formatierung
        if self.format == "json":
            line = self._format_json(alert)
        else:
            line = self._format_tsv(alert)

        # Anhängen an Datei
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
