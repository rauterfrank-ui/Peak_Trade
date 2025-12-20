"""
Peak_Trade Cloud Backup Manager Tests
=====================================

Tests for CloudBackupManager functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.backup.cloud_backup_manager import CloudBackupManager
from src.backup.s3_client import S3BackupClient


class TestCloudBackupManager:
    """Tests for CloudBackupManager class."""
    
    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client."""
        mock = MagicMock(spec=S3BackupClient)
        mock.bucket_name = "test-bucket"
        return mock
    
    @pytest.fixture
    def mock_recovery_manager(self):
        """Create a mock recovery manager."""
        with patch('src.backup.cloud_backup_manager.RecoveryManager') as mock:
            yield mock
    
    @pytest.fixture
    def backup_manager(self, mock_s3_client, mock_recovery_manager, tmp_path):
        """Create CloudBackupManager with mocks."""
        manager = CloudBackupManager(
            s3_client=mock_s3_client,
            local_backup_dir=tmp_path / "backups",
            s3_prefix="test/backups/"
        )
        return manager
    
    def test_init(self, mock_s3_client, tmp_path):
        """Test CloudBackupManager initialization."""
        manager = CloudBackupManager(
            s3_client=mock_s3_client,
            local_backup_dir=tmp_path / "backups"
        )
        
        assert manager.s3 == mock_s3_client
        assert manager.local_backup_dir == tmp_path / "backups"
        assert manager.s3_prefix == "peak-trade/backups/"
    
    def test_create_and_upload_backup_success(self, backup_manager, tmp_path):
        """Test successful backup creation and upload."""
        # Setup mocks
        backup_id = "backup_test_123"
        backup_manager.recovery_manager.create_backup.return_value = backup_id
        
        # Create backup directory structure
        backup_path = backup_manager.local_backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        (backup_path / "metadata.json").write_text('{"test": "data"}')
        
        # Mock successful upload
        backup_manager.s3.upload_file.return_value = True
        
        # Create backup
        result = backup_manager.create_and_upload_backup(
            include_config=True,
            include_state=True,
            tags=["test"],
            description="Test backup"
        )
        
        assert result == backup_id
        backup_manager.recovery_manager.create_backup.assert_called_once()
        backup_manager.s3.upload_file.assert_called_once()
    
    def test_create_and_upload_backup_local_failure(self, backup_manager):
        """Test backup when local backup creation fails."""
        backup_manager.recovery_manager.create_backup.return_value = None
        
        result = backup_manager.create_and_upload_backup()
        
        assert result is None
        backup_manager.s3.upload_file.assert_not_called()
    
    def test_create_and_upload_backup_upload_failure(self, backup_manager, tmp_path):
        """Test backup when S3 upload fails."""
        backup_id = "backup_test_456"
        backup_manager.recovery_manager.create_backup.return_value = backup_id
        
        # Create backup directory
        backup_path = backup_manager.local_backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        (backup_path / "metadata.json").write_text('{"test": "data"}')
        
        # Mock failed upload
        backup_manager.s3.upload_file.return_value = False
        
        result = backup_manager.create_and_upload_backup()
        
        assert result is None
    
    def test_create_archive(self, backup_manager, tmp_path):
        """Test creating tar.gz archive."""
        # Create backup directory with files
        backup_id = "backup_archive_test"
        backup_path = backup_manager.local_backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        (backup_path / "test.txt").write_text("test content")
        (backup_path / "metadata.json").write_text('{"id": "test"}')
        
        # Create archive
        archive_path = backup_manager._create_archive(backup_path, backup_id)
        
        assert archive_path is not None
        assert archive_path.exists()
        assert archive_path.suffix == ".gz"
        assert backup_id in archive_path.name
    
    def test_restore_from_cloud_success(self, backup_manager, tmp_path):
        """Test successful restore from cloud."""
        backup_id = "backup_restore_test"
        
        # Mock successful download
        backup_manager.s3.download_file.return_value = True
        
        # Create archive that will be "downloaded"
        archive_path = backup_manager.local_backup_dir / f"{backup_id}.tar.gz"
        backup_manager.local_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a valid tar.gz archive
        import tarfile
        backup_dir = backup_manager.local_backup_dir / backup_id
        backup_dir.mkdir(exist_ok=True)
        (backup_dir / "test.txt").write_text("test")
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_dir, arcname=backup_id)
        
        # Mock successful restore
        backup_manager.recovery_manager.restore_backup.return_value = True
        
        # Restore
        result = backup_manager.restore_from_cloud(backup_id)
        
        assert result is True
        backup_manager.s3.download_file.assert_called_once()
        backup_manager.recovery_manager.restore_backup.assert_called_once()
    
    def test_restore_from_cloud_download_failure(self, backup_manager):
        """Test restore when download fails."""
        backup_manager.s3.download_file.return_value = False
        
        result = backup_manager.restore_from_cloud("nonexistent_backup")
        
        assert result is False
        backup_manager.recovery_manager.restore_backup.assert_not_called()
    
    def test_list_cloud_backups(self, backup_manager):
        """Test listing cloud backups."""
        expected_backups = [
            {
                'key': 'test/backups/backup1.tar.gz',
                'size': 1024,
                'last_modified': datetime.now(),
                'etag': '"abc"'
            }
        ]
        backup_manager.s3.list_backups.return_value = expected_backups
        
        backups = backup_manager.list_cloud_backups()
        
        assert backups == expected_backups
        backup_manager.s3.list_backups.assert_called_once_with(prefix="test/backups/")
    
    def test_sync_to_cloud_new_backups(self, backup_manager, tmp_path):
        """Test syncing new local backups to cloud."""
        # Create local backup directories
        backup1_dir = backup_manager.local_backup_dir / "backup_1"
        backup2_dir = backup_manager.local_backup_dir / "backup_2"
        backup1_dir.mkdir(parents=True)
        backup2_dir.mkdir(parents=True)
        (backup1_dir / "file.txt").write_text("content1")
        (backup2_dir / "file.txt").write_text("content2")
        
        # Mock: no backups in cloud yet
        backup_manager.s3.list_backups.return_value = []
        backup_manager.s3.upload_file.return_value = True
        
        # Sync
        synced = backup_manager.sync_to_cloud()
        
        assert synced == 2
        assert backup_manager.s3.upload_file.call_count == 2
    
    def test_sync_to_cloud_skips_existing(self, backup_manager, tmp_path):
        """Test sync skips backups already in cloud."""
        # Create local backup
        backup_dir = backup_manager.local_backup_dir / "backup_existing"
        backup_dir.mkdir(parents=True)
        (backup_dir / "file.txt").write_text("content")
        
        # Mock: backup already exists in cloud
        backup_manager.s3.list_backups.return_value = [
            {'key': 'test/backups/backup_existing.tar.gz'}
        ]
        
        # Sync
        synced = backup_manager.sync_to_cloud()
        
        assert synced == 0
        backup_manager.s3.upload_file.assert_not_called()
    
    def test_sync_to_cloud_mixed_scenario(self, backup_manager, tmp_path):
        """Test sync with mix of new and existing backups."""
        # Create local backups
        backup1_dir = backup_manager.local_backup_dir / "backup_new"
        backup2_dir = backup_manager.local_backup_dir / "backup_existing"
        backup1_dir.mkdir(parents=True)
        backup2_dir.mkdir(parents=True)
        (backup1_dir / "file.txt").write_text("new")
        (backup2_dir / "file.txt").write_text("existing")
        
        # Mock: one backup exists in cloud
        backup_manager.s3.list_backups.return_value = [
            {'key': 'test/backups/backup_existing.tar.gz'}
        ]
        backup_manager.s3.upload_file.return_value = True
        
        # Sync
        synced = backup_manager.sync_to_cloud()
        
        assert synced == 1
        backup_manager.s3.upload_file.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
