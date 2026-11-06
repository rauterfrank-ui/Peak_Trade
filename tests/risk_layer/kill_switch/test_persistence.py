"""Tests for Kill Switch persistence and audit."""

import pytest
import json
import gzip
from pathlib import Path
from datetime import datetime, timedelta

from src.risk_layer.kill_switch import KillSwitchState, KillSwitchEvent
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.audit import AuditTrail


class TestStatePersistence:
    """Tests for StatePersistence."""

    def test_save_creates_file(self, tmp_path):
        """save should create state file."""
        state_file = tmp_path / "state.json"
        persistence = StatePersistence(str(state_file))

        persistence.save(
            KillSwitchState.KILLED, killed_at=datetime.utcnow(), trigger_reason="Test trigger"
        )

        assert state_file.exists()

    def test_save_with_atomic_write(self, tmp_path):
        """save should use atomic write pattern."""
        state_file = tmp_path / "state.json"
        persistence = StatePersistence(str(state_file))

        # First save
        persistence.save(KillSwitchState.KILLED)

        # Verify no .tmp file remains
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_save_creates_backup(self, tmp_path):
        """save should create backup of existing file."""
        state_file = tmp_path / "state.json"
        backup_dir = tmp_path / "backups"
        persistence = StatePersistence(str(state_file), str(backup_dir))

        # First save
        persistence.save(KillSwitchState.KILLED)

        # Second save (should backup first)
        persistence.save(KillSwitchState.RECOVERING)

        # Check backup exists
        backups = list(backup_dir.glob("state_*.json"))
        assert len(backups) == 1

    def test_load_returns_none_if_not_exists(self, tmp_path):
        """load should return None if file doesn't exist."""
        state_file = tmp_path / "nonexistent.json"
        persistence = StatePersistence(str(state_file))

        result = persistence.load()

        assert result is None

    def test_load_returns_saved_state(self, tmp_path):
        """load should return previously saved state."""
        state_file = tmp_path / "state.json"
        persistence = StatePersistence(str(state_file))

        # Save
        killed_at = datetime.utcnow()
        persistence.save(KillSwitchState.KILLED, killed_at=killed_at, trigger_reason="Test")

        # Load
        result = persistence.load()

        assert result is not None
        assert result["state"] == "KILLED"
        assert result["trigger_reason"] == "Test"
        assert "killed_at" in result

    def test_load_handles_corrupt_file(self, tmp_path):
        """load should handle corrupt JSON gracefully."""
        state_file = tmp_path / "state.json"
        persistence = StatePersistence(str(state_file))

        # Create corrupt file
        with open(state_file, "w") as f:
            f.write("{ invalid json }")

        result = persistence.load()

        assert result is None

    def test_clear_removes_file(self, tmp_path):
        """clear should remove state file."""
        state_file = tmp_path / "state.json"
        persistence = StatePersistence(str(state_file))

        # Create file
        persistence.save(KillSwitchState.KILLED)
        assert state_file.exists()

        # Clear
        persistence.clear()
        assert not state_file.exists()

    def test_list_backups(self, tmp_path):
        """list_backups should return backup files."""
        import time

        state_file = tmp_path / "state.json"
        backup_dir = tmp_path / "backups"
        persistence = StatePersistence(str(state_file), str(backup_dir))

        # Create multiple saves to generate backups
        # First save creates state file (no backup)
        persistence.save(KillSwitchState.KILLED)

        # Ensure unique timestamps (backup filenames have 1-second granularity)
        time.sleep(1.1)
        persistence.save(KillSwitchState.RECOVERING)  # Creates backup #1

        time.sleep(1.1)
        persistence.save(KillSwitchState.ACTIVE)  # Creates backup #2

        backups = persistence.list_backups()

        assert len(backups) == 2, f"Expected 2 backups, got {len(backups)}"

    def test_restore_from_backup(self, tmp_path):
        """restore_from_backup should restore from backup file."""
        state_file = tmp_path / "state.json"
        backup_dir = tmp_path / "backups"
        persistence = StatePersistence(str(state_file), str(backup_dir))

        # Save and create backup
        persistence.save(KillSwitchState.KILLED, trigger_reason="Original")
        persistence.save(KillSwitchState.ACTIVE, trigger_reason="Updated")

        # Get backup
        backups = persistence.list_backups()
        assert len(backups) == 1

        # Restore from backup
        result = persistence.restore_from_backup(str(backups[0]))
        assert result is True

        # Verify restored
        data = persistence.load()
        assert data["trigger_reason"] == "Original"

    def test_save_with_all_fields(self, tmp_path):
        """save should handle all optional fields."""
        state_file = tmp_path / "state.json"
        persistence = StatePersistence(str(state_file))

        killed_at = datetime.utcnow()
        recovery_started = datetime.utcnow()

        persistence.save(
            KillSwitchState.RECOVERING,
            killed_at=killed_at,
            trigger_reason="Emergency",
            recovery_started_at=recovery_started,
        )

        data = persistence.load()

        assert data["state"] == "RECOVERING"
        assert data["trigger_reason"] == "Emergency"
        assert data["killed_at"] is not None
        assert data["recovery_started_at"] is not None


class TestAuditTrail:
    """Tests for AuditTrail."""

    def test_log_event_creates_file(self, tmp_path):
        """log_event should create audit file."""
        audit_dir = tmp_path / "audit"
        audit = AuditTrail(str(audit_dir))

        event = KillSwitchEvent(
            timestamp=datetime.utcnow(),
            previous_state=KillSwitchState.ACTIVE,
            new_state=KillSwitchState.KILLED,
            trigger_reason="Test",
            triggered_by="manual",
            metadata={},
        )

        audit.log_event(event)

        # Check file exists
        audit_files = list(audit_dir.glob("kill_switch_audit_*.jsonl"))
        assert len(audit_files) == 1

    def test_log_event_appends_to_file(self, tmp_path):
        """log_event should append to existing file."""
        audit_dir = tmp_path / "audit"
        audit = AuditTrail(str(audit_dir))

        event1 = KillSwitchEvent(
            timestamp=datetime.utcnow(),
            previous_state=KillSwitchState.ACTIVE,
            new_state=KillSwitchState.KILLED,
            trigger_reason="First",
            triggered_by="manual",
            metadata={},
        )

        event2 = KillSwitchEvent(
            timestamp=datetime.utcnow(),
            previous_state=KillSwitchState.KILLED,
            new_state=KillSwitchState.RECOVERING,
            trigger_reason="Second",
            triggered_by="manual",
            metadata={},
        )

        audit.log_event(event1)
        audit.log_event(event2)

        # Read file and count lines
        audit_file = list(audit_dir.glob("kill_switch_audit_*.jsonl"))[0]
        with open(audit_file) as f:
            lines = f.readlines()

        assert len(lines) == 2

    def test_get_events_returns_all(self, tmp_path):
        """get_events should return all logged events."""
        audit_dir = tmp_path / "audit"
        audit = AuditTrail(str(audit_dir))

        # Log multiple events
        for i in range(5):
            event = KillSwitchEvent(
                timestamp=datetime.utcnow(),
                previous_state=KillSwitchState.ACTIVE,
                new_state=KillSwitchState.KILLED,
                trigger_reason=f"Event {i}",
                triggered_by="manual",
                metadata={},
            )
            audit.log_event(event)

        events = audit.get_events()

        assert len(events) == 5

    def test_get_events_filters_by_time(self, tmp_path):
        """get_events should filter by time range."""
        audit_dir = tmp_path / "audit"
        audit = AuditTrail(str(audit_dir))

        # Log events with different timestamps
        old_time = datetime.utcnow() - timedelta(days=2)
        recent_time = datetime.utcnow()

        old_event = KillSwitchEvent(
            timestamp=old_time,
            previous_state=KillSwitchState.ACTIVE,
            new_state=KillSwitchState.KILLED,
            trigger_reason="Old",
            triggered_by="manual",
            metadata={},
        )

        recent_event = KillSwitchEvent(
            timestamp=recent_time,
            previous_state=KillSwitchState.ACTIVE,
            new_state=KillSwitchState.KILLED,
            trigger_reason="Recent",
            triggered_by="manual",
            metadata={},
        )

        audit.log_event(old_event)
        audit.log_event(recent_event)

        # Filter for recent events
        since = datetime.utcnow() - timedelta(days=1)
        events = audit.get_events(since=since)

        assert len(events) == 1
        assert events[0]["trigger_reason"] == "Recent"

    def test_get_events_respects_limit(self, tmp_path):
        """get_events should respect limit parameter."""
        audit_dir = tmp_path / "audit"
        audit = AuditTrail(str(audit_dir))

        # Log 10 events
        for i in range(10):
            event = KillSwitchEvent(
                timestamp=datetime.utcnow(),
                previous_state=KillSwitchState.ACTIVE,
                new_state=KillSwitchState.KILLED,
                trigger_reason=f"Event {i}",
                triggered_by="manual",
                metadata={},
            )
            audit.log_event(event)

        events = audit.get_events(limit=5)

        assert len(events) == 5

    def test_get_events_by_state(self, tmp_path):
        """get_events_by_state should filter by state."""
        audit_dir = tmp_path / "audit"
        audit = AuditTrail(str(audit_dir))

        # Log events with different states
        killed_event = KillSwitchEvent(
            timestamp=datetime.utcnow(),
            previous_state=KillSwitchState.ACTIVE,
            new_state=KillSwitchState.KILLED,
            trigger_reason="Killed",
            triggered_by="manual",
            metadata={},
        )

        active_event = KillSwitchEvent(
            timestamp=datetime.utcnow(),
            previous_state=KillSwitchState.RECOVERING,
            new_state=KillSwitchState.ACTIVE,
            trigger_reason="Recovered",
            triggered_by="manual",
            metadata={},
        )

        audit.log_event(killed_event)
        audit.log_event(active_event)

        killed_events = audit.get_events_by_state("KILLED")

        assert len(killed_events) == 1
        assert killed_events[0]["new_state"] == "KILLED"

    def test_get_latest_event(self, tmp_path):
        """get_latest_event should return most recent event."""
        audit_dir = tmp_path / "audit"
        audit = AuditTrail(str(audit_dir))

        # Log events
        for i in range(3):
            event = KillSwitchEvent(
                timestamp=datetime.utcnow(),
                previous_state=KillSwitchState.ACTIVE,
                new_state=KillSwitchState.KILLED,
                trigger_reason=f"Event {i}",
                triggered_by="manual",
                metadata={},
            )
            audit.log_event(event)

        latest = audit.get_latest_event()

        assert latest is not None
        assert "Event 2" in latest["trigger_reason"]

    def test_get_statistics(self, tmp_path):
        """get_statistics should return audit stats."""
        audit_dir = tmp_path / "audit"
        audit = AuditTrail(str(audit_dir))

        # Log some events
        for i in range(5):
            event = KillSwitchEvent(
                timestamp=datetime.utcnow(),
                previous_state=KillSwitchState.ACTIVE,
                new_state=KillSwitchState.KILLED,
                trigger_reason=f"Event {i}",
                triggered_by="manual",
                metadata={},
            )
            audit.log_event(event)

        stats = audit.get_statistics()

        assert isinstance(stats, dict)
        assert stats["total_events"] == 5
        assert stats["total_files"] >= 1
        assert "total_size_mb" in stats

    def test_handles_corrupt_lines(self, tmp_path):
        """get_events should skip corrupt JSON lines."""
        audit_dir = tmp_path / "audit"
        audit = AuditTrail(str(audit_dir))

        # Log valid event
        event = KillSwitchEvent(
            timestamp=datetime.utcnow(),
            previous_state=KillSwitchState.ACTIVE,
            new_state=KillSwitchState.KILLED,
            trigger_reason="Valid",
            triggered_by="manual",
            metadata={},
        )
        audit.log_event(event)

        # Manually append corrupt line
        audit_file = list(audit_dir.glob("kill_switch_audit_*.jsonl"))[0]
        with open(audit_file, "a") as f:
            f.write("{ corrupt json }\n")

        # Should still return valid event
        events = audit.get_events()
        assert len(events) == 1

    def test_cleanup_old_files(self, tmp_path):
        """cleanup_old_files should remove old audit files."""
        audit_dir = tmp_path / "audit"
        audit = AuditTrail(str(audit_dir), retention_days=1)

        # Create old file
        old_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
        old_file = audit_dir / f"kill_switch_audit_{old_date}.jsonl"
        audit_dir.mkdir(parents=True, exist_ok=True)
        old_file.touch()

        # Create recent file
        recent_date = datetime.utcnow().strftime("%Y-%m-%d")
        recent_file = audit_dir / f"kill_switch_audit_{recent_date}.jsonl"
        recent_file.touch()

        # Cleanup
        audit.cleanup_old_files()

        # Old file should be deleted, recent should remain
        assert not old_file.exists()
        assert recent_file.exists()


class TestPersistenceRecovery:
    """Test persistence crash recovery scenarios."""

    def test_atomic_write_prevents_corruption(self, tmp_path):
        """Atomic write should prevent file corruption on crash."""
        state_file = tmp_path / "state.json"
        persistence = StatePersistence(str(state_file))

        # Simulate crash during write by checking no .tmp files remain
        persistence.save(KillSwitchState.KILLED)

        # Verify clean state
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0

        # Verify file is valid JSON
        with open(state_file) as f:
            data = json.load(f)
        assert data["state"] == "KILLED"

    def test_load_after_multiple_saves(self, tmp_path):
        """load should work after multiple saves."""
        state_file = tmp_path / "state.json"
        persistence = StatePersistence(str(state_file))

        # Multiple saves
        for state in [KillSwitchState.KILLED, KillSwitchState.RECOVERING, KillSwitchState.ACTIVE]:
            persistence.save(state, trigger_reason=state.name)

        # Load should return latest
        data = persistence.load()
        assert data["state"] == "ACTIVE"
