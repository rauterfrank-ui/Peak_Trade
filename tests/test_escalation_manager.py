# tests/test_escalation_manager.py
"""
Tests für Escalation & On-Call Integration (Phase 85)
=====================================================

Tests für:
- EscalationEvent / EscalationTarget Models
- NullEscalationProvider
- PagerDutyLikeProviderStub
- EscalationManager
- build_escalation_manager_from_config
"""
from __future__ import annotations

import logging
from datetime import UTC
from unittest.mock import MagicMock

import pytest

from src.infra.escalation import (
    EscalationEvent,
    EscalationManager,
    EscalationTarget,
    NullEscalationProvider,
    PagerDutyLikeProviderStub,
    build_escalation_manager_from_config,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_critical_event() -> EscalationEvent:
    """Erstellt Sample-CRITICAL-Event."""
    return EscalationEvent(
        alert_id="alert_123",
        severity="CRITICAL",
        alert_type="RISK",
        summary="Risk Severity changed: YELLOW → RED",
        details={"old_status": "yellow", "new_status": "red", "daily_loss": -600.0},
        symbol="BTC/EUR",
        session_id="session_456",
    )


@pytest.fixture
def sample_warn_event() -> EscalationEvent:
    """Erstellt Sample-WARN-Event."""
    return EscalationEvent(
        alert_id="alert_789",
        severity="WARN",
        alert_type="RISK",
        summary="Risk Severity changed: GREEN → YELLOW",
        details={"old_status": "green", "new_status": "yellow"},
    )


@pytest.fixture
def sample_target() -> EscalationTarget:
    """Erstellt Sample-Target."""
    return EscalationTarget(
        name="Primary Risk On-Call",
        provider="pagerduty_stub",
        routing_key="test-routing-key",
        min_severity="CRITICAL",
        enabled=True,
    )


# =============================================================================
# ESCALATION EVENT TESTS
# =============================================================================


class TestEscalationEvent:
    """Tests für EscalationEvent Dataclass."""

    def test_construction(self, sample_critical_event: EscalationEvent):
        """Testet EscalationEvent-Konstruktion."""
        assert sample_critical_event.alert_id == "alert_123"
        assert sample_critical_event.severity == "CRITICAL"
        assert sample_critical_event.alert_type == "RISK"
        assert "YELLOW → RED" in sample_critical_event.summary
        assert sample_critical_event.symbol == "BTC/EUR"
        assert sample_critical_event.session_id == "session_456"

    def test_default_timestamp(self):
        """Testet dass Timestamp automatisch gesetzt wird."""
        event = EscalationEvent(
            alert_id="test",
            severity="WARN",
            alert_type="SYSTEM",
            summary="Test",
        )
        assert event.created_at is not None
        assert event.created_at.tzinfo == UTC

    def test_to_dict(self, sample_critical_event: EscalationEvent):
        """Testet Serialisierung zu Dict."""
        d = sample_critical_event.to_dict()
        assert d["alert_id"] == "alert_123"
        assert d["severity"] == "CRITICAL"
        assert d["alert_type"] == "RISK"
        assert "created_at" in d
        assert isinstance(d["details"], dict)

    def test_from_dict(self):
        """Testet Deserialisierung aus Dict."""
        data = {
            "alert_id": "test_id",
            "severity": "WARN",
            "alert_type": "EXECUTION",
            "summary": "Test Summary",
            "details": {"key": "value"},
            "symbol": "ETH/EUR",
        }
        event = EscalationEvent.from_dict(data)
        assert event.alert_id == "test_id"
        assert event.severity == "WARN"
        assert event.symbol == "ETH/EUR"


# =============================================================================
# ESCALATION TARGET TESTS
# =============================================================================


class TestEscalationTarget:
    """Tests für EscalationTarget Dataclass."""

    def test_construction(self, sample_target: EscalationTarget):
        """Testet EscalationTarget-Konstruktion."""
        assert sample_target.name == "Primary Risk On-Call"
        assert sample_target.provider == "pagerduty_stub"
        assert sample_target.routing_key == "test-routing-key"
        assert sample_target.min_severity == "CRITICAL"
        assert sample_target.enabled is True

    def test_defaults(self):
        """Testet Default-Werte."""
        target = EscalationTarget(name="minimal")
        assert target.provider == "null"
        assert target.routing_key is None
        assert target.min_severity == "CRITICAL"
        assert target.enabled is True

    def test_to_dict(self, sample_target: EscalationTarget):
        """Testet Serialisierung zu Dict."""
        d = sample_target.to_dict()
        assert d["name"] == "Primary Risk On-Call"
        assert d["provider"] == "pagerduty_stub"
        assert d["routing_key"] == "test-routing-key"

    def test_from_dict(self):
        """Testet Deserialisierung aus Dict."""
        data = {
            "name": "Secondary On-Call",
            "provider": "opsgenie",
            "min_severity": "WARN",
        }
        target = EscalationTarget.from_dict(data)
        assert target.name == "Secondary On-Call"
        assert target.provider == "opsgenie"
        assert target.min_severity == "WARN"


# =============================================================================
# NULL PROVIDER TESTS
# =============================================================================


class TestNullEscalationProvider:
    """Tests für NullEscalationProvider."""

    def test_name(self):
        """Testet Provider-Name."""
        provider = NullEscalationProvider()
        assert provider.name == "null"

    def test_send_does_nothing(
        self,
        sample_critical_event: EscalationEvent,
        sample_target: EscalationTarget,
    ):
        """Testet dass send() nichts tut aber nicht crasht."""
        provider = NullEscalationProvider(log_would_escalate=False)
        # Sollte keine Exception werfen
        provider.send(sample_critical_event, sample_target)

    def test_send_logs_when_enabled(
        self,
        sample_critical_event: EscalationEvent,
        sample_target: EscalationTarget,
        caplog,
    ):
        """Testet dass send() loggt wenn aktiviert."""
        provider = NullEscalationProvider(log_would_escalate=True)

        with caplog.at_level(logging.INFO):
            provider.send(sample_critical_event, sample_target)

        assert "NULL-ESCALATION" in caplog.text
        assert "Would escalate" in caplog.text


# =============================================================================
# PAGERDUTY-LIKE STUB PROVIDER TESTS
# =============================================================================


class TestPagerDutyLikeProviderStub:
    """Tests für PagerDutyLikeProviderStub."""

    def test_name(self):
        """Testet Provider-Name."""
        provider = PagerDutyLikeProviderStub()
        assert provider.name == "pagerduty_stub"

    def test_send_stores_payload(
        self,
        sample_critical_event: EscalationEvent,
        sample_target: EscalationTarget,
    ):
        """Testet dass send() Payload speichert."""
        provider = PagerDutyLikeProviderStub()
        assert len(provider.sent_payloads) == 0

        provider.send(sample_critical_event, sample_target)

        assert len(provider.sent_payloads) == 1
        payload = provider.sent_payloads[0]
        assert "routing_key" in payload
        assert "event_action" in payload
        assert payload["event_action"] == "trigger"
        assert "payload" in payload

    def test_payload_structure(
        self,
        sample_critical_event: EscalationEvent,
        sample_target: EscalationTarget,
    ):
        """Testet PagerDuty-Payload-Struktur."""
        provider = PagerDutyLikeProviderStub()
        provider.send(sample_critical_event, sample_target)

        payload = provider.sent_payloads[0]

        # Top-level
        assert payload["routing_key"] == "test-routing-key"
        assert payload["dedup_key"] == "peak_trade_alert_123"

        # Payload-Sektion
        inner = payload["payload"]
        assert inner["severity"] == "critical"
        assert inner["source"] == "peak_trade:risk"
        assert "timestamp" in inner
        assert "custom_details" in inner

        # Custom details
        details = inner["custom_details"]
        assert details["alert_id"] == "alert_123"
        assert details["symbol"] == "BTC/EUR"

    def test_severity_mapping(self):
        """Testet Severity-Mapping."""
        provider = PagerDutyLikeProviderStub()
        target = EscalationTarget(name="test")

        # CRITICAL → critical
        event = EscalationEvent(
            alert_id="1", severity="CRITICAL", alert_type="RISK", summary="Test"
        )
        provider.send(event, target)
        assert provider.sent_payloads[-1]["payload"]["severity"] == "critical"

        # WARN → warning
        event = EscalationEvent(
            alert_id="2", severity="WARN", alert_type="RISK", summary="Test"
        )
        provider.send(event, target)
        assert provider.sent_payloads[-1]["payload"]["severity"] == "warning"

        # INFO → info
        event = EscalationEvent(
            alert_id="3", severity="INFO", alert_type="RISK", summary="Test"
        )
        provider.send(event, target)
        assert provider.sent_payloads[-1]["payload"]["severity"] == "info"

    def test_clear_sent_payloads(
        self,
        sample_critical_event: EscalationEvent,
        sample_target: EscalationTarget,
    ):
        """Testet clear_sent_payloads()."""
        provider = PagerDutyLikeProviderStub()
        provider.send(sample_critical_event, sample_target)
        assert len(provider.sent_payloads) == 1

        provider.clear_sent_payloads()
        assert len(provider.sent_payloads) == 0

    def test_no_real_calls_by_default(
        self,
        sample_critical_event: EscalationEvent,
        sample_target: EscalationTarget,
        caplog,
    ):
        """Testet dass keine echten API-Calls gemacht werden."""
        provider = PagerDutyLikeProviderStub(
            api_url="https://events.pagerduty.com/v2/enqueue",
            enable_real_calls=True,  # Aktiviert, aber Phase 85 macht trotzdem keine Calls
        )

        with caplog.at_level(logging.WARNING):
            provider.send(sample_critical_event, sample_target)

        # Warnung dass real calls nicht implementiert sind
        assert "not implemented in Phase 85" in caplog.text


# =============================================================================
# ESCALATION MANAGER TESTS
# =============================================================================


class TestEscalationManager:
    """Tests für EscalationManager."""

    def test_disabled_globally(
        self,
        sample_critical_event: EscalationEvent,
        sample_target: EscalationTarget,
    ):
        """Testet dass Manager nichts tut wenn global deaktiviert."""
        provider = PagerDutyLikeProviderStub()
        manager = EscalationManager(
            provider=provider,
            targets=[sample_target],
            enabled=False,  # Deaktiviert
            current_environment="live",
        )

        result = manager.maybe_escalate(sample_critical_event)

        assert result is False
        assert len(provider.sent_payloads) == 0

    def test_wrong_environment(
        self,
        sample_critical_event: EscalationEvent,
        sample_target: EscalationTarget,
    ):
        """Testet dass Manager nichts tut in falscher Umgebung."""
        provider = PagerDutyLikeProviderStub()
        manager = EscalationManager(
            provider=provider,
            targets=[sample_target],
            enabled=True,
            enabled_environments={"live"},  # Nur live
            current_environment="paper",  # Aber wir sind in paper
        )

        result = manager.maybe_escalate(sample_critical_event)

        assert result is False
        assert len(provider.sent_payloads) == 0

    def test_non_critical_severity(
        self,
        sample_warn_event: EscalationEvent,
        sample_target: EscalationTarget,
    ):
        """Testet dass non-critical Events nicht eskaliert werden."""
        provider = PagerDutyLikeProviderStub()
        manager = EscalationManager(
            provider=provider,
            targets=[sample_target],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},  # Nur CRITICAL
            current_environment="live",
        )

        result = manager.maybe_escalate(sample_warn_event)  # WARN Event

        assert result is False
        assert len(provider.sent_payloads) == 0

    def test_critical_in_live_escalates(
        self,
        sample_critical_event: EscalationEvent,
        sample_target: EscalationTarget,
    ):
        """Testet dass CRITICAL in live eskaliert wird."""
        provider = PagerDutyLikeProviderStub()
        manager = EscalationManager(
            provider=provider,
            targets=[sample_target],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},
            current_environment="live",
        )

        result = manager.maybe_escalate(sample_critical_event)

        assert result is True
        assert len(provider.sent_payloads) == 1

    def test_provider_error_does_not_raise(
        self,
        sample_critical_event: EscalationEvent,
        sample_target: EscalationTarget,
    ):
        """Testet dass Provider-Fehler nicht nach außen propagieren."""
        provider = MagicMock()
        provider.send.side_effect = Exception("Provider failed!")

        manager = EscalationManager(
            provider=provider,
            targets=[sample_target],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},
            current_environment="live",
        )

        # Sollte NICHT crashen
        result = manager.maybe_escalate(sample_critical_event)

        assert result is False  # Keine erfolgreiche Eskalation
        provider.send.assert_called_once()

    def test_multiple_targets(self, sample_critical_event: EscalationEvent):
        """Testet dass mehrere Targets eskaliert werden."""
        provider = PagerDutyLikeProviderStub()
        target1 = EscalationTarget(name="Primary", min_severity="CRITICAL")
        target2 = EscalationTarget(name="Secondary", min_severity="CRITICAL")

        manager = EscalationManager(
            provider=provider,
            targets=[target1, target2],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},
            current_environment="live",
        )

        result = manager.maybe_escalate(sample_critical_event)

        assert result is True
        assert len(provider.sent_payloads) == 2

    def test_target_disabled(
        self,
        sample_critical_event: EscalationEvent,
    ):
        """Testet dass deaktivierte Targets übersprungen werden."""
        provider = PagerDutyLikeProviderStub()
        enabled_target = EscalationTarget(name="Enabled", enabled=True)
        disabled_target = EscalationTarget(name="Disabled", enabled=False)

        manager = EscalationManager(
            provider=provider,
            targets=[enabled_target, disabled_target],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},
            current_environment="live",
        )

        result = manager.maybe_escalate(sample_critical_event)

        assert result is True
        assert len(provider.sent_payloads) == 1

    def test_target_severity_filtering(
        self,
        sample_warn_event: EscalationEvent,
    ):
        """Testet dass Target-min_severity respektiert wird."""
        provider = PagerDutyLikeProviderStub()
        warn_target = EscalationTarget(name="Warn", min_severity="WARN")
        critical_target = EscalationTarget(name="Critical", min_severity="CRITICAL")

        manager = EscalationManager(
            provider=provider,
            targets=[warn_target, critical_target],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"WARN", "CRITICAL"},  # WARN erlaubt
            current_environment="live",
        )

        result = manager.maybe_escalate(sample_warn_event)

        assert result is True
        # Nur warn_target sollte eskaliert werden
        assert len(provider.sent_payloads) == 1


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================


class TestBuildEscalationManagerFromConfig:
    """Tests für build_escalation_manager_from_config Factory."""

    def test_disabled_config(self):
        """Testet dass deaktivierte Config Null-Provider verwendet."""
        config = {
            "escalation": {
                "enabled": False,
            }
        }
        manager = build_escalation_manager_from_config(config)

        assert manager.enabled is False

    def test_default_config(self):
        """Testet Default-Konfiguration."""
        config = {
            "escalation": {
                "enabled": True,
                "enabled_environments": ["live"],
                "provider": "null",
                "critical_severities": ["CRITICAL"],
            }
        }
        manager = build_escalation_manager_from_config(config)

        assert manager.enabled is True
        assert manager.enabled_environments == {"live"}
        assert manager.critical_severities == {"CRITICAL"}

    def test_environment_from_config(self):
        """Testet Environment aus Config."""
        config = {
            "environment": {"mode": "testnet"},
            "escalation": {
                "enabled": True,
            },
        }
        manager = build_escalation_manager_from_config(config)

        assert manager.current_environment == "testnet"

    def test_environment_override(self):
        """Testet Environment-Override."""
        config = {
            "environment": {"mode": "paper"},
            "escalation": {
                "enabled": True,
            },
        }
        manager = build_escalation_manager_from_config(config, environment="live")

        assert manager.current_environment == "live"

    def test_targets_from_config(self):
        """Testet Target-Erstellung aus Config."""
        config = {
            "escalation": {
                "enabled": True,
                "provider": "pagerduty_stub",
                "targets": {
                    "primary": {
                        "name": "Primary On-Call",
                        "provider": "pagerduty_stub",
                        "routing_key": "key123",
                        "min_severity": "CRITICAL",
                        "enabled": True,
                    },
                    "secondary": {
                        "name": "Secondary On-Call",
                        "min_severity": "WARN",
                        "enabled": False,
                    },
                },
            },
        }
        manager = build_escalation_manager_from_config(config)

        # Manager sollte 2 Targets haben
        assert len(manager._targets) == 2

    def test_pagerduty_provider_from_config(self):
        """Testet PagerDuty-Provider-Erstellung."""
        config = {
            "escalation": {
                "enabled": True,
                "provider": "pagerduty_stub",
                "providers": {
                    "pagerduty_stub": {
                        "api_url": "https://events.pagerduty.com/v2/enqueue",
                        "enable_real_calls": False,
                    },
                },
            },
        }
        manager = build_escalation_manager_from_config(config)

        # Provider sollte PagerDutyLikeProviderStub sein
        assert isinstance(manager._provider, PagerDutyLikeProviderStub)


# =============================================================================
# ACCEPTANCE CRITERIA TESTS
# =============================================================================


class TestPhase85AcceptanceCriteria:
    """
    Tests für Phase 85 Akzeptanzkriterien.

    1. Non-critical Severity → keine Eskalation
    2. Critical Severity in disabled Environment → keine Eskalation
    3. Critical Severity in enabled Environment → Provider wird aufgerufen
    4. Provider wirft Exception → Error wird geschluckt, keine Propagation
    """

    def test_ac1_non_critical_no_escalation(self):
        """AC1: Non-critical Severity → keine Eskalation."""
        provider = PagerDutyLikeProviderStub()
        manager = EscalationManager(
            provider=provider,
            targets=[EscalationTarget(name="test")],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},
            current_environment="live",
        )

        event = EscalationEvent(
            alert_id="1",
            severity="WARN",  # Nicht CRITICAL
            alert_type="RISK",
            summary="Test",
        )
        result = manager.maybe_escalate(event)

        assert result is False
        assert len(provider.sent_payloads) == 0

    def test_ac2_critical_in_disabled_environment_no_escalation(self):
        """AC2: Critical in disabled Environment → keine Eskalation."""
        provider = PagerDutyLikeProviderStub()
        manager = EscalationManager(
            provider=provider,
            targets=[EscalationTarget(name="test")],
            enabled=True,
            enabled_environments={"live"},  # Nur live
            critical_severities={"CRITICAL"},
            current_environment="paper",  # Aber paper
        )

        event = EscalationEvent(
            alert_id="1",
            severity="CRITICAL",
            alert_type="RISK",
            summary="Test",
        )
        result = manager.maybe_escalate(event)

        assert result is False
        assert len(provider.sent_payloads) == 0

    def test_ac3_critical_in_enabled_environment_escalates(self):
        """AC3: Critical in enabled Environment → Provider aufgerufen."""
        provider = PagerDutyLikeProviderStub()
        manager = EscalationManager(
            provider=provider,
            targets=[EscalationTarget(name="test", routing_key="key123")],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},
            current_environment="live",
        )

        event = EscalationEvent(
            alert_id="test_alert",
            severity="CRITICAL",
            alert_type="RISK",
            summary="Critical Alert",
        )
        result = manager.maybe_escalate(event)

        assert result is True
        assert len(provider.sent_payloads) == 1
        assert provider.sent_payloads[0]["dedup_key"] == "peak_trade_test_alert"

    def test_ac4_provider_exception_swallowed(self):
        """AC4: Provider-Exception wird geschluckt."""
        provider = MagicMock()
        provider.send.side_effect = RuntimeError("Provider crashed!")

        manager = EscalationManager(
            provider=provider,
            targets=[EscalationTarget(name="test")],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},
            current_environment="live",
        )

        event = EscalationEvent(
            alert_id="1",
            severity="CRITICAL",
            alert_type="RISK",
            summary="Test",
        )

        # MUSS ohne Exception durchlaufen
        result = manager.maybe_escalate(event)

        # Eskalation fehlgeschlagen, aber keine Exception
        assert result is False
        provider.send.assert_called_once()



