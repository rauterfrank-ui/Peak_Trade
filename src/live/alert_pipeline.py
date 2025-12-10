# src/live/alert_pipeline.py
"""
Peak_Trade: Alert-Pipeline (Phase 82)
======================================

Robuste, konfigurierbare Alert-Pipeline für Live-/Shadow-/Testnet-Trading.
Sendet kritische Ereignisse automatisch an menschliche Operatoren.

Features:
- AlertSeverity (INFO, WARN, CRITICAL)
- AlertCategory (RISK, EXECUTION, SYSTEM)
- AlertMessage mit strukturierten Daten
- AlertChannel Interface mit SlackAlertChannel und EmailAlertChannel
- AlertPipelineManager für Multi-Channel-Routing
- Factory-Funktion für Config-basierte Erstellung
- Severity-Transition-Tracking für Risk-Status-Änderungen

Usage:
    from src.live.alert_pipeline import (
        AlertSeverity,
        AlertCategory,
        AlertMessage,
        AlertPipelineManager,
        build_alert_pipeline_from_config,
    )

    # Aus Config erstellen
    manager = build_alert_pipeline_from_config(config)

    # Alert senden
    alert = AlertMessage(
        title="Risk Severity changed: GREEN → YELLOW",
        body="Daily loss approaching limit (85%)",
        severity=AlertSeverity.WARN,
        category=AlertCategory.RISK,
        source="live_risk_severity",
    )
    manager.send(alert)
"""
from __future__ import annotations

import json
import logging
import os
import smtplib
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import IntEnum, Enum
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from src.infra.runbooks import RunbookLink
    from src.infra.escalation import EscalationManager

logger = logging.getLogger(__name__)


# =============================================================================
# ALERT SEVERITY
# =============================================================================


class AlertSeverity(IntEnum):
    """
    Alert-Severity für Klassifizierung der Dringlichkeit.

    Mapping von Risk-Konzepten:
    - GREEN → kein Alert (oder INFO für Recovery)
    - YELLOW → WARN
    - RED → CRITICAL
    - Hard Limit Breach → CRITICAL

    Vergleich: CRITICAL > WARN > INFO
    """

    INFO = 10
    WARN = 20
    CRITICAL = 30

    @classmethod
    def from_risk_status(cls, status: str) -> "AlertSeverity":
        """
        Konvertiert Risk-Status zu AlertSeverity.

        Args:
            status: "green", "yellow" oder "red"

        Returns:
            Entsprechende AlertSeverity
        """
        mapping = {
            "green": cls.INFO,
            "yellow": cls.WARN,
            "red": cls.CRITICAL,
        }
        return mapping.get(status.lower(), cls.INFO)

    @classmethod
    def from_string(cls, value: str) -> "AlertSeverity":
        """
        Parst String zu AlertSeverity.

        Args:
            value: "info", "warn", "warning" oder "critical"

        Returns:
            AlertSeverity
        """
        value_lower = value.lower().strip()
        if value_lower == "info":
            return cls.INFO
        elif value_lower in ("warn", "warning"):
            return cls.WARN
        elif value_lower == "critical":
            return cls.CRITICAL
        else:
            logger.warning(f"Unknown alert severity '{value}', defaulting to WARN")
            return cls.WARN


# =============================================================================
# ALERT CATEGORY
# =============================================================================


class AlertCategory(str, Enum):
    """
    Kategorie des Alerts für Filterung und Routing.

    - RISK: Risk-Management-Events (Severity-Changes, Limit-Breaches)
    - EXECUTION: Execution-Pipeline-Events (Order-Fehler, Fill-Probleme)
    - SYSTEM: System-Health-Events (Heartbeat-Fails, API-Fehler)
    """

    RISK = "RISK"
    EXECUTION = "EXECUTION"
    SYSTEM = "SYSTEM"

    @classmethod
    def from_string(cls, value: str) -> "AlertCategory":
        """Parst String zu AlertCategory."""
        try:
            return cls(value.upper())
        except ValueError:
            logger.warning(f"Unknown alert category '{value}', defaulting to SYSTEM")
            return cls.SYSTEM


# =============================================================================
# ALERT MESSAGE
# =============================================================================


@dataclass
class AlertMessage:
    """
    Ein strukturierter Alert zur Benachrichtigung menschlicher Operatoren.

    Attributes:
        title: Kurzer Titel des Alerts
        body: Detaillierte Beschreibung mit Kontext
        severity: Dringlichkeitsstufe (INFO, WARN, CRITICAL)
        category: Kategorie (RISK, EXECUTION, SYSTEM)
        source: Quelle des Alerts (z.B. "live_risk_severity", "live_risk_limits")
        session_id: Optional Session-ID für Kontext
        timestamp: Zeitstempel des Events (UTC)
        context: Zusätzliche strukturierte Daten (Metriken, Limits, etc.)
    """

    title: str
    body: str
    severity: AlertSeverity
    category: AlertCategory
    source: str
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert AlertMessage zu Dict für Serialisierung."""
        return {
            "title": self.title,
            "body": self.body,
            "severity": self.severity.name,
            "category": self.category.value,
            "source": self.source,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }


# =============================================================================
# ALERT CHANNEL PROTOCOL
# =============================================================================


class AlertChannel(Protocol):
    """
    Protocol für Alert-Channels.

    Jeder Channel hat:
    - name: Eindeutiger Identifier
    - is_enabled: Ob der Channel aktiv ist
    - min_severity: Minimale Severity für diesen Channel

    Implementierungen müssen send() bereitstellen.
    """

    @property
    def name(self) -> str:
        """Name des Channels."""
        ...

    @property
    def is_enabled(self) -> bool:
        """Ob der Channel aktiviert ist."""
        ...

    @property
    def min_severity(self) -> AlertSeverity:
        """Minimale Severity für diesen Channel."""
        ...

    def send(self, alert: AlertMessage) -> None:
        """
        Sendet einen Alert über diesen Channel.

        Args:
            alert: AlertMessage zum Senden
        """
        ...


# =============================================================================
# SLACK ALERT CHANNEL
# =============================================================================


@dataclass
class SlackChannelConfig:
    """
    Konfiguration für SlackAlertChannel.

    Attributes:
        webhook_url: Slack Incoming Webhook URL
        channel: Optional Channel-Override (z.B. "#peak-trade-alerts")
        username: Bot-Username (z.B. "peak-trade-bot")
        icon_emoji: Emoji für den Bot (z.B. ":rotating_light:")
        min_severity: Minimale Severity für diesen Channel
        enabled: Ob der Channel aktiviert ist
        timeout_seconds: HTTP-Timeout für Requests
    """

    webhook_url: str
    channel: Optional[str] = None
    username: str = "peak-trade-bot"
    icon_emoji: str = ":rotating_light:"
    min_severity: AlertSeverity = AlertSeverity.WARN
    enabled: bool = True
    timeout_seconds: float = 5.0


class SlackAlertChannel:
    """
    Slack-Alert-Channel via Incoming Webhook.

    Features:
    - Strukturierte Slack-Blocks mit Severity-Farben
    - Konfigurierbare Channel/Username/Emoji
    - Robuste Fehlerbehandlung (kein Crash bei Netzwerkfehlern)
    - Severity-basiertes Filtering
    """

    # Severity-Farben für Slack-Attachments
    SEVERITY_COLORS = {
        AlertSeverity.INFO: "#36a64f",  # Grün
        AlertSeverity.WARN: "#ffc107",  # Gelb/Orange
        AlertSeverity.CRITICAL: "#dc3545",  # Rot
    }

    SEVERITY_EMOJIS = {
        AlertSeverity.INFO: "ℹ️",
        AlertSeverity.WARN: "⚠️",
        AlertSeverity.CRITICAL: "🚨",
    }

    def __init__(self, config: SlackChannelConfig) -> None:
        """
        Initialisiert SlackAlertChannel.

        Args:
            config: SlackChannelConfig mit Webhook-URL und Optionen
        """
        self._config = config
        self._logger = logging.getLogger(f"{__name__}.SlackAlertChannel")

    @property
    def name(self) -> str:
        return "slack"

    @property
    def is_enabled(self) -> bool:
        return self._config.enabled and bool(self._config.webhook_url)

    @property
    def min_severity(self) -> AlertSeverity:
        return self._config.min_severity

    def send(self, alert: AlertMessage) -> None:
        """
        Sendet Alert an Slack via Webhook.

        Args:
            alert: AlertMessage zum Senden
        """
        if not self.is_enabled:
            return

        if alert.severity < self.min_severity:
            return

        try:
            payload = self._build_payload(alert)
            self._send_webhook(payload)
            self._logger.debug(f"Slack alert sent: {alert.title}")
        except Exception as e:
            # Fehler loggen, aber nicht nach außen propagieren
            self._logger.error(f"Failed to send Slack alert: {e}", exc_info=True)

    def _build_payload(self, alert: AlertMessage) -> Dict[str, Any]:
        """
        Baut Slack-Webhook-Payload mit Blocks.

        Args:
            alert: AlertMessage

        Returns:
            Dict für JSON-Serialisierung
        """
        emoji = self.SEVERITY_EMOJIS.get(alert.severity, "📢")
        color = self.SEVERITY_COLORS.get(alert.severity, "#808080")

        # Header-Text
        header = f"{emoji} *[{alert.severity.name}]* {alert.title}"

        # Body-Felder
        fields = []

        # Kategorie und Source
        fields.append({
            "title": "Category",
            "value": alert.category.value,
            "short": True,
        })
        fields.append({
            "title": "Source",
            "value": f"`{alert.source}`",
            "short": True,
        })

        # Session-ID falls vorhanden
        if alert.session_id:
            fields.append({
                "title": "Session",
                "value": f"`{alert.session_id}`",
                "short": True,
            })

        # Timestamp
        fields.append({
            "title": "Time (UTC)",
            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "short": True,
        })

        # Context-Daten (kompakt) - ohne runbooks (separat behandelt)
        context_items = {k: v for k, v in alert.context.items() if k != "runbooks"}
        if context_items:
            context_lines = []
            for key, value in list(context_items.items())[:5]:  # Max 5 Einträge
                if isinstance(value, float):
                    context_lines.append(f"• {key}: {value:.2f}")
                else:
                    context_lines.append(f"• {key}: {value}")
            if len(context_items) > 5:
                context_lines.append(f"... +{len(context_items) - 5} more")
            fields.append({
                "title": "Context",
                "value": "\n".join(context_lines),
                "short": False,
            })

        # Phase 84: Runbooks-Sektion
        runbooks = alert.context.get("runbooks", [])
        if runbooks:
            runbook_lines = []
            for rb in runbooks[:3]:  # Max 3 Runbooks
                runbook_lines.append(f"• <{rb['url']}|{rb['title']}>")
            if len(runbooks) > 3:
                runbook_lines.append(f"... +{len(runbooks) - 3} more")
            fields.append({
                "title": "📋 Runbooks",
                "value": "\n".join(runbook_lines),
                "short": False,
            })

        # Attachment mit Farbe
        attachment = {
            "color": color,
            "fallback": f"[{alert.severity.name}] {alert.title}: {alert.body}",
            "pretext": header,
            "text": alert.body,
            "fields": fields,
            "footer": "Peak_Trade Alert Pipeline",
            "ts": int(alert.timestamp.timestamp()),
        }

        payload: Dict[str, Any] = {
            "attachments": [attachment],
        }

        # Optionale Overrides
        if self._config.channel:
            payload["channel"] = self._config.channel
        if self._config.username:
            payload["username"] = self._config.username
        if self._config.icon_emoji:
            payload["icon_emoji"] = self._config.icon_emoji

        return payload

    def _send_webhook(self, payload: Dict[str, Any]) -> None:
        """
        Sendet Payload an Slack-Webhook.

        Args:
            payload: Dict für JSON-Serialisierung

        Raises:
            Exception bei Netzwerkfehlern
        """
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        req = urllib.request.Request(
            self._config.webhook_url,
            data=data,
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(
            req, timeout=self._config.timeout_seconds
        ) as response:
            # Response ignorieren, nur Status-Code prüfen
            if response.status != 200:
                raise RuntimeError(f"Slack webhook returned {response.status}")


# =============================================================================
# EMAIL ALERT CHANNEL
# =============================================================================


@dataclass
class EmailChannelConfig:
    """
    Konfiguration für EmailAlertChannel.

    Attributes:
        smtp_host: SMTP-Server-Host
        smtp_port: SMTP-Server-Port
        use_tls: Ob TLS/STARTTLS verwendet werden soll
        username: SMTP-Login-Username
        password_env_var: Environment-Variable für SMTP-Passwort
        from_addr: Absender-Adresse
        to_addrs: Liste von Empfänger-Adressen
        min_severity: Minimale Severity für diesen Channel
        enabled: Ob der Channel aktiviert ist
        timeout_seconds: SMTP-Timeout
    """

    smtp_host: str
    smtp_port: int = 587
    use_tls: bool = True
    username: str = ""
    password_env_var: str = ""
    from_addr: str = ""
    to_addrs: List[str] = field(default_factory=list)
    min_severity: AlertSeverity = AlertSeverity.CRITICAL
    enabled: bool = False
    timeout_seconds: float = 30.0


class EmailAlertChannel:
    """
    E-Mail-Alert-Channel via SMTP.

    Features:
    - TLS/STARTTLS-Support
    - Strukturierte E-Mail mit HTML und Plain-Text
    - Passwort aus Environment-Variable (sicher)
    - Robuste Fehlerbehandlung
    """

    SEVERITY_SYMBOLS = {
        AlertSeverity.INFO: "ℹ️",
        AlertSeverity.WARN: "⚠️",
        AlertSeverity.CRITICAL: "🚨",
    }

    def __init__(self, config: EmailChannelConfig) -> None:
        """
        Initialisiert EmailAlertChannel.

        Args:
            config: EmailChannelConfig mit SMTP-Einstellungen
        """
        self._config = config
        self._logger = logging.getLogger(f"{__name__}.EmailAlertChannel")

    @property
    def name(self) -> str:
        return "email"

    @property
    def is_enabled(self) -> bool:
        return (
            self._config.enabled
            and bool(self._config.smtp_host)
            and bool(self._config.from_addr)
            and bool(self._config.to_addrs)
        )

    @property
    def min_severity(self) -> AlertSeverity:
        return self._config.min_severity

    def send(self, alert: AlertMessage) -> None:
        """
        Sendet Alert per E-Mail.

        Args:
            alert: AlertMessage zum Senden
        """
        if not self.is_enabled:
            return

        if alert.severity < self.min_severity:
            return

        try:
            msg = self._build_email(alert)
            self._send_email(msg)
            self._logger.debug(f"Email alert sent: {alert.title}")
        except Exception as e:
            # Fehler loggen, aber nicht nach außen propagieren
            self._logger.error(f"Failed to send email alert: {e}", exc_info=True)

    def _build_email(self, alert: AlertMessage) -> MIMEMultipart:
        """
        Baut E-Mail-Message mit HTML und Plain-Text.

        Args:
            alert: AlertMessage

        Returns:
            MIMEMultipart E-Mail-Message
        """
        symbol = self.SEVERITY_SYMBOLS.get(alert.severity, "📢")

        # Subject
        subject = f"[PEAK_TRADE][{alert.severity.name}][{alert.category.value}] {alert.title}"

        # Plain-Text Body
        text_lines = [
            f"{symbol} {alert.title}",
            "",
            alert.body,
            "",
            f"Severity: {alert.severity.name}",
            f"Category: {alert.category.value}",
            f"Source: {alert.source}",
            f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]

        if alert.session_id:
            text_lines.append(f"Session: {alert.session_id}")

        # Context-Daten (ohne runbooks)
        context_items = {k: v for k, v in alert.context.items() if k != "runbooks"}
        if context_items:
            text_lines.append("")
            text_lines.append("Context:")
            for key, value in context_items.items():
                if isinstance(value, float):
                    text_lines.append(f"  • {key}: {value:.4f}")
                else:
                    text_lines.append(f"  • {key}: {value}")

        # Phase 84: Runbooks-Sektion
        runbooks = alert.context.get("runbooks", [])
        if runbooks:
            text_lines.append("")
            text_lines.append("📋 Runbooks:")
            for rb in runbooks:
                text_lines.append(f"  • {rb['title']}: {rb['url']}")

        text_body = "\n".join(text_lines)

        # HTML Body
        severity_colors = {
            AlertSeverity.INFO: "#28a745",
            AlertSeverity.WARN: "#ffc107",
            AlertSeverity.CRITICAL: "#dc3545",
        }
        color = severity_colors.get(alert.severity, "#6c757d")

        context_html = ""
        context_items = {k: v for k, v in alert.context.items() if k != "runbooks"}
        if context_items:
            context_rows = []
            for key, value in context_items.items():
                if isinstance(value, float):
                    val_str = f"{value:.4f}"
                else:
                    val_str = str(value)
                context_rows.append(f"<tr><td><strong>{key}</strong></td><td>{val_str}</td></tr>")
            context_html = f"""
            <h3>Context</h3>
            <table border="1" cellpadding="5" cellspacing="0">
                {''.join(context_rows)}
            </table>
            """

        # Phase 84: Runbooks HTML
        runbooks_html = ""
        runbooks = alert.context.get("runbooks", [])
        if runbooks:
            runbook_items = []
            for rb in runbooks:
                runbook_items.append(
                    f'<li><a href="{rb["url"]}" style="color: #10b981;">📘 {rb["title"]}</a></li>'
                )
            runbooks_html = f"""
            <h3>📋 Runbooks</h3>
            <ul>
                {''.join(runbook_items)}
            </ul>
            """

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: {color}; color: white; padding: 15px; border-radius: 5px;">
                <h2>{symbol} [{alert.severity.name}] {alert.title}</h2>
            </div>
            <div style="padding: 15px;">
                <p style="font-size: 16px;">{alert.body}</p>
                <hr>
                <table>
                    <tr><td><strong>Category:</strong></td><td>{alert.category.value}</td></tr>
                    <tr><td><strong>Source:</strong></td><td><code>{alert.source}</code></td></tr>
                    <tr><td><strong>Time:</strong></td><td>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
                    {'<tr><td><strong>Session:</strong></td><td><code>' + alert.session_id + '</code></td></tr>' if alert.session_id else ''}
                </table>
                {context_html}
                {runbooks_html}
            </div>
            <div style="font-size: 12px; color: #666; padding: 10px;">
                Peak_Trade Alert Pipeline | Phase 84
            </div>
        </body>
        </html>
        """

        # E-Mail zusammenbauen
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._config.from_addr
        msg["To"] = ", ".join(self._config.to_addrs)

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        return msg

    def _send_email(self, msg: MIMEMultipart) -> None:
        """
        Sendet E-Mail via SMTP.

        Args:
            msg: MIMEMultipart E-Mail-Message
        """
        # Passwort aus Environment-Variable
        password = ""
        if self._config.password_env_var:
            password = os.environ.get(self._config.password_env_var, "")
            if not password:
                self._logger.warning(
                    f"Email password env var '{self._config.password_env_var}' not set"
                )

        if self._config.use_tls:
            # STARTTLS
            context = ssl.create_default_context()
            with smtplib.SMTP(
                self._config.smtp_host,
                self._config.smtp_port,
                timeout=self._config.timeout_seconds,
            ) as server:
                server.starttls(context=context)
                if self._config.username and password:
                    server.login(self._config.username, password)
                server.sendmail(
                    self._config.from_addr,
                    self._config.to_addrs,
                    msg.as_string(),
                )
        else:
            # Plain SMTP
            with smtplib.SMTP(
                self._config.smtp_host,
                self._config.smtp_port,
                timeout=self._config.timeout_seconds,
            ) as server:
                if self._config.username and password:
                    server.login(self._config.username, password)
                server.sendmail(
                    self._config.from_addr,
                    self._config.to_addrs,
                    msg.as_string(),
                )


# =============================================================================
# NULL ALERT CHANNEL (für deaktivierte Alerts)
# =============================================================================


class NullAlertChannel:
    """
    Null-Channel der keine Alerts sendet.

    Verwendet wenn Alerts global deaktiviert sind.
    """

    @property
    def name(self) -> str:
        return "null"

    @property
    def is_enabled(self) -> bool:
        return False

    @property
    def min_severity(self) -> AlertSeverity:
        return AlertSeverity.CRITICAL

    def send(self, alert: AlertMessage) -> None:
        """Tut nichts."""
        pass


# =============================================================================
# ALERT PIPELINE MANAGER
# =============================================================================


class AlertPipelineManager:
    """
    Zentrale Verwaltung der Alert-Pipeline.

    Features:
    - Multi-Channel-Routing
    - Severity-basierte Filterung pro Channel
    - Enabled-Check pro Channel
    - Robuste Fehlerbehandlung (ein Channel-Fehler stoppt nicht andere)
    - Automatische Persistierung für Alert-Historie (Phase 83)
    - Optionale Escalation für kritische Alerts (Phase 85)

    Usage:
        >>> manager = AlertPipelineManager([slack_channel, email_channel])
        >>> manager.send(alert)  # Routet zu allen passenden Channels und speichert
    """

    def __init__(
        self,
        channels: Sequence[AlertChannel],
        persist_alerts: bool = True,
        escalation_manager: Optional["EscalationManager"] = None,
    ) -> None:
        """
        Initialisiert AlertPipelineManager.

        Args:
            channels: Liste von AlertChannel-Implementierungen
            persist_alerts: Ob Alerts für die Historie gespeichert werden sollen (Phase 83)
            escalation_manager: Optionaler EscalationManager für On-Call-Integration (Phase 85)
        """
        self._channels = list(channels)
        self._persist_alerts = persist_alerts
        self._escalation_manager = escalation_manager
        self._logger = logging.getLogger(f"{__name__}.AlertPipelineManager")

    @property
    def channels(self) -> List[AlertChannel]:
        """Liste aller konfigurierten Channels."""
        return self._channels

    @property
    def enabled_channels(self) -> List[AlertChannel]:
        """Liste aller aktivierten Channels."""
        return [c for c in self._channels if c.is_enabled]

    @property
    def persist_alerts(self) -> bool:
        """Ob Alerts persistiert werden."""
        return self._persist_alerts

    @property
    def escalation_manager(self) -> Optional["EscalationManager"]:
        """Optionaler EscalationManager (Phase 85)."""
        return self._escalation_manager

    def send(self, alert: AlertMessage) -> None:
        """
        Sendet Alert an alle passenden Channels und speichert für Historie.

        Filterung:
        - Channel muss enabled sein
        - Alert-Severity >= Channel-min_severity

        Phase 83: Alerts werden automatisch für die Web-Dashboard-Historie
        gespeichert (unabhängig von Channel-Filterung).

        Phase 84: Runbooks werden automatisch vor dem Senden angehängt.

        Phase 85: Kritische Alerts werden optional an On-Call eskaliert.

        Args:
            alert: AlertMessage zum Senden
        """
        # Phase 84: Runbooks an Alert anhängen
        self._attach_runbooks(alert)

        # Phase 83: Alert persistieren für Historie
        if self._persist_alerts:
            self._persist_alert(alert)

        # Phase 85: Escalation für kritische Alerts
        self._maybe_escalate(alert)

        # An Channels senden
        for channel in self._channels:
            if not channel.is_enabled:
                continue

            if alert.severity < channel.min_severity:
                continue

            try:
                channel.send(alert)
            except Exception as e:
                # Fehler loggen, aber weiter zu anderen Channels
                self._logger.error(
                    f"Failed to send alert via {channel.name}: {e}",
                    exc_info=True,
                )

    def _attach_runbooks(self, alert: AlertMessage) -> None:
        """
        Hängt passende Runbooks an den Alert an (Phase 84).

        Runbooks werden in alert.context["runbooks"] als Liste von Dicts gespeichert.
        Dies ermöglicht einfache JSON-Serialisierung und Template-Zugriff.

        Args:
            alert: AlertMessage zum Erweitern
        """
        try:
            # Lazy import um zirkuläre Abhängigkeiten zu vermeiden
            from src.infra.runbooks import resolve_runbooks_for_alert

            runbooks = resolve_runbooks_for_alert(alert)
            if runbooks:
                alert.context["runbooks"] = [
                    {"id": rb.id, "title": rb.title, "url": rb.url}
                    for rb in runbooks
                ]
        except Exception as e:
            # Fehler loggen, aber nicht propagieren
            self._logger.debug(f"Failed to attach runbooks: {e}")

    def _persist_alert(self, alert: AlertMessage) -> None:
        """
        Speichert Alert für die Historie (Phase 83).

        Args:
            alert: AlertMessage zum Speichern
        """
        try:
            # Lazy import um zirkuläre Abhängigkeiten zu vermeiden
            from src.live.alert_storage import store_alert
            store_alert(alert)
        except Exception as e:
            # Fehler loggen, aber nicht propagieren
            self._logger.debug(f"Failed to persist alert: {e}")

    def _maybe_escalate(self, alert: AlertMessage) -> None:
        """
        Eskaliert Alert optional an On-Call (Phase 85).

        Escalation ist eine optionale Anreicherung. Fehler werden geloggt,
        aber NIEMALS propagiert - die Alert-Pipeline darf nicht blockiert werden.

        Args:
            alert: AlertMessage zum potenziellen Eskalieren
        """
        if self._escalation_manager is None:
            return

        try:
            # Lazy import um zirkuläre Abhängigkeiten zu vermeiden
            from src.infra.escalation import EscalationEvent
            import uuid

            # EscalationEvent aus AlertMessage bauen
            event = EscalationEvent(
                alert_id=str(uuid.uuid4()),
                severity=alert.severity.name,
                alert_type=alert.category.value,
                summary=alert.title,
                details={
                    "body": alert.body,
                    "source": alert.source,
                    **alert.context,
                },
                symbol=alert.context.get("symbol"),
                session_id=alert.session_id,
                created_at=alert.timestamp,
            )

            # Eskalieren (Manager entscheidet ob wirklich eskaliert wird)
            self._escalation_manager.maybe_escalate(event)

        except Exception as e:
            # KRITISCH: Fehler NIEMALS propagieren
            self._logger.debug(f"Failed to escalate alert: {e}")

    # Convenience-Methoden für direktes Alerting

    def send_risk_alert(
        self,
        title: str,
        body: str,
        severity: AlertSeverity,
        source: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Convenience-Methode für Risk-Alerts.

        Args:
            title: Alert-Titel
            body: Alert-Body
            severity: AlertSeverity
            source: Alert-Quelle
            session_id: Optional Session-ID
            context: Optional Context-Daten
        """
        alert = AlertMessage(
            title=title,
            body=body,
            severity=severity,
            category=AlertCategory.RISK,
            source=source,
            session_id=session_id,
            context=context or {},
        )
        self.send(alert)

    def send_execution_alert(
        self,
        title: str,
        body: str,
        severity: AlertSeverity,
        source: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Convenience-Methode für Execution-Alerts."""
        alert = AlertMessage(
            title=title,
            body=body,
            severity=severity,
            category=AlertCategory.EXECUTION,
            source=source,
            session_id=session_id,
            context=context or {},
        )
        self.send(alert)

    def send_system_alert(
        self,
        title: str,
        body: str,
        severity: AlertSeverity,
        source: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Convenience-Methode für System-Alerts."""
        alert = AlertMessage(
            title=title,
            body=body,
            severity=severity,
            category=AlertCategory.SYSTEM,
            source=source,
            session_id=session_id,
            context=context or {},
        )
        self.send(alert)


# =============================================================================
# SEVERITY TRANSITION TRACKER
# =============================================================================


class SeverityTransitionTracker:
    """
    Tracker für Risk-Severity-Transitions.

    Erkennt Übergänge zwischen GREEN/YELLOW/RED und generiert
    entsprechende Alerts nur bei tatsächlichen Änderungen.

    Alert-Pflicht:
    - GREEN → YELLOW: WARN
    - YELLOW → RED: CRITICAL
    - RED → YELLOW: WARN (Recovery, optional)
    - RED → GREEN: INFO (Full Recovery, optional)

    Usage:
        >>> tracker = SeverityTransitionTracker(alert_manager)
        >>> # Bei jedem Risk-Check:
        >>> tracker.update("yellow", session_id="sess_123", context={...})
    """

    # Transition-Severity-Mapping
    TRANSITION_SEVERITY = {
        ("green", "yellow"): AlertSeverity.WARN,
        ("green", "red"): AlertSeverity.CRITICAL,
        ("yellow", "red"): AlertSeverity.CRITICAL,
        ("yellow", "green"): AlertSeverity.INFO,
        ("red", "yellow"): AlertSeverity.WARN,
        ("red", "green"): AlertSeverity.INFO,
    }

    # Ob Recovery-Alerts gesendet werden sollen (konfigurierbar)
    SEND_RECOVERY_ALERTS = True

    def __init__(
        self,
        alert_manager: AlertPipelineManager,
        send_recovery_alerts: bool = True,
    ) -> None:
        """
        Initialisiert SeverityTransitionTracker.

        Args:
            alert_manager: AlertPipelineManager für Alert-Versand
            send_recovery_alerts: Ob Recovery-Alerts gesendet werden sollen
        """
        self._alert_manager = alert_manager
        self._current_status: Optional[str] = None
        self._send_recovery_alerts = send_recovery_alerts
        self._logger = logging.getLogger(f"{__name__}.SeverityTransitionTracker")

    @property
    def current_status(self) -> Optional[str]:
        """Aktueller Risk-Status (green/yellow/red)."""
        return self._current_status

    def update(
        self,
        new_status: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[AlertMessage]:
        """
        Aktualisiert den Status und sendet ggf. einen Alert.

        Args:
            new_status: Neuer Risk-Status ("green", "yellow", "red")
            session_id: Optional Session-ID
            context: Optional Context-Daten (Metriken, Limits, etc.)

        Returns:
            AlertMessage wenn ein Alert gesendet wurde, sonst None
        """
        new_status = new_status.lower()
        old_status = self._current_status

        # Erste Initialisierung
        if old_status is None:
            self._current_status = new_status
            self._logger.debug(f"Initial risk status: {new_status}")
            return None

        # Keine Änderung
        if old_status == new_status:
            return None

        # Transition erkannt
        self._current_status = new_status
        transition_key = (old_status, new_status)

        severity = self.TRANSITION_SEVERITY.get(transition_key)
        if severity is None:
            self._logger.warning(f"Unknown transition: {old_status} → {new_status}")
            return None

        # Recovery-Alerts optional
        is_recovery = new_status in ("green", "yellow") and old_status == "red"
        is_partial_recovery = new_status == "green" and old_status == "yellow"

        if (is_recovery or is_partial_recovery) and not self._send_recovery_alerts:
            self._logger.debug(
                f"Recovery transition {old_status} → {new_status} (alerts disabled)"
            )
            return None

        # Alert erstellen
        title = f"Risk Severity changed: {old_status.upper()} → {new_status.upper()}"

        if new_status == "red":
            body = "⛔ KRITISCH: Risk-Status ist auf RED gewechselt. Neue Orders werden blockiert. Sofortige Aufmerksamkeit erforderlich."
        elif new_status == "yellow":
            if old_status == "green":
                body = "⚠️ WARNUNG: Risk-Status ist auf YELLOW gewechselt. Mindestens ein Limit im Warnbereich. Erhöhte Aufmerksamkeit erforderlich."
            else:  # from red
                body = "📉 RECOVERY: Risk-Status ist von RED auf YELLOW zurückgegangen. Limits wieder unter Breach-Schwelle, aber weiterhin erhöht."
        else:  # green
            body = "✅ RECOVERY: Risk-Status ist auf GREEN zurückgekehrt. Alle Limits komfortabel eingehalten."

        alert = AlertMessage(
            title=title,
            body=body,
            severity=severity,
            category=AlertCategory.RISK,
            source="live_risk_severity",
            session_id=session_id,
            context=context or {},
        )

        # Alert senden
        self._alert_manager.send(alert)
        self._logger.info(f"Risk transition alert: {old_status} → {new_status}")

        return alert

    def reset(self) -> None:
        """Setzt den Tracker zurück (z.B. bei Session-Neustart)."""
        self._current_status = None


# =============================================================================
# CONFIG-BASED FACTORY
# =============================================================================


def build_alert_pipeline_from_config(
    config: Mapping[str, Any],
    environment: Optional[str] = None,
) -> AlertPipelineManager:
    """
    Baut AlertPipelineManager aus Config-Dict.

    Config-Struktur:
        [alerts]
        enabled = true
        default_min_severity = "WARN"

        [alerts.slack]
        enabled = true
        webhook_url = "https://hooks.slack.com/services/XXX/YYY/ZZZ"
        min_severity = "WARN"
        channel = "#peak-trade-alerts"
        username = "peak-trade-bot"
        icon_emoji = ":rotating_light:"

        [alerts.email]
        enabled = false
        min_severity = "CRITICAL"
        smtp_host = "smtp.example.com"
        smtp_port = 587
        use_tls = true
        username = "alerts@example.com"
        password_env_var = "PEAK_TRADE_SMTP_PASSWORD"
        from_addr = "alerts@example.com"
        to_addrs = ["ops@example.com"]

        [escalation]
        enabled = true
        enabled_environments = ["live"]
        provider = "pagerduty_stub"
        critical_severities = ["CRITICAL"]

    Args:
        config: Config-Dict (z.B. aus TOML)
        environment: Aktuelles Environment (für Escalation-Gating)

    Returns:
        Konfigurierter AlertPipelineManager
    """
    alerts_config = config.get("alerts", {})

    # Global deaktiviert?
    if not alerts_config.get("enabled", True):
        logger.info("Alert pipeline globally disabled")
        return AlertPipelineManager([NullAlertChannel()])

    # Default-Severity
    default_severity_str = alerts_config.get("default_min_severity", "WARN")
    default_severity = AlertSeverity.from_string(default_severity_str)

    channels: List[AlertChannel] = []

    # Slack-Channel
    slack_config = alerts_config.get("slack", {})
    if slack_config.get("enabled", False):
        webhook_url = slack_config.get("webhook_url", "")
        if webhook_url:
            severity_str = slack_config.get("min_severity", default_severity_str)
            channel_cfg = SlackChannelConfig(
                webhook_url=webhook_url,
                channel=slack_config.get("channel"),
                username=slack_config.get("username", "peak-trade-bot"),
                icon_emoji=slack_config.get("icon_emoji", ":rotating_light:"),
                min_severity=AlertSeverity.from_string(severity_str),
                enabled=True,
                timeout_seconds=float(slack_config.get("timeout_seconds", 5.0)),
            )
            channels.append(SlackAlertChannel(channel_cfg))
            logger.info(f"Slack alert channel configured (min_severity={severity_str})")
        else:
            logger.warning("Slack channel enabled but no webhook_url configured")

    # Email-Channel
    email_config = alerts_config.get("email", {})
    if email_config.get("enabled", False):
        smtp_host = email_config.get("smtp_host", "")
        if smtp_host:
            severity_str = email_config.get("min_severity", "CRITICAL")
            to_addrs = email_config.get("to_addrs", [])
            if isinstance(to_addrs, str):
                to_addrs = [to_addrs]

            channel_cfg = EmailChannelConfig(
                smtp_host=smtp_host,
                smtp_port=int(email_config.get("smtp_port", 587)),
                use_tls=bool(email_config.get("use_tls", True)),
                username=email_config.get("username", ""),
                password_env_var=email_config.get("password_env_var", ""),
                from_addr=email_config.get("from_addr", ""),
                to_addrs=to_addrs,
                min_severity=AlertSeverity.from_string(severity_str),
                enabled=True,
                timeout_seconds=float(email_config.get("timeout_seconds", 30.0)),
            )
            channels.append(EmailAlertChannel(channel_cfg))
            logger.info(f"Email alert channel configured (min_severity={severity_str})")
        else:
            logger.warning("Email channel enabled but no smtp_host configured")

    # Falls keine Channels konfiguriert, Null-Channel
    if not channels:
        logger.info("No alert channels configured, using null channel")
        channels.append(NullAlertChannel())

    # Phase 85: EscalationManager erstellen (optional)
    escalation_manager = _build_escalation_manager(config, environment)

    return AlertPipelineManager(
        channels,
        escalation_manager=escalation_manager,
    )


def _build_escalation_manager(
    config: Mapping[str, Any],
    environment: Optional[str] = None,
) -> Optional["EscalationManager"]:
    """
    Baut EscalationManager aus Config (Phase 85).

    Fehler beim Laden des EscalationManagers werden geloggt,
    aber nicht propagiert - Escalation ist optional.

    Args:
        config: Config-Dict
        environment: Aktuelles Environment

    Returns:
        EscalationManager oder None wenn deaktiviert/fehlerhaft
    """
    try:
        escalation_config = config.get("escalation", {})

        # Escalation deaktiviert?
        if not escalation_config.get("enabled", False):
            logger.debug("Escalation disabled in config")
            return None

        # Lazy import
        from src.infra.escalation import build_escalation_manager_from_config

        manager = build_escalation_manager_from_config(config, environment)
        logger.info(
            f"Escalation manager configured: provider={escalation_config.get('provider', 'null')}"
        )
        return manager

    except Exception as e:
        # Fehler loggen, aber nicht propagieren
        logger.warning(f"Failed to build escalation manager: {e}")
        return None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "AlertSeverity",
    "AlertCategory",
    # Message
    "AlertMessage",
    # Channel Configs
    "SlackChannelConfig",
    "EmailChannelConfig",
    # Channels
    "SlackAlertChannel",
    "EmailAlertChannel",
    "NullAlertChannel",
    "AlertChannel",
    # Manager
    "AlertPipelineManager",
    # Tracker
    "SeverityTransitionTracker",
    # Factory
    "build_alert_pipeline_from_config",
]
