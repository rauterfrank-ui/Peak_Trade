"""
Backup Manager
===============

Manages creation, storage, and lifecycle of backups.

CLI Usage:
    python -m src.infra.backup.backup_manager create --type portfolio
    python -m src.infra.backup.backup_manager list
    python -m src.infra.backup.backup_manager restore --id <backup_id>
"""

from __future__ import annotations

import gzip
import json
import logging
import shutil
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    
    backup_id: str
    backup_type: str
    timestamp: datetime
    size_bytes: int
    compressed: bool
    source_path: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BackupMetadata:
        """Create from dictionary."""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class BackupManager:
    """
    Manages backups for Peak Trade.
    
    Handles creation, listing, and management of backups with
    retention policies and compression.
    """
    
    def __init__(
        self,
        backup_dir: str = "./backups",
        retention_days: int = 30,
        compress: bool = True,
    ):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory for storing backups
            retention_days: Days to retain backups
            compress: Whether to compress backups
        """
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.compress = compress
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"BackupManager initialized: dir={backup_dir}, "
            f"retention={retention_days} days"
        )
    
    def create_backup(
        self,
        backup_type: str,
        source_path: str,
        description: Optional[str] = None,
    ) -> str:
        """
        Create a backup.
        
        Args:
            backup_type: Type of backup (e.g., "portfolio", "config")
            source_path: Path to data to backup
            description: Optional description
            
        Returns:
            Backup ID
        """
        # Generate backup ID
        timestamp = datetime.now()
        backup_id = f"{backup_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Create backup directory
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copy source data
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source path not found: {source_path}")
        
        if source.is_file():
            # Backup single file
            dest = backup_path / source.name
            if self.compress:
                self._compress_file(source, dest.with_suffix(dest.suffix + ".gz"))
            else:
                shutil.copy2(source, dest)
        else:
            # Backup directory
            dest = backup_path / source.name
            shutil.copytree(source, dest)
            
            if self.compress:
                # Compress directory into archive
                archive_path = backup_path / f"{source.name}.tar.gz"
                shutil.make_archive(
                    str(archive_path.with_suffix("")),
                    "gztar",
                    root_dir=backup_path,
                    base_dir=source.name,
                )
                # Remove uncompressed directory
                shutil.rmtree(dest)
        
        # Calculate total size
        total_size = sum(
            f.stat().st_size
            for f in backup_path.rglob("*")
            if f.is_file()
        )
        
        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            timestamp=timestamp,
            size_bytes=total_size,
            compressed=self.compress,
            source_path=source_path,
            description=description,
        )
        
        # Save metadata
        metadata_file = backup_path / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        logger.info(
            f"Backup created: {backup_id} "
            f"(size={total_size / 1024:.2f} KB, compressed={self.compress})"
        )
        
        return backup_id
    
    def _compress_file(self, source: Path, dest: Path) -> None:
        """Compress a file using gzip."""
        with open(source, "rb") as f_in:
            with gzip.open(dest, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def list_backups(
        self,
        backup_type: Optional[str] = None,
    ) -> List[BackupMetadata]:
        """
        List all backups.
        
        Args:
            backup_type: Filter by backup type
            
        Returns:
            List of backup metadata
        """
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if not backup_dir.is_dir():
                continue
            
            metadata_file = backup_dir / "metadata.json"
            if not metadata_file.exists():
                continue
            
            try:
                with open(metadata_file) as f:
                    data = json.load(f)
                metadata = BackupMetadata.from_dict(data)
                
                # Filter by type if specified
                if backup_type and metadata.backup_type != backup_type:
                    continue
                
                backups.append(metadata)
                
            except Exception as e:
                logger.warning(f"Failed to load backup metadata: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        
        return backups
    
    def get_backup_path(self, backup_id: str) -> Path:
        """
        Get path to a backup.
        
        Args:
            backup_id: Backup ID
            
        Returns:
            Path to backup directory
            
        Raises:
            FileNotFoundError: If backup not found
        """
        backup_path = self.backup_dir / backup_id
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")
        return backup_path
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.
        
        Args:
            backup_id: Backup ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            backup_path = self.get_backup_path(backup_id)
            shutil.rmtree(backup_path)
            logger.info(f"Backup deleted: {backup_id}")
            return True
        except FileNotFoundError:
            logger.warning(f"Backup not found: {backup_id}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """
        Delete backups older than retention period.
        
        Returns:
            Number of backups deleted
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0
        
        for metadata in self.list_backups():
            if metadata.timestamp < cutoff_date:
                if self.delete_backup(metadata.backup_id):
                    deleted_count += 1
        
        logger.info(
            f"Cleaned up {deleted_count} old backups "
            f"(older than {self.retention_days} days)"
        )
        
        return deleted_count


def main() -> int:
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Peak Trade Backup Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create backup
    create_parser = subparsers.add_parser("create", help="Create a backup")
    create_parser.add_argument("--type", required=True, help="Backup type")
    create_parser.add_argument("--source", required=True, help="Source path")
    create_parser.add_argument("--description", help="Backup description")
    
    # List backups
    list_parser = subparsers.add_parser("list", help="List backups")
    list_parser.add_argument("--type", help="Filter by backup type")
    
    # Delete backup
    delete_parser = subparsers.add_parser("delete", help="Delete a backup")
    delete_parser.add_argument("--id", required=True, help="Backup ID")
    
    # Cleanup old backups
    subparsers.add_parser("cleanup", help="Clean up old backups")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    
    manager = BackupManager()
    
    if args.command == "create":
        try:
            backup_id = manager.create_backup(
                backup_type=args.type,
                source_path=args.source,
                description=args.description,
            )
            print(f"Backup created: {backup_id}")
            return 0
        except Exception as e:
            print(f"Error creating backup: {e}", file=sys.stderr)
            return 1
    
    elif args.command == "list":
        backups = manager.list_backups(backup_type=args.type)
        
        if not backups:
            print("No backups found")
            return 0
        
        print(f"\nFound {len(backups)} backup(s):\n")
        for backup in backups:
            print(f"ID: {backup.backup_id}")
            print(f"  Type: {backup.backup_type}")
            print(f"  Date: {backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Size: {backup.size_bytes / 1024:.2f} KB")
            if backup.description:
                print(f"  Description: {backup.description}")
            print()
        
        return 0
    
    elif args.command == "delete":
        if manager.delete_backup(args.id):
            print(f"Backup deleted: {args.id}")
            return 0
        else:
            print(f"Backup not found: {args.id}", file=sys.stderr)
            return 1
    
    elif args.command == "cleanup":
        count = manager.cleanup_old_backups()
        print(f"Cleaned up {count} old backup(s)")
        return 0
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
