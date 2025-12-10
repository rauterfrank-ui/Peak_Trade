"""
Tests für Slack Notifier
=========================

Testet die Slack-Integration für Test Health Automation.

Stand: Dezember 2024
"""

from __future__ import annotations

import datetime as dt
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from src.notifications.base import Alert
from src.notifications.slack import (
    SlackNotifier,
    send_test_health_slack_notification,
)


class TestSlackNotifier:
    """Tests für SlackNotifier-Klasse."""

    def test_init_with_webhook_url(self):
        """Test: SlackNotifier mit Webhook-URL erstellen."""
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/services/TEST")
        
        assert notifier.enabled is True
        assert notifier.webhook_url == "https://hooks.slack.com/services/TEST"

    def test_init_without_webhook_url(self):
        """Test: SlackNotifier ohne Webhook-URL → disabled."""
        notifier = SlackNotifier(webhook_url=None)
        
        assert notifier.enabled is False
        assert notifier.webhook_url is None

    def test_init_with_empty_webhook_url(self):
        """Test: SlackNotifier mit leerer Webhook-URL → disabled."""
        notifier = SlackNotifier(webhook_url="")
        
        assert notifier.enabled is False

    def test_from_env_with_env_var(self):
        """Test: SlackNotifier aus ENV-Variable erstellen."""
        with patch.dict(os.environ, {"TEST_WEBHOOK": "https://hooks.slack.com/test"}):
            notifier = SlackNotifier.from_env("TEST_WEBHOOK")
            
            assert notifier.enabled is True
            assert notifier.webhook_url == "https://hooks.slack.com/test"

    def test_from_env_without_env_var(self):
        """Test: SlackNotifier aus fehlender ENV-Variable → disabled."""
        with patch.dict(os.environ, {}, clear=True):
            notifier = SlackNotifier.from_env("NONEXISTENT_WEBHOOK")
            
            assert notifier.enabled is False

    def test_send_disabled_notifier_does_nothing(self):
        """Test: Disabled Notifier sendet nichts."""
        notifier = SlackNotifier(webhook_url=None)
        
        alert = Alert(
            level="critical",
            source="test",
            message="Test message",
            timestamp=dt.datetime.utcnow(),
        )
        
        # Sollte keine Exception werfen
        notifier.send(alert)

    @patch("urllib.request.urlopen")
    def test_send_alert_success(self, mock_urlopen):
        """Test: Alert erfolgreich an Slack senden."""
        # Mock Response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        
        alert = Alert(
            level="warning",
            source="test_health",
            message="Test message",
            timestamp=dt.datetime.utcnow(),
            context={"key": "value"},
        )
        
        notifier.send(alert)
        
        # Prüfe ob urlopen aufgerufen wurde
        assert mock_urlopen.called

    @patch("urllib.request.urlopen")
    def test_send_alert_failure_is_caught(self, mock_urlopen):
        """Test: Fehler beim Senden werden abgefangen (fail-safe)."""
        # Mock wirft Exception
        mock_urlopen.side_effect = Exception("Network error")
        
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        
        alert = Alert(
            level="critical",
            source="test",
            message="Test",
            timestamp=dt.datetime.utcnow(),
        )
        
        # Sollte keine Exception durchlassen
        notifier.send(alert)

    def test_format_alert_text_basic(self):
        """Test: Alert-Text formatieren."""
        notifier = SlackNotifier(webhook_url="https://test")
        
        alert = Alert(
            level="warning",
            source="test_health",
            message="Health check failed",
            timestamp=dt.datetime(2025, 12, 10, 14, 30, 0),
        )
        
        text = notifier._format_alert_text(alert)
        
        assert "[Peak_Trade · TestHealth]" in text
        assert "WARNING" in text
        assert "test_health" in text
        assert "Health check failed" in text
        assert "2025-12-10 14:30:00 UTC" in text

    def test_format_alert_text_with_context(self):
        """Test: Alert-Text mit Context formatieren."""
        notifier = SlackNotifier(webhook_url="https://test")
        
        alert = Alert(
            level="critical",
            source="test_health",
            message="Critical failure",
            timestamp=dt.datetime.utcnow(),
            context={"profile": "weekly_core", "failed_checks": 3},
        )
        
        text = notifier._format_alert_text(alert)
        
        assert "profile: weekly_core" in text
        assert "failed_checks: 3" in text


class TestSendTestHealthSlackNotification:
    """Tests für send_test_health_slack_notification() Convenience-Funktion."""

    @patch("urllib.request.urlopen")
    def test_send_notification_success(self, mock_urlopen):
        """Test: Test-Health-Notification erfolgreich senden."""
        # Mock Response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        # Mock ENV-Variable
        with patch.dict(
            os.environ, {"TEST_WEBHOOK": "https://hooks.slack.com/test"}
        ):
            from src.ops.test_health_runner import TriggerViolation
            
            violations = [
                TriggerViolation(
                    severity="error",
                    trigger_name="max_fail_rate",
                    message="Fail-Rate zu hoch: 30% > 20%",
                    actual_value=0.3,
                    threshold_value=0.2,
                )
            ]
            
            send_test_health_slack_notification(
                profile_name="weekly_core",
                health_score=65.0,
                failed_checks=3,
                passed_checks=7,
                violations=violations,
                report_path="reports/test_health/test",
                webhook_env_var="TEST_WEBHOOK",
            )
            
            # Prüfe ob urlopen aufgerufen wurde
            assert mock_urlopen.called

    def test_send_notification_without_env_var(self):
        """Test: Notification ohne ENV-Variable → nichts passiert."""
        with patch.dict(os.environ, {}, clear=True):
            # Sollte keine Exception werfen
            send_test_health_slack_notification(
                profile_name="test",
                health_score=100.0,
                failed_checks=0,
                passed_checks=5,
                violations=[],
                report_path="test",
                webhook_env_var="NONEXISTENT_WEBHOOK",
            )

    @patch("urllib.request.urlopen")
    def test_send_notification_failure_is_caught(self, mock_urlopen):
        """Test: Fehler beim Senden werden abgefangen."""
        mock_urlopen.side_effect = Exception("Network error")
        
        with patch.dict(
            os.environ, {"TEST_WEBHOOK": "https://hooks.slack.com/test"}
        ):
            # Sollte keine Exception durchlassen
            send_test_health_slack_notification(
                profile_name="test",
                health_score=50.0,
                failed_checks=5,
                passed_checks=5,
                violations=[],
                report_path="test",
                webhook_env_var="TEST_WEBHOOK",
            )
