#!/usr/bin/env python
"""
Backup Manager CLI

Command-line interface for backup management.
Usage:
    python -m src.infra.backup.backup_manager create [--type TYPE]
    python -m src.infra.backup.backup_manager list [--type TYPE]
    python -m src.infra.backup.backup_manager restore [BACKUP_ID]
    python -m src.infra.backup.backup_manager delete BACKUP_ID
"""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.infra.backup import BackupManager, BackupConfig, RecoveryManager


def cmd_create(args):
    """Create backup"""
    backup_type = "manual"
    if "--type" in args:
        idx = args.index("--type")
        if idx + 1 < len(args):
            backup_type = args[idx + 1]
    
    manager = BackupManager()
    
    # Sammle Daten zum Sichern
    data = {
        "timestamp": datetime.now().isoformat(),
        "note": f"Manual backup created via CLI at {datetime.now()}",
    }
    
    # Füge Portfolio-State hinzu (wenn vorhanden)
    # TODO: Implement portfolio state collection
    
    backup_id = manager.create_backup(data, backup_type=backup_type)
    print(f"✓ Backup created: {backup_id}")
    
    # Zeige Info
    backups = manager.list_backups()
    if backups:
        latest = backups[0]
        print(f"  Size: {latest.size_bytes / 1024:.1f} KB")
        print(f"  Files: {len(latest.files)}")


def cmd_list(args):
    """List backups"""
    backup_type = None
    if "--type" in args:
        idx = args.index("--type")
        if idx + 1 < len(args):
            backup_type = args[idx + 1]
    
    manager = BackupManager()
    backups = manager.list_backups(backup_type=backup_type)
    
    if not backups:
        print("No backups found.")
        return
    
    print(f"\nFound {len(backups)} backup(s):\n")
    print(f"{'Backup ID':<40} {'Type':<12} {'Size (KB)':<12} {'Timestamp'}")
    print("-" * 90)
    
    for backup in backups:
        size_kb = backup.size_bytes / 1024
        timestamp = backup.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{backup.backup_id:<40} {backup.backup_type:<12} {size_kb:<12.1f} {timestamp}")


def cmd_restore(args):
    """Restore backup"""
    recovery = RecoveryManager()
    
    # Backup-ID aus args oder latest
    backup_id = None
    if len(args) > 1:
        backup_id = args[1]
    
    if backup_id is None:
        # Restore latest
        backup_id = recovery.get_latest_backup()
        if backup_id is None:
            print("Error: No backups found")
            sys.exit(1)
        print(f"Restoring latest backup: {backup_id}")
    else:
        print(f"Restoring backup: {backup_id}")
    
    try:
        data = recovery.restore_backup(backup_id)
        print(f"✓ Backup restored successfully")
        print(f"  Keys: {list(data.keys())}")
    except Exception as e:
        print(f"✗ Restore failed: {e}")
        sys.exit(1)


def cmd_delete(args):
    """Delete backup"""
    if len(args) < 2:
        print("Error: BACKUP_ID required")
        sys.exit(1)
    
    backup_id = args[1]
    manager = BackupManager()
    
    # Bestätige
    print(f"Delete backup '{backup_id}'? (y/N): ", end="")
    confirm = input().strip().lower()
    
    if confirm != "y":
        print("Cancelled")
        return
    
    try:
        manager.delete_backup(backup_id)
        print(f"✓ Backup deleted: {backup_id}")
    except Exception as e:
        print(f"✗ Delete failed: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[1:]
    
    if command == "create":
        cmd_create(args)
    elif command == "list":
        cmd_list(args)
    elif command == "restore":
        cmd_restore(args)
    elif command == "delete":
        cmd_delete(args)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
