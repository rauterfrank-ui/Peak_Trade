# tests/test_alert_pipeline.py
"""
Tests für Alert-Pipeline (Phase 82)
===================================

Tests für:
- AlertSeverity
- AlertCategory
- AlertMessage
- SlackAlertChannel
- EmailAlertChannel
- NullAlertChannel
- AlertPipelineManager
- SeverityTransitionTracker
- build_alert_pipeline_from_config
"""
from __future__ import annotations

from datetime import UTC
from unittest.mock import MagicMock, patch

import pytest

from src.live.alert_pipeline import (
    AlertCategory,
    AlertMessage,
    AlertPipelineManager,
    AlertSeverity,
    EmailAlertChannel,
    EmailChannelConfig,
    NullAlertChannel,
    SeverityTransitionTracker,
    SlackAlertChannel,
    SlackChannelConfig,
    build_alert_pipeline_from_config,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_alert_info() -> AlertMessage:
    """Erstellt Sample-INFO-Alert."""
    return AlertMessage(
        title="Test Info Alert",
        body="This is an info alert for testing.",
        severity=AlertSeverity.INFO,
        category=AlertCategory.SYSTEM,
        source="test.source",
        session_id="test_session_123",
        context={"key": "value", "number": 42.5},
    )


@pytest.fixture
def sample_alert_warn() -> AlertMessage:
    """Erstellt Sample-WARN-Alert."""
    return AlertMessage(
        title="Test Warning Alert",
        body="This is a warning alert for testing.",
        severity=AlertSeverity.WARN,
        category=AlertCategory.RISK,
        source="test.risk",
        session_id="test_session_456",
        context={"daily_loss": -250.50, "limit": 500.0},
    )


@pytest.fixture
def sample_alert_critical() -> AlertMessage:
    """Erstellt Sample-CRITICAL-Alert."""
    return AlertMessage(
        title="Test Critical Alert",
        body="This is a critical alert for testing.",
        severity=AlertSeverity.CRITICAL,
        category=AlertCategory.RISK,
        source="test.risk.breach",
        session_id="test_session_789",
        context={"breach_type": "daily_loss", "value": -600.0, "limit": 500.0},
    )


@pytest.fixture
def mock_slack_channel() -> SlackAlertChannel:
    """Erstellt SlackAlertChannel mit Mock-Config."""
    config = SlackChannelConfig(
        webhook_url="https://hooks.slack.com/services/TEST/TEST/TEST",
        channel="#test-alerts",
        username="test-bot",
        icon_emoji=":test:",
        min_severity=AlertSeverity.WARN,
        enabled=True,
        timeout_seconds=5.0,
    )
    return SlackAlertChannel(config)


@pytest.fixture
def mock_email_channel() -> EmailAlertChannel:
    """Erstellt EmailAlertChannel mit Mock-Config."""
    config = EmailChannelConfig(
        smtp_host="smtp.test.com",
        smtp_port=587,
        use_tls=True,
        username="test@test.com",
        password_env_var="TEST_SMTP_PASSWORD",
        from_addr="alerts@test.com",
        to_addrs=["ops@test.com", "backup@test.com"],
        min_severity=AlertSeverity.CRITICAL,
        enabled=True,
        timeout_seconds=30.0,
    )
    return EmailAlertChannel(config)


# =============================================================================
# ALERTSEVERITY TESTS
# =============================================================================


class TestAlertSeverity:
    """Tests für AlertSeverity Enum."""

    def test_ordering(self):
        """Testet dass AlertSeverity-Ordering korrekt ist."""
        assert AlertSeverity.INFO < AlertSeverity.WARN
        assert AlertSeverity.WARN < AlertSeverity.CRITICAL
        assert AlertSeverity.INFO < AlertSeverity.CRITICAL

    def test_comparison(self):
        """Testet AlertSeverity-Vergleiche."""
        assert AlertSeverity.WARN >= AlertSeverity.INFO
        assert AlertSeverity.CRITICAL >= AlertSeverity.WARN
        assert AlertSeverity.CRITICAL > AlertSeverity.INFO

    def test_from_risk_status(self):
        """Testet Konvertierung von Risk-Status."""
        assert AlertSeverity.from_risk_status("green") == AlertSeverity.INFO
        assert AlertSeverity.from_risk_status("yellow") == AlertSeverity.WARN
        assert AlertSeverity.from_risk_status("red") == AlertSeverity.CRITICAL
        # Case-insensitive
        assert AlertSeverity.from_risk_status("GREEN") == AlertSeverity.INFO
        assert AlertSeverity.from_risk_status("Yellow") == AlertSeverity.WARN

    def test_from_string(self):
        """Testet String-Parsing."""
        assert AlertSeverity.from_string("info") == AlertSeverity.INFO
        assert AlertSeverity.from_string("INFO") == AlertSeverity.INFO
        assert AlertSeverity.from_string("warn") == AlertSeverity.WARN
        assert AlertSeverity.from_string("warning") == AlertSeverity.WARN
        assert AlertSeverity.from_string("WARN") == AlertSeverity.WARN
        assert AlertSeverity.from_string("critical") == AlertSeverity.CRITICAL
        assert AlertSeverity.from_string("CRITICAL") == AlertSeverity.CRITICAL

    def test_from_string_unknown_defaults_to_warn(self):
        """Testet dass unbekannte Strings zu WARN werden."""
        assert AlertSeverity.from_string("unknown") == AlertSeverity.WARN
        assert AlertSeverity.from_string("") == AlertSeverity.WARN


# =============================================================================
# ALERTCATEGORY TESTS
# =============================================================================


class TestAlertCategory:
    """Tests für AlertCategory Enum."""

    def test_values(self):
        """Testet dass alle Kategorien definiert sind."""
        assert AlertCategory.RISK.value == "RISK"
        assert AlertCategory.EXECUTION.value == "EXECUTION"
        assert AlertCategory.SYSTEM.value == "SYSTEM"

    def test_from_string(self):
        """Testet String-Parsing."""
        assert AlertCategory.from_string("RISK") == AlertCategory.RISK
        assert AlertCategory.from_string("risk") == AlertCategory.RISK
        assert AlertCategory.from_string("EXECUTION") == AlertCategory.EXECUTION
        assert AlertCategory.from_string("system") == AlertCategory.SYSTEM

    def test_from_string_unknown_defaults_to_system(self):
        """Testet dass unbekannte Strings zu SYSTEM werden."""
        assert AlertCategory.from_string("unknown") == AlertCategory.SYSTEM


# =============================================================================
# ALERTMESSAGE TESTS
# =============================================================================


class TestAlertMessage:
    """Tests für AlertMessage Dataclass."""

    def test_construction(self, sample_alert_warn: AlertMessage):
        """Testet AlertMessage-Konstruktion."""
        assert sample_alert_warn.title == "Test Warning Alert"
        assert sample_alert_warn.body == "This is a warning alert for testing."
        assert sample_alert_warn.severity == AlertSeverity.WARN
        assert sample_alert_warn.category == AlertCategory.RISK
        assert sample_alert_warn.source == "test.risk"
        assert sample_alert_warn.session_id == "test_session_456"
        assert "daily_loss" in sample_alert_warn.context

    def test_default_timestamp(self):
        """Testet dass Timestamp automatisch gesetzt wird."""
        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            source="test",
        )
        assert alert.timestamp is not None
        assert alert.timestamp.tzinfo == UTC

    def test_default_context_is_empty_dict(self):
        """Testet dass Context default ein leeres Dict ist."""
        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            source="test",
        )
        assert alert.context == {}
        # Prüfe dass es ein neues Dict ist, nicht ein geteiltes
        assert alert.context is not AlertMessage.__dataclass_fields__["context"].default_factory()

    def test_to_dict(self, sample_alert_critical: AlertMessage):
        """Testet Serialisierung zu Dict."""
        d = sample_alert_critical.to_dict()
        assert d["title"] == "Test Critical Alert"
        assert d["severity"] == "CRITICAL"
        assert d["category"] == "RISK"
        assert d["source"] == "test.risk.breach"
        assert d["session_id"] == "test_session_789"
        assert "timestamp" in d
        assert isinstance(d["context"], dict)


# =============================================================================
# NULL ALERT CHANNEL TESTS
# =============================================================================


class TestNullAlertChannel:
    """Tests für NullAlertChannel."""

    def test_properties(self):
        """Testet NullAlertChannel-Properties."""
        channel = NullAlertChannel()
        assert channel.name == "null"
        assert channel.is_enabled is False
        assert channel.min_severity == AlertSeverity.CRITICAL

    def test_send_does_nothing(self, sample_alert_critical: AlertMessage):
        """Testet dass send() nichts tut."""
        channel = NullAlertChannel()
        # Sollte keine Exception werfen
        channel.send(sample_alert_critical)


# =============================================================================
# SLACK ALERT CHANNEL TESTS
# =============================================================================


class TestSlackAlertChannel:
    """Tests für SlackAlertChannel."""

    def test_properties(self, mock_slack_channel: SlackAlertChannel):
        """Testet SlackAlertChannel-Properties."""
        assert mock_slack_channel.name == "slack"
        assert mock_slack_channel.is_enabled is True
        assert mock_slack_channel.min_severity == AlertSeverity.WARN

    def test_is_enabled_false_when_no_webhook(self):
        """Testet dass Channel deaktiviert ist ohne Webhook-URL."""
        config = SlackChannelConfig(
            webhook_url="",
            enabled=True,
        )
        channel = SlackAlertChannel(config)
        assert channel.is_enabled is False

    def test_is_enabled_false_when_disabled(self):
        """Testet dass Channel deaktiviert ist wenn enabled=False."""
        config = SlackChannelConfig(
            webhook_url="https://hooks.slack.com/test",
            enabled=False,
        )
        channel = SlackAlertChannel(config)
        assert channel.is_enabled is False

    def test_build_payload_structure(self, mock_slack_channel: SlackAlertChannel, sample_alert_warn: AlertMessage):
        """Testet dass Payload korrekt strukturiert ist."""
        payload = mock_slack_channel._build_payload(sample_alert_warn)

        assert "attachments" in payload
        assert len(payload["attachments"]) == 1

        attachment = payload["attachments"][0]
        assert "color" in attachment
        assert "fallback" in attachment
        assert "pretext" in attachment
        assert "text" in attachment
        assert "fields" in attachment
        assert "footer" in attachment
        assert "ts" in attachment

        # Prüfe Overrides
        assert payload.get("channel") == "#test-alerts"
        assert payload.get("username") == "test-bot"
        assert payload.get("icon_emoji") == ":test:"

    def test_severity_filtering(self, mock_slack_channel: SlackAlertChannel, sample_alert_info: AlertMessage):
        """Testet dass Alerts unter min_severity ignoriert werden."""
        with patch.object(mock_slack_channel, "_send_webhook") as mock_send:
            # INFO < WARN (min_severity), sollte nicht gesendet werden
            mock_slack_channel.send(sample_alert_info)
            mock_send.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_send_success(self, mock_urlopen, mock_slack_channel: SlackAlertChannel, sample_alert_critical: AlertMessage):
        """Testet erfolgreichen Alert-Versand."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        mock_slack_channel.send(sample_alert_critical)
        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_send_failure_does_not_raise(self, mock_urlopen, mock_slack_channel: SlackAlertChannel, sample_alert_critical: AlertMessage):
        """Testet dass Fehler beim Senden keine Exception werfen."""
        mock_urlopen.side_effect = Exception("Network error")

        # Sollte keine Exception werfen
        mock_slack_channel.send(sample_alert_critical)


# =============================================================================
# EMAIL ALERT CHANNEL TESTS
# =============================================================================


class TestEmailAlertChannel:
    """Tests für EmailAlertChannel."""

    def test_properties(self, mock_email_channel: EmailAlertChannel):
        """Testet EmailAlertChannel-Properties."""
        assert mock_email_channel.name == "email"
        assert mock_email_channel.is_enabled is True
        assert mock_email_channel.min_severity == AlertSeverity.CRITICAL

    def test_is_enabled_false_when_no_smtp_host(self):
        """Testet dass Channel deaktiviert ist ohne SMTP-Host."""
        config = EmailChannelConfig(
            smtp_host="",
            enabled=True,
            from_addr="test@test.com",
            to_addrs=["ops@test.com"],
        )
        channel = EmailAlertChannel(config)
        assert channel.is_enabled is False

    def test_is_enabled_false_when_no_to_addrs(self):
        """Testet dass Channel deaktiviert ist ohne Empfänger."""
        config = EmailChannelConfig(
            smtp_host="smtp.test.com",
            enabled=True,
            from_addr="test@test.com",
            to_addrs=[],
        )
        channel = EmailAlertChannel(config)
        assert channel.is_enabled is False

    def test_build_email_structure(self, mock_email_channel: EmailAlertChannel, sample_alert_critical: AlertMessage):
        """Testet dass E-Mail korrekt strukturiert ist."""
        msg = mock_email_channel._build_email(sample_alert_critical)

        assert msg["Subject"].startswith("[PEAK_TRADE][CRITICAL][RISK]")
        assert msg["From"] == "alerts@test.com"
        assert "ops@test.com" in msg["To"]
        assert "backup@test.com" in msg["To"]

        # Prüfe dass Multipart (text + html)
        assert msg.is_multipart()
        parts = msg.get_payload()
        assert len(parts) == 2

    def test_severity_filtering(self, mock_email_channel: EmailAlertChannel, sample_alert_warn: AlertMessage):
        """Testet dass Alerts unter min_severity ignoriert werden."""
        with patch.object(mock_email_channel, "_send_email") as mock_send:
            # WARN < CRITICAL (min_severity), sollte nicht gesendet werden
            mock_email_channel.send(sample_alert_warn)
            mock_send.assert_not_called()

    @patch("smtplib.SMTP")
    def test_send_success(self, mock_smtp, mock_email_channel: EmailAlertChannel, sample_alert_critical: AlertMessage):
        """Testet erfolgreichen E-Mail-Versand."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        with patch.dict("os.environ", {"TEST_SMTP_PASSWORD": "testpass"}):
            mock_email_channel.send(sample_alert_critical)

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_failure_does_not_raise(self, mock_smtp, mock_email_channel: EmailAlertChannel, sample_alert_critical: AlertMessage):
        """Testet dass Fehler beim Senden keine Exception werfen."""
        mock_smtp.side_effect = Exception("SMTP error")

        # Sollte keine Exception werfen
        mock_email_channel.send(sample_alert_critical)


# =============================================================================
# ALERT PIPELINE MANAGER TESTS
# =============================================================================


class TestAlertPipelineManager:
    """Tests für AlertPipelineManager."""

    def test_empty_channels(self):
        """Testet Manager mit leeren Channels."""
        manager = AlertPipelineManager([])
        assert manager.channels == []
        assert manager.enabled_channels == []

    def test_channels_list(self):
        """Testet dass Channels korrekt gelistet werden."""
        null_channel = NullAlertChannel()
        manager = AlertPipelineManager([null_channel])
        assert len(manager.channels) == 1
        assert manager.channels[0] is null_channel

    def test_enabled_channels_filtering(self):
        """Testet dass nur aktivierte Channels zurückgegeben werden."""
        # Erstelle enabled und disabled Channels
        enabled_config = SlackChannelConfig(
            webhook_url="https://test.slack.com",
            enabled=True,
        )
        disabled_config = SlackChannelConfig(
            webhook_url="https://test.slack.com",
            enabled=False,
        )
        enabled_channel = SlackAlertChannel(enabled_config)
        disabled_channel = SlackAlertChannel(disabled_config)

        manager = AlertPipelineManager([enabled_channel, disabled_channel])
        assert len(manager.enabled_channels) == 1
        assert manager.enabled_channels[0] is enabled_channel

    def test_send_routes_to_all_matching_channels(self, sample_alert_critical: AlertMessage):
        """Testet dass Alerts an alle passenden Channels gesendet werden."""
        channel1 = MagicMock()
        channel1.is_enabled = True
        channel1.min_severity = AlertSeverity.WARN

        channel2 = MagicMock()
        channel2.is_enabled = True
        channel2.min_severity = AlertSeverity.CRITICAL

        manager = AlertPipelineManager([channel1, channel2])
        manager.send(sample_alert_critical)

        channel1.send.assert_called_once_with(sample_alert_critical)
        channel2.send.assert_called_once_with(sample_alert_critical)

    def test_send_skips_disabled_channels(self, sample_alert_critical: AlertMessage):
        """Testet dass deaktivierte Channels übersprungen werden."""
        channel = MagicMock()
        channel.is_enabled = False
        channel.min_severity = AlertSeverity.INFO

        manager = AlertPipelineManager([channel])
        manager.send(sample_alert_critical)

        channel.send.assert_not_called()

    def test_send_respects_min_severity(self, sample_alert_warn: AlertMessage):
        """Testet dass min_severity respektiert wird."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.CRITICAL  # Höher als WARN

        manager = AlertPipelineManager([channel])
        manager.send(sample_alert_warn)

        channel.send.assert_not_called()

    def test_send_continues_on_channel_error(self, sample_alert_critical: AlertMessage):
        """Testet dass Fehler in einem Channel andere nicht blockieren."""
        failing_channel = MagicMock()
        failing_channel.is_enabled = True
        failing_channel.min_severity = AlertSeverity.INFO
        failing_channel.name = "failing"
        failing_channel.send.side_effect = Exception("Channel error")

        working_channel = MagicMock()
        working_channel.is_enabled = True
        working_channel.min_severity = AlertSeverity.INFO
        working_channel.name = "working"

        manager = AlertPipelineManager([failing_channel, working_channel])
        manager.send(sample_alert_critical)

        failing_channel.send.assert_called_once()
        working_channel.send.assert_called_once()

    def test_convenience_methods(self):
        """Testet die Convenience-Methoden."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO

        manager = AlertPipelineManager([channel])

        # Test send_risk_alert
        manager.send_risk_alert(
            title="Risk Alert",
            body="Body",
            severity=AlertSeverity.WARN,
            source="test",
        )
        assert channel.send.call_count == 1
        sent_alert = channel.send.call_args[0][0]
        assert sent_alert.category == AlertCategory.RISK

        # Reset
        channel.reset_mock()

        # Test send_execution_alert
        manager.send_execution_alert(
            title="Execution Alert",
            body="Body",
            severity=AlertSeverity.CRITICAL,
            source="test",
        )
        sent_alert = channel.send.call_args[0][0]
        assert sent_alert.category == AlertCategory.EXECUTION

        # Reset
        channel.reset_mock()

        # Test send_system_alert
        manager.send_system_alert(
            title="System Alert",
            body="Body",
            severity=AlertSeverity.INFO,
            source="test",
        )
        sent_alert = channel.send.call_args[0][0]
        assert sent_alert.category == AlertCategory.SYSTEM


# =============================================================================
# SEVERITY TRANSITION TRACKER TESTS
# =============================================================================


class TestSeverityTransitionTracker:
    """Tests für SeverityTransitionTracker."""

    def test_initial_status_is_none(self):
        """Testet dass initialer Status None ist."""
        manager = AlertPipelineManager([NullAlertChannel()])
        tracker = SeverityTransitionTracker(manager)
        assert tracker.current_status is None

    def test_first_update_sets_status_no_alert(self):
        """Testet dass erste Update Status setzt aber keinen Alert sendet."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO
        manager = AlertPipelineManager([channel])

        tracker = SeverityTransitionTracker(manager)
        result = tracker.update("green")

        assert tracker.current_status == "green"
        assert result is None
        channel.send.assert_not_called()

    def test_same_status_no_alert(self):
        """Testet dass gleicher Status keinen Alert auslöst."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO
        manager = AlertPipelineManager([channel])

        tracker = SeverityTransitionTracker(manager)
        tracker.update("yellow")  # Initial
        channel.reset_mock()

        result = tracker.update("yellow")  # Gleich
        assert result is None
        channel.send.assert_not_called()

    def test_green_to_yellow_sends_warn(self):
        """Testet GREEN → YELLOW Alert."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO
        manager = AlertPipelineManager([channel])

        tracker = SeverityTransitionTracker(manager)
        tracker.update("green")
        channel.reset_mock()

        result = tracker.update("yellow")

        assert result is not None
        assert result.severity == AlertSeverity.WARN
        assert "GREEN → YELLOW" in result.title
        channel.send.assert_called_once()

    def test_yellow_to_red_sends_critical(self):
        """Testet YELLOW → RED Alert."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO
        manager = AlertPipelineManager([channel])

        tracker = SeverityTransitionTracker(manager)
        tracker.update("yellow")
        channel.reset_mock()

        result = tracker.update("red")

        assert result is not None
        assert result.severity == AlertSeverity.CRITICAL
        assert "YELLOW → RED" in result.title
        channel.send.assert_called_once()

    def test_green_to_red_sends_critical(self):
        """Testet GREEN → RED Alert (direkt)."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO
        manager = AlertPipelineManager([channel])

        tracker = SeverityTransitionTracker(manager)
        tracker.update("green")
        channel.reset_mock()

        result = tracker.update("red")

        assert result is not None
        assert result.severity == AlertSeverity.CRITICAL
        assert "GREEN → RED" in result.title

    def test_red_to_yellow_recovery_alert(self):
        """Testet RED → YELLOW Recovery-Alert."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO
        manager = AlertPipelineManager([channel])

        tracker = SeverityTransitionTracker(manager, send_recovery_alerts=True)
        tracker.update("red")
        channel.reset_mock()

        result = tracker.update("yellow")

        assert result is not None
        assert result.severity == AlertSeverity.WARN
        assert "RED → YELLOW" in result.title
        assert "RECOVERY" in result.body

    def test_red_to_green_recovery_alert(self):
        """Testet RED → GREEN Recovery-Alert."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO
        manager = AlertPipelineManager([channel])

        tracker = SeverityTransitionTracker(manager, send_recovery_alerts=True)
        tracker.update("red")
        channel.reset_mock()

        result = tracker.update("green")

        assert result is not None
        assert result.severity == AlertSeverity.INFO
        assert "RED → GREEN" in result.title
        assert "RECOVERY" in result.body

    def test_recovery_alerts_can_be_disabled(self):
        """Testet dass Recovery-Alerts deaktiviert werden können."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO
        manager = AlertPipelineManager([channel])

        tracker = SeverityTransitionTracker(manager, send_recovery_alerts=False)
        tracker.update("red")
        channel.reset_mock()

        result = tracker.update("yellow")

        assert result is None
        channel.send.assert_not_called()

    def test_reset(self):
        """Testet Tracker-Reset."""
        manager = AlertPipelineManager([NullAlertChannel()])
        tracker = SeverityTransitionTracker(manager)

        tracker.update("yellow")
        assert tracker.current_status == "yellow"

        tracker.reset()
        assert tracker.current_status is None

    def test_context_is_passed_to_alert(self):
        """Testet dass Context an Alert übergeben wird."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO
        manager = AlertPipelineManager([channel])

        tracker = SeverityTransitionTracker(manager)
        tracker.update("green")
        channel.reset_mock()

        context = {"daily_loss": -250.0, "limit": 500.0}
        result = tracker.update("yellow", session_id="sess_123", context=context)

        assert result is not None
        assert result.session_id == "sess_123"
        assert result.context == context

    def test_case_insensitive_status(self):
        """Testet dass Status case-insensitive ist."""
        channel = MagicMock()
        channel.is_enabled = True
        channel.min_severity = AlertSeverity.INFO
        manager = AlertPipelineManager([channel])

        tracker = SeverityTransitionTracker(manager)
        tracker.update("GREEN")  # Uppercase
        assert tracker.current_status == "green"

        channel.reset_mock()
        result = tracker.update("YELLOW")  # Uppercase
        assert tracker.current_status == "yellow"
        assert result is not None


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================


class TestBuildAlertPipelineFromConfig:
    """Tests für build_alert_pipeline_from_config Factory."""

    def test_empty_config_returns_null_channel(self):
        """Testet dass leere Config Null-Channel zurückgibt."""
        manager = build_alert_pipeline_from_config({})
        assert len(manager.channels) == 1
        assert isinstance(manager.channels[0], NullAlertChannel)

    def test_disabled_alerts_returns_null_channel(self):
        """Testet dass deaktivierte Alerts Null-Channel zurückgeben."""
        config = {
            "alerts": {
                "enabled": False,
            }
        }
        manager = build_alert_pipeline_from_config(config)
        assert len(manager.channels) == 1
        assert isinstance(manager.channels[0], NullAlertChannel)

    def test_slack_channel_from_config(self):
        """Testet Slack-Channel-Erstellung aus Config."""
        config = {
            "alerts": {
                "enabled": True,
                "default_min_severity": "WARN",
                "slack": {
                    "enabled": True,
                    "webhook_url": "https://hooks.slack.com/test",
                    "min_severity": "WARN",
                    "channel": "#alerts",
                    "username": "bot",
                    "icon_emoji": ":robot:",
                },
            }
        }
        manager = build_alert_pipeline_from_config(config)

        assert len(manager.channels) == 1
        assert isinstance(manager.channels[0], SlackAlertChannel)
        assert manager.channels[0].is_enabled is True
        assert manager.channels[0].min_severity == AlertSeverity.WARN

    def test_email_channel_from_config(self):
        """Testet Email-Channel-Erstellung aus Config."""
        config = {
            "alerts": {
                "enabled": True,
                "email": {
                    "enabled": True,
                    "smtp_host": "smtp.test.com",
                    "smtp_port": 587,
                    "use_tls": True,
                    "username": "user",
                    "password_env_var": "SMTP_PASS",
                    "from_addr": "from@test.com",
                    "to_addrs": ["to@test.com"],
                    "min_severity": "CRITICAL",
                },
            }
        }
        manager = build_alert_pipeline_from_config(config)

        assert len(manager.channels) == 1
        assert isinstance(manager.channels[0], EmailAlertChannel)
        assert manager.channels[0].is_enabled is True
        assert manager.channels[0].min_severity == AlertSeverity.CRITICAL

    def test_multiple_channels_from_config(self):
        """Testet mehrere Channels aus Config."""
        config = {
            "alerts": {
                "enabled": True,
                "slack": {
                    "enabled": True,
                    "webhook_url": "https://hooks.slack.com/test",
                    "min_severity": "WARN",
                },
                "email": {
                    "enabled": True,
                    "smtp_host": "smtp.test.com",
                    "from_addr": "from@test.com",
                    "to_addrs": ["to@test.com"],
                    "min_severity": "CRITICAL",
                },
            }
        }
        manager = build_alert_pipeline_from_config(config)

        assert len(manager.channels) == 2
        channel_types = {type(c) for c in manager.channels}
        assert SlackAlertChannel in channel_types
        assert EmailAlertChannel in channel_types

    def test_slack_without_webhook_url_is_skipped(self):
        """Testet dass Slack ohne Webhook-URL übersprungen wird."""
        config = {
            "alerts": {
                "enabled": True,
                "slack": {
                    "enabled": True,
                    "webhook_url": "",  # Leer
                },
            }
        }
        manager = build_alert_pipeline_from_config(config)

        # Sollte Null-Channel zurückgeben, da Slack ungültig
        assert len(manager.channels) == 1
        assert isinstance(manager.channels[0], NullAlertChannel)

    def test_email_without_smtp_host_is_skipped(self):
        """Testet dass Email ohne SMTP-Host übersprungen wird."""
        config = {
            "alerts": {
                "enabled": True,
                "email": {
                    "enabled": True,
                    "smtp_host": "",  # Leer
                },
            }
        }
        manager = build_alert_pipeline_from_config(config)

        # Sollte Null-Channel zurückgeben
        assert len(manager.channels) == 1
        assert isinstance(manager.channels[0], NullAlertChannel)

    def test_to_addrs_as_string(self):
        """Testet dass to_addrs als String akzeptiert wird."""
        config = {
            "alerts": {
                "enabled": True,
                "email": {
                    "enabled": True,
                    "smtp_host": "smtp.test.com",
                    "from_addr": "from@test.com",
                    "to_addrs": "single@test.com",  # String statt Liste
                    "min_severity": "CRITICAL",
                },
            }
        }
        manager = build_alert_pipeline_from_config(config)

        assert len(manager.channels) == 1
        assert isinstance(manager.channels[0], EmailAlertChannel)


# =============================================================================
# ACCEPTANCE CRITERIA TESTS
# =============================================================================


class TestAcceptanceCriteria:
    """
    Tests für die Phase 82 Akzeptanzkriterien.

    1. Severity-Change GREEN → YELLOW erzeugt Slack-Alert mit Severity WARN
    2. Severity-Change YELLOW → RED erzeugt Slack-Alert mit Severity CRITICAL
    3. Hard-Limit-Breach erzeugt Slack-Alert mit Severity CRITICAL
    4. Alerts respektieren Channel-spezifische min_severity
    5. Globale Deaktivierung unterdrückt alle Alerts
    6. Fehlende/ungültige Slack-Konfiguration führt zu Log, nicht Crash
    """

    def test_ac1_green_to_yellow_sends_warn_alert(self):
        """AC1: GREEN → YELLOW erzeugt WARN Alert."""
        sent_alerts: list[AlertMessage] = []

        class CaptureChannel:
            name = "capture"
            is_enabled = True
            min_severity = AlertSeverity.INFO

            def send(self, alert: AlertMessage) -> None:
                sent_alerts.append(alert)

        manager = AlertPipelineManager([CaptureChannel()])
        tracker = SeverityTransitionTracker(manager)

        tracker.update("green")
        tracker.update("yellow")

        assert len(sent_alerts) == 1
        assert sent_alerts[0].severity == AlertSeverity.WARN

    def test_ac2_yellow_to_red_sends_critical_alert(self):
        """AC2: YELLOW → RED erzeugt CRITICAL Alert."""
        sent_alerts: list[AlertMessage] = []

        class CaptureChannel:
            name = "capture"
            is_enabled = True
            min_severity = AlertSeverity.INFO

            def send(self, alert: AlertMessage) -> None:
                sent_alerts.append(alert)

        manager = AlertPipelineManager([CaptureChannel()])
        tracker = SeverityTransitionTracker(manager)

        tracker.update("yellow")
        tracker.update("red")

        assert len(sent_alerts) == 1
        assert sent_alerts[0].severity == AlertSeverity.CRITICAL

    def test_ac3_hard_limit_breach_sends_critical_alert(self):
        """AC3: Hard-Limit-Breach erzeugt CRITICAL Alert."""
        sent_alerts: list[AlertMessage] = []

        class CaptureChannel:
            name = "capture"
            is_enabled = True
            min_severity = AlertSeverity.INFO

            def send(self, alert: AlertMessage) -> None:
                sent_alerts.append(alert)

        manager = AlertPipelineManager([CaptureChannel()])

        # Simuliere Hard-Limit-Breach
        manager.send_risk_alert(
            title="MaxDailyLoss limit breached",
            body="Daily loss exceeded limit: -600.00 / 500.00",
            severity=AlertSeverity.CRITICAL,
            source="live_risk_limits",
            context={"breach_type": "max_daily_loss", "value": -600.0, "limit": 500.0},
        )

        assert len(sent_alerts) == 1
        assert sent_alerts[0].severity == AlertSeverity.CRITICAL
        assert sent_alerts[0].category == AlertCategory.RISK

    def test_ac4_channel_min_severity_is_respected(self):
        """AC4: Channel-spezifische min_severity wird respektiert."""
        warn_alerts: list[AlertMessage] = []
        critical_alerts: list[AlertMessage] = []

        class WarnChannel:
            name = "warn"
            is_enabled = True
            min_severity = AlertSeverity.WARN

            def send(self, alert: AlertMessage) -> None:
                warn_alerts.append(alert)

        class CriticalChannel:
            name = "critical"
            is_enabled = True
            min_severity = AlertSeverity.CRITICAL

            def send(self, alert: AlertMessage) -> None:
                critical_alerts.append(alert)

        manager = AlertPipelineManager([WarnChannel(), CriticalChannel()])

        # WARN Alert
        warn_alert = AlertMessage(
            title="Warning",
            body="Warning body",
            severity=AlertSeverity.WARN,
            category=AlertCategory.RISK,
            source="test",
        )
        manager.send(warn_alert)

        # WARN geht nur an WarnChannel
        assert len(warn_alerts) == 1
        assert len(critical_alerts) == 0

        # CRITICAL Alert
        critical_alert = AlertMessage(
            title="Critical",
            body="Critical body",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.RISK,
            source="test",
        )
        manager.send(critical_alert)

        # CRITICAL geht an beide
        assert len(warn_alerts) == 2
        assert len(critical_alerts) == 1

    def test_ac5_global_disable_suppresses_all_alerts(self):
        """AC5: Globale Deaktivierung unterdrückt alle Alerts."""
        config = {
            "alerts": {
                "enabled": False,
                "slack": {
                    "enabled": True,
                    "webhook_url": "https://test.slack.com",
                },
            }
        }
        manager = build_alert_pipeline_from_config(config)

        # Sollte Null-Channel haben
        assert len(manager.enabled_channels) == 0

    def test_ac6_invalid_slack_config_does_not_crash(self):
        """AC6: Ungültige Slack-Config führt zu Log, nicht Crash."""
        config = {
            "alerts": {
                "enabled": True,
                "slack": {
                    "enabled": True,
                    "webhook_url": "",  # Ungültig
                },
            }
        }

        # Sollte keine Exception werfen
        manager = build_alert_pipeline_from_config(config)
        assert manager is not None

        # Und ein Alert senden sollte auch nicht crashen
        alert = AlertMessage(
            title="Test",
            body="Test",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.SYSTEM,
            source="test",
        )
        manager.send(alert)  # Sollte nicht crashen


# =============================================================================
# PHASE 84 - RUNBOOK INTEGRATION TESTS
# =============================================================================


class TestPhase84RunbookIntegration:
    """
    Tests für Phase 84: Runbook-Integration in Alerts.

    Testet:
    - Automatisches Anhängen von Runbooks an Alerts
    - Runbooks in Slack-Payload
    - Runbooks in Email-Body
    - Runbooks in context["runbooks"]
    """

    def test_manager_attaches_runbooks_to_alert(self):
        """Testet dass AlertPipelineManager Runbooks an Alerts anhängt."""
        sent_alerts: list[AlertMessage] = []

        class CaptureChannel:
            name = "capture"
            is_enabled = True
            min_severity = AlertSeverity.INFO

            def send(self, alert: AlertMessage) -> None:
                sent_alerts.append(alert)

        manager = AlertPipelineManager([CaptureChannel()], persist_alerts=False)

        # Risk-Alert mit bekannter Source
        alert = AlertMessage(
            title="Test Risk Alert",
            body="Body",
            severity=AlertSeverity.WARN,
            category=AlertCategory.RISK,
            source="live_risk_severity",
        )
        manager.send(alert)

        assert len(sent_alerts) == 1
        assert "runbooks" in sent_alerts[0].context
        assert len(sent_alerts[0].context["runbooks"]) >= 1

        # Prüfe Struktur
        runbook = sent_alerts[0].context["runbooks"][0]
        assert "id" in runbook
        assert "title" in runbook
        assert "url" in runbook

    def test_runbooks_contain_expected_entries(self):
        """Testet dass erwartete Runbooks enthalten sind."""
        sent_alerts: list[AlertMessage] = []

        class CaptureChannel:
            name = "capture"
            is_enabled = True
            min_severity = AlertSeverity.INFO

            def send(self, alert: AlertMessage) -> None:
                sent_alerts.append(alert)

        manager = AlertPipelineManager([CaptureChannel()], persist_alerts=False)

        # RISK + live_risk_severity sollte Risk-Severity-Runbook enthalten
        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.RISK,
            source="live_risk_severity",
        )
        manager.send(alert)

        runbook_ids = [rb["id"] for rb in sent_alerts[0].context.get("runbooks", [])]
        assert "live_risk_severity" in runbook_ids
        assert "live_alert_pipeline" in runbook_ids

    def test_slack_payload_includes_runbooks_section(self, mock_slack_channel: SlackAlertChannel):
        """Testet dass Slack-Payload Runbooks-Sektion enthält."""
        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.RISK,
            source="live_risk_severity",
            context={
                "runbooks": [
                    {"id": "test_rb", "title": "Test Runbook", "url": "https://example.com/runbook"},
                ]
            },
        )

        payload = mock_slack_channel._build_payload(alert)

        # Prüfe dass Runbooks-Feld vorhanden ist
        attachment = payload["attachments"][0]
        field_titles = [f["title"] for f in attachment["fields"]]
        assert "📋 Runbooks" in field_titles

        # Prüfe dass URL im Link-Format ist
        runbooks_field = next(f for f in attachment["fields"] if f["title"] == "📋 Runbooks")
        assert "<https://example.com/runbook|Test Runbook>" in runbooks_field["value"]

    def test_email_body_includes_runbooks_section(self, mock_email_channel: EmailAlertChannel):
        """Testet dass Email-Body Runbooks-Sektion enthält."""
        import base64

        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.RISK,
            source="live_risk_severity",
            context={
                "runbooks": [
                    {"id": "test_rb", "title": "Test Runbook", "url": "https://example.com/runbook"},
                ]
            },
        )

        msg = mock_email_channel._build_email(alert)
        parts = msg.get_payload()

        # Plain-Text-Teil (möglicherweise base64-codiert)
        plain_payload = parts[0].get_payload()
        if parts[0].get("Content-Transfer-Encoding") == "base64":
            plain_text = base64.b64decode(plain_payload).decode("utf-8")
        else:
            plain_text = plain_payload

        assert "Runbooks:" in plain_text
        assert "Test Runbook" in plain_text
        assert "https://example.com/runbook" in plain_text

        # HTML-Teil (möglicherweise base64-codiert)
        html_payload = parts[1].get_payload()
        if parts[1].get("Content-Transfer-Encoding") == "base64":
            html_text = base64.b64decode(html_payload).decode("utf-8")
        else:
            html_text = html_payload

        assert "Runbooks" in html_text
        assert 'href="https://example.com/runbook"' in html_text

    def test_alerts_without_matching_runbooks(self):
        """Testet Alerts ohne passende Runbooks."""
        sent_alerts: list[AlertMessage] = []

        class CaptureChannel:
            name = "capture"
            is_enabled = True
            min_severity = AlertSeverity.INFO

            def send(self, alert: AlertMessage) -> None:
                sent_alerts.append(alert)

        manager = AlertPipelineManager([CaptureChannel()], persist_alerts=False)

        # Alert mit unbekannter Source - sollte trotzdem Fallback-Runbooks haben
        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.WARN,
            category=AlertCategory.SYSTEM,
            source="completely_unknown_source_xyz",
        )
        manager.send(alert)

        # Sollte mindestens live_alert_pipeline als Fallback haben
        runbooks = sent_alerts[0].context.get("runbooks", [])
        assert len(runbooks) >= 1

    def test_slack_payload_without_runbooks(self, mock_slack_channel: SlackAlertChannel):
        """Testet dass Slack-Payload ohne Runbooks korrekt funktioniert."""
        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.RISK,
            source="test",
            context={},  # Keine Runbooks
        )

        payload = mock_slack_channel._build_payload(alert)

        # Sollte keine Runbooks-Sektion haben
        attachment = payload["attachments"][0]
        field_titles = [f["title"] for f in attachment["fields"]]
        assert "📋 Runbooks" not in field_titles

    def test_email_body_without_runbooks(self, mock_email_channel: EmailAlertChannel):
        """Testet dass Email-Body ohne Runbooks korrekt funktioniert."""
        import base64

        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.RISK,
            source="test",
            context={},  # Keine Runbooks
        )

        msg = mock_email_channel._build_email(alert)
        parts = msg.get_payload()

        # Plain-Text-Teil (möglicherweise base64-codiert)
        plain_payload = parts[0].get_payload()
        if parts[0].get("Content-Transfer-Encoding") == "base64":
            plain_text = base64.b64decode(plain_payload).decode("utf-8")
        else:
            plain_text = plain_payload

        # Sollte keine Runbooks-Sektion haben
        assert "📋 Runbooks:" not in plain_text

    def test_context_preserved_with_runbooks(self):
        """Testet dass vorhandener Context mit Runbooks erweitert wird."""
        sent_alerts: list[AlertMessage] = []

        class CaptureChannel:
            name = "capture"
            is_enabled = True
            min_severity = AlertSeverity.INFO

            def send(self, alert: AlertMessage) -> None:
                sent_alerts.append(alert)

        manager = AlertPipelineManager([CaptureChannel()], persist_alerts=False)

        # Alert mit vorhandenem Context
        alert = AlertMessage(
            title="Test",
            body="Body",
            severity=AlertSeverity.WARN,
            category=AlertCategory.RISK,
            source="live_risk_severity",
            context={"existing_key": "existing_value", "number": 42},
        )
        manager.send(alert)

        # Prüfe dass vorhandener Context erhalten bleibt
        assert sent_alerts[0].context.get("existing_key") == "existing_value"
        assert sent_alerts[0].context.get("number") == 42
        # Und Runbooks hinzugefügt wurden
        assert "runbooks" in sent_alerts[0].context
