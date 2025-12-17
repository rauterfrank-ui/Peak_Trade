"""
Backup Manager

Automatische Backups für Portfolio-States, Trading-History und Konfigurationen.
"""

import gzip
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BackupConfig:
    """Backup-Konfiguration"""
    backup_path: str = "./backups"
    compress: bool = True
    retention_days: int = 30
    include_portfolio: bool = True
    include_history: bool = True
    include_config: bool = True
    include_learned: bool = True


@dataclass
class BackupInfo:
    """Backup-Metadaten"""
    backup_id: str
    timestamp: datetime
    backup_type: str
    size_bytes: int
    compressed: bool
    files: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary"""
        return {
            "backup_id": self.backup_id,
            "timestamp": self.timestamp.isoformat(),
            "backup_type": self.backup_type,
            "size_bytes": self.size_bytes,
            "compressed": self.compressed,
            "files": self.files,
        }


class BackupManager:
    """
    Backup-Manager für automatische Backups.
    
    Beispiel:
        manager = BackupManager(config)
        
        # Erstelle Backup
        backup_id = manager.create_backup(data={"portfolio": {...}})
        
        # Liste Backups
        backups = manager.list_backups()
        
        # Lade Backup
        data = manager.load_backup(backup_id)
    """

    def __init__(self, config: Optional[BackupConfig] = None):
        self.config = config or BackupConfig()
        self.backup_dir = Path(self.config.backup_path)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        data: Dict[str, Any],
        backup_type: str = "manual",
    ) -> str:
        """
        Erstelle Backup.
        
        Args:
            data: Daten die gesichert werden sollen
            backup_type: Type des Backups (manual, automatic, scheduled)
            
        Returns:
            Backup-ID
        """
        # Generiere Backup-ID
        timestamp = datetime.now()
        backup_id = f"{backup_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        files = []
        total_size = 0
        
        # Speichere Daten
        for key, value in data.items():
            filename = f"{key}.json"
            file_path = backup_path / filename
            
            # Schreibe JSON
            json_data = json.dumps(value, indent=2)
            
            if self.config.compress:
                file_path = backup_path / f"{filename}.gz"
                with gzip.open(file_path, "wt", encoding="utf-8") as f:
                    f.write(json_data)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(json_data)
            
            files.append(str(file_path.name))
            total_size += file_path.stat().st_size
        
        # Speichere Metadaten
        backup_info = BackupInfo(
            backup_id=backup_id,
            timestamp=timestamp,
            backup_type=backup_type,
            size_bytes=total_size,
            compressed=self.config.compress,
            files=files,
        )
        
        metadata_path = backup_path / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(backup_info.to_dict(), f, indent=2)
        
        # Cleanup alte Backups
        self._cleanup_old_backups()
        
        return backup_id

    def load_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Lade Backup.
        
        Args:
            backup_id: Backup-ID
            
        Returns:
            Backup-Daten
        """
        backup_path = self.backup_dir / backup_id
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup '{backup_id}' not found")
        
        # Lade Metadaten
        metadata_path = backup_path / "metadata.json"
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        # Lade Daten
        data = {}
        for filename in metadata["files"]:
            file_path = backup_path / filename
            
            # Bestimme Key (entferne .json oder .json.gz)
            key = filename.replace(".json.gz", "").replace(".json", "")
            
            # Lade JSON
            if filename.endswith(".gz"):
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    data[key] = json.load(f)
            else:
                with open(file_path, encoding="utf-8") as f:
                    data[key] = json.load(f)
        
        return data

    def list_backups(self, backup_type: Optional[str] = None) -> List[BackupInfo]:
        """
        Liste alle Backups.
        
        Args:
            backup_type: Optional: Filtere nach Backup-Type
            
        Returns:
            Liste von BackupInfo
        """
        backups = []
        
        for backup_path in sorted(self.backup_dir.iterdir()):
            if not backup_path.is_dir():
                continue
            
            metadata_path = backup_path / "metadata.json"
            if not metadata_path.exists():
                continue
            
            with open(metadata_path) as f:
                metadata = json.load(f)
            
            # Filtere nach Type
            if backup_type and metadata["backup_type"] != backup_type:
                continue
            
            backup_info = BackupInfo(
                backup_id=metadata["backup_id"],
                timestamp=datetime.fromisoformat(metadata["timestamp"]),
                backup_type=metadata["backup_type"],
                size_bytes=metadata["size_bytes"],
                compressed=metadata["compressed"],
                files=metadata["files"],
            )
            backups.append(backup_info)
        
        return sorted(backups, key=lambda x: x.timestamp, reverse=True)

    def delete_backup(self, backup_id: str):
        """Lösche Backup"""
        backup_path = self.backup_dir / backup_id
        if backup_path.exists():
            shutil.rmtree(backup_path)

    def _cleanup_old_backups(self):
        """Lösche alte Backups basierend auf Retention-Policy"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        for backup_info in self.list_backups():
            if backup_info.timestamp < cutoff_date:
                self.delete_backup(backup_info.backup_id)


# Global Backup Manager
_global_backup_manager: Optional[BackupManager] = None


def get_backup_manager(config: Optional[BackupConfig] = None) -> BackupManager:
    """Hole globalen Backup Manager"""
    global _global_backup_manager
    if _global_backup_manager is None:
        _global_backup_manager = BackupManager(config)
    return _global_backup_manager
