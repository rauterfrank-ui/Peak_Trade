"""
Tests for telemetry alerting system (Phase 16I).
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.execution.alerting.models import AlertSeverity, AlertEvent
from src.execution.alerting.rules import (
    AlertRule,
    RuleType,
    rule_health_check_critical,
    rule_degradation_detected,
    rule_leading_indicator_disk_growth,
    DEFAULT_RULES,
)
from src.execution.alerting.engine import AlertEngine
from src.execution.alerting.adapters import ConsoleAlertSink, WebhookAlertSink
from src.execution.alerting.persistence import AlertStore


# =============================================================================
# MODELS TESTS
# =============================================================================

def test_alert_severity_priority():
    """Test alert severity priority ordering."""
    assert AlertSeverity.CRITICAL.priority > AlertSeverity.WARN.priority
    assert AlertSeverity.WARN.priority > AlertSeverity.INFO.priority


def test_alert_event_creation():
    """Test creating an alert event."""
    alert = AlertEvent(
        source="test",
        severity=AlertSeverity.WARN,
        title="Test Alert",
        body="This is a test alert",
    )
    
    assert alert.source == "test"
    assert alert.severity == AlertSeverity.WARN
    assert alert.title == "Test Alert"
    assert alert.body == "This is a test alert"
    assert alert.dedupe_key == "test:Test Alert"
    assert isinstance(alert.timestamp_utc, datetime)


def test_alert_event_to_dict():
    """Test alert event serialization."""
    alert = AlertEvent(
        source="test",
        severity=AlertSeverity.CRITICAL,
        title="Critical Test",
        body="Critical test body",
        labels={"env": "test"},
    )
    
    data = alert.to_dict()
    
    assert data["source"] == "test"
    assert data["severity"] == "critical"
    assert data["title"] == "Critical Test"
    assert data["labels"]["env"] == "test"


def test_alert_event_from_dict():
    """Test alert event deserialization."""
    data = {
        "id": "test-123",
        "timestamp_utc": "2025-12-20T10:00:00+00:00",
        "source": "test",
        "severity": "warn",
        "title": "Test",
        "body": "Test body",
        "labels": {},
        "dedupe_key": "test:Test",
    }
    
    alert = AlertEvent.from_dict(data)
    
    assert alert.id == "test-123"
    assert alert.source == "test"
    assert alert.severity == AlertSeverity.WARN


def test_alert_event_format_console():
    """Test console formatting."""
    alert = AlertEvent(
        source="test",
        severity=AlertSeverity.INFO,
        title="Info Alert",
        body="Info body",
    )
    
    output = alert.format_console()
    
    assert "Info Alert" in output
    assert "test" in output
    assert "Info body" in output


# =============================================================================
# RULES TESTS
# =============================================================================

def test_rule_health_check_critical():
    """Test health check critical rule."""
    context_ok = {"health_report": {"status": "ok"}}
    context_critical = {"health_report": {"status": "critical"}}
    
    assert not rule_health_check_critical(context_ok)
    assert rule_health_check_critical(context_critical)


def test_rule_degradation_detected():
    """Test degradation detection rule."""
    context_ok = {"degradation": {"degrading": False}}
    context_degrading = {"degradation": {"degrading": True}}
    
    assert not rule_degradation_detected(context_ok)
    assert rule_degradation_detected(context_degrading)


def test_rule_leading_indicator_disk_growth():
    """Test leading indicator disk growth rule."""
    context_ok = {"degradation": {"reasons": []}}
    context_growth = {
        "degradation": {"reasons": ["Disk usage increasing (100 → 200 MB)"]}
    }
    
    assert not rule_leading_indicator_disk_growth(context_ok)
    assert rule_leading_indicator_disk_growth(context_growth)


def test_alert_rule_evaluate():
    """Test alert rule evaluation."""
    rule = AlertRule(
        rule_id="test_rule",
        enabled=True,
        rule_type=RuleType.HEALTH_CHECK,
        severity=AlertSeverity.WARN,
        title_template="Test Alert",
        body_template="Test body",
        predicate=lambda ctx: ctx.get("trigger", False),
    )
    
    context_no_trigger = {"trigger": False}
    context_trigger = {"trigger": True}
    
    # Should not fire
    alert = rule.evaluate(context_no_trigger)
    assert alert is None
    
    # Should fire
    alert = rule.evaluate(context_trigger)
    assert alert is not None
    assert alert.severity == AlertSeverity.WARN
    assert alert.title == "Test Alert"


def test_alert_rule_disabled():
    """Test disabled rule doesn't fire."""
    rule = AlertRule(
        rule_id="disabled_rule",
        enabled=False,
        rule_type=RuleType.HEALTH_CHECK,
        severity=AlertSeverity.WARN,
        title_template="Test",
        body_template="Test",
        predicate=lambda ctx: True,  # Always true
    )
    
    alert = rule.evaluate({})
    assert alert is None


def test_default_rules_exist():
    """Test that default rules are defined."""
    assert len(DEFAULT_RULES) > 0
    
    rule_ids = [r.rule_id for r in DEFAULT_RULES]
    assert "health_critical" in rule_ids
    assert "degradation_detected" in rule_ids


# =============================================================================
# ENGINE TESTS
# =============================================================================

def test_alert_engine_creation():
    """Test alert engine creation."""
    engine = AlertEngine(max_alerts_per_run=10)
    
    assert engine.max_alerts_per_run == 10
    assert len(engine.rules) > 0


def test_alert_engine_evaluate_no_alerts():
    """Test engine evaluation with no alerts."""
    engine = AlertEngine(rules=[])
    
    alerts = engine.evaluate(health_report={"status": "ok"})
    
    assert alerts == []


def test_alert_engine_evaluate_with_alert():
    """Test engine evaluation that triggers an alert."""
    rule = AlertRule(
        rule_id="test_rule",
        enabled=True,
        rule_type=RuleType.HEALTH_CHECK,
        severity=AlertSeverity.CRITICAL,
        title_template="Critical Health",
        body_template="Health status: {health_status}",
        predicate=lambda ctx: ctx.get("health_status") == "critical",
    )
    
    engine = AlertEngine(rules=[rule])
    
    health_report = {"status": "critical", "exit_code": 3, "checks": []}
    
    alerts = engine.evaluate(health_report=health_report)
    
    assert len(alerts) == 1
    assert alerts[0].severity == AlertSeverity.CRITICAL
    assert "Critical Health" in alerts[0].title


def test_alert_engine_cooldown():
    """Test engine cooldown logic."""
    rule = AlertRule(
        rule_id="cooldown_test",
        enabled=True,
        rule_type=RuleType.HEALTH_CHECK,
        severity=AlertSeverity.WARN,
        title_template="Cooldown Test",
        body_template="Test",
        predicate=lambda ctx: True,  # Always fires
        cooldown_seconds=60,  # 1 minute
    )
    
    engine = AlertEngine(rules=[rule])
    
    # First evaluation - should fire
    alerts1 = engine.evaluate(health_report={"status": "critical"})
    assert len(alerts1) == 1
    
    # Second evaluation immediately - should not fire (cooldown)
    alerts2 = engine.evaluate(health_report={"status": "critical"})
    assert len(alerts2) == 0


def test_alert_engine_dedupe():
    """Test engine deduplication logic."""
    rule = AlertRule(
        rule_id="dedupe_test",
        enabled=True,
        rule_type=RuleType.HEALTH_CHECK,
        severity=AlertSeverity.WARN,
        title_template="Dedupe Test",
        body_template="Test",
        predicate=lambda ctx: True,
        cooldown_seconds=0,  # No cooldown
        dedupe_window_seconds=60,  # 1 minute dedupe
    )
    
    engine = AlertEngine(rules=[rule])
    
    # First evaluation - should fire
    alerts1 = engine.evaluate(health_report={"status": "critical"})
    assert len(alerts1) == 1
    
    # Clear cooldown state but not dedupe
    engine._last_fire_by_rule_id.clear()
    
    # Second evaluation - should not fire (dedupe)
    alerts2 = engine.evaluate(health_report={"status": "critical"})
    assert len(alerts2) == 0


def test_alert_engine_rate_limiting():
    """Test engine rate limiting."""
    # Create multiple rules that all fire
    rules = [
        AlertRule(
            rule_id=f"rule_{i}",
            enabled=True,
            rule_type=RuleType.HEALTH_CHECK,
            severity=AlertSeverity.WARN,
            title_template=f"Alert {i}",
            body_template="Test",
            predicate=lambda ctx: True,
        )
        for i in range(30)
    ]
    
    engine = AlertEngine(rules=rules, max_alerts_per_run=10)
    
    alerts = engine.evaluate(health_report={"status": "critical"})
    
    # Should be limited to 10
    assert len(alerts) == 10


def test_alert_engine_severity_ordering():
    """Test that alerts are ordered by severity."""
    rules = [
        AlertRule(
            rule_id="info_rule",
            enabled=True,
            rule_type=RuleType.HEALTH_CHECK,
            severity=AlertSeverity.INFO,
            title_template="Info",
            body_template="Info",
            predicate=lambda ctx: True,
        ),
        AlertRule(
            rule_id="critical_rule",
            enabled=True,
            rule_type=RuleType.HEALTH_CHECK,
            severity=AlertSeverity.CRITICAL,
            title_template="Critical",
            body_template="Critical",
            predicate=lambda ctx: True,
        ),
        AlertRule(
            rule_id="warn_rule",
            enabled=True,
            rule_type=RuleType.HEALTH_CHECK,
            severity=AlertSeverity.WARN,
            title_template="Warn",
            body_template="Warn",
            predicate=lambda ctx: True,
        ),
    ]
    
    engine = AlertEngine(rules=rules)
    
    alerts = engine.evaluate(health_report={"status": "critical"})
    
    # Should be ordered: critical, warn, info
    assert len(alerts) == 3
    assert alerts[0].severity == AlertSeverity.CRITICAL
    assert alerts[1].severity == AlertSeverity.WARN
    assert alerts[2].severity == AlertSeverity.INFO


def test_alert_engine_enable_disable_rule():
    """Test enabling/disabling rules."""
    engine = AlertEngine(rules=DEFAULT_RULES.copy())
    
    # Disable a rule
    engine.disable_rule("health_critical")
    rule = engine.get_rule_by_id("health_critical")
    assert not rule.enabled
    
    # Enable it back
    engine.enable_rule("health_critical")
    rule = engine.get_rule_by_id("health_critical")
    assert rule.enabled


# =============================================================================
# ADAPTERS TESTS
# =============================================================================

def test_console_sink_send():
    """Test console sink sends alerts."""
    sink = ConsoleAlertSink(color=False)
    
    alert = AlertEvent(
        source="test",
        severity=AlertSeverity.WARN,
        title="Test Alert",
        body="Test body",
    )
    
    success = sink.send(alert)
    assert success


def test_webhook_sink_disabled():
    """Test webhook sink respects enabled flag."""
    sink = WebhookAlertSink(
        url="https://example.com/webhook",
        enabled=False,
    )
    
    alert = AlertEvent(
        source="test",
        severity=AlertSeverity.WARN,
        title="Test",
        body="Test",
    )
    
    # Should return False (disabled)
    success = sink.send(alert)
    assert not success


def test_webhook_sink_no_url():
    """Test webhook sink handles missing URL."""
    sink = WebhookAlertSink(
        url="",
        enabled=True,
    )
    
    alert = AlertEvent(
        source="test",
        severity=AlertSeverity.WARN,
        title="Test",
        body="Test",
    )
    
    # Should return False (no URL)
    success = sink.send(alert)
    assert not success


# =============================================================================
# PERSISTENCE TESTS
# =============================================================================

def test_alert_store_add_and_get():
    """Test alert store add and get."""
    store = AlertStore(max_size=10)
    
    alert = AlertEvent(
        source="test",
        severity=AlertSeverity.WARN,
        title="Test",
        body="Test",
    )
    
    store.add(alert)
    
    latest = store.get_latest(limit=5)
    assert len(latest) == 1
    assert latest[0].title == "Test"


def test_alert_store_get_by_severity():
    """Test alert store filtering by severity."""
    store = AlertStore(max_size=10)
    
    alert1 = AlertEvent(source="test", severity=AlertSeverity.WARN, title="Warn", body="Warn")
    alert2 = AlertEvent(source="test", severity=AlertSeverity.CRITICAL, title="Critical", body="Critical")
    
    store.add(alert1)
    store.add(alert2)
    
    critical_alerts = store.get_by_severity("critical", limit=5)
    assert len(critical_alerts) == 1
    assert critical_alerts[0].severity == AlertSeverity.CRITICAL


def test_alert_store_max_size():
    """Test alert store respects max size."""
    store = AlertStore(max_size=5)
    
    for i in range(10):
        alert = AlertEvent(
            source="test",
            severity=AlertSeverity.INFO,
            title=f"Alert {i}",
            body="Test",
        )
        store.add(alert)
    
    latest = store.get_latest(limit=100)
    
    # Should only keep last 5
    assert len(latest) == 5


def test_alert_store_clear():
    """Test alert store clear."""
    store = AlertStore(max_size=10)
    
    for i in range(5):
        alert = AlertEvent(
            source="test",
            severity=AlertSeverity.INFO,
            title=f"Alert {i}",
            body="Test",
        )
        store.add(alert)
    
    assert len(store.get_latest(limit=100)) == 5
    
    store.clear()
    
    assert len(store.get_latest(limit=100)) == 0
