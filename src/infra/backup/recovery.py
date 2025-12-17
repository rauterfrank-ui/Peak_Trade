"""
Recovery Manager
=================

Handles restoration of backups.
"""

from __future__ import annotations

import gzip
import logging
import shutil
import tarfile
from pathlib import Path
from typing import Optional

from src.infra.backup.backup_manager import BackupManager, BackupMetadata

logger = logging.getLogger(__name__)


class RecoveryManager:
    """
    Manages recovery from backups.
    
    Handles restoration of backed-up data with validation.
    """
    
    def __init__(self, backup_manager: Optional[BackupManager] = None):
        """
        Initialize recovery manager.
        
        Args:
            backup_manager: BackupManager instance (creates new if None)
        """
        self.backup_manager = backup_manager or BackupManager()
    
    def restore_backup(
        self,
        backup_id: str,
        destination: str,
        overwrite: bool = False,
    ) -> bool:
        """
        Restore a backup to a destination.
        
        Args:
            backup_id: Backup ID to restore
            destination: Destination path
            overwrite: Whether to overwrite existing files
            
        Returns:
            True if successful
            
        Raises:
            FileNotFoundError: If backup not found
            FileExistsError: If destination exists and overwrite=False
        """
        # Get backup path
        backup_path = self.backup_manager.get_backup_path(backup_id)
        
        # Load metadata
        metadata_file = backup_path / "metadata.json"
        import json
        with open(metadata_file) as f:
            data = json.load(f)
        metadata = BackupMetadata.from_dict(data)
        
        logger.info(f"Restoring backup: {backup_id} to {destination}")
        
        # Check destination
        dest = Path(destination)
        if dest.exists() and not overwrite:
            raise FileExistsError(
                f"Destination exists: {destination}. Use overwrite=True to replace."
            )
        
        # Find backup files (excluding metadata)
        backup_files = [
            f for f in backup_path.iterdir()
            if f.name != "metadata.json"
        ]
        
        if not backup_files:
            raise ValueError(f"No backup data found in {backup_id}")
        
        # Restore based on file type
        if len(backup_files) == 1:
            backup_file = backup_files[0]
            
            # Check if it's a compressed archive
            if backup_file.suffix == ".gz" and backup_file.stem.endswith(".tar"):
                # Extract tar.gz archive
                self._extract_archive(backup_file, dest.parent)
                logger.info(f"Extracted archive to {dest.parent}")
            
            elif backup_file.suffix == ".gz":
                # Decompress single file
                self._decompress_file(backup_file, dest)
                logger.info(f"Decompressed file to {dest}")
            
            else:
                # Copy file directly
                if dest.is_dir():
                    dest = dest / backup_file.name
                shutil.copy2(backup_file, dest)
                logger.info(f"Copied file to {dest}")
        else:
            # Multiple files, copy directory
            dest.mkdir(parents=True, exist_ok=True)
            for backup_file in backup_files:
                shutil.copy2(backup_file, dest / backup_file.name)
            logger.info(f"Copied {len(backup_files)} files to {dest}")
        
        logger.info(f"Backup restored successfully: {backup_id}")
        return True
    
    def _extract_archive(self, archive_path: Path, destination: Path) -> None:
        """Extract a tar.gz archive."""
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(destination)
    
    def _decompress_file(self, source: Path, dest: Path) -> None:
        """Decompress a gzip file."""
        # Remove .gz extension for output file
        if dest.is_dir():
            dest = dest / source.stem
        
        with gzip.open(source, "rb") as f_in:
            with open(dest, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify a backup's integrity.
        
        Args:
            backup_id: Backup ID to verify
            
        Returns:
            True if backup is valid
        """
        try:
            # Get backup path
            backup_path = self.backup_manager.get_backup_path(backup_id)
            
            # Check metadata exists
            metadata_file = backup_path / "metadata.json"
            if not metadata_file.exists():
                logger.error(f"Backup {backup_id} missing metadata")
                return False
            
            # Load and validate metadata
            import json
            with open(metadata_file) as f:
                data = json.load(f)
            metadata = BackupMetadata.from_dict(data)
            
            # Check backup files exist
            backup_files = [
                f for f in backup_path.iterdir()
                if f.name != "metadata.json"
            ]
            
            if not backup_files:
                logger.error(f"Backup {backup_id} has no data files")
                return False
            
            logger.info(f"Backup {backup_id} verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
