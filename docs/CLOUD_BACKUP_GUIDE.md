# Cloud Backup Integration Guide

## Overview

Peak Trade now supports S3-compatible cloud backup for disaster recovery. This feature enables automatic, encrypted backups to cloud storage providers including:

- **AWS S3**
- **MinIO** (self-hosted)
- **DigitalOcean Spaces**
- **Any S3-compatible storage**

## Features

✅ Automatic compression (tar.gz)
✅ Server-side encryption (AES256)
✅ Configurable retention policies
✅ Scheduled automated backups
✅ Easy disaster recovery
✅ Local testing with MinIO

## Quick Start

### 1. Configure S3 Credentials

Create a `.env` file or export environment variables:

```bash
export S3_ACCESS_KEY=your_access_key
export S3_SECRET_KEY=your_secret_key
export S3_BUCKET_NAME=peak-trade-backups
export S3_REGION=us-east-1

# For MinIO or DigitalOcean Spaces:
export S3_ENDPOINT_URL=http://localhost:9000
```

### 2. Install Dependencies

```bash
pip install boto3>=1.34.0
```

### 3. Test Connection

```bash
python scripts/restore_from_cloud.py --list
```

### 4. Create Your First Backup

```bash
python scripts/backup_to_cloud.py
```

## Configuration

Edit `config/backup.toml` to customize backup behavior:

```toml
[backup]
enabled = true
local_dir = "backups"
schedule = "0 2 * * *"  # Daily at 2 AM

[backup.s3]
enabled = true
bucket_name = "peak-trade-backups"
access_key = "${S3_ACCESS_KEY}"
secret_key = "${S3_SECRET_KEY}"
endpoint_url = ""  # Empty for AWS, set for MinIO/Spaces
region = "us-east-1"
prefix = "peak-trade/backups/"
encrypt = true

[backup.retention]
keep_daily = 7     # Keep all backups for 7 days
keep_weekly = 4    # Keep weekly for 4 weeks
keep_monthly = 12  # Keep monthly for 12 months
```

## Usage

### Manual Backup

Create a one-time backup and upload to S3:

```bash
python scripts/backup_to_cloud.py
```

### Sync All Local Backups

Upload all existing local backups to S3:

```bash
python scripts/backup_to_cloud.py --sync-all
```

### Apply Retention Policy

Clean up old backups according to retention rules:

```bash
python scripts/backup_to_cloud.py --apply-retention
```

### List Available Backups

View all backups in S3:

```bash
python scripts/restore_from_cloud.py --list
```

### Restore from Cloud

Restore a specific backup:

```bash
python scripts/restore_from_cloud.py --backup-id BACKUP_ID
```

Dry-run to validate before restoring:

```bash
python scripts/restore_from_cloud.py --backup-id BACKUP_ID --dry-run
```

## Automated Backups

### Setup Cron Jobs

Run the setup script to configure automated backups:

```bash
bash scripts/setup_cron.sh
```

This creates two cron jobs:
- **Daily backup**: Every day at 2:00 AM
- **Retention cleanup**: Every Sunday at 3:00 AM

Logs are written to `logs/backup.log`.

### View Cron Jobs

```bash
crontab -l
```

### Remove Cron Jobs

```bash
crontab -e
# Delete the Peak Trade backup lines
```

## Local Testing with MinIO

MinIO provides S3-compatible storage for local development and testing.

### 1. Start MinIO

```bash
docker compose -f docker/docker-compose.minio.yml up -d
```

### 2. Configure Environment

```bash
export S3_ACCESS_KEY=minioadmin
export S3_SECRET_KEY=minioadmin
export S3_BUCKET_NAME=peak-trade-backups
export S3_ENDPOINT_URL=http://localhost:9000
export S3_REGION=us-east-1
```

### 3. Access MinIO Console

Open your browser to: http://localhost:9001

- **Username**: minioadmin
- **Password**: minioadmin

### 4. Test Backup/Restore

```bash
# Create backup
python scripts/backup_to_cloud.py

# List backups
python scripts/restore_from_cloud.py --list

# Restore backup
python scripts/restore_from_cloud.py --backup-id <BACKUP_ID>
```

### 5. Stop MinIO

```bash
docker compose -f docker/docker-compose.minio.yml down
```

## Disaster Recovery

In case of system failure or data loss:

### 1. Setup Fresh Environment

Install dependencies and configure S3 credentials on the new system.

### 2. List Available Backups

```bash
python scripts/restore_from_cloud.py --list
```

### 3. Restore Latest Backup

```bash
python scripts/restore_from_cloud.py --backup-id <LATEST_BACKUP_ID>
```

### 4. Verify Restoration

Check that all critical files and configurations are restored.

### 5. Resume Operations

Restart your trading system with restored configuration.

## Retention Policy

The default retention policy keeps:

- **7 days**: All daily backups
- **4 weeks**: One backup per week
- **12 months**: One backup per month

Older backups are automatically deleted.

### Custom Retention

Modify `config/backup.toml`:

```toml
[backup.retention]
keep_daily = 14    # Keep 14 days
keep_weekly = 8    # Keep 8 weeks
keep_monthly = 24  # Keep 24 months
```

## Security

### Encryption

All backups are encrypted at rest using AES-256 server-side encryption.

### Access Control

- Use IAM roles with minimal required permissions for AWS S3
- Rotate access keys regularly
- Never commit credentials to version control

### Recommended IAM Policy (AWS)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::peak-trade-backups",
        "arn:aws:s3:::peak-trade-backups/*"
      ]
    }
  ]
}
```

## Cloud Provider Setup

### AWS S3

1. Create S3 bucket
2. Create IAM user with S3 permissions
3. Generate access keys
4. Configure environment variables

### DigitalOcean Spaces

1. Create Space
2. Generate API keys
3. Set endpoint URL:

```bash
export S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
```

### MinIO (Self-Hosted)

1. Deploy MinIO server
2. Create bucket via web console
3. Generate access keys
4. Set custom endpoint URL

## Troubleshooting

### Connection Errors

**Problem**: Cannot connect to S3

**Solution**: 
- Verify credentials are set correctly
- Check network connectivity
- Verify endpoint URL for MinIO/Spaces

### Bucket Not Found

**Problem**: Bucket doesn't exist

**Solution**:
- The client will attempt to create the bucket automatically
- Verify your IAM permissions allow `s3:CreateBucket`
- Or create the bucket manually

### Upload Failures

**Problem**: Backup upload fails

**Solution**:
- Check available disk space
- Verify write permissions to local backup directory
- Check S3 storage quotas

### Large Backup Files

**Problem**: Backups are too large

**Solution**:
- Exclude data files: use `include_data=False`
- Clean up old local backups before syncing
- Increase S3 timeout settings

## API Reference

### S3BackupClient

```python
from src.backup.s3_client import S3BackupClient

client = S3BackupClient(
    bucket_name="peak-trade-backups",
    access_key="your-key",
    secret_key="your-secret",
    endpoint_url=None,  # Optional for MinIO/Spaces
    region="us-east-1"
)

# Upload file
client.upload_file(Path("backup.tar.gz"), "backups/backup.tar.gz")

# Download file
client.download_file("backups/backup.tar.gz", Path("restored.tar.gz"))

# List backups
backups = client.list_backups(prefix="backups/")

# Delete backup
client.delete_backup("backups/old-backup.tar.gz")

# Apply retention
deleted = client.apply_retention_policy(keep_daily=7, keep_weekly=4, keep_monthly=12)
```

### CloudBackupManager

```python
from src.backup.cloud_backup_manager import CloudBackupManager
from src.backup.s3_client import S3BackupClient

s3 = S3BackupClient(...)
manager = CloudBackupManager(s3_client=s3)

# Create and upload backup
backup_id = manager.create_and_upload_backup(
    include_config=True,
    include_state=True,
    tags=["daily", "automated"],
    description="Daily backup"
)

# Restore from cloud
success = manager.restore_from_cloud(backup_id)

# Sync local backups
synced = manager.sync_to_cloud()

# List cloud backups
backups = manager.list_cloud_backups()
```

## Best Practices

1. **Test regularly**: Perform test restores periodically
2. **Monitor logs**: Check `logs/backup.log` for issues
3. **Verify backups**: Use dry-run mode to validate backups
4. **Geographic redundancy**: Consider multi-region S3 buckets
5. **Backup before updates**: Always backup before major changes
6. **Document procedures**: Keep recovery procedures documented
7. **Access control**: Use minimal IAM permissions
8. **Encryption**: Always enable encryption for production backups

## Support

For issues or questions:
- Check the troubleshooting section above
- Review logs in `logs/backup.log`
- Verify S3 credentials and permissions
- Test with MinIO locally first

## License

Part of Peak Trade - Proprietary Software
