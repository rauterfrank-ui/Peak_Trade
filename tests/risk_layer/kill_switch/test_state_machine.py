"""Tests for Kill Switch state machine."""

import pytest
import time
from datetime import datetime

from src.risk_layer.kill_switch import KillSwitch, KillSwitchState


class TestStateTransitions:
    """Tests for state machine transitions."""

    def test_initial_state_is_active(self, kill_switch):
        """Initial state should be ACTIVE."""
        assert kill_switch.state == KillSwitchState.ACTIVE
        assert kill_switch.is_active
        assert not kill_switch.is_killed

    def test_trigger_changes_to_killed(self, kill_switch):
        """Trigger should change state to KILLED."""
        result = kill_switch.trigger("Test trigger")

        assert result is True
        assert kill_switch.state == KillSwitchState.KILLED
        assert kill_switch.is_killed
        assert not kill_switch.is_active

    def test_double_trigger_is_idempotent(self, kill_switch):
        """Double trigger should be safe and idempotent."""
        kill_switch.trigger("First trigger")
        result = kill_switch.trigger("Second trigger")

        assert result is True
        assert kill_switch.state == KillSwitchState.KILLED

        # Should have only 1 event (idempotent - second trigger doesn't create new event)
        events = kill_switch.get_audit_trail()
        assert len(events) == 1
        assert events[0].trigger_reason == "First trigger"

    def test_recovery_starts_cooldown(self, kill_switch):
        """Recovery should start cooldown phase."""
        kill_switch.trigger("Test")
        result = kill_switch.request_recovery("operator")

        assert result is True
        assert kill_switch.state == KillSwitchState.RECOVERING

    def test_recovery_requires_killed_state(self, kill_switch):
        """Recovery only possible from KILLED state."""
        result = kill_switch.request_recovery("operator")

        assert result is False
        assert kill_switch.state == KillSwitchState.ACTIVE

    def test_complete_recovery_after_cooldown(self, kill_switch):
        """Complete recovery after cooldown."""
        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")

        # Wait for cooldown (1 second in test config)
        time.sleep(1.1)

        result = kill_switch.complete_recovery()

        assert result is True
        assert kill_switch.state == KillSwitchState.ACTIVE
        assert kill_switch.is_active
        assert not kill_switch.is_killed

    def test_complete_recovery_blocked_during_cooldown(self, kill_switch):
        """Complete recovery blocked during cooldown."""
        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")

        # Try immediately (before cooldown)
        result = kill_switch.complete_recovery()

        assert result is False
        assert kill_switch.state == KillSwitchState.RECOVERING

    def test_trigger_during_recovery_returns_to_killed(self, kill_switch):
        """Trigger during recovery should return to KILLED."""
        kill_switch.trigger("First")
        kill_switch.request_recovery("operator")

        assert kill_switch.state == KillSwitchState.RECOVERING

        # Trigger again during recovery
        result = kill_switch.trigger("Second emergency")

        assert result is True
        assert kill_switch.state == KillSwitchState.KILLED


class TestAuditTrail:
    """Tests for audit trail functionality."""

    def test_events_are_recorded(self, kill_switch):
        """Events should be recorded in audit trail."""
        kill_switch.trigger("Test reason", triggered_by="manual")

        events = kill_switch.get_audit_trail()

        assert len(events) == 1
        assert events[0].trigger_reason == "Test reason"
        assert events[0].triggered_by == "manual"
        assert events[0].previous_state == KillSwitchState.ACTIVE
        assert events[0].new_state == KillSwitchState.KILLED

    def test_multiple_events_are_recorded(self, kill_switch):
        """Multiple events should be recorded in order."""
        kill_switch.trigger("Trigger")
        kill_switch.request_recovery("operator")
        time.sleep(1.1)
        kill_switch.complete_recovery()

        events = kill_switch.get_audit_trail()

        assert len(events) == 3
        assert events[0].new_state == KillSwitchState.KILLED
        assert events[1].new_state == KillSwitchState.RECOVERING
        assert events[2].new_state == KillSwitchState.ACTIVE

    def test_event_has_timestamp(self, kill_switch):
        """Events should have timestamp."""
        before = datetime.utcnow()
        kill_switch.trigger("Test")
        after = datetime.utcnow()

        events = kill_switch.get_audit_trail()
        event_time = events[0].timestamp

        assert before <= event_time <= after


class TestCheckAndBlock:
    """Tests for trading gate functionality."""

    def test_check_and_block_returns_false_when_active(self, kill_switch):
        """check_and_block() should return False when active."""
        assert kill_switch.check_and_block() is False

    def test_check_and_block_returns_true_when_killed(self, kill_switch):
        """check_and_block() should return True when killed."""
        kill_switch.trigger("Test")
        assert kill_switch.check_and_block() is True

    def test_check_and_block_returns_true_when_recovering(self, kill_switch):
        """check_and_block() should return True during recovery."""
        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")
        assert kill_switch.check_and_block() is True


class TestCallbacks:
    """Tests for callback system."""

    def test_on_kill_callback_is_called(self, kill_switch):
        """On-kill callback should be called when triggered."""
        called = []

        def callback(event):
            called.append(event)

        kill_switch.register_on_kill(callback)
        kill_switch.trigger("Test")

        assert len(called) == 1
        assert called[0].new_state == KillSwitchState.KILLED

    def test_on_recover_callback_is_called(self, kill_switch):
        """On-recover callback should be called when recovered."""
        called = []

        def callback(event):
            called.append(event)

        kill_switch.register_on_recover(callback)

        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")
        time.sleep(1.1)
        kill_switch.complete_recovery()

        assert len(called) == 1
        assert called[0].new_state == KillSwitchState.ACTIVE

    def test_callback_exceptions_are_caught(self, kill_switch):
        """Callback exceptions should not crash the system."""
        def bad_callback(event):
            raise ValueError("Callback error")

        kill_switch.register_on_kill(bad_callback)

        # Should not raise
        result = kill_switch.trigger("Test")
        assert result is True


class TestStatus:
    """Tests for status reporting."""

    def test_get_status_returns_dict(self, kill_switch):
        """get_status() should return status dictionary."""
        status = kill_switch.get_status()

        assert isinstance(status, dict)
        assert "state" in status
        assert "is_killed" in status
        assert "is_active" in status
        assert status["state"] == "ACTIVE"

    def test_status_includes_killed_at(self, kill_switch):
        """Status should include killed_at timestamp when killed."""
        kill_switch.trigger("Test")
        status = kill_switch.get_status()

        assert status["killed_at"] is not None
        assert status["state"] == "KILLED"

    def test_status_includes_cooldown_remaining(self, kill_switch):
        """Status should include cooldown remaining during recovery."""
        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")

        status = kill_switch.get_status()

        assert "cooldown_remaining_seconds" in status
        assert status["cooldown_remaining_seconds"] > 0
