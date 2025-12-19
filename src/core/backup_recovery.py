"""
Peak_Trade Backup & Recovery Module
===================================
Provides backup and recovery functionality for critical system state, configuration,
and data to ensure resilience and disaster recovery capabilities.

Module Components:
- StateSnapshot: Captures system state snapshots
- ConfigBackup: Backs up configuration files
- DataBackup: Backs up critical data files
- RecoveryManager: Orchestrates backup and recovery operations

Usage:
    from src.core.backup_recovery import RecoveryManager
    
    # Create recovery manager
    recovery_mgr = RecoveryManager(backup_dir="backups")
    
    # Create backup
    backup_id = recovery_mgr.create_backup(
        include_config=True,
        include_state=True,
        include_data=True
    )
    
    # Restore from backup
    recovery_mgr.restore_backup(backup_id)
    
    # List available backups
    backups = recovery_mgr.list_backups()
"""

import json
import logging
import shutil
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    if hasattr(datetime, 'UTC'):
        return datetime.now(datetime.UTC)
    else:
        return datetime.utcnow()


class BackupType(Enum):
    """Types of backups."""
    FULL = "full"           # Complete backup (config + state + data)
    CONFIG = "config"       # Configuration files only
    STATE = "state"         # System state only
    DATA = "data"           # Data files only
    INCREMENTAL = "incremental"  # Changed files only


class BackupStatus(Enum):
    """Backup operation status."""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"


@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    backup_id: str
    backup_type: BackupType
    created_at: str  # ISO format timestamp
    status: BackupStatus
    size_bytes: int = 0
    files_count: int = 0
    description: str = ""
    tags: List[str] = field(default_factory=list)
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['backup_type'] = self.backup_type.value
        data['status'] = self.status.value
        return data


class StateSnapshot:
    """
    Captures and restores system state snapshots.
    
    State includes runtime information, metrics, and operational data
    that should be preserved for recovery.
    """
    
    def __init__(self):
        self._state_providers: Dict[str, Callable] = {}
        logger.info("StateSnapshot initialized")
    
    def register_provider(self, name: str, provider_func: Callable) -> None:
        """
        Register a state provider function.
        
        Args:
            name: Unique name for the state provider
            provider_func: Function that returns state dict
            
        Example:
            def get_system_metrics():
                return {"cpu_usage": 50, "memory_mb": 1024}
            
            snapshot.register_provider("metrics", get_system_metrics)
        """
        self._state_providers[name] = provider_func
        logger.info(f"State provider '{name}' registered")
    
    def capture(self) -> Dict[str, Any]:
        """
        Capture current system state from all registered providers.
        
        Returns:
            Dictionary containing state from all providers
        """
        state = {
            "timestamp": get_utc_now().isoformat(),
            "providers": {}
        }
        
        for name, provider in self._state_providers.items():
            try:
                provider_state = provider()
                state["providers"][name] = provider_state
                logger.debug(f"Captured state from provider '{name}'")
            except Exception as e:
                logger.error(f"Failed to capture state from provider '{name}': {e}")
                state["providers"][name] = {"error": str(e)}
        
        return state
    
    def save(self, output_path: Path) -> None:
        """
        Capture state and save to file.
        
        Args:
            output_path: Path to save the state snapshot
        """
        state = self.capture()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        logger.info(f"State snapshot saved to {output_path}")
    
    def load(self, input_path: Path) -> Dict[str, Any]:
        """
        Load state snapshot from file.
        
        Args:
            input_path: Path to load the state snapshot from
            
        Returns:
            State dictionary
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        logger.info(f"State snapshot loaded from {input_path}")
        return state


class ConfigBackup:
    """
    Backs up and restores configuration files.
    
    Handles TOML, JSON, and other configuration file formats.
    """
    
    def __init__(self, config_paths: Optional[List[Path]] = None):
        """
        Initialize configuration backup.
        
        Args:
            config_paths: List of configuration file paths to back up
        """
        self.config_paths = config_paths or []
        logger.info(f"ConfigBackup initialized with {len(self.config_paths)} paths")
    
    def add_config(self, path: Path) -> None:
        """Add a configuration file to backup list."""
        if path not in self.config_paths:
            self.config_paths.append(path)
            logger.debug(f"Added config path: {path}")
    
    def backup(self, backup_dir: Path) -> int:
        """
        Backup all configuration files to backup directory.
        
        Args:
            backup_dir: Directory to store backups
            
        Returns:
            Number of files backed up
        """
        backup_dir.mkdir(parents=True, exist_ok=True)
        files_backed_up = 0
        
        for config_path in self.config_paths:
            if not config_path.exists():
                logger.warning(f"Config file not found: {config_path}")
                continue
            
            try:
                # Use just the filename to avoid path issues
                dest_path = backup_dir / config_path.name
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(config_path, dest_path)
                files_backed_up += 1
                logger.debug(f"Backed up config: {config_path} -> {dest_path}")
            except Exception as e:
                logger.error(f"Failed to backup config {config_path}: {e}")
        
        logger.info(f"Backed up {files_backed_up} configuration files")
        return files_backed_up
    
    def restore(self, backup_dir: Path, dry_run: bool = False) -> int:
        """
        Restore configuration files from backup directory.
        
        Args:
            backup_dir: Directory containing backups
            dry_run: If True, only simulate restore without actual changes
            
        Returns:
            Number of files restored
        """
        if not backup_dir.exists():
            logger.error(f"Backup directory not found: {backup_dir}")
            return 0
        
        files_restored = 0
        
        for config_path in self.config_paths:
            try:
                # Use just the filename to match backup logic
                source_path = backup_dir / config_path.name
                
                if not source_path.exists():
                    logger.warning(f"Backup file not found: {source_path}")
                    continue
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would restore: {source_path} -> {config_path}")
                else:
                    config_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, config_path)
                    logger.info(f"Restored config: {source_path} -> {config_path}")
                
                files_restored += 1
            except Exception as e:
                logger.error(f"Failed to restore config {config_path}: {e}")
        
        action = "Would restore" if dry_run else "Restored"
        logger.info(f"{action} {files_restored} configuration files")
        return files_restored


class DataBackup:
    """
    Backs up and restores critical data files and directories.
    
    Handles data files that need to be preserved for recovery.
    """
    
    def __init__(self, data_paths: Optional[List[Path]] = None):
        """
        Initialize data backup.
        
        Args:
            data_paths: List of data file/directory paths to back up
        """
        self.data_paths = data_paths or []
        logger.info(f"DataBackup initialized with {len(self.data_paths)} paths")
    
    def add_data_path(self, path: Path) -> None:
        """Add a data path to backup list."""
        if path not in self.data_paths:
            self.data_paths.append(path)
            logger.debug(f"Added data path: {path}")
    
    def backup(self, backup_dir: Path) -> tuple[int, int]:
        """
        Backup all data files to backup directory.
        
        Args:
            backup_dir: Directory to store backups
            
        Returns:
            Tuple of (files_count, total_size_bytes)
        """
        backup_dir.mkdir(parents=True, exist_ok=True)
        files_backed_up = 0
        total_size = 0
        
        for data_path in self.data_paths:
            if not data_path.exists():
                logger.warning(f"Data path not found: {data_path}")
                continue
            
            try:
                # Use just the filename/dirname for simpler path handling
                dest_path = backup_dir / data_path.name
                
                if data_path.is_file():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(data_path, dest_path)
                    total_size += data_path.stat().st_size
                    files_backed_up += 1
                elif data_path.is_dir():
                    shutil.copytree(data_path, dest_path, dirs_exist_ok=True)
                    # Count files and size
                    for file in dest_path.rglob('*'):
                        if file.is_file():
                            files_backed_up += 1
                            total_size += file.stat().st_size
                
                logger.debug(f"Backed up data: {data_path} -> {dest_path}")
            except Exception as e:
                logger.error(f"Failed to backup data {data_path}: {e}")
        
        logger.info(f"Backed up {files_backed_up} data files ({total_size} bytes)")
        return files_backed_up, total_size
    
    def restore(self, backup_dir: Path, dry_run: bool = False) -> int:
        """
        Restore data files from backup directory.
        
        Args:
            backup_dir: Directory containing backups
            dry_run: If True, only simulate restore without actual changes
            
        Returns:
            Number of files restored
        """
        if not backup_dir.exists():
            logger.error(f"Backup directory not found: {backup_dir}")
            return 0
        
        files_restored = 0
        
        for data_path in self.data_paths:
            try:
                # Use just the filename/dirname to match backup logic
                source_path = backup_dir / data_path.name
                
                if not source_path.exists():
                    logger.warning(f"Backup path not found: {source_path}")
                    continue
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would restore: {source_path} -> {data_path}")
                    if source_path.is_file():
                        files_restored += 1
                    else:
                        files_restored += sum(1 for _ in source_path.rglob('*') if _.is_file())
                else:
                    if source_path.is_file():
                        data_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, data_path)
                        files_restored += 1
                    elif source_path.is_dir():
                        shutil.copytree(source_path, data_path, dirs_exist_ok=True)
                        files_restored += sum(1 for _ in data_path.rglob('*') if _.is_file())
                    
                    logger.info(f"Restored data: {source_path} -> {data_path}")
            except Exception as e:
                logger.error(f"Failed to restore data {data_path}: {e}")
        
        action = "Would restore" if dry_run else "Restored"
        logger.info(f"{action} {files_restored} data files")
        return files_restored


class RecoveryManager:
    """
    Orchestrates backup and recovery operations.
    
    Manages backup lifecycle, metadata, and recovery workflows.
    
    Example:
        recovery = RecoveryManager(backup_dir="backups")
        
        # Create backup
        backup_id = recovery.create_backup(
            include_config=True,
            include_state=True,
            description="Daily backup"
        )
        
        # List backups
        backups = recovery.list_backups()
        
        # Restore
        recovery.restore_backup(backup_id)
    """
    
    def __init__(self, backup_dir: str = "backups"):
        """
        Initialize recovery manager.
        
        Args:
            backup_dir: Root directory for all backups
        """
        self.backup_root = Path(backup_dir)
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        self.state_snapshot = StateSnapshot()
        self.config_backup = ConfigBackup()
        self.data_backup = DataBackup()
        
        logger.info(f"RecoveryManager initialized with backup_dir={backup_dir}")
    
    def _generate_backup_id(self) -> str:
        """Generate unique backup ID based on timestamp with microseconds."""
        timestamp = time.time()
        # Include microseconds for uniqueness
        return f"backup_{int(timestamp * 1000000)}_{get_utc_now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def _get_backup_dir(self, backup_id: str) -> Path:
        """Get backup directory path for a given backup ID."""
        return self.backup_root / backup_id
    
    def _save_metadata(self, backup_dir: Path, metadata: BackupMetadata) -> None:
        """Save backup metadata to file."""
        metadata_file = backup_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved metadata for backup {metadata.backup_id}")
    
    def _load_metadata(self, backup_dir: Path) -> Optional[BackupMetadata]:
        """Load backup metadata from file."""
        metadata_file = backup_dir / "metadata.json"
        if not metadata_file.exists():
            return None
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert string enums back to enum instances
        data['backup_type'] = BackupType(data['backup_type'])
        data['status'] = BackupStatus(data['status'])
        
        return BackupMetadata(**data)
    
    def create_backup(
        self,
        include_config: bool = True,
        include_state: bool = True,
        include_data: bool = False,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Create a new backup.
        
        Args:
            include_config: Include configuration files
            include_state: Include system state snapshot
            include_data: Include data files
            description: Human-readable description
            tags: Optional tags for categorization
            
        Returns:
            Backup ID
        """
        backup_id = self._generate_backup_id()
        backup_dir = self._get_backup_dir(backup_id)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Creating backup {backup_id}")
        
        # Determine backup type
        if include_config and include_state and include_data:
            backup_type = BackupType.FULL
        elif include_config:
            backup_type = BackupType.CONFIG
        elif include_state:
            backup_type = BackupType.STATE
        elif include_data:
            backup_type = BackupType.DATA
        else:
            backup_type = BackupType.FULL
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            created_at=get_utc_now().isoformat(),
            status=BackupStatus.IN_PROGRESS,
            description=description,
            tags=tags or []
        )
        
        try:
            files_count = 0
            total_size = 0
            
            # Backup configuration
            if include_config and len(self.config_backup.config_paths) > 0:
                config_dir = backup_dir / "config"
                count = self.config_backup.backup(config_dir)
                files_count += count
            
            # Backup state
            if include_state:
                state_file = backup_dir / "state.json"
                self.state_snapshot.save(state_file)
                files_count += 1
                total_size += state_file.stat().st_size
            
            # Backup data
            if include_data and len(self.data_backup.data_paths) > 0:
                data_dir = backup_dir / "data"
                count, size = self.data_backup.backup(data_dir)
                files_count += count
                total_size += size
            
            # Update metadata
            metadata.status = BackupStatus.SUCCESS
            metadata.files_count = files_count
            metadata.size_bytes = total_size
            self._save_metadata(backup_dir, metadata)
            
            logger.info(
                f"Backup {backup_id} completed successfully: "
                f"{files_count} files, {total_size} bytes"
            )
            
        except Exception as e:
            logger.error(f"Backup {backup_id} failed: {e}", exc_info=True)
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            self._save_metadata(backup_dir, metadata)
            raise
        
        return backup_id
    
    def restore_backup(
        self,
        backup_id: str,
        restore_config: bool = True,
        restore_state: bool = False,
        restore_data: bool = False,
        dry_run: bool = False
    ) -> bool:
        """
        Restore from a backup.
        
        Args:
            backup_id: ID of the backup to restore
            restore_config: Restore configuration files
            restore_state: Restore state (note: requires manual application)
            restore_data: Restore data files
            dry_run: If True, only simulate restore
            
        Returns:
            True if restore successful, False otherwise
        """
        backup_dir = self._get_backup_dir(backup_id)
        if not backup_dir.exists():
            logger.error(f"Backup {backup_id} not found")
            return False
        
        metadata = self._load_metadata(backup_dir)
        if not metadata:
            logger.error(f"Metadata not found for backup {backup_id}")
            return False
        
        if metadata.status != BackupStatus.SUCCESS:
            logger.error(
                f"Cannot restore backup {backup_id} with status {metadata.status.value}"
            )
            return False
        
        action = "DRY RUN restore" if dry_run else "Restoring"
        logger.info(f"{action} from backup {backup_id}")
        
        try:
            # Restore configuration
            if restore_config:
                config_dir = backup_dir / "config"
                if config_dir.exists():
                    self.config_backup.restore(config_dir, dry_run=dry_run)
            
            # Restore state
            if restore_state:
                state_file = backup_dir / "state.json"
                if state_file.exists():
                    state = self.state_snapshot.load(state_file)
                    logger.info(
                        f"State snapshot loaded (manual application required): "
                        f"{len(state.get('providers', {}))} providers"
                    )
            
            # Restore data
            if restore_data:
                data_dir = backup_dir / "data"
                if data_dir.exists():
                    self.data_backup.restore(data_dir, dry_run=dry_run)
            
            logger.info(f"Restore from backup {backup_id} completed")
            return True
            
        except Exception as e:
            logger.error(f"Restore from backup {backup_id} failed: {e}", exc_info=True)
            return False
    
    def list_backups(
        self,
        tags: Optional[List[str]] = None,
        backup_type: Optional[BackupType] = None
    ) -> List[BackupMetadata]:
        """
        List available backups.
        
        Args:
            tags: Filter by tags
            backup_type: Filter by backup type
            
        Returns:
            List of backup metadata, sorted by creation time (newest first)
        """
        backups = []
        
        for backup_dir in self.backup_root.iterdir():
            if not backup_dir.is_dir():
                continue
            
            metadata = self._load_metadata(backup_dir)
            if not metadata:
                continue
            
            # Apply filters
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            
            if backup_type and metadata.backup_type != backup_type:
                continue
            
            backups.append(metadata)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda m: m.created_at, reverse=True)
        
        logger.debug(f"Listed {len(backups)} backups")
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.
        
        Args:
            backup_id: ID of the backup to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        backup_dir = self._get_backup_dir(backup_id)
        if not backup_dir.exists():
            logger.warning(f"Backup {backup_id} not found")
            return False
        
        try:
            shutil.rmtree(backup_dir)
            logger.info(f"Deleted backup {backup_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """
        Delete old backups, keeping only the most recent ones.
        
        Args:
            keep_count: Number of backups to keep
            
        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            logger.info(f"No cleanup needed, have {len(backups)} backups (keep {keep_count})")
            return 0
        
        backups_to_delete = backups[keep_count:]
        deleted_count = 0
        
        for metadata in backups_to_delete:
            if self.delete_backup(metadata.backup_id):
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old backups")
        return deleted_count


__all__ = [
    "BackupType",
    "BackupStatus",
    "BackupMetadata",
    "StateSnapshot",
    "ConfigBackup",
    "DataBackup",
    "RecoveryManager",
]
