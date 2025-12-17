"""
Recovery Manager

Recovery-Prozeduren für Backups.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .backup_manager import BackupManager, BackupConfig, get_backup_manager


class RecoveryError(Exception):
    """Raised bei Recovery-Fehlern"""
    pass


class RecoveryManager:
    """
    Recovery-Manager für Backup-Wiederherstellung.
    
    Beispiel:
        manager = RecoveryManager()
        
        # Restore Backup
        data = manager.restore_backup(backup_id)
        
        # Verify Backup
        is_valid = manager.verify_backup(backup_id)
    """

    def __init__(self, backup_manager: Optional[BackupManager] = None):
        self.backup_manager = backup_manager or get_backup_manager()

    def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Stelle Backup wieder her.
        
        Args:
            backup_id: Backup-ID
            
        Returns:
            Wiederhergestellte Daten
            
        Raises:
            RecoveryError: Wenn Wiederherstellung fehlschlägt
        """
        try:
            data = self.backup_manager.load_backup(backup_id)
            return data
        except Exception as e:
            raise RecoveryError(f"Failed to restore backup '{backup_id}': {e}") from e

    def verify_backup(self, backup_id: str) -> bool:
        """
        Verifiziere Backup-Integrität.
        
        Args:
            backup_id: Backup-ID
            
        Returns:
            True wenn Backup gültig ist
        """
        try:
            # Versuche Backup zu laden
            data = self.backup_manager.load_backup(backup_id)
            
            # Prüfe ob Daten nicht leer sind
            if not data:
                return False
            
            # Weitere Validierungen könnten hier hinzugefügt werden
            return True
            
        except Exception:
            return False

    def get_latest_backup(self, backup_type: Optional[str] = None) -> Optional[str]:
        """
        Hole neuestes Backup.
        
        Args:
            backup_type: Optional: Filtere nach Backup-Type
            
        Returns:
            Backup-ID oder None
        """
        backups = self.backup_manager.list_backups(backup_type=backup_type)
        if backups:
            return backups[0].backup_id
        return None

    def restore_latest_backup(self, backup_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Stelle neuestes Backup wieder her.
        
        Args:
            backup_type: Optional: Filtere nach Backup-Type
            
        Returns:
            Wiederhergestellte Daten
            
        Raises:
            RecoveryError: Wenn keine Backups gefunden oder Wiederherstellung fehlschlägt
        """
        backup_id = self.get_latest_backup(backup_type=backup_type)
        if backup_id is None:
            raise RecoveryError("No backups found")
        
        return self.restore_backup(backup_id)


# Global Recovery Manager
_global_recovery_manager: Optional[RecoveryManager] = None


def get_recovery_manager(
    backup_manager: Optional[BackupManager] = None
) -> RecoveryManager:
    """Hole globalen Recovery Manager"""
    global _global_recovery_manager
    if _global_recovery_manager is None:
        _global_recovery_manager = RecoveryManager(backup_manager)
    return _global_recovery_manager
