# src/notifications/base.py
"""
Peak_Trade Notification Layer – Base Types
==========================================
Definiert die grundlegenden Datenstrukturen für das Alerting-System.

Alert:
    Datenstruktur für einen einzelnen Alert mit:
    - level: info | warning | critical
    - source: Ursprung des Alerts (z.B. "forward_signal", "live_risk", "analytics")
    - message: Menschenlesbare Nachricht
    - timestamp: Zeitpunkt des Alerts
    - context: Zusätzliche strukturierte Daten

Notifier:
    Protocol/Interface für Alert-Versand.
    Implementierungen: ConsoleNotifier, FileNotifier, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Literal, Protocol, runtime_checkable


# Alert-Level als Literal-Type für Typ-Sicherheit
AlertLevel = Literal["info", "warning", "critical"]


@dataclass
class Alert:
    """
    Ein einzelner Alert aus dem Peak_Trade System.

    Attributes:
        level: Schweregrad des Alerts ("info", "warning", "critical")
        source: Ursprung des Alerts (z.B. "forward_signal", "live_risk", "analytics")
        message: Menschenlesbare Nachricht
        timestamp: Zeitpunkt des Alerts (UTC empfohlen)
        context: Zusätzliche strukturierte Daten (z.B. symbol, strategy_key, metrics)

    Examples:
        >>> from datetime import datetime
        >>> alert = Alert(
        ...     level="warning",
        ...     source="forward_signal",
        ...     message="Signal flip detected: LONG -> SHORT",
        ...     timestamp=datetime.utcnow(),
        ...     context={"symbol": "BTC/EUR", "strategy_key": "ma_crossover"},
        ... )
    """

    level: AlertLevel
    source: str
    message: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validiert Alert-Daten nach Initialisierung."""
        valid_levels = ("info", "warning", "critical")
        if self.level not in valid_levels:
            raise ValueError(f"Invalid alert level: {self.level}. Must be one of {valid_levels}")
        if not self.source:
            raise ValueError("Alert source cannot be empty")
        if not self.message:
            raise ValueError("Alert message cannot be empty")


@runtime_checkable
class Notifier(Protocol):
    """
    Protocol für Alert-Versand.

    Alle Notifier-Implementierungen müssen eine send()-Methode bereitstellen.
    Dies ermöglicht einfache Erweiterbarkeit für E-Mail, Telegram, Webhook, etc.

    Examples:
        >>> class MyNotifier:
        ...     def send(self, alert: Alert) -> None:
        ...         # Custom implementation
        ...         pass
    """

    def send(self, alert: Alert) -> None:
        """
        Versendet einen Alert.

        Args:
            alert: Der zu versendende Alert
        """
        ...


# =============================================================================
# HELPER FUNKTIONEN
# =============================================================================


def create_alert(
    *,
    level: AlertLevel,
    source: str,
    message: str,
    context: Dict[str, Any] | None = None,
) -> Alert:
    """
    Convenience-Funktion zum Erstellen eines Alerts mit aktuellem Timestamp.

    Args:
        level: Schweregrad ("info", "warning", "critical")
        source: Ursprung des Alerts
        message: Menschenlesbare Nachricht
        context: Optionale zusätzliche Daten

    Returns:
        Alert-Objekt mit aktuellem UTC-Timestamp

    Examples:
        >>> alert = create_alert(
        ...     level="critical",
        ...     source="live_risk",
        ...     message="Daily loss limit exceeded",
        ...     context={"loss_pct": -5.2, "limit_pct": -3.0},
        ... )
    """
    return Alert(
        level=level,
        source=source,
        message=message,
        timestamp=datetime.utcnow(),
        context=context or {},
    )


def signal_level_from_value(signal: float) -> AlertLevel:
    """
    Bestimmt das Alert-Level basierend auf dem Signalwert.

    Args:
        signal: Signalwert (-1, 0, +1 oder kontinuierlich)

    Returns:
        "warning" für starke Signale (abs >= 1), sonst "info"

    Examples:
        >>> signal_level_from_value(1.0)
        'warning'
        >>> signal_level_from_value(0.5)
        'info'
        >>> signal_level_from_value(-1.0)
        'warning'
    """
    if abs(signal) >= 1.0:
        return "warning"
    return "info"
