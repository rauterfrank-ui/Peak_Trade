#!/usr/bin/env python3
"""
Peak_Trade Slack Notifier
==========================

Slack-Integration für Test Health Automation.
Sendet Alerts bei fehlgeschlagenen Checks und Trigger-Violations.

Autor: Peak_Trade Ops Team
Stand: Dezember 2024
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional

from src.notifications.base import Alert, Notifier


class SlackNotifier:
    """
    Slack-Notifier für Peak_Trade Alerts.

    Verwendet Slack Incoming Webhooks für einfache Integration.

    Attributes:
        webhook_url: Slack Webhook URL (aus ENV oder explizit)
        enabled: Ob Notifier aktiv ist (False wenn webhook_url fehlt)

    Examples:
        >>> notifier = SlackNotifier.from_env("PEAK_TRADE_SLACK_WEBHOOK")
        >>> alert = Alert(
        ...     level="critical",
        ...     source="test_health",
        ...     message="Test Health failed",
        ...     timestamp=datetime.utcnow(),
        ... )
        >>> notifier.send(alert)
    """

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialisiert SlackNotifier.

        Parameters
        ----------
        webhook_url : Optional[str]
            Slack Webhook URL. Wenn None, ist Notifier disabled.
        """
        self.webhook_url = webhook_url
        self.enabled = webhook_url is not None and len(webhook_url) > 0

    @classmethod
    def from_env(cls, env_var: str = "PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH") -> SlackNotifier:
        """
        Erstellt SlackNotifier aus ENV-Variable.

        Parameters
        ----------
        env_var : str
            Name der ENV-Variable (default: PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH)

        Returns
        -------
        SlackNotifier
            Notifier-Instanz (disabled wenn ENV-Variable nicht gesetzt)
        """
        webhook_url = os.getenv(env_var)
        return cls(webhook_url=webhook_url)

    def send(self, alert: Alert) -> None:
        """
        Sendet einen Alert an Slack.

        Parameters
        ----------
        alert : Alert
            Der zu versendende Alert

        Notes
        -----
        - Exceptions beim Versand werden abgefangen und geloggt (fail-safe)
        - Wenn enabled=False, wird nichts gesendet
        """
        if not self.enabled:
            return

        try:
            self._send_to_slack(alert)
        except Exception as e:
            # Fail-safe: Slack-Fehler killen nicht die Pipeline
            print(f"⚠️  Slack-Notification fehlgeschlagen: {e}")

    def _send_to_slack(self, alert: Alert) -> None:
        """
        Interne Funktion: Sendet Alert an Slack Webhook.

        Parameters
        ----------
        alert : Alert
            Der zu versendende Alert

        Raises
        ------
        Exception
            Bei Netzwerk- oder API-Fehlern
        """
        # Baue Slack-Message
        text = self._format_alert_text(alert)

        payload = {"text": text}
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            # Optional: Response-Code prüfen
            if resp.status != 200:
                raise Exception(f"Slack API returned status {resp.status}")

    def _format_alert_text(self, alert: Alert) -> str:
        """
        Formatiert Alert als Slack-Text (Markdown-kompatibel).

        Parameters
        ----------
        alert : Alert
            Der zu formatierende Alert

        Returns
        -------
        str
            Formatierter Slack-Text
        """
        # Emoji basierend auf Level
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨",
        }.get(alert.level, "📢")

        # Header
        lines = [
            f"{emoji} *[Peak_Trade · TestHealth]* {alert.level.upper()}",
            "",
            f"*Source:* {alert.source}",
            f"*Message:* {alert.message}",
            f"*Timestamp:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]

        # Context (falls vorhanden)
        if alert.context:
            lines.append("")
            lines.append("*Details:*")
            for key, value in alert.context.items():
                lines.append(f"  • {key}: {value}")

        return "\n".join(lines)


def send_test_health_slack_notification(
    profile_name: str,
    health_score: float,
    failed_checks: int,
    passed_checks: int,
    violations: list,
    report_path: str,
    webhook_env_var: str = "PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH",
) -> None:
    """
    Convenience-Funktion: Sendet Test-Health-Notification an Slack.

    Parameters
    ----------
    profile_name : str
        Name des Profils (z.B. "weekly_core")
    health_score : float
        Health-Score (0-100)
    failed_checks : int
        Anzahl fehlgeschlagener Checks
    passed_checks : int
        Anzahl erfolgreicher Checks
    violations : list
        Liste von Trigger-Violations
    report_path : str
        Pfad zum Report
    webhook_env_var : str
        ENV-Variable für Webhook URL

    Examples
    --------
    >>> send_test_health_slack_notification(
    ...     profile_name="weekly_core",
    ...     health_score=75.0,
    ...     failed_checks=2,
    ...     passed_checks=8,
    ...     violations=[...],
    ...     report_path="reports/test_health/...",
    ... )
    """
    notifier = SlackNotifier.from_env(webhook_env_var)

    if not notifier.enabled:
        return

    # Baue Nachricht
    severity_icon = "🟢" if health_score >= 80 else "🟡" if health_score >= 50 else "🔴"

    message_lines = [
        f"{severity_icon} *Test Health Report: {profile_name}*",
        "",
        f"*Health Score:* {health_score:.1f} / 100.0",
        f"*Passed Checks:* {passed_checks}",
        f"*Failed Checks:* {failed_checks}",
    ]

    # Violations (falls vorhanden)
    if violations:
        message_lines.append("")
        message_lines.append(f"*Trigger Violations:* {len(violations)}")
        for v in violations[:5]:  # Max. 5 anzeigen
            severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(v.severity, "?")
            message_lines.append(f"  {severity_emoji} {v.message}")

        if len(violations) > 5:
            message_lines.append(f"  ... und {len(violations) - 5} weitere")

    # Report-Link
    message_lines.append("")
    message_lines.append(f"*Report:* `{report_path}`")

    message = "\n".join(message_lines)

    # Sende als JSON-Payload direkt
    try:
        payload = {"text": message}
        data = json.dumps(payload).encode("utf-8")

        webhook_url = os.getenv(webhook_env_var)
        if not webhook_url:
            return

        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                print(f"⚠️  Slack API returned status {resp.status}")

    except Exception as e:
        # Fail-safe: Slack-Fehler killen nicht die Pipeline
        print(f"⚠️  Slack-Notification fehlgeschlagen: {e}")


def send_test_health_slack_notification_v1(
    message: str,
    webhook_env_var: str = "PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH",
) -> None:
    """
    Sendet eine fertig formatierte TestHealth v1 Slack-Nachricht.

    Parameters
    ----------
    message : str
        Fertig formatierte Nachricht
    webhook_env_var : str
        ENV-Variable für Webhook URL

    Examples
    --------
    >>> send_test_health_slack_notification_v1(
    ...     message="[Peak_Trade · TestHealth v1] Status: FAILED\\n...",
    ... )
    """
    webhook_url = os.getenv(webhook_env_var)
    if not webhook_url:
        return

    try:
        payload = {"text": message}
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                print(f"⚠️  Slack API returned status {resp.status}")

    except Exception as e:
        # Fail-safe: Slack-Fehler killen nicht die Pipeline
        print(f"⚠️  Slack-Notification v1 fehlgeschlagen: {e}")
