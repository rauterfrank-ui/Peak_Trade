# S3 Cloud Backup Integration

This implementation adds comprehensive S3-compatible cloud backup integration to Peak Trade for disaster recovery.

## Quick Links

- **Full Documentation**: [docs/CLOUD_BACKUP_GUIDE.md](docs/CLOUD_BACKUP_GUIDE.md)
- **Configuration**: [config/backup.toml](config/backup.toml)
- **Environment Variables**: [docker/.env.example](docker/.env.example)

## What's Included

### Core Components
- `src/backup/s3_client.py` - S3-compatible storage client
- `src/backup/cloud_backup_manager.py` - Cloud backup lifecycle manager

### Automation Scripts
- `scripts/backup_to_cloud.py` - Create/upload backups, sync, apply retention
- `scripts/restore_from_cloud.py` - List and restore backups
- `scripts/setup_cron.sh` - Configure automated backups

### Testing & Development
- `tests/test_s3_client.py` - S3 client tests (14 tests)
- `tests/test_cloud_backup_manager.py` - Backup manager tests (11 tests)
- `docker/docker-compose.minio.yml` - Local MinIO testing environment

## Quick Start

### 1. Install Dependencies
```bash
pip install boto3>=1.34.0
```

### 2. Configure Credentials
```bash
export S3_ACCESS_KEY=your_access_key
export S3_SECRET_KEY=your_secret_key
export S3_BUCKET_NAME=peak-trade-backups
export S3_REGION=us-east-1
```

### 3. Create First Backup
```bash
python scripts/backup_to_cloud.py
```

### 4. Setup Automated Backups
```bash
bash scripts/setup_cron.sh
```

## Features

✅ **S3-Compatible Storage**: Works with AWS S3, MinIO, DigitalOcean Spaces, and any S3-compatible service
✅ **Automatic Compression**: All backups compressed with tar.gz before upload
✅ **Encryption**: Server-side AES-256 encryption at rest
✅ **Retention Policies**: Configurable (7 daily, 4 weekly, 12 monthly by default)
✅ **Scheduled Backups**: Cron-based automation for daily backups and weekly cleanup
✅ **Disaster Recovery**: Easy restore from cloud with dry-run validation
✅ **Local Testing**: MinIO docker-compose for development and testing

## Testing

All tests passing:
```bash
# Run S3 client tests
python3 -m pytest tests/test_s3_client.py -v

# Run cloud backup manager tests
python3 -m pytest tests/test_cloud_backup_manager.py -v

# Run all backup tests
python3 -m pytest tests/test_*backup* -v
```

## Cloud Provider Support

- **AWS S3**: Native support
- **MinIO**: Self-hosted S3-compatible storage
- **DigitalOcean Spaces**: Set `S3_ENDPOINT_URL`
- **Any S3-compatible storage**: Configure endpoint URL

## Security

✅ Passed CodeQL security scan (0 vulnerabilities)
✅ Server-side encryption (AES-256)
✅ Secure credential management via environment variables
✅ No secrets in code or configuration files

## Architecture

```
Local Backup → Compress (tar.gz) → Upload to S3 → Retention Policy
     ↓                                    ↓
  Recovery Manager                Cloud Storage
     ↓                                    ↓
  Restore ← Extract ← Download ← Disaster Recovery
```

## Example Usage

### Manual Backup
```bash
python scripts/backup_to_cloud.py
```

### Sync All Local Backups
```bash
python scripts/backup_to_cloud.py --sync-all
```

### Apply Retention Policy
```bash
python scripts/backup_to_cloud.py --apply-retention
```

### List Cloud Backups
```bash
python scripts/restore_from_cloud.py --list
```

### Restore Backup
```bash
python scripts/restore_from_cloud.py --backup-id BACKUP_ID
```

### Dry-Run Restore
```bash
python scripts/restore_from_cloud.py --backup-id BACKUP_ID --dry-run
```

## Local Testing with MinIO

```bash
# Start MinIO
docker compose -f docker/docker-compose.minio.yml up -d

# Configure for MinIO
export S3_ACCESS_KEY=minioadmin
export S3_SECRET_KEY=minioadmin
export S3_BUCKET_NAME=peak-trade-backups
export S3_ENDPOINT_URL=http://localhost:9000
export S3_REGION=us-east-1

# Test backup/restore
python scripts/backup_to_cloud.py
python scripts/restore_from_cloud.py --list

# Access web console at http://localhost:9001
```

## Retention Policy

Default retention strategy:
- **Daily**: Keep all backups for 7 days
- **Weekly**: Keep 1 backup per week for 4 weeks
- **Monthly**: Keep 1 backup per month for 12 months

Customize in `config/backup.toml`:
```toml
[backup.retention]
keep_daily = 7
keep_weekly = 4
keep_monthly = 12
```

## Automated Backups

Setup cron jobs for automated backups:
```bash
bash scripts/setup_cron.sh
```

This configures:
- Daily backup at 2:00 AM
- Weekly retention cleanup on Sundays at 3:00 AM

Logs written to: `logs/backup.log`

## API Reference

### S3BackupClient
```python
from src.backup.s3_client import S3BackupClient

client = S3BackupClient(
    bucket_name="peak-trade-backups",
    access_key="key",
    secret_key="secret",
    endpoint_url=None,  # Optional
    region="us-east-1"
)

# Operations
client.upload_file(local_path, s3_key, metadata={}, encrypt=True)
client.download_file(s3_key, local_path)
client.list_backups(prefix="backups/")
client.delete_backup(s3_key)
client.apply_retention_policy(keep_daily=7, keep_weekly=4, keep_monthly=12)
```

### CloudBackupManager
```python
from src.backup.cloud_backup_manager import CloudBackupManager

manager = CloudBackupManager(s3_client=client)

# Operations
backup_id = manager.create_and_upload_backup(
    include_config=True,
    include_state=True,
    tags=["automated"],
    description="Daily backup"
)
manager.restore_from_cloud(backup_id, dry_run=False)
manager.sync_to_cloud()
manager.list_cloud_backups()
```

## Implementation Details

### Code Changes
- Added `src/backup/` module with S3 client and cloud backup manager
- Created automation scripts for backup, restore, and cron setup
- Added MinIO docker-compose for local testing
- Comprehensive test coverage (25 tests)
- Complete documentation

### Dependencies
- `boto3>=1.34.0` - AWS SDK for Python (S3 integration)

### Configuration Files
- `config/backup.toml` - Cloud backup configuration
- `docker/.env.example` - S3 credentials template
- `docker/docker-compose.minio.yml` - MinIO testing setup

### Performance Optimizations
- Efficient retention policy with proper weekly/monthly filtering
- Optimized sync operation to avoid N+1 query pattern
- Compressed backups to minimize storage costs

## Best Practices

1. **Test Regularly**: Perform test restores periodically
2. **Monitor Logs**: Check `logs/backup.log` for issues
3. **Use Dry-Run**: Validate backups before actual restore
4. **Geographic Redundancy**: Consider multi-region S3 buckets
5. **Backup Before Updates**: Always backup before major changes
6. **Minimal IAM Permissions**: Use least privilege access control
7. **Enable Encryption**: Always use encryption for production

## Troubleshooting

See [docs/CLOUD_BACKUP_GUIDE.md](docs/CLOUD_BACKUP_GUIDE.md) for detailed troubleshooting guide.

Common issues:
- **Connection errors**: Verify credentials and endpoint URL
- **Bucket not found**: Check IAM permissions or create bucket manually
- **Upload failures**: Check disk space and S3 quotas
- **Large backups**: Consider excluding data files

## Support

For detailed information, see [docs/CLOUD_BACKUP_GUIDE.md](docs/CLOUD_BACKUP_GUIDE.md).

## License

Part of Peak Trade - Proprietary Software
