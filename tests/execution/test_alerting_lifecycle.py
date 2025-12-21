"""
Tests for telemetry alerting lifecycle (Phase 16J).
"""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.execution.alerting.models import AlertSeverity, AlertEvent
from src.execution.alerting.history import AlertHistory
from src.execution.alerting.operator_state import OperatorState, OperatorAction
from src.execution.alerting.engine import AlertEngine
from src.execution.alerting.rules import AlertRule, RuleType


# =============================================================================
# ALERT HISTORY TESTS
# =============================================================================


def test_alert_history_append():
    """Test appending alerts to history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "alerts_history.jsonl"
        history = AlertHistory(history_path=history_path, enabled=True)

        alert = AlertEvent(
            source="test",
            severity=AlertSeverity.WARN,
            title="Test Alert",
            body="Test body",
        )

        success = history.append(alert, delivery_status="sent")

        assert success
        assert history_path.exists()

        # Verify JSONL content
        with open(history_path, "r") as f:
            lines = f.readlines()

        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["title"] == "Test Alert"
        assert entry["delivery_status"] == "sent"


def test_alert_history_query():
    """Test querying alert history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "alerts_history.jsonl"
        history = AlertHistory(history_path=history_path, enabled=True)

        # Add multiple alerts
        for i in range(5):
            alert = AlertEvent(
                source="test",
                severity=AlertSeverity.WARN if i % 2 == 0 else AlertSeverity.CRITICAL,
                title=f"Alert {i}",
                body="Test",
            )
            history.append(alert)

        # Query all
        results = history.query()
        assert len(results) == 5

        # Query by severity
        warn_results = history.query(severity="warn")
        assert len(warn_results) == 3

        critical_results = history.query(severity="critical")
        assert len(critical_results) == 2


def test_alert_history_query_with_time_filter():
    """Test querying with time filters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "alerts_history.jsonl"
        history = AlertHistory(history_path=history_path, enabled=True)

        now = datetime.now(timezone.utc)

        # Add alerts with different timestamps
        for i in range(5):
            alert = AlertEvent(
                source="test",
                severity=AlertSeverity.WARN,
                title=f"Alert {i}",
                body="Test",
            )
            alert.timestamp_utc = now - timedelta(days=i)
            history.append(alert)

        # Query last 2 days
        since = now - timedelta(days=2)
        results = history.query(since=since)

        assert len(results) <= 3  # Days 0, 1, 2


def test_alert_history_cleanup_old():
    """Test cleaning up old history entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "alerts_history.jsonl"
        history = AlertHistory(history_path=history_path, retain_days=7, enabled=True)

        now = datetime.now(timezone.utc)

        # Add old and recent alerts
        for i in range(10):
            alert = AlertEvent(
                source="test",
                severity=AlertSeverity.WARN,
                title=f"Alert {i}",
                body="Test",
            )
            alert.timestamp_utc = now - timedelta(days=i)
            history.append(alert)

        # Cleanup (keep last 7 days)
        removed = history.cleanup_old()

        assert removed > 0

        # Verify
        results = history.query()
        assert len(results) <= 8  # Days 0-7


def test_alert_history_get_stats():
    """Test getting alert statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "alerts_history.jsonl"
        history = AlertHistory(history_path=history_path, enabled=True)

        # Add alerts
        for i in range(10):
            alert = AlertEvent(
                source="test",
                severity=AlertSeverity.WARN if i < 7 else AlertSeverity.CRITICAL,
                title=f"Alert {i}",
                body="Test",
                labels={"rule_id": "test_rule" if i < 5 else "other_rule"},
            )
            history.append(alert, delivery_status="sent" if i % 2 == 0 else "failed")

        stats = history.get_stats()

        assert stats["total"] == 10
        assert stats["by_severity"]["warn"] == 7
        assert stats["by_severity"]["critical"] == 3
        assert "test_rule" in stats["by_rule"]
        assert "other_rule" in stats["by_rule"]
        assert "sent" in stats["by_status"]
        assert "failed" in stats["by_status"]


# =============================================================================
# OPERATOR STATE TESTS
# =============================================================================


def test_operator_state_ack():
    """Test acknowledging alerts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"
        state = OperatorState(state_path=state_path, enabled=True)

        success = state.ack("test_dedupe_key", ttl_seconds=3600)

        assert success
        assert state.is_acked("test_dedupe_key", severity="warn")
        assert state_path.exists()


def test_operator_state_ack_critical_bypass():
    """Test that CRITICAL alerts bypass ACK by default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"
        state = OperatorState(state_path=state_path, enabled=True, suppress_critical_on_ack=False)

        state.ack("test_dedupe_key")

        # WARN should be acked
        assert state.is_acked("test_dedupe_key", severity="warn")

        # CRITICAL should bypass ACK
        assert not state.is_acked("test_dedupe_key", severity="critical")


def test_operator_state_ack_critical_suppression():
    """Test that CRITICAL can be suppressed if configured."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"
        state = OperatorState(state_path=state_path, enabled=True, suppress_critical_on_ack=True)

        state.ack("test_dedupe_key")

        # Both should be acked
        assert state.is_acked("test_dedupe_key", severity="warn")
        assert state.is_acked("test_dedupe_key", severity="critical")


def test_operator_state_ack_ttl_expiry():
    """Test ACK TTL expiry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"
        state = OperatorState(state_path=state_path, enabled=True)

        # ACK with 1 second TTL
        state.ack("test_dedupe_key", ttl_seconds=1)

        # Should be acked immediately
        assert state.is_acked("test_dedupe_key", severity="warn")

        # Wait for expiry
        import time

        time.sleep(1.5)

        # Should be expired
        assert not state.is_acked("test_dedupe_key", severity="warn")


def test_operator_state_snooze():
    """Test snoozing rules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"
        state = OperatorState(state_path=state_path, enabled=True)

        success = state.snooze("test_rule", ttl_seconds=3600)

        assert success
        assert state.is_snoozed("test_rule")


def test_operator_state_unsnooze():
    """Test unsnoozing rules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"
        state = OperatorState(state_path=state_path, enabled=True)

        state.snooze("test_rule", ttl_seconds=3600)
        assert state.is_snoozed("test_rule")

        state.unsnooze("test_rule")
        assert not state.is_snoozed("test_rule")


def test_operator_state_snooze_ttl_expiry():
    """Test snooze TTL expiry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"
        state = OperatorState(state_path=state_path, enabled=True)

        # Snooze with 1 second TTL
        state.snooze("test_rule", ttl_seconds=1)

        # Should be snoozed immediately
        assert state.is_snoozed("test_rule")

        # Wait for expiry
        import time

        time.sleep(1.5)

        # Should be expired
        assert not state.is_snoozed("test_rule")


def test_operator_state_persistence():
    """Test state persistence across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"

        # Create state and ACK
        state1 = OperatorState(state_path=state_path, enabled=True)
        state1.ack("test_dedupe_key")
        state1.snooze("test_rule", ttl_seconds=3600)

        # Create new instance and verify
        state2 = OperatorState(state_path=state_path, enabled=True)

        assert state2.is_acked("test_dedupe_key", severity="warn")
        assert state2.is_snoozed("test_rule")


def test_operator_state_disabled():
    """Test that operator state is disabled by default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"
        state = OperatorState(state_path=state_path, enabled=False)

        # ACK should fail
        success = state.ack("test_dedupe_key")
        assert not success

        # Check should return False
        assert not state.is_acked("test_dedupe_key", severity="warn")


# =============================================================================
# ENGINE INTEGRATION TESTS
# =============================================================================


def test_engine_with_operator_state_snooze():
    """Test engine respects snoozed rules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"
        operator_state = OperatorState(state_path=state_path, enabled=True)

        # Create rule
        rule = AlertRule(
            rule_id="test_rule",
            enabled=True,
            rule_type=RuleType.HEALTH_CHECK,
            severity=AlertSeverity.WARN,
            title_template="Test",
            body_template="Test",
            predicate=lambda ctx: True,  # Always fires
        )

        # Build engine with operator state
        engine = AlertEngine(rules=[rule], operator_state=operator_state)

        # Should fire initially
        alerts = engine.evaluate(health_report={"status": "critical"})
        assert len(alerts) == 1

        # Snooze rule
        operator_state.snooze("test_rule", ttl_seconds=3600)

        # Should not fire (snoozed)
        alerts = engine.evaluate(health_report={"status": "critical"})
        assert len(alerts) == 0


def test_engine_with_operator_state_ack():
    """Test engine respects acked alerts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "alerts_state.json"
        operator_state = OperatorState(state_path=state_path, enabled=True)

        # Create rule
        rule = AlertRule(
            rule_id="test_rule",
            enabled=True,
            rule_type=RuleType.HEALTH_CHECK,
            severity=AlertSeverity.WARN,
            title_template="Test Alert",
            body_template="Test",
            predicate=lambda ctx: True,
        )

        # Build engine with operator state
        engine = AlertEngine(rules=[rule], operator_state=operator_state)

        # Should fire initially
        alerts = engine.evaluate(health_report={"status": "critical"})
        assert len(alerts) == 1

        # ACK alert
        dedupe_key = alerts[0].dedupe_key
        operator_state.ack(dedupe_key)

        # Should not fire (acked)
        alerts = engine.evaluate(health_report={"status": "critical"})
        assert len(alerts) == 0


def test_engine_without_operator_state():
    """Test engine works without operator state (backward compat)."""
    rule = AlertRule(
        rule_id="test_rule",
        enabled=True,
        rule_type=RuleType.HEALTH_CHECK,
        severity=AlertSeverity.WARN,
        title_template="Test",
        body_template="Test",
        predicate=lambda ctx: True,
    )

    # Engine without operator_state (Phase 16I compatibility)
    engine = AlertEngine(rules=[rule], operator_state=None)

    # Should fire normally
    alerts = engine.evaluate(health_report={"status": "critical"})
    assert len(alerts) == 1
