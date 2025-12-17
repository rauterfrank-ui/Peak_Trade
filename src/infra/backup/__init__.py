"""
Backup & Recovery Module for Peak Trade
=========================================

Provides automated backup and recovery functionality for critical data.

Components:
    - BackupManager: Creates and manages backups
    - Recovery: Restores from backups

Usage:
    from src.infra.backup import BackupManager
    
    manager = BackupManager()
    backup_id = manager.create_backup("portfolio_state")
    manager.restore_backup(backup_id)
"""

from src.infra.backup.backup_manager import BackupManager, BackupMetadata
from src.infra.backup.recovery import RecoveryManager

__all__ = [
    "BackupManager",
    "BackupMetadata",
    "RecoveryManager",
]
