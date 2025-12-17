# Backup & Recovery

## Overview

Peak Trade's backup system provides automated backup and recovery for critical data including portfolio states, trading history, configurations, and more.

## Components

1. **BackupManager** - Creates and manages backups
2. **RecoveryManager** - Restores data from backups
3. **Retention Policies** - Automatic cleanup of old backups

## Configuration

Configure backups in `config.toml`:

```toml
[backup]
enabled = true
interval_hours = 24                # Hours between automatic backups
retention_days = 30                # Days to retain backups
backup_path = "./backups"          # Backup storage directory
compress = true                    # Compress backups with gzip

[backup.targets]
portfolio_states = true            # Portfolio state snapshots
trading_history = true             # Trading history and orders
configurations = true              # Configuration files
experiment_results = false         # Experiment results (can be large)
```

## Creating Backups

### Using CLI

```bash
# Create a backup
python -m src.infra.backup.backup_manager create \
    --type portfolio \
    --source ./data/portfolio_state.json \
    --description "Daily portfolio backup"

# Using Makefile
make backup TYPE=portfolio SOURCE=./data/portfolio_state.json
```

### Programmatic Usage

```python
from src.infra.backup import BackupManager

manager = BackupManager(
    backup_dir="./backups",
    retention_days=30,
    compress=True
)

# Create a backup
backup_id = manager.create_backup(
    backup_type="portfolio",
    source_path="./data/portfolio_state.json",
    description="Daily portfolio backup"
)

print(f"Backup created: {backup_id}")
```

### Backup Types

Common backup types:
- `portfolio` - Portfolio states and positions
- `trading_history` - Order history and trades
- `config` - Configuration files
- `experiments` - Experiment results
- `strategies` - Strategy configurations
- `data` - Market data cache

## Listing Backups

### Using CLI

```bash
# List all backups
python -m src.infra.backup.backup_manager list

# List backups of specific type
python -m src.infra.backup.backup_manager list --type portfolio

# Using Makefile
make backup-list
```

### Programmatic Usage

```python
manager = BackupManager()

# List all backups
backups = manager.list_backups()
for backup in backups:
    print(f"ID: {backup.backup_id}")
    print(f"Type: {backup.backup_type}")
    print(f"Date: {backup.timestamp}")
    print(f"Size: {backup.size_bytes / 1024:.2f} KB")
    print()

# List specific type
portfolio_backups = manager.list_backups(backup_type="portfolio")
```

## Restoring Backups

### Using CLI

```bash
# Restore a backup
python -m src.infra.backup.recovery restore \
    --id portfolio_20251217_162039 \
    --dest ./data/restored/

# Note: Makefile target requires ID and DEST
make restore ID=portfolio_20251217_162039 DEST=./data/restored/
```

### Programmatic Usage

```python
from src.infra.backup import BackupManager, RecoveryManager

# Create managers
backup_mgr = BackupManager()
recovery_mgr = RecoveryManager(backup_manager=backup_mgr)

# Restore a backup
success = recovery_mgr.restore_backup(
    backup_id="portfolio_20251217_162039",
    destination="./data/restored/",
    overwrite=False  # Set True to overwrite existing files
)

if success:
    print("Backup restored successfully")
```

## Verifying Backups

```python
from src.infra.backup import RecoveryManager

recovery = RecoveryManager()

# Verify backup integrity
is_valid = recovery.verify_backup("portfolio_20251217_162039")

if is_valid:
    print("Backup is valid and can be restored")
else:
    print("Backup verification failed")
```

## Automatic Cleanup

### Using CLI

```bash
# Clean up old backups
python -m src.infra.backup.backup_manager cleanup

# Using Makefile
make backup-cleanup
```

### Programmatic Usage

```python
manager = BackupManager(retention_days=30)

# Delete backups older than retention period
deleted_count = manager.cleanup_old_backups()
print(f"Deleted {deleted_count} old backups")
```

### Manual Deletion

```bash
# Delete specific backup
python -m src.infra.backup.backup_manager delete \
    --id portfolio_20251217_162039
```

```python
manager = BackupManager()
manager.delete_backup("portfolio_20251217_162039")
```

## Backup Structure

Backups are organized as follows:

```
backups/
├── portfolio_20251217_162039/
│   ├── metadata.json
│   └── portfolio_state.json.gz
├── config_20251217_163000/
│   ├── metadata.json
│   └── config.toml
└── trading_history_20251217_164500/
    ├── metadata.json
    └── trades.tar.gz
```

### Metadata Format

Each backup includes metadata:

```json
{
  "backup_id": "portfolio_20251217_162039",
  "backup_type": "portfolio",
  "timestamp": "2025-12-17T16:20:39.123456",
  "size_bytes": 102400,
  "compressed": true,
  "source_path": "./data/portfolio_state.json",
  "description": "Daily portfolio backup"
}
```

## Compression

Backups can be compressed using gzip:

- **Single files**: Compressed with `.gz` extension
- **Directories**: Archived as `.tar.gz`

Compression is enabled by default but can be disabled:

```python
manager = BackupManager(compress=False)
```

## Automated Backups

### Scheduled Backups

Create a scheduled backup script:

```python
#!/usr/bin/env python
"""
Automated backup script for Peak Trade.
Run via cron or systemd timer.
"""

import sys
from pathlib import Path
from datetime import datetime
from src.infra.backup import BackupManager

def run_automated_backup():
    manager = BackupManager(
        backup_dir="./backups",
        retention_days=30,
        compress=True
    )
    
    # Backup portfolio state
    if Path("./data/portfolio_state.json").exists():
        backup_id = manager.create_backup(
            backup_type="portfolio",
            source_path="./data/portfolio_state.json",
            description=f"Automated backup {datetime.now()}"
        )
        print(f"Portfolio backup created: {backup_id}")
    
    # Backup configurations
    if Path("./config.toml").exists():
        backup_id = manager.create_backup(
            backup_type="config",
            source_path="./config.toml",
            description=f"Automated config backup {datetime.now()}"
        )
        print(f"Config backup created: {backup_id}")
    
    # Clean up old backups
    deleted = manager.cleanup_old_backups()
    print(f"Cleaned up {deleted} old backups")

if __name__ == "__main__":
    try:
        run_automated_backup()
        sys.exit(0)
    except Exception as e:
        print(f"Backup failed: {e}", file=sys.stderr)
        sys.exit(1)
```

### Cron Schedule

Add to crontab for daily backups:

```bash
# Run daily at 2 AM
0 2 * * * /path/to/python /path/to/automated_backup.py >> /var/log/peak_trade_backup.log 2>&1
```

## Recovery Procedures

### Emergency Recovery

1. **Identify the backup to restore**:
```bash
make backup-list
```

2. **Verify backup integrity**:
```python
from src.infra.backup import RecoveryManager

recovery = RecoveryManager()
is_valid = recovery.verify_backup("backup_id")
```

3. **Stop the application** (if running)

4. **Restore the backup**:
```bash
make restore ID=backup_id DEST=./data/
```

5. **Verify restored data**

6. **Restart the application**

### Point-in-Time Recovery

Restore system to a specific point in time:

```python
from src.infra.backup import BackupManager, RecoveryManager
from datetime import datetime

manager = BackupManager()
recovery = RecoveryManager()

# Find backups from specific date
target_date = datetime(2025, 12, 17, 16, 0, 0)

backups = manager.list_backups()
for backup in backups:
    if backup.timestamp <= target_date:
        print(f"Restoring: {backup.backup_id}")
        recovery.restore_backup(
            backup_id=backup.backup_id,
            destination=f"./restored/{backup.backup_type}/",
            overwrite=True
        )
        break
```

## Best Practices

1. **Regular Backups**
   - Schedule automated backups (daily recommended)
   - Back up before major changes
   - Test restore procedures regularly

2. **Multiple Retention Periods**
   ```python
   # Daily backups: 30 days retention
   daily_manager = BackupManager(retention_days=30)
   
   # Weekly backups: 90 days retention
   weekly_manager = BackupManager(
       backup_dir="./backups/weekly",
       retention_days=90
   )
   ```

3. **Off-site Backups**
   - Copy backups to remote storage
   - Use cloud storage (S3, etc.)
   - Maintain geographic redundancy

4. **Backup Verification**
   - Verify backups after creation
   - Test restores periodically
   - Monitor backup sizes

5. **Encryption** (Future Enhancement)
   ```python
   # Future: Encrypted backups
   manager = BackupManager(
       compress=True,
       encrypt=True,
       encryption_key="your-encryption-key"
   )
   ```

## Monitoring Backups

### Health Check Integration

```python
from src.infra.backup import BackupManager
from src.infra.health.checks.base_check import BaseHealthCheck, HealthStatus

class BackupHealthCheck(BaseHealthCheck):
    def __init__(self):
        super().__init__("Backup System")
    
    def check(self):
        manager = BackupManager()
        backups = manager.list_backups()
        
        if not backups:
            return self._create_result(
                status=HealthStatus.YELLOW,
                message="No backups found"
            )
        
        # Check if latest backup is recent
        latest = backups[0]
        age_hours = (datetime.now() - latest.timestamp).total_seconds() / 3600
        
        if age_hours > 48:
            return self._create_result(
                status=HealthStatus.YELLOW,
                message=f"Latest backup is {age_hours:.1f} hours old"
            )
        
        return self._create_result(
            status=HealthStatus.GREEN,
            message=f"Backup system operational, {len(backups)} backups"
        )
```

## Troubleshooting

### Backup Fails

**Problem**: Backup creation fails

**Solutions**:
1. Check disk space: `df -h`
2. Verify source path exists
3. Check write permissions on backup directory
4. Review logs for detailed error

### Restore Fails

**Problem**: Restore operation fails

**Solutions**:
1. Verify backup exists: `make backup-list`
2. Verify backup integrity
3. Check destination permissions
4. Ensure sufficient disk space

### Backups Too Large

**Problem**: Backups consuming too much space

**Solutions**:
1. Enable compression: `compress=True`
2. Reduce retention period
3. Exclude large/unnecessary data
4. Use incremental backups (future enhancement)

## See Also

- [Health Checks](HEALTH_CHECKS.md) - System health monitoring
- [Monitoring](MONITORING.md) - Comprehensive monitoring setup
- [Circuit Breaker](CIRCUIT_BREAKER.md) - Failure handling patterns
