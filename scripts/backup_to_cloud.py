#!/usr/bin/env python3
"""
Automated cloud backup script for Peak Trade.

Usage:
    python scripts/backup_to_cloud.py
    python scripts/backup_to_cloud.py --sync-all
    python scripts/backup_to_cloud.py --apply-retention
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
    """Main entry point for cloud backup script."""
    parser = argparse.ArgumentParser(description="Peak Trade Cloud Backup")
    parser.add_argument("--sync-all", action="store_true", help="Sync all local backups to S3")
    parser.add_argument("--apply-retention", action="store_true", help="Apply retention policy")
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
    
    # Initialize backup manager
    backup_manager = CloudBackupManager(s3)
    
    if args.sync_all:
        # Sync all local backups
        print("Syncing all local backups to S3...")
        synced = backup_manager.sync_to_cloud()
        print(f"✅ Synced {synced} backups to S3")
    
    elif args.apply_retention:
        # Apply retention policy
        print("Applying retention policy...")
        deleted = s3.apply_retention_policy()
        print(f"✅ Deleted {deleted} old backups")
    
    else:
        # Create new backup and upload
        print("Creating new backup...")
        backup_id = backup_manager.create_and_upload_backup(
            include_config=True,
            include_state=True,
            tags=["automated", "daily"],
            description="Automated daily backup"
        )
        
        if backup_id:
            print(f"✅ Backup created and uploaded: {backup_id}")
        else:
            print("❌ Backup failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
