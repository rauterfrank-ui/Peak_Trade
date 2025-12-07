# src/live/alert_manager.py
"""
Peak_Trade: Alert Manager v1 (Phase 66)
========================================

Zentrale Verwaltung von Alerts mit Notifier-Integration.

Nutzt das bestehende Alert-System (AlertEvent, AlertSink) und erweitert es
um einen AlertManager für einfachere Nutzung.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

from .alerts import (
    AlertEvent,
    AlertLevel,
    AlertSink,
    LoggingAlertSink,
    StderrAlertSink,
    MultiAlertSink,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Alert Manager
# =============================================================================


class AlertManager:
    """
    Zentrale Verwaltung von Alerts.

    Features:
    - Einfache Alert-Erstellung (info, warning, critical)
    - Multi-Notifier-Support
    - Robuste Fehlerbehandlung (ein Notifier-Fehler crasht nicht die anderen)

    Usage:
        >>> manager = AlertManager(notifiers=[LoggingAlertSink(...), ConsoleAlertNotifier(...)])
        >>> manager.warning(
        ...     source="monitoring",
        ...     code="PNL_DROP",
        ...     message="PnL dropped by 5%",
        ...     run_id="shadow_20251207_...",
        ...     details={"drop_pct": 5.0}
        ... )
    """

    def __init__(self, notifiers: Sequence[AlertSink]) -> None:
        """
        Initialisiert AlertManager.

        Args:
            notifiers: Liste von Alert-Sinks (Notifier)
        """
        self._notifiers = list(notifiers)
        self._sink = MultiAlertSink(self._notifiers) if len(self._notifiers) > 1 else (self._notifiers[0] if self._notifiers else None)

    def raise_alert(
        self,
        level: AlertLevel,
        source: str,
        code: str,
        message: str,
        run_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Erstellt und sendet einen Alert.

        Args:
            level: Alert-Level (INFO, WARNING, CRITICAL)
            source: Quelle des Alerts (z.B. "monitoring", "risk", "exchange")
            code: Maschinenlesbarer Code (z.B. "PNL_DROP", "NO_EVENTS")
            message: Menschenlesbare Nachricht
            run_id: Optional Run-ID
            details: Zusätzliche Details
        """
        if not self._sink:
            logger.debug("No alert sink configured, skipping alert")
            return

        # Context aufbauen
        context: Dict[str, Any] = {}
        if run_id:
            context["run_id"] = run_id
        if details:
            context.update(details)

        # Alert-Event erstellen
        alert = AlertEvent(
            ts=datetime.now(timezone.utc),
            level=level,
            source=source,
            code=code,
            message=message,
            context=context,
        )

        # Alert senden
        try:
            self._sink.send(alert)
        except Exception as e:
            # Robust: Fehler in Notifier crasht nicht den AlertManager
            logger.error(f"Fehler beim Senden des Alerts: {e}", exc_info=True)

    def info(
        self,
        source: str,
        code: str,
        message: str,
        run_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Erstellt einen INFO-Alert."""
        self.raise_alert(
            level=AlertLevel.INFO,
            source=source,
            code=code,
            message=message,
            run_id=run_id,
            details=details,
        )

    def warning(
        self,
        source: str,
        code: str,
        message: str,
        run_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Erstellt einen WARNING-Alert."""
        self.raise_alert(
            level=AlertLevel.WARNING,
            source=source,
            code=code,
            message=message,
            run_id=run_id,
            details=details,
        )

    def critical(
        self,
        source: str,
        code: str,
        message: str,
        run_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Erstellt einen CRITICAL-Alert."""
        self.raise_alert(
            level=AlertLevel.CRITICAL,
            source=source,
            code=code,
            message=message,
            run_id=run_id,
            details=details,
        )


# =============================================================================
# Stub Notifiers (für zukünftige Integration)
# =============================================================================


class ConsoleAlertNotifier:
    """
    Console-Notifier für lesbare Ausgabe auf stdout.

    Nutzt StderrAlertSink intern und implementiert AlertSink Protocol.
    """

    def __init__(self, min_level: AlertLevel = AlertLevel.WARNING) -> None:
        """
        Initialisiert ConsoleAlertNotifier.

        Args:
            min_level: Minimaler Alert-Level
        """
        self._sink = StderrAlertSink(min_level=min_level)

    def send(self, alert: AlertEvent) -> None:
        """
        Sendet Alert auf Console (AlertSink Protocol).

        Args:
            alert: Alert-Event
        """
        self._sink.send(alert)


class EmailAlertNotifier:
    """
    E-Mail-Notifier (Stub für Phase 66).

    Interface ist vorbereitet für echte SMTP-Integration in späteren Phasen.

    Attributes:
        smtp_host: SMTP-Host
        smtp_port: SMTP-Port
        from_addr: Absender-Adresse
        to_addrs: Liste von Empfänger-Adressen
        use_tls: Ob TLS verwendet werden soll
    """

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        from_addr: str = "",
        to_addrs: Sequence[str] = (),
        use_tls: bool = True,
    ) -> None:
        """
        Initialisiert EmailAlertNotifier (Stub).

        Args:
            smtp_host: SMTP-Host
            smtp_port: SMTP-Port
            from_addr: Absender-Adresse
            to_addrs: Liste von Empfänger-Adressen
            use_tls: Ob TLS verwendet werden soll
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_addr = from_addr
        self.to_addrs = list(to_addrs)
        self.use_tls = use_tls

    def send(self, alert: AlertEvent) -> None:
        """
        Sendet Alert per E-Mail (Stub, AlertSink Protocol).

        Args:
            alert: Alert-Event

        NOTE: In Phase 66 ist dies ein Stub. Echte SMTP-Integration folgt in späteren Phasen.
        """
        logger.info(
            f"[EMAIL-STUB] Would send alert to {self.to_addrs}: "
            f"[{alert.level.name}] {alert.source} - {alert.code}: {alert.message}"
        )


class TelegramAlertNotifier:
    """
    Telegram-Notifier (Stub für Phase 66).

    Interface ist vorbereitet für echte Telegram-Bot-Integration in späteren Phasen.

    Attributes:
        bot_token: Telegram-Bot-Token
        chat_id: Telegram-Chat-ID
    """

    def __init__(self, bot_token: str = "", chat_id: str = "") -> None:
        """
        Initialisiert TelegramAlertNotifier (Stub).

        Args:
            bot_token: Telegram-Bot-Token
            chat_id: Telegram-Chat-ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, alert: AlertEvent) -> None:
        """
        Sendet Alert per Telegram (Stub, AlertSink Protocol).

        Args:
            alert: Alert-Event

        NOTE: In Phase 66 ist dies ein Stub. Echte Telegram-API-Integration folgt in späteren Phasen.
        """
        logger.info(
            f"[TELEGRAM-STUB] Would send alert to chat {self.chat_id}: "
            f"[{alert.level.name}] {alert.source} - {alert.code}: {alert.message}"
        )

