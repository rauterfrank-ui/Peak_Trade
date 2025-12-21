#!/usr/bin/env python3
"""
Restore backup from S3 cloud storage.

Usage:
    python scripts/restore_from_cloud.py --list
    python scripts/restore_from_cloud.py --backup-id BACKUP_ID
    python scripts/restore_from_cloud.py --backup-id BACKUP_ID --dry-run
"""

import argparse
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backup.s3_client import S3BackupClient
from src.backup.cloud_backup_manager import CloudBackupManager


def main():
    """Main entry point for restore from cloud script."""
    parser = argparse.ArgumentParser(description="Restore from Cloud")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--backup-id", help="Backup ID to restore")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (validate only)")
    args = parser.parse_args()
    
    # Get S3 configuration from environment
    bucket_name = os.getenv("S3_BUCKET_NAME", "peak-trade-backups")
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    endpoint_url = os.getenv("S3_ENDPOINT_URL")
    region = os.getenv("S3_REGION", "us-east-1")
    
    if not access_key or not secret_key:
        print("❌ Error: S3_ACCESS_KEY and S3_SECRET_KEY environment variables are required")
        print("Please set them in your environment or .env file")
        sys.exit(1)
    
    # Initialize S3 client
    try:
        s3 = S3BackupClient(
            bucket_name=bucket_name,
            access_key=access_key,
            secret_key=secret_key,
            endpoint_url=endpoint_url if endpoint_url else None,
            region=region
        )
    except Exception as e:
        print(f"❌ Failed to initialize S3 client: {e}")
        sys.exit(1)
    
    backup_manager = CloudBackupManager(s3)
    
    if args.list:
        # List backups
        print("📦 Listing backups in S3...\n")
        backups = backup_manager.list_cloud_backups()
        if not backups:
            print("No backups found in S3")
            return
        
        print(f"Found {len(backups)} backups:\n")
        for backup in backups:
            print(f"  - {backup['key']}")
            print(f"    Size: {backup['size'] / 1024 / 1024:.2f} MB")
            print(f"    Modified: {backup['last_modified']}")
            print()
    
    elif args.backup_id:
        # Restore backup
        print(f"{'[DRY RUN] ' if args.dry_run else ''}Restoring backup: {args.backup_id}")
        success = backup_manager.restore_from_cloud(
            backup_id=args.backup_id,
            dry_run=args.dry_run
        )
        
        if success:
            action = 'validated' if args.dry_run else 'completed'
            print(f"✅ Restore {action}: {args.backup_id}")
        else:
            print(f"❌ Restore failed: {args.backup_id}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
