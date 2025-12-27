"""
Email Alert Channel
===================

Sends alerts via SMTP email.
"""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List

from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.base_channel import (
    AlertChannel,
    ChannelHealth,
    ChannelStatus,
)


class EmailChannel(AlertChannel):
    """
    Email alert channel via SMTP.

    Features:
    - HTML and plain text emails
    - TLS/STARTTLS support
    - Multiple recipients
    - Severity-based subject prefixes

    Config:
        smtp_host: SMTP server hostname (e.g., "smtp.gmail.com")
        smtp_port: SMTP port (default: 587 for TLS)
        smtp_user: SMTP username (from env)
        smtp_password: SMTP password (from env: ${SMTP_PASSWORD})
        from_address: Sender email address
        to_addresses: List of recipient emails
        use_tls: Enable TLS (default: True)
    """

    def __init__(
        self,
        config: Dict[str, Any],
        min_severity: AlertSeverity = AlertSeverity.CRITICAL,
    ):
        """
        Initialize email channel.

        Args:
            config: Channel configuration
            min_severity: Minimum severity (default: CRITICAL - email is expensive)
        """
        super().__init__(name="email", config=config, min_severity=min_severity)

        self.smtp_host = config.get("smtp_host", "")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_user = config.get("smtp_user", "")
        self.smtp_password = config.get("smtp_password", "")
        self.from_address = config.get("from_address", "alerts@peak-trade.local")
        self.to_addresses = config.get("to_addresses", [])
        self.use_tls = config.get("use_tls", True)

        # Validate configuration
        if self._enabled:
            missing = []
            if not self.smtp_host:
                missing.append("smtp_host")
            if not self.smtp_user:
                missing.append("smtp_user")
            if not self.smtp_password:
                missing.append("smtp_password")
            if not self.to_addresses:
                missing.append("to_addresses")

            if missing:
                self._health.status = ChannelStatus.FAILED
                self._health.message = f"Missing config: {', '.join(missing)}"
                self._enabled = False

    async def send(self, event: AlertEvent) -> bool:
        """
        Send alert via email.

        Args:
            event: AlertEvent to send

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Build email message
            msg = self._build_message(event)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.use_tls:
                    server.starttls()

                # Login
                server.login(self.smtp_user, self.smtp_password)

                # Send
                server.send_message(msg)

            return True

        except smtplib.SMTPException as e:
            self._health.last_error = f"SMTP error: {e}"
            return False
        except Exception as e:
            self._health.last_error = str(e)
            return False

    def _build_message(self, event: AlertEvent) -> MIMEMultipart:
        """
        Build email message.

        Args:
            event: AlertEvent to format

        Returns:
            MIMEMultipart email message
        """
        msg = MIMEMultipart("alternative")

        # Subject with severity prefix
        severity_emoji = self._get_severity_emoji(event.severity)
        msg["Subject"] = f"{severity_emoji} [{event.severity.value.upper()}] {event.source}: {event.message[:50]}"
        msg["From"] = self.from_address
        msg["To"] = ", ".join(self.to_addresses)

        # Plain text version
        text_body = self._build_text_body(event)
        msg.attach(MIMEText(text_body, "plain"))

        # HTML version
        html_body = self._build_html_body(event)
        msg.attach(MIMEText(html_body, "html"))

        return msg

    def _get_severity_emoji(self, severity: AlertSeverity) -> str:
        """Get emoji for severity."""
        return {
            AlertSeverity.DEBUG: "🔍",
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨",
        }.get(severity, "📢")

    def _build_text_body(self, event: AlertEvent) -> str:
        """Build plain text email body."""
        lines = [
            "Peak_Trade Alert Notification",
            "=" * 60,
            "",
            f"Severity:  {event.severity.value.upper()}",
            f"Category:  {event.category.value}",
            f"Source:    {event.source}",
            f"Time:      {event.timestamp.isoformat()}",
            "",
            "Message:",
            event.message,
            "",
        ]

        if event.context:
            lines.append("Context:")
            for key, value in event.context.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        lines.append(f"Event ID: {event.event_id}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _build_html_body(self, event: AlertEvent) -> str:
        """Build HTML email body."""
        # Severity color
        severity_color = {
            AlertSeverity.DEBUG: "#6c757d",
            AlertSeverity.INFO: "#17a2b8",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.ERROR: "#dc3545",
            AlertSeverity.CRITICAL: "#8b0000",
        }.get(event.severity, "#333")

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 20px auto; border: 1px solid #ddd; }}
                .header {{ background: {severity_color}; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .field {{ margin-bottom: 10px; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #333; }}
                .context {{ background: #f8f9fa; padding: 10px; margin-top: 10px; border-left: 4px solid {severity_color}; }}
                .footer {{ background: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{self._get_severity_emoji(event.severity)} {event.severity.value.upper()} Alert</h2>
                </div>
                <div class="content">
                    <div class="field">
                        <span class="label">Source:</span>
                        <span class="value">{event.source}</span>
                    </div>
                    <div class="field">
                        <span class="label">Category:</span>
                        <span class="value">{event.category.value}</span>
                    </div>
                    <div class="field">
                        <span class="label">Time:</span>
                        <span class="value">{event.timestamp.isoformat()}</span>
                    </div>
                    <div class="field">
                        <span class="label">Message:</span>
                        <div class="value">{event.message}</div>
                    </div>
        """

        if event.context:
            html += '<div class="context"><strong>Context:</strong><br/>'
            for key, value in event.context.items():
                html += f'<div>&nbsp;&nbsp;{key}: {value}</div>'
            html += '</div>'

        html += f"""
                </div>
                <div class="footer">
                    Event ID: {event.event_id}
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def health_check(self) -> ChannelHealth:
        """
        Check email channel health.

        Returns:
            ChannelHealth
        """
        self._health.last_check = datetime.utcnow()

        if not self._enabled:
            self._health.status = ChannelStatus.DISABLED
            self._health.message = "Channel disabled or misconfigured"
            return self._health

        # Basic validation
        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.to_addresses]):
            self._health.status = ChannelStatus.FAILED
            self._health.message = "Incomplete configuration"
        else:
            self._health.status = ChannelStatus.HEALTHY
            self._health.message = f"SMTP configured: {self.smtp_host}:{self.smtp_port}"

        return self._health
