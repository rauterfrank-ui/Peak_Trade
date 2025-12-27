"""
Email Notification Channel
===========================

Sends alerts via SMTP email (disabled by default).
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from ..models import AlertEvent

logger = logging.getLogger(__name__)


class EmailChannel:
    """
    Email notification channel (SMTP).

    Features:
    - Sends alerts via SMTP
    - Configurable via environment variables
    - Disabled by default (requires configuration)
    - HTML email formatting

    Environment Variables:
        RISK_ALERTS_SMTP_HOST: SMTP server host
        RISK_ALERTS_SMTP_PORT: SMTP server port (default: 587)
        RISK_ALERTS_SMTP_USER: SMTP username
        RISK_ALERTS_SMTP_PASSWORD: SMTP password
        RISK_ALERTS_EMAIL_FROM: From email address
        RISK_ALERTS_EMAIL_TO: Comma-separated list of recipient emails
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        to_emails: Optional[List[str]] = None,
    ):
        """
        Initialize email channel.

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port (default: 587)
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: From email address
            to_emails: List of recipient emails
        """
        self.smtp_host = smtp_host or os.getenv("RISK_ALERTS_SMTP_HOST")
        self.smtp_port = smtp_port or int(os.getenv("RISK_ALERTS_SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("RISK_ALERTS_SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("RISK_ALERTS_SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("RISK_ALERTS_EMAIL_FROM")
        
        # Parse to_emails from env or use provided list
        if to_emails:
            self.to_emails = to_emails
        else:
            to_env = os.getenv("RISK_ALERTS_EMAIL_TO", "")
            self.to_emails = [e.strip() for e in to_env.split(",") if e.strip()]

    @property
    def enabled(self) -> bool:
        """Email channel is enabled only if all required config is present."""
        return all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password,
            self.from_email,
            self.to_emails,
        ])

    def send(self, alert: AlertEvent) -> bool:
        """Send alert via email."""
        if not self.enabled:
            logger.debug("Email channel disabled (missing configuration)")
            return False

        try:
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)

            # Create HTML body
            html_body = self._format_html(alert)
            msg.attach(MIMEText(html_body, "html"))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Alert sent via email to {len(self.to_emails)} recipients")
            return True

        except Exception as e:
            logger.error(f"Email channel error: {e}", exc_info=True)
            return False

    def _format_html(self, alert: AlertEvent) -> str:
        """Format alert as HTML email."""
        severity_color = {
            "info": "#17a2b8",
            "warn": "#ffc107",
            "critical": "#dc3545",
        }
        color = severity_color.get(alert.severity.value, "#6c757d")

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="border-left: 4px solid {color}; padding-left: 15px; margin-bottom: 20px;">
                <h2 style="color: {color}; margin-bottom: 5px;">{alert.title}</h2>
                <p style="color: #666; margin-top: 5px;">
                    <strong>Source:</strong> {alert.source}<br/>
                    <strong>Time:</strong> {alert.timestamp_utc.isoformat()}<br/>
                    <strong>Severity:</strong> {alert.severity.value.upper()}
                </p>
            </div>
            <div style="margin-bottom: 20px;">
                <h3>Message</h3>
                <p>{alert.body}</p>
            </div>
        """

        if alert.labels:
            html += "<div><h3>Labels</h3><ul>"
            for key, value in alert.labels.items():
                html += f"<li><strong>{key}:</strong> {value}</li>"
            html += "</ul></div>"

        if alert.metadata:
            html += f"<div><h3>Metadata</h3><pre>{alert.metadata}</pre></div>"

        html += """
        </body>
        </html>
        """

        return html
