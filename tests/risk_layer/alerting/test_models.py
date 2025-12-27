"""
Tests for Risk Layer Alert Models
==================================
"""

from datetime import datetime, timezone

import pytest

from src.risk_layer.alerting.models import AlertSeverity, AlertEvent


def test_alert_severity_priority():
    """Test alert severity priority ordering."""
    assert AlertSeverity.CRITICAL.priority > AlertSeverity.WARN.priority
    assert AlertSeverity.WARN.priority > AlertSeverity.INFO.priority


def test_alert_event_creation():
    """Test creating an alert event."""
    alert = AlertEvent(
        source="risk_gate",
        severity=AlertSeverity.WARN,
        title="Test Alert",
        body="This is a test alert",
    )

    assert alert.source == "risk_gate"
    assert alert.severity == AlertSeverity.WARN
    assert alert.title == "Test Alert"
    assert alert.body == "This is a test alert"
    assert isinstance(alert.timestamp_utc, datetime)
    assert alert.id is not None


def test_alert_event_with_labels():
    """Test alert event with labels."""
    alert = AlertEvent(
        source="var_gate",
        severity=AlertSeverity.CRITICAL,
        title="VaR Breach",
        body="Portfolio VaR exceeded threshold",
        labels={"portfolio": "main", "threshold": "95%"},
    )

    assert alert.labels["portfolio"] == "main"
    assert alert.labels["threshold"] == "95%"


def test_alert_event_to_dict():
    """Test alert event serialization."""
    alert = AlertEvent(
        source="kill_switch",
        severity=AlertSeverity.CRITICAL,
        title="Kill Switch Activated",
        body="Emergency shutdown triggered",
        labels={"reason": "drawdown_limit"},
    )

    data = alert.to_dict()

    assert data["source"] == "kill_switch"
    assert data["severity"] == "critical"
    assert data["title"] == "Kill Switch Activated"
    assert data["labels"]["reason"] == "drawdown_limit"
    assert "timestamp_utc" in data


def test_alert_event_from_dict():
    """Test alert event deserialization."""
    data = {
        "id": "test-123",
        "timestamp_utc": "2025-12-20T10:00:00+00:00",
        "source": "stress_gate",
        "severity": "warn",
        "title": "Stress Test Warning",
        "body": "Stress scenario approaching threshold",
        "labels": {"scenario": "market_crash"},
    }

    alert = AlertEvent.from_dict(data)

    assert alert.id == "test-123"
    assert alert.source == "stress_gate"
    assert alert.severity == AlertSeverity.WARN
    assert alert.title == "Stress Test Warning"
    assert alert.labels["scenario"] == "market_crash"


def test_alert_event_format_console():
    """Test console formatting."""
    alert = AlertEvent(
        source="liquidity_gate",
        severity=AlertSeverity.INFO,
        title="Liquidity Check",
        body="Sufficient liquidity available",
    )

    output = alert.format_console()

    assert "Liquidity Check" in output
    assert "liquidity_gate" in output
    assert "INFO" in output


def test_alert_event_string_severity():
    """Test that string severity is converted to enum."""
    alert = AlertEvent(
        source="test",
        severity="critical",  # String instead of enum
        title="Test",
        body="Test body",
    )

    assert isinstance(alert.severity, AlertSeverity)
    assert alert.severity == AlertSeverity.CRITICAL


def test_alert_event_with_metadata():
    """Test alert with metadata."""
    metadata = {
        "position_size": 1000,
        "limit": 800,
        "breach_percent": 25.0,
    }

    alert = AlertEvent(
        source="position_sizer",
        severity=AlertSeverity.WARN,
        title="Position Size Warning",
        body="Position approaching limit",
        metadata=metadata,
    )

    assert alert.metadata["position_size"] == 1000
    assert alert.metadata["limit"] == 800
    assert alert.metadata["breach_percent"] == 25.0
