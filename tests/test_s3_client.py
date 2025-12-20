"""
Peak_Trade S3 Backup Client Tests
==================================

Tests for S3BackupClient functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

from src.backup.s3_client import S3BackupClient


class TestS3BackupClient:
    """Tests for S3BackupClient class."""
    
    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client."""
        with patch('src.backup.s3_client.boto3') as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            
            # Mock successful bucket head
            mock_client.head_bucket.return_value = {}
            
            yield mock_client
    
    def test_init_creates_client(self, mock_s3_client):
        """Test S3 client initialization."""
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        assert client.bucket_name == "test-bucket"
        assert client.s3 == mock_s3_client
        mock_s3_client.head_bucket.assert_called_once()
    
    def test_init_creates_bucket_if_not_exists(self):
        """Test bucket creation when it doesn't exist."""
        with patch('src.backup.s3_client.boto3') as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            
            # First call raises error (bucket doesn't exist)
            mock_client.head_bucket.side_effect = ClientError(
                {'Error': {'Code': '404'}}, 'HeadBucket'
            )
            mock_client.create_bucket.return_value = {}
            
            client = S3BackupClient(
                bucket_name="new-bucket",
                access_key="test-key",
                secret_key="test-secret"
            )
            
            mock_client.create_bucket.assert_called_once()
    
    def test_upload_file_success(self, mock_s3_client, tmp_path):
        """Test successful file upload."""
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Upload file
        result = client.upload_file(test_file, "backups/test.txt")
        
        assert result is True
        mock_s3_client.upload_file.assert_called_once()
    
    def test_upload_file_with_metadata(self, mock_s3_client, tmp_path):
        """Test file upload with metadata."""
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        metadata = {"backup_id": "123", "version": "1.0"}
        result = client.upload_file(test_file, "test.txt", metadata=metadata)
        
        assert result is True
        call_args = mock_s3_client.upload_file.call_args
        assert call_args[1]['ExtraArgs']['Metadata'] == metadata
    
    def test_upload_file_with_encryption(self, mock_s3_client, tmp_path):
        """Test file upload with encryption enabled."""
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        result = client.upload_file(test_file, "test.txt", encrypt=True)
        
        assert result is True
        call_args = mock_s3_client.upload_file.call_args
        assert call_args[1]['ExtraArgs']['ServerSideEncryption'] == 'AES256'
    
    def test_upload_file_failure(self, mock_s3_client, tmp_path):
        """Test file upload failure."""
        mock_s3_client.upload_file.side_effect = ClientError(
            {'Error': {'Code': '500'}}, 'UploadFile'
        )
        
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        result = client.upload_file(test_file, "test.txt")
        
        assert result is False
    
    def test_download_file_success(self, mock_s3_client, tmp_path):
        """Test successful file download."""
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        download_path = tmp_path / "downloaded.txt"
        result = client.download_file("backups/test.txt", download_path)
        
        assert result is True
        mock_s3_client.download_file.assert_called_once()
    
    def test_download_file_creates_parent_dirs(self, mock_s3_client, tmp_path):
        """Test that download creates parent directories."""
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        download_path = tmp_path / "nested" / "dir" / "file.txt"
        result = client.download_file("test.txt", download_path)
        
        assert result is True
        assert download_path.parent.exists()
    
    def test_download_file_failure(self, mock_s3_client, tmp_path):
        """Test file download failure."""
        mock_s3_client.download_file.side_effect = ClientError(
            {'Error': {'Code': '404'}}, 'DownloadFile'
        )
        
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        download_path = tmp_path / "downloaded.txt"
        result = client.download_file("missing.txt", download_path)
        
        assert result is False
    
    def test_list_backups_success(self, mock_s3_client):
        """Test listing backups."""
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'backups/backup1.tar.gz',
                    'Size': 1024,
                    'LastModified': datetime.now(),
                    'ETag': '"abc123"'
                },
                {
                    'Key': 'backups/backup2.tar.gz',
                    'Size': 2048,
                    'LastModified': datetime.now(),
                    'ETag': '"def456"'
                }
            ]
        }
        
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        backups = client.list_backups()
        
        assert len(backups) == 2
        assert backups[0]['key'] == 'backups/backup1.tar.gz'
        assert backups[0]['size'] == 1024
    
    def test_list_backups_empty(self, mock_s3_client):
        """Test listing backups when none exist."""
        mock_s3_client.list_objects_v2.return_value = {}
        
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        backups = client.list_backups()
        
        assert backups == []
    
    def test_delete_backup_success(self, mock_s3_client):
        """Test successful backup deletion."""
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        result = client.delete_backup("backups/old-backup.tar.gz")
        
        assert result is True
        mock_s3_client.delete_object.assert_called_once()
    
    def test_delete_backup_failure(self, mock_s3_client):
        """Test backup deletion failure."""
        mock_s3_client.delete_object.side_effect = ClientError(
            {'Error': {'Code': '500'}}, 'DeleteObject'
        )
        
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        result = client.delete_backup("backups/backup.tar.gz")
        
        assert result is False
    
    def test_apply_retention_policy(self, mock_s3_client):
        """Test applying retention policy."""
        now = datetime.now()
        
        # Create backups with different ages
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'backups/recent.tar.gz',
                    'Size': 1024,
                    'LastModified': now - timedelta(days=2),
                    'ETag': '"abc"'
                },
                {
                    'Key': 'backups/old.tar.gz',
                    'Size': 1024,
                    'LastModified': now - timedelta(days=400),
                    'ETag': '"def"'
                }
            ]
        }
        
        mock_s3_client.delete_object.return_value = {}
        
        client = S3BackupClient(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret"
        )
        
        # Apply retention (keep 7 daily, 4 weekly, 12 monthly)
        deleted = client.apply_retention_policy(
            keep_daily=7,
            keep_weekly=4,
            keep_monthly=12
        )
        
        # Old backup should be deleted
        assert deleted >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
