"""
S3-Compatible Cloud Backup Client
==================================

Provides S3-compatible storage integration for Peak Trade backups.

Supports:
- AWS S3
- MinIO
- DigitalOcean Spaces
- Any S3-compatible storage

Features:
- Automatic uploads
- Backup rotation
- Retention policies
- Encryption at rest
- Versioning support
"""

import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Optional, List, Dict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class S3BackupClient:
    """
    S3-compatible backup client.
    
    Supports AWS S3, MinIO, DigitalOcean Spaces, and any S3-compatible storage.
    
    Features:
    - Automatic uploads
    - Backup rotation
    - Retention policies
    - Encryption at rest
    - Versioning support
    """
    
    def __init__(
        self,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
        region: str = "us-east-1"
    ):
        """
        Initialize S3 backup client.
        
        Args:
            bucket_name: S3 bucket name
            access_key: AWS access key ID
            secret_key: AWS secret access key
            endpoint_url: Optional endpoint URL (for MinIO, Spaces, etc.)
            region: AWS region name
        """
        self.bucket_name = bucket_name
        
        # Initialize S3 client
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            region_name=region
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError:
            try:
                self.s3.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created bucket {self.bucket_name}")
            except ClientError as e:
                logger.error(f"Failed to create bucket: {e}")
                raise
    
    def upload_file(
        self,
        local_path: Path,
        s3_key: str,
        metadata: Optional[Dict[str, str]] = None,
        encrypt: bool = True
    ) -> bool:
        """
        Upload file to S3.
        
        Args:
            local_path: Local file path
            s3_key: S3 object key (path in bucket)
            metadata: Optional metadata tags
            encrypt: Enable server-side encryption
        
        Returns:
            True if successful, False otherwise
        """
        try:
            extra_args = {}
            
            if encrypt:
                extra_args['ServerSideEncryption'] = 'AES256'
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Uploaded {local_path} to s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False
    
    def download_file(
        self,
        s3_key: str,
        local_path: Path
    ) -> bool:
        """
        Download file from S3.
        
        Args:
            s3_key: S3 object key
            local_path: Local destination path
        
        Returns:
            True if successful, False otherwise
        """
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.s3.download_file(
                self.bucket_name,
                s3_key,
                str(local_path)
            )
            
            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to download {s3_key}: {e}")
            return False
    
    def list_backups(self, prefix: str = "backups/") -> List[Dict]:
        """
        List all backups in S3.
        
        Args:
            prefix: S3 key prefix to filter
        
        Returns:
            List of backup metadata dicts
        """
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            backups = []
            for obj in response.get('Contents', []):
                backups.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            return backups
            
        except ClientError as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def delete_backup(self, s3_key: str) -> bool:
        """Delete backup from S3."""
        try:
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {s3_key}: {e}")
            return False
    
    def apply_retention_policy(
        self,
        prefix: str = "backups/",
        keep_daily: int = 7,
        keep_weekly: int = 4,
        keep_monthly: int = 12
    ) -> int:
        """
        Apply backup retention policy.
        
        Retention Strategy:
        - Keep all backups from last N days (daily)
        - Keep 1 backup per week for last M weeks
        - Keep 1 backup per month for last K months
        - Delete everything older
        
        Args:
            prefix: S3 key prefix
            keep_daily: Days to keep all backups
            keep_weekly: Weeks to keep weekly backups
            keep_monthly: Months to keep monthly backups
        
        Returns:
            Number of backups deleted
        """
        backups = self.list_backups(prefix)
        if not backups:
            return 0
        
        now = datetime.now()
        deleted = 0
        
        # Sort backups by date (oldest first)
        backups.sort(key=lambda b: b['last_modified'])
        
        # Time cutoffs
        daily_cutoff = now - timedelta(days=keep_daily)
        weekly_cutoff = now - timedelta(weeks=keep_weekly + keep_daily // 7)
        monthly_cutoff = now - timedelta(days=keep_monthly * 30)
        
        # Track which backups to keep
        kept_weekly = {}  # week_number: backup
        kept_monthly = {}  # month_key: backup
        to_delete = []
        
        for backup in backups:
            backup_date = backup['last_modified'].replace(tzinfo=None)
            
            # Keep all recent (daily)
            if backup_date >= daily_cutoff:
                continue
            
            # Weekly retention
            if backup_date >= weekly_cutoff:
                week_key = backup_date.strftime("%Y-W%W")
                if week_key not in kept_weekly:
                    kept_weekly[week_key] = backup
                    continue
                else:
                    to_delete.append(backup)
                    continue
            
            # Monthly retention
            if backup_date >= monthly_cutoff:
                month_key = backup_date.strftime("%Y-%m")
                if month_key not in kept_monthly:
                    kept_monthly[month_key] = backup
                    continue
                else:
                    to_delete.append(backup)
                    continue
            
            # Too old - delete
            to_delete.append(backup)
        
        # Delete backups
        for backup in to_delete:
            if self.delete_backup(backup['key']):
                deleted += 1
        
        logger.info(f"Retention policy applied: deleted {deleted} old backups")
        return deleted


__all__ = ["S3BackupClient"]
