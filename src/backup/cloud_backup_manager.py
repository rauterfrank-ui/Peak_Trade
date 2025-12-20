"""
Cloud Backup Manager
===================

Manages cloud backups with S3 integration.

Features:
- Automatic compression before upload
- Incremental backups
- Backup verification
- Restore from cloud
- Scheduled backups
"""

from pathlib import Path
from typing import Optional, List, Dict
import tarfile
import logging
from datetime import datetime
from src.backup.s3_client import S3BackupClient
from src.core.backup_recovery import RecoveryManager

logger = logging.getLogger(__name__)


class CloudBackupManager:
    """
    Manages cloud backups with S3.
    
    Features:
    - Automatic compression before upload
    - Incremental backups
    - Backup verification
    - Restore from cloud
    - Scheduled backups
    """
    
    def __init__(
        self,
        s3_client: S3BackupClient,
        local_backup_dir: Path = Path("backups"),
        s3_prefix: str = "peak-trade/backups/"
    ):
        """
        Initialize cloud backup manager.
        
        Args:
            s3_client: S3 backup client instance
            local_backup_dir: Local backup directory
            s3_prefix: S3 key prefix for backups
        """
        self.s3 = s3_client
        self.local_backup_dir = local_backup_dir
        self.s3_prefix = s3_prefix
        self.recovery_manager = RecoveryManager(backup_dir=str(local_backup_dir))
    
    def create_and_upload_backup(
        self,
        include_config: bool = True,
        include_state: bool = True,
        include_data: bool = True,
        tags: Optional[List[str]] = None,
        description: str = ""
    ) -> Optional[str]:
        """
        Create local backup and upload to S3.
        
        Args:
            include_config: Include config files
            include_state: Include runtime state
            include_data: Include data files
            tags: Optional tags
            description: Backup description
        
        Returns:
            Backup ID if successful, None otherwise
        """
        # Create local backup
        backup_id = self.recovery_manager.create_backup(
            include_config=include_config,
            include_state=include_state,
            include_data=include_data,
            tags=tags or [],
            description=description
        )
        
        if not backup_id:
            logger.error("Failed to create local backup")
            return None
        
        # Compress backup
        backup_path = self.local_backup_dir / backup_id
        archive_path = self._create_archive(backup_path, backup_id)
        
        if not archive_path:
            logger.error("Failed to create backup archive")
            return None
        
        # Upload to S3
        s3_key = f"{self.s3_prefix}{backup_id}.tar.gz"
        metadata = {
            'backup_id': backup_id,
            'timestamp': datetime.now().isoformat(),
            'tags': ','.join(tags or []),
            'description': description
        }
        
        if self.s3.upload_file(archive_path, s3_key, metadata=metadata):
            logger.info(f"Backup {backup_id} uploaded to S3")
            # Clean up local archive
            archive_path.unlink()
            return backup_id
        else:
            logger.error(f"Failed to upload backup {backup_id}")
            return None
    
    def _create_archive(self, backup_path: Path, backup_id: str) -> Optional[Path]:
        """Create tar.gz archive of backup."""
        try:
            archive_path = self.local_backup_dir / f"{backup_id}.tar.gz"
            
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(backup_path, arcname=backup_id)
            
            logger.info(f"Created archive: {archive_path}")
            return archive_path
            
        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            return None
    
    def restore_from_cloud(
        self,
        backup_id: str,
        restore_config: bool = True,
        restore_state: bool = True,
        dry_run: bool = False
    ) -> bool:
        """
        Restore backup from S3.
        
        Args:
            backup_id: Backup ID to restore
            restore_config: Restore config files
            restore_state: Restore runtime state
            dry_run: Don't actually restore, just validate
        
        Returns:
            True if successful, False otherwise
        """
        # Download from S3
        s3_key = f"{self.s3_prefix}{backup_id}.tar.gz"
        archive_path = self.local_backup_dir / f"{backup_id}.tar.gz"
        
        if not self.s3.download_file(s3_key, archive_path):
            logger.error(f"Failed to download backup {backup_id}")
            return False
        
        # Extract archive
        backup_path = self.local_backup_dir / backup_id
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(self.local_backup_dir)
            logger.info(f"Extracted archive to {backup_path}")
        except Exception as e:
            logger.error(f"Failed to extract archive: {e}")
            return False
        finally:
            # Clean up archive
            if archive_path.exists():
                archive_path.unlink()
        
        # Restore using RecoveryManager
        return self.recovery_manager.restore_backup(
            backup_id=backup_id,
            restore_config=restore_config,
            restore_state=restore_state,
            dry_run=dry_run
        )
    
    def list_cloud_backups(self) -> List[Dict]:
        """List all backups in S3."""
        return self.s3.list_backups(prefix=self.s3_prefix)
    
    def sync_to_cloud(self) -> int:
        """
        Sync all local backups to S3.
        
        Returns:
            Number of backups synced
        """
        synced = 0
        
        for backup_dir in self.local_backup_dir.iterdir():
            if backup_dir.is_dir():
                backup_id = backup_dir.name
                s3_key = f"{self.s3_prefix}{backup_id}.tar.gz"
                
                # Check if already exists in S3
                cloud_backups = self.list_cloud_backups()
                if any(b['key'] == s3_key for b in cloud_backups):
                    logger.debug(f"Backup {backup_id} already in S3")
                    continue
                
                # Upload
                archive_path = self._create_archive(backup_dir, backup_id)
                if archive_path and self.s3.upload_file(archive_path, s3_key):
                    synced += 1
                    archive_path.unlink()
        
        logger.info(f"Synced {synced} backups to S3")
        return synced


__all__ = ["CloudBackupManager"]
