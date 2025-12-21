"""
Peak_Trade Backup & Recovery Module Tests
=========================================
Comprehensive unit tests for backup and recovery functionality.
"""

import json
import pytest
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

from src.core.backup_recovery import (
    BackupType,
    BackupStatus,
    BackupMetadata,
    StateSnapshot,
    ConfigBackup,
    DataBackup,
    RecoveryManager,
)


# ==============================================================================
# StateSnapshot Tests
# ==============================================================================


class TestStateSnapshot:
    """Tests for StateSnapshot class."""

    def test_state_snapshot_init(self):
        """Test state snapshot initialization."""
        snapshot = StateSnapshot()
        assert snapshot._state_providers == {}

    def test_register_provider(self):
        """Test registering state providers."""
        snapshot = StateSnapshot()

        def mock_provider():
            return {"key": "value"}

        snapshot.register_provider("test", mock_provider)
        assert "test" in snapshot._state_providers

    def test_capture_state(self):
        """Test capturing state from providers."""
        snapshot = StateSnapshot()

        def provider1():
            return {"metric1": 100}

        def provider2():
            return {"metric2": 200}

        snapshot.register_provider("provider1", provider1)
        snapshot.register_provider("provider2", provider2)

        state = snapshot.capture()

        assert "timestamp" in state
        assert "providers" in state
        assert state["providers"]["provider1"]["metric1"] == 100
        assert state["providers"]["provider2"]["metric2"] == 200

    def test_capture_handles_provider_error(self):
        """Test that capture handles provider errors gracefully."""
        snapshot = StateSnapshot()

        def failing_provider():
            raise ValueError("Provider error")

        def working_provider():
            return {"data": "ok"}

        snapshot.register_provider("failing", failing_provider)
        snapshot.register_provider("working", working_provider)

        state = snapshot.capture()

        # Should capture state despite one provider failing
        assert "error" in state["providers"]["failing"]
        assert state["providers"]["working"]["data"] == "ok"

    def test_save_and_load(self, tmp_path):
        """Test saving and loading state snapshots."""
        snapshot = StateSnapshot()

        def provider():
            return {"value": 42}

        snapshot.register_provider("test", provider)

        output_path = tmp_path / "state.json"
        snapshot.save(output_path)

        assert output_path.exists()

        loaded_state = snapshot.load(output_path)
        assert loaded_state["providers"]["test"]["value"] == 42


# ==============================================================================
# ConfigBackup Tests
# ==============================================================================


class TestConfigBackup:
    """Tests for ConfigBackup class."""

    def test_config_backup_init(self):
        """Test config backup initialization."""
        backup = ConfigBackup()
        assert backup.config_paths == []

        paths = [Path("config.toml")]
        backup_with_paths = ConfigBackup(paths)
        assert len(backup_with_paths.config_paths) == 1

    def test_add_config(self):
        """Test adding config paths."""
        backup = ConfigBackup()
        backup.add_config(Path("config1.toml"))
        backup.add_config(Path("config2.json"))

        assert len(backup.config_paths) == 2

        # Adding duplicate should not increase count
        backup.add_config(Path("config1.toml"))
        assert len(backup.config_paths) == 2

    def test_backup_config_files(self, tmp_path):
        """Test backing up configuration files."""
        # Create test config files
        config_dir = tmp_path / "configs"
        config_dir.mkdir()

        config1 = config_dir / "config1.toml"
        config1.write_text("key = 'value1'")

        config2 = config_dir / "config2.json"
        config2.write_text('{"key": "value2"}')

        # Backup configs
        backup = ConfigBackup([config1, config2])
        backup_dir = tmp_path / "backup"

        count = backup.backup(backup_dir)

        assert count == 2
        assert (backup_dir / config1.name).exists()
        assert (backup_dir / config2.name).exists()

    def test_backup_handles_missing_files(self, tmp_path):
        """Test backup handles missing files gracefully."""
        missing_file = tmp_path / "missing.toml"
        backup = ConfigBackup([missing_file])

        backup_dir = tmp_path / "backup"
        count = backup.backup(backup_dir)

        # Should not crash, but count should be 0
        assert count == 0

    def test_restore_config_files(self, tmp_path):
        """Test restoring configuration files."""
        # Create backup
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()

        config_backup = backup_dir / "config.toml"
        config_backup.write_text("restored = true")

        # Restore
        restore_path = tmp_path / "config.toml"
        backup = ConfigBackup([restore_path])

        count = backup.restore(backup_dir)

        assert count == 1
        assert restore_path.exists()
        assert "restored = true" in restore_path.read_text()

    def test_restore_dry_run(self, tmp_path):
        """Test restore in dry-run mode."""
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()

        config_backup = backup_dir / "config.toml"
        config_backup.write_text("content")

        restore_path = tmp_path / "config.toml"
        backup = ConfigBackup([restore_path])

        count = backup.restore(backup_dir, dry_run=True)

        # Should report success but not create file
        assert count == 1
        assert not restore_path.exists()


# ==============================================================================
# DataBackup Tests
# ==============================================================================


class TestDataBackup:
    """Tests for DataBackup class."""

    def test_data_backup_init(self):
        """Test data backup initialization."""
        backup = DataBackup()
        assert backup.data_paths == []

    def test_add_data_path(self):
        """Test adding data paths."""
        backup = DataBackup()
        backup.add_data_path(Path("data.csv"))

        assert len(backup.data_paths) == 1

    def test_backup_single_file(self, tmp_path):
        """Test backing up a single file."""
        data_file = tmp_path / "data.csv"
        data_file.write_text("col1,col2\n1,2\n3,4")

        backup = DataBackup([data_file])
        backup_dir = tmp_path / "backup"

        count, size = backup.backup(backup_dir)

        assert count == 1
        assert size > 0
        assert (backup_dir / data_file.name).exists()

    def test_backup_directory(self, tmp_path):
        """Test backing up a directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        (data_dir / "file1.txt").write_text("content1")
        (data_dir / "file2.txt").write_text("content2")

        subdir = data_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        backup = DataBackup([data_dir])
        backup_dir = tmp_path / "backup"

        count, size = backup.backup(backup_dir)

        assert count == 3
        assert size > 0

    def test_restore_data_files(self, tmp_path):
        """Test restoring data files."""
        # Create backup
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()

        data_backup = backup_dir / "data.txt"
        data_backup.write_text("restored data")

        # Restore
        restore_path = tmp_path / "data.txt"
        backup = DataBackup([restore_path])

        count = backup.restore(backup_dir)

        assert count == 1
        assert restore_path.exists()
        assert "restored data" in restore_path.read_text()


# ==============================================================================
# RecoveryManager Tests
# ==============================================================================


class TestRecoveryManager:
    """Tests for RecoveryManager class."""

    @pytest.fixture
    def recovery_mgr(self, tmp_path):
        """Create a recovery manager with temporary backup directory."""
        return RecoveryManager(backup_dir=str(tmp_path / "backups"))

    @pytest.fixture
    def sample_config(self, tmp_path):
        """Create a sample configuration file."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("setting = 'value'")
        return config_file

    def test_recovery_manager_init(self, recovery_mgr):
        """Test recovery manager initialization."""
        assert recovery_mgr.backup_root.exists()
        assert isinstance(recovery_mgr.state_snapshot, StateSnapshot)
        assert isinstance(recovery_mgr.config_backup, ConfigBackup)
        assert isinstance(recovery_mgr.data_backup, DataBackup)

    def test_generate_backup_id(self, recovery_mgr):
        """Test backup ID generation."""
        backup_id = recovery_mgr._generate_backup_id()

        assert backup_id.startswith("backup_")
        assert len(backup_id) > 20

    def test_create_backup_config_only(self, recovery_mgr, sample_config):
        """Test creating a config-only backup."""
        recovery_mgr.config_backup.add_config(sample_config)

        backup_id = recovery_mgr.create_backup(
            include_config=True, include_state=False, include_data=False, description="Test backup"
        )

        assert backup_id is not None
        backup_dir = recovery_mgr._get_backup_dir(backup_id)
        assert backup_dir.exists()
        assert (backup_dir / "metadata.json").exists()

    def test_create_backup_with_state(self, recovery_mgr):
        """Test creating a backup with state snapshot."""
        # Register a state provider
        recovery_mgr.state_snapshot.register_provider("test", lambda: {"metric": 123})

        backup_id = recovery_mgr.create_backup(
            include_config=False, include_state=True, include_data=False
        )

        backup_dir = recovery_mgr._get_backup_dir(backup_id)
        assert (backup_dir / "state.json").exists()

    def test_create_full_backup(self, recovery_mgr, sample_config, tmp_path):
        """Test creating a full backup."""
        # Setup config
        recovery_mgr.config_backup.add_config(sample_config)

        # Setup state
        recovery_mgr.state_snapshot.register_provider("test", lambda: {"data": "value"})

        # Setup data
        data_file = tmp_path / "data.txt"
        data_file.write_text("test data")
        recovery_mgr.data_backup.add_data_path(data_file)

        backup_id = recovery_mgr.create_backup(
            include_config=True,
            include_state=True,
            include_data=True,
            description="Full backup",
            tags=["test", "full"],
        )

        # Verify backup structure
        backup_dir = recovery_mgr._get_backup_dir(backup_id)
        assert (backup_dir / "metadata.json").exists()
        assert (backup_dir / "state.json").exists()
        assert (backup_dir / "config").exists()
        assert (backup_dir / "data").exists()

        # Verify metadata
        metadata = recovery_mgr._load_metadata(backup_dir)
        assert metadata.backup_type == BackupType.FULL
        assert metadata.status == BackupStatus.SUCCESS
        assert metadata.description == "Full backup"
        assert "test" in metadata.tags
        assert metadata.files_count > 0

    def test_list_backups(self, recovery_mgr, sample_config):
        """Test listing backups."""
        recovery_mgr.config_backup.add_config(sample_config)

        # Create multiple backups
        backup_id1 = recovery_mgr.create_backup(include_config=True, tags=["daily"])
        backup_id2 = recovery_mgr.create_backup(include_config=True, tags=["weekly"])

        # List all backups
        backups = recovery_mgr.list_backups()
        assert len(backups) == 2

        # Filter by tags
        daily_backups = recovery_mgr.list_backups(tags=["daily"])
        assert len(daily_backups) == 1

        # Filter by type
        config_backups = recovery_mgr.list_backups(backup_type=BackupType.CONFIG)
        assert len(config_backups) == 2

    def test_restore_backup(self, recovery_mgr, sample_config, tmp_path):
        """Test restoring from backup."""
        recovery_mgr.config_backup.add_config(sample_config)

        # Create backup
        backup_id = recovery_mgr.create_backup(include_config=True)

        # Modify original file
        sample_config.write_text("modified = true")

        # Restore
        success = recovery_mgr.restore_backup(backup_id, restore_config=True)

        assert success
        # Original content should be restored
        assert "setting = 'value'" in sample_config.read_text()

    def test_restore_dry_run(self, recovery_mgr, sample_config):
        """Test restore in dry-run mode."""
        recovery_mgr.config_backup.add_config(sample_config)

        backup_id = recovery_mgr.create_backup(include_config=True)

        original_content = sample_config.read_text()
        sample_config.write_text("modified")

        # Dry run should not modify file
        success = recovery_mgr.restore_backup(backup_id, restore_config=True, dry_run=True)

        assert success
        assert sample_config.read_text() == "modified"

    def test_restore_nonexistent_backup(self, recovery_mgr):
        """Test restoring from nonexistent backup."""
        success = recovery_mgr.restore_backup("nonexistent_backup_id")
        assert not success

    def test_delete_backup(self, recovery_mgr, sample_config):
        """Test deleting a backup."""
        recovery_mgr.config_backup.add_config(sample_config)

        backup_id = recovery_mgr.create_backup(include_config=True)

        # Verify backup exists
        assert recovery_mgr._get_backup_dir(backup_id).exists()

        # Delete backup
        success = recovery_mgr.delete_backup(backup_id)
        assert success

        # Verify backup is deleted
        assert not recovery_mgr._get_backup_dir(backup_id).exists()

    def test_cleanup_old_backups(self, recovery_mgr, sample_config):
        """Test cleaning up old backups."""
        recovery_mgr.config_backup.add_config(sample_config)

        # Create 15 backups
        for i in range(15):
            recovery_mgr.create_backup(include_config=True, description=f"Backup {i}")

        # Keep only 10
        deleted_count = recovery_mgr.cleanup_old_backups(keep_count=10)

        assert deleted_count == 5

        remaining_backups = recovery_mgr.list_backups()
        assert len(remaining_backups) == 10

    def test_backup_metadata_serialization(self):
        """Test backup metadata serialization."""
        metadata = BackupMetadata(
            backup_id="test_123",
            backup_type=BackupType.FULL,
            created_at="2024-12-17T10:30:00",
            status=BackupStatus.SUCCESS,
            size_bytes=1024,
            files_count=5,
            description="Test backup",
            tags=["test", "production"],
        )

        # Convert to dict
        data = metadata.to_dict()

        assert data["backup_id"] == "test_123"
        assert data["backup_type"] == "full"
        assert data["status"] == "success"
        assert data["size_bytes"] == 1024
        assert "test" in data["tags"]


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestBackupRecoveryIntegration:
    """Integration tests for complete backup/recovery workflows."""

    def test_complete_backup_restore_workflow(self, tmp_path):
        """Test complete backup and restore workflow."""
        # Setup workspace
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        config_file = workspace / "config.toml"
        config_file.write_text("[settings]\nvalue = 42")

        data_file = workspace / "data.csv"
        data_file.write_text("a,b,c\n1,2,3")

        # Initialize recovery manager
        recovery = RecoveryManager(backup_dir=str(tmp_path / "backups"))
        recovery.config_backup.add_config(config_file)
        recovery.data_backup.add_data_path(data_file)
        recovery.state_snapshot.register_provider(
            "app_state", lambda: {"running": True, "version": "1.0"}
        )

        # Create backup
        backup_id = recovery.create_backup(
            include_config=True,
            include_state=True,
            include_data=True,
            description="Complete backup",
            tags=["integration-test"],
        )

        # Verify backup
        backups = recovery.list_backups()
        assert len(backups) == 1
        assert backups[0].backup_type == BackupType.FULL
        assert backups[0].files_count >= 2

        # Corrupt workspace
        config_file.write_text("corrupted")
        data_file.write_text("corrupted")

        # Restore
        success = recovery.restore_backup(
            backup_id, restore_config=True, restore_data=True, restore_state=True
        )

        assert success
        assert "[settings]" in config_file.read_text()
        assert "a,b,c" in data_file.read_text()

    def test_multiple_backups_and_selective_restore(self, tmp_path):
        """Test creating multiple backups and selective restore."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        config_file = workspace / "config.toml"
        config_file.write_text("version = 1")

        recovery = RecoveryManager(backup_dir=str(tmp_path / "backups"))
        recovery.config_backup.add_config(config_file)

        # Create version 1 backup
        backup_v1 = recovery.create_backup(
            include_config=True, description="Version 1", tags=["v1"]
        )

        # Update config
        config_file.write_text("version = 2")

        # Create version 2 backup
        backup_v2 = recovery.create_backup(
            include_config=True, description="Version 2", tags=["v2"]
        )

        # Corrupt config
        config_file.write_text("corrupted")

        # Restore version 1
        recovery.restore_backup(backup_v1, restore_config=True)
        assert "version = 1" in config_file.read_text()

        # Restore version 2
        recovery.restore_backup(backup_v2, restore_config=True)
        assert "version = 2" in config_file.read_text()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
