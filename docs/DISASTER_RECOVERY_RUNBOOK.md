# Disaster Recovery Runbook

> **Version:** 1.0  
> **Last Updated:** December 2024  
> **Owner:** Peak_Trade Operations Team

## Overview

This runbook provides step-by-step procedures for detecting, responding to, and recovering from system disasters using the Peak_Trade resilience system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Disaster Scenarios](#disaster-scenarios)
3. [Recovery Procedures](#recovery-procedures)
4. [Verification Steps](#verification-steps)
5. [Post-Recovery Actions](#post-recovery-actions)
6. [Escalation](#escalation)

## Prerequisites

### Required Tools
- Access to Peak_Trade system
- Recovery Manager configured
- Recent backup available
- Health check system operational

### Required Knowledge
- Basic Python
- Peak_Trade architecture
- Backup/recovery system usage

### Preparation Checklist
- [ ] Backups configured and running
- [ ] Health checks registered
- [ ] Recovery manager initialized
- [ ] Backup retention policy set
- [ ] Alert system configured

## Disaster Scenarios

### Scenario 1: Configuration Corruption

**Symptoms:**
- System fails to start
- Config file unreadable
- Health checks fail for config

**Detection:**
```python
from src.core.resilience import health_check

results = health_check.run_all()
if not results["config"].healthy:
    print("⚠️  Config health check failed")
```

**Recovery:** See [Procedure A: Config Recovery](#procedure-a-config-recovery)

---

### Scenario 2: Data Loss

**Symptoms:**
- Critical data files missing
- Data directory deleted
- Trading records unavailable

**Detection:**
```python
from pathlib import Path

critical_files = [
    Path("data/positions.csv"),
    Path("data/trades.csv"),
]

for file in critical_files:
    if not file.exists():
        print(f"⚠️  Critical file missing: {file}")
```

**Recovery:** See [Procedure B: Data Recovery](#procedure-b-data-recovery)

---

### Scenario 3: Complete System Failure

**Symptoms:**
- Multiple systems failing
- Config and data corrupted
- System completely unresponsive

**Detection:**
```python
from src.core.resilience import health_check

if not health_check.is_system_healthy():
    results = health_check.run_all()
    failed = [name for name, r in results.items() if not r.healthy]
    print(f"⚠️  Multiple failures: {', '.join(failed)}")
```

**Recovery:** See [Procedure C: Full System Recovery](#procedure-c-full-system-recovery)

---

### Scenario 4: Backup System Failure

**Symptoms:**
- No recent backups available
- Backup directory corrupted
- Backup creation failing

**Detection:**
```python
from src.core.backup_recovery import RecoveryManager
from datetime import datetime, timedelta

recovery = RecoveryManager()
backups = recovery.list_backups()

if not backups:
    print("🚨 No backups available")
else:
    latest = backups[0]
    age = datetime.now() - datetime.fromisoformat(latest.created_at.replace('Z', ''))
    if age > timedelta(hours=24):
        print(f"⚠️  Latest backup is {age.total_seconds()/3600:.1f} hours old")
```

**Recovery:** See [Procedure D: Backup System Recovery](#procedure-d-backup-system-recovery)

## Recovery Procedures

### Procedure A: Config Recovery

**Time Estimate:** 5-10 minutes  
**Impact:** Medium - System restart required

#### Steps

1. **Stop the system** (if running)
   ```bash
   # Stop any running processes
   pkill -f "python.*live_ops"
   ```

2. **Verify backup availability**
   ```python
   from src.core.backup_recovery import RecoveryManager

   recovery = RecoveryManager(backup_dir="backups")
   backups = recovery.list_backups()

   print(f"Available backups: {len(backups)}")
   for backup in backups[:5]:
       print(f"  - {backup.backup_id[:30]}... ({backup.created_at})")
   ```

3. **Select recovery backup**
   ```python
   # Use most recent successful backup
   backup_to_restore = backups[0]
   print(f"Selected backup: {backup_to_restore.backup_id}")
   print(f"Description: {backup_to_restore.description}")
   ```

4. **Dry-run restore** (recommended)
   ```python
   success = recovery.restore_backup(
       backup_to_restore.backup_id,
       restore_config=True,
       dry_run=True
   )

   if success:
       print("✅ Dry-run successful, proceeding with actual restore")
   else:
       print("❌ Dry-run failed, investigate before proceeding")
       # STOP HERE and escalate
   ```

5. **Perform actual restore**
   ```python
   success = recovery.restore_backup(
       backup_to_restore.backup_id,
       restore_config=True,
       restore_state=False,
       restore_data=False
   )

   if success:
       print("✅ Config restored successfully")
   else:
       print("❌ Restore failed")
       # Escalate immediately
   ```

6. **Verify configuration**
   ```python
   from pathlib import Path

   config_file = Path("config/config.toml")
   if config_file.exists():
       print(f"✅ Config file exists ({config_file.stat().st_size} bytes)")
       # Check content is valid
       try:
           import toml
           config = toml.load(config_file)
           print("✅ Config file is valid TOML")
       except Exception as e:
           print(f"❌ Config file invalid: {e}")
   ```

7. **Run health checks**
   ```python
   from src.core.resilience import health_check

   results = health_check.run_all()
   if results["config"].healthy:
       print("✅ Config health check passed")
   else:
       print("❌ Config health check still failing")
       # Escalate
   ```

8. **Restart system**
   ```bash
   # Restart services
   python scripts/live_ops.py health --config config/config.toml
   ```

#### Success Criteria
- [ ] Config file restored
- [ ] Config file is valid
- [ ] Health checks pass
- [ ] System starts successfully

---

### Procedure B: Data Recovery

**Time Estimate:** 10-30 minutes  
**Impact:** High - Trading operations affected

#### Steps

1. **Assess data loss extent**
   ```python
   from pathlib import Path

   critical_paths = [
       Path("data/positions.csv"),
       Path("data/trades.csv"),
       Path("data/reports/"),
   ]

   missing = [p for p in critical_paths if not p.exists()]
   print(f"Missing: {len(missing)}/{len(critical_paths)} items")
   for path in missing:
       print(f"  - {path}")
   ```

2. **Identify suitable backup**
   ```python
   from src.core.backup_recovery import RecoveryManager, BackupType

   recovery = RecoveryManager()

   # Find backups with data
   data_backups = [
       b for b in recovery.list_backups()
       if b.backup_type in [BackupType.FULL, BackupType.DATA]
       and b.status == BackupStatus.SUCCESS
   ]

   if not data_backups:
       print("🚨 No data backups available!")
       # Escalate immediately

   backup_to_restore = data_backups[0]
   print(f"Selected backup: {backup_to_restore.backup_id}")
   print(f"Files: {backup_to_restore.files_count}")
   print(f"Size: {backup_to_restore.size_bytes} bytes")
   ```

3. **Calculate data loss window**
   ```python
   from datetime import datetime

   backup_time = datetime.fromisoformat(
       backup_to_restore.created_at.replace('Z', '+00:00')
   )
   current_time = datetime.now(backup_time.tzinfo)
   data_loss_window = current_time - backup_time

   print(f"⚠️  Data loss window: {data_loss_window.total_seconds()/3600:.1f} hours")
   print("   (All data from this period will be lost)")
   ```

4. **Stop trading operations**
   ```bash
   # Stop all trading activities
   # Ensure no active orders
   python scripts/live_ops.py portfolio --config config/config.toml
   # Cancel any pending orders manually if necessary
   ```

5. **Backup current state** (if any data exists)
   ```python
   # Create backup of current state before restore
   current_backup = recovery.create_backup(
       include_data=True,
       description="Pre-recovery current state",
       tags=["pre-recovery", "emergency"]
   )
   print(f"Current state backed up: {current_backup}")
   ```

6. **Restore data**
   ```python
   success = recovery.restore_backup(
       backup_to_restore.backup_id,
       restore_config=False,
       restore_state=False,
       restore_data=True
   )

   if success:
       print("✅ Data restored successfully")
   else:
       print("❌ Data restore failed")
       # Escalate immediately
   ```

7. **Verify data integrity**
   ```python
   import pandas as pd

   # Check positions file
   positions = pd.read_csv("data/positions.csv")
   print(f"✅ Positions restored: {len(positions)} rows")

   # Check trades file
   trades = pd.read_csv("data/trades.csv")
   print(f"✅ Trades restored: {len(trades)} rows")

   # Verify data makes sense
   if len(positions) > 0:
       print(f"   Latest position: {positions.iloc[-1]['symbol']}")
   ```

8. **Reconcile with external systems**
   ```python
   # Compare restored data with exchange balances
   # This step is critical to ensure consistency
   from src.exchange.client import get_exchange_client

   exchange = get_exchange_client()
   exchange_balance = exchange.fetch_balance()

   # Compare with restored positions
   # Log any discrepancies
   print("Reconciliation required with exchange")
   ```

#### Success Criteria
- [ ] Data files restored
- [ ] Data integrity verified
- [ ] Data reconciled with external systems
- [ ] Health checks pass
- [ ] Trading can safely resume

---

### Procedure C: Full System Recovery

**Time Estimate:** 30-60 minutes  
**Impact:** Critical - Complete system down

#### Steps

1. **Declare incident**
   - Notify stakeholders
   - Document start time
   - Assemble recovery team if available

2. **Assess situation**
   ```python
   from src.core.resilience import health_check
   from src.core.backup_recovery import RecoveryManager

   # Run all health checks
   results = health_check.run_all()
   failed_checks = [name for name, r in results.items() if not r.healthy]

   print(f"Failed checks: {', '.join(failed_checks)}")

   # Check backup availability
   recovery = RecoveryManager()
   backups = recovery.list_backups()
   print(f"Available backups: {len(backups)}")
   ```

3. **Select recovery point**
   ```python
   # Find most recent FULL backup
   full_backups = [
       b for b in backups
       if b.backup_type == BackupType.FULL
       and b.status == BackupStatus.SUCCESS
   ]

   if not full_backups:
       print("🚨 No full backups available!")
       # May need to perform partial recovery
       # Escalate to senior engineer

   recovery_backup = full_backups[0]
   print(f"Recovery point: {recovery_backup.created_at}")
   print(f"Description: {recovery_backup.description}")
   ```

4. **Document current state**
   ```bash
   # Take snapshots of current state for post-mortem
   ls -laR data/ > /tmp/pre_recovery_data_state.txt
   ls -laR config/ > /tmp/pre_recovery_config_state.txt
   cp config/config.toml /tmp/corrupted_config.toml.bak 2>/dev/null || true
   ```

5. **Perform complete restore**
   ```python
   print("🔧 Initiating full system restore...")

   success = recovery.restore_backup(
       recovery_backup.backup_id,
       restore_config=True,
       restore_state=True,
       restore_data=True,
       dry_run=False
   )

   if not success:
       print("❌ CRITICAL: Full restore failed")
       # Stop here and escalate to senior engineer immediately
       raise Exception("Full restore failed")

   print("✅ Full restore completed")
   ```

6. **Verify system integrity**
   ```python
   # Re-run all health checks
   results = health_check.run_all()
   all_healthy = all(r.healthy for r in results.values())

   if all_healthy:
       print("✅ All health checks passed")
   else:
       failed = [name for name, r in results.items() if not r.healthy]
       print(f"⚠️  Some checks still failing: {', '.join(failed)}")
       # May need additional recovery steps
   ```

7. **Restart services**
   ```bash
   # Restart in order
   python scripts/live_ops.py health --config config/config.toml
   ```

8. **Create post-recovery backup**
   ```python
   verification_backup = recovery.create_backup(
       include_config=True,
       include_state=True,
       include_data=True,
       description="Post-recovery verification backup",
       tags=["recovery", "verified", "post-incident"]
   )
   print(f"Verification backup created: {verification_backup}")
   ```

#### Success Criteria
- [ ] All systems restored
- [ ] All health checks pass
- [ ] Services restarted
- [ ] Post-recovery backup created
- [ ] System operational

---

### Procedure D: Backup System Recovery

**Time Estimate:** 15-30 minutes  
**Impact:** Low to Medium - Backups unavailable

This scenario is particularly concerning as it affects disaster recovery capability itself.

#### Steps

1. **Assess backup system**
   ```python
   from src.core.backup_recovery import RecoveryManager
   from pathlib import Path

   backup_dir = Path("backups")

   # Check backup directory
   if not backup_dir.exists():
       print("🚨 Backup directory missing!")
       backup_dir.mkdir(parents=True)
       print("✅ Created backup directory")

   # Check permissions
   if not os.access(backup_dir, os.W_OK):
       print("❌ No write permission to backup directory")
       # Fix permissions

   # List existing backups
   recovery = RecoveryManager()
   backups = recovery.list_backups()
   print(f"Found {len(backups)} existing backups")
   ```

2. **Verify backup integrity**
   ```python
   for backup in backups:
       backup_path = recovery._get_backup_dir(backup.backup_id)

       # Check metadata
       metadata_file = backup_path / "metadata.json"
       if not metadata_file.exists():
           print(f"⚠️  {backup.backup_id}: Missing metadata")

       # Check files count
       actual_files = sum(1 for _ in backup_path.rglob("*") if _.is_file())
       if actual_files == 0:
           print(f"⚠️  {backup.backup_id}: No files found")
   ```

3. **Create new backup immediately**
   ```python
   try:
       new_backup = recovery.create_backup(
           include_config=True,
           include_state=True,
           include_data=True,
           description="Emergency backup after system recovery",
           tags=["emergency", "manual"]
       )
       print(f"✅ Emergency backup created: {new_backup}")
   except Exception as e:
       print(f"❌ Cannot create backup: {e}")
       # Investigate error and fix underlying issue
   ```

4. **Set up automated backups**
   ```python
   # Ensure backup cron job or scheduler is configured
   # This is system-specific
   print("Verify automated backup schedule:")
   print("  - Daily backups at 2 AM")
   print("  - Weekly backups on Sunday")
   print("  - Pre-deployment backups")
   ```

#### Success Criteria
- [ ] Backup directory accessible
- [ ] Can create new backups
- [ ] Existing backups verified
- [ ] Automated backup schedule confirmed

## Verification Steps

After any recovery procedure, perform these verification steps:

### 1. Health Checks

```python
from src.core.resilience import health_check

results = health_check.run_all()

print("\n" + "="*60)
print("HEALTH CHECK RESULTS")
print("="*60)

for name, result in results.items():
    status = "✅" if result.healthy else "❌"
    print(f"{status} {name.upper()}: {result.message}")

if all(r.healthy for r in results.values()):
    print("\n🟢 System Healthy")
else:
    print("\n🔴 System Unhealthy")
```

### 2. Data Integrity

```python
import pandas as pd

# Check critical data files
files_to_check = {
    "positions": "data/positions.csv",
    "trades": "data/trades.csv",
}

for name, path in files_to_check.items():
    try:
        df = pd.read_csv(path)
        print(f"✅ {name}: {len(df)} rows")
    except Exception as e:
        print(f"❌ {name}: {e}")
```

### 3. Configuration Validity

```python
import toml
from pathlib import Path

config_file = Path("config/config.toml")

try:
    config = toml.load(config_file)
    print("✅ Configuration valid")

    # Check critical keys
    required_keys = ["trading", "risk", "live"]
    for key in required_keys:
        if key in config:
            print(f"  ✅ {key} section present")
        else:
            print(f"  ⚠️  {key} section missing")
except Exception as e:
    print(f"❌ Configuration invalid: {e}")
```

### 4. External Connectivity

```python
# Check exchange connectivity
from src.exchange.client import get_exchange_client

try:
    exchange = get_exchange_client()
    ticker = exchange.fetch_ticker("BTC/USD")
    print(f"✅ Exchange connectivity: {ticker['last']}")
except Exception as e:
    print(f"❌ Exchange connectivity failed: {e}")
```

## Post-Recovery Actions

### Immediate (0-1 hour)

1. **Create verification backup**
   ```python
   recovery.create_backup(
       include_config=True,
       include_state=True,
       include_data=True,
       description="Post-recovery verified state",
       tags=["post-recovery", "verified"]
   )
   ```

2. **Document incident**
   - What failed
   - When detected
   - Recovery steps taken
   - Time to recovery
   - Data loss (if any)

3. **Notify stakeholders**
   - System restored
   - Impact assessment
   - Data loss window
   - Next steps

### Short-term (1-24 hours)

1. **Monitor system closely**
   - Run health checks every hour
   - Watch for anomalies
   - Check logs for errors

2. **Reconcile data**
   - Compare with external systems
   - Verify position accuracy
   - Check for missing data

3. **Update runbook** (if needed)
   - Document lessons learned
   - Update procedures
   - Add new scenarios

### Long-term (1-7 days)

1. **Conduct post-mortem**
   - Root cause analysis
   - Timeline of events
   - What worked well
   - What needs improvement

2. **Implement improvements**
   - Fix root cause
   - Improve monitoring
   - Update backup strategy
   - Enhanced testing

3. **Schedule disaster recovery drill**
   - Test recovery procedures
   - Train team members
   - Update documentation

## Escalation

### Level 1: Self-Service
- Use this runbook
- Follow procedures
- Document actions

### Level 2: Team Lead
**Escalate if:**
- Recovery procedures fail
- Backup not available
- Data loss > 24 hours
- Multiple systems affected

**Contact:** Team Lead via Slack/Email

### Level 3: Senior Engineer
**Escalate if:**
- Complete system failure
- Critical data corruption
- External systems affected
- Security incident suspected

**Contact:** Senior Engineer on-call

### Level 4: Emergency
**Escalate if:**
- Live trading affected
- Financial loss occurring
- Legal/compliance issue
- Security breach confirmed

**Contact:** CTO/CEO immediately

## Testing & Drills

### Monthly Drill Schedule

**Week 1:** Config Recovery
- Simulate config corruption
- Practice Procedure A
- Time recovery process

**Week 2:** Data Recovery
- Simulate data loss
- Practice Procedure B
- Verify data integrity

**Week 3:** Full System Recovery
- Simulate complete failure
- Practice Procedure C
- Test all procedures

**Week 4:** Backup System Check
- Verify all backups
- Test restore process
- Update retention policy

### Drill Checklist

- [ ] Schedule drill time
- [ ] Notify team (no surprises)
- [ ] Prepare test environment
- [ ] Run drill procedures
- [ ] Time each step
- [ ] Document issues found
- [ ] Update runbook
- [ ] Schedule next drill

## Appendix

### Quick Reference Commands

```bash
# Health check
python scripts/health_dashboard.py

# Create backup
python -c "from src.core.backup_recovery import RecoveryManager; \
           r = RecoveryManager(); \
           print(r.create_backup(include_config=True, include_data=True))"

# List backups
python -c "from src.core.backup_recovery import RecoveryManager; \
           r = RecoveryManager(); \
           [print(b.backup_id, b.created_at) for b in r.list_backups()[:5]]"

# Restore backup
python -c "from src.core.backup_recovery import RecoveryManager; \
           r = RecoveryManager(); \
           r.restore_backup('BACKUP_ID', restore_config=True, restore_data=True)"
```

### Contact Information

**Peak_Trade Operations Team**
- Slack: #peak-trade-ops
- Email: ops@peak-trade.local
- On-Call: See PagerDuty schedule

**Backup Locations**
- Primary: `./backups/`
- Secondary: (Configure as needed)
- Off-site: (Configure as needed)

### Related Documentation

- [RESILIENCE.md](RESILIENCE.md) - Complete resilience system documentation
- [INCIDENT_SIMULATION_AND_DRILLS.md](INCIDENT_SIMULATION_AND_DRILLS.md) - Incident drill procedures
- [RUNBOOKS_AND_INCIDENT_HANDLING.md](RUNBOOKS_AND_INCIDENT_HANDLING.md) - General incident handling

---

**Document History:**
- v1.0 (December 2024) - Initial version
- Next review: March 2025
