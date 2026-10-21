"""Peak_Trade Slack notifier for Test Health Automation.

The runner contract and the legacy test surface are both present.
A configured webhook is not delivery authorization. This module has no
transport and performs no HTTP POST.
"""

from __future__ import annotations

import os
from typing import Optional

from src.notifications.base import Alert

EXTERNAL_EFFECT_AUTHORIZED = False


class SlackNotifier:
    """Formats test-health alerts and refuses external delivery."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self.enabled = webhook_url is not None and len(webhook_url) > 0

    @classmethod
    def from_env(cls, env_var: str = "PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH") -> SlackNotifier:
        webhook_url = os.getenv(env_var)
        return cls(webhook_url=webhook_url)

    def send(self, alert: Alert) -> None:
        if not self.enabled:
            return
        try:
            text = self._format_alert_text(alert)
            _deny_external_effect(text, self.webhook_url)
        except Exception:
            print("Slack-Notification fehlgeschlagen")

    def _format_alert_text(self, alert: Alert) -> str:
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨",
        }.get(alert.level, "📢")
        lines = [
            f"{emoji} *[Peak_Trade · TestHealth]* {alert.level.upper()}",
            "",
            f"*Source:* {alert.source}",
            f"*Message:* {alert.message}",
            f"*Timestamp:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]
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
    """Accept the legacy test-health arguments and do not deliver them."""
    try:
        notifier = SlackNotifier.from_env(webhook_env_var)
        if not notifier.enabled:
            return
        severity_icon = "🟢" if health_score >= 80 else "🟡" if health_score >= 50 else "🔴"
        message_lines = [
            f"{severity_icon} *Test Health Report: {profile_name}*",
            "",
            f"*Health Score:* {health_score:.1f} / 100.0",
            f"*Passed Checks:* {passed_checks}",
            f"*Failed Checks:* {failed_checks}",
        ]
        if violations:
            message_lines.append("")
            message_lines.append(f"*Trigger Violations:* {len(violations)}")
            for violation in violations[:5]:
                severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(
                    violation.severity, "?"
                )
                message_lines.append(f"  {severity_emoji} {violation.message}")
            if len(violations) > 5:
                message_lines.append(f"  ... und {len(violations) - 5} weitere")
        message_lines.append("")
        message_lines.append(f"*Report:* `{report_path}`")
        _deny_external_effect("\n".join(message_lines), notifier.webhook_url)
    except Exception:
        print("Slack-Notification fehlgeschlagen")


def send_test_health_slack_notification_v1(
    message: str,
    webhook_env_var: str = "PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH",
) -> None:
    """Runner entry. The message stays local; the webhook variable grants nothing."""
    try:
        webhook_url = os.getenv(webhook_env_var)
        if not webhook_url:
            return
        _deny_external_effect(message, webhook_url)
    except Exception:
        print("Slack-Notification v1 fehlgeschlagen")


def _deny_external_effect(message: str, webhook_url: Optional[str]) -> None:
    """Keep message and webhook_url local. No transport exists behind this gate."""
    if EXTERNAL_EFFECT_AUTHORIZED:
        raise RuntimeError("external effect is closed")
    if message == "" and not webhook_url:
        return
    return
