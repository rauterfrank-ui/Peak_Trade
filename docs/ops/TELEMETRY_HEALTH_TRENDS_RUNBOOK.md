# Telemetry Health Trends Runbook – Phase 16H

**Purpose:** Historical health monitoring & trend analysis for telemetry observability stack.

**Tools:**
- Snapshot Capture: `scripts/telemetry_health_snapshot.py`
- Trends Dashboard: `/live/telemetry` (Health Trends section)
- Trends API: `/api/telemetry/health/trends?days=30`

---

## 🎯 Quick Start

### 1. Capture First Snapshot

```bash
# Capture current health snapshot
python3 scripts/telemetry_health_snapshot.py

# Output:
# ✅ Snapshot captured at 2025-12-20T10:00:00+00:00
#    Severity: OK
#    Disk: 250.5 MB (12.2%)
#    Parse error rate: 0.0%
#    Output: logs/telemetry_health_snapshots.jsonl
```

**Exit Codes:**
- `0` = Success (snapshot captured)
- `1` = Error (failed to capture or write)

### 2. View Trends (Dashboard)

```bash
# Start dashboard
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

# Open browser
open http://127.0.0.1:8000/live/telemetry
```

**Dashboard Features:**
- Health Trends section with 24h/7d/30d windows
- Worst severity indicators
- Disk usage min/avg/max
- Critical/warn counts

### 3. Query Trends (API)

```bash
# Last 30 days
curl http://127.0.0.1:8000/api/telemetry/health/trends?days=30 | python3 -m json.tool

# Last 7 days
curl "http://127.0.0.1:8000/api/telemetry/health/trends?days=7"
```

---

## 📊 Understanding Metrics

### Snapshot Schema

Each snapshot captures:
- **Timestamp (UTC):** When the snapshot was taken
- **Severity:** Overall health status (ok/warn/critical)
- **Disk Usage:** MB + percentage vs threshold
- **Retention Staleness:** Hours since last retention run
- **Compression Failures:** Percentage of failed compressions
- **Parse Error Rate:** Percentage of invalid JSONL lines

### Time Windows

**Last 24 Hours:**
- Most granular view
- Useful for: Detecting recent incidents, validating fixes
- Recommended snapshot frequency: Hourly

**Last 7 Days:**
- Weekly patterns
- Useful for: Identifying recurring issues, capacity planning
- Shows: Disk trends, average health status

**Last 30 Days:**
- Long-term trends
- Useful for: Growth analysis, seasonal patterns
- Shows: Overall stability, degradation indicators

---

## 📈 Interpreting Trends

### 1. Worst Severity Indicator

**OK (Green):**
- All checks passed
- No action required

**WARN (Yellow):**
- Non-critical thresholds exceeded
- Action: Review trends, plan preventive measures

**CRITICAL (Red):**
- Critical thresholds exceeded
- Action: Immediate investigation required

### 2. Disk Usage Trends

**Stable (flat trend):**
- ✅ Healthy: Retention is working
- No action needed

**Increasing (upward trend):**
- ⚠️  Warning: Disk usage growing
- Action:
  ```bash
  # Check disk usage
  du -sh logs/execution

  # Apply retention
  python3 scripts/ops/telemetry_retention.py --apply

  # If critical, use aggressive policy
  python3 scripts/ops/telemetry_retention.py --apply \
    --max-age-days 7 \
    --keep-last-n 50
  ```

**Sudden spike:**
- 🔴 Critical: Investigate immediately
- Possible causes:
  - Large telemetry sessions
  - Retention not running
  - Compression disabled
- Action:
  ```bash
  # Check recent sessions
  python3 scripts/view_execution_telemetry.py --limit 10

  # Check retention status
  ls -lh logs/execution/.last_retention_run
  ```

### 3. Parse Error Rate

**Consistent 0%:**
- ✅ Healthy: All logs valid
- No action needed

**Increasing:**
- ⚠️  Warning: Data quality degrading
- Possible causes:
  - Disk full during logging
  - Interrupted processes
  - Corrupted files
- Action:
  ```bash
  # Find problematic sessions
  python3 scripts/view_execution_telemetry.py --json 2>&1 | grep -i error

  # Check disk space
  df -h
  ```

### 4. Severity Counts (Critical/Warn)

**0 critical, 0 warn (last 24h):**
- ✅ Healthy: System stable

**1-2 warnings (last 24h):**
- ℹ️  Info: Transient issues
- Action: Monitor, no immediate action

**3+ warnings (last 24h):**
- ⚠️  Warning: Pattern forming
- Action: Investigate root cause

**Any critical (last 24h):**
- 🔴 Critical: Investigate immediately
- Action: Follow incident runbook

---

## 🚨 Leading Indicators

### Early Warning Signs

**Indicator 1: Disk Usage Growth Rate**
- **What:** Average disk usage increasing > 20% per week
- **Why it matters:** Predicts capacity issues 2-4 weeks ahead
- **Action:**
  ```bash
  # Review trend
  curl "http://127.0.0.1:8000/api/telemetry/health/trends?days=30" | \
    python3 -m json.tool | grep -A 3 "disk_mb"

  # Plan capacity: lower retention threshold or add storage
  ```

**Indicator 2: Increasing Warn Count**
- **What:** Warn count growing over time (week-over-week)
- **Why it matters:** System health degrading gradually
- **Action:** Review warn reasons in recent snapshots, address root causes

**Indicator 3: Parse Error Rate > 1%**
- **What:** Any non-zero parse error rate that persists
- **Why it matters:** Data quality issue, may hide real problems
- **Action:** Immediate investigation (see Parse Error Rate section)

---

## 🔧 Automation & Scheduling

### Recommended Snapshot Schedule

**Hourly (Production):**
```bash
# Crontab entry (hourly)
0 * * * * cd /path/to/Peak_Trade && python3 scripts/telemetry_health_snapshot.py --quiet
```

**Daily (Development):**
```bash
# Crontab entry (daily at 2 AM)
0 2 * * * cd /path/to/Peak_Trade && python3 scripts/telemetry_health_snapshot.py --quiet
```

**Manual (Testing):**
```bash
# Capture snapshot now
python3 scripts/telemetry_health_snapshot.py
```

### Snapshot Retention

**Default:** 90 days (configurable)

**Prune old snapshots:**
```bash
# Manual prune (keep last 60 days)
python3 -c "
from pathlib import Path
from src.execution.telemetry_health_trends import prune_old_snapshots

path = Path('logs/telemetry_health_snapshots.jsonl')
removed, kept = prune_old_snapshots(path, days=60)
print(f'Removed: {removed}, Kept: {kept}')
"
```

---

## 📊 Degradation Detection

### What is Degradation?

Degradation is detected when:
- High critical rate (>50% in last 10 snapshots)
- High warn+critical rate (>70% in last 10 snapshots)
- Disk usage increasing >20% (first half vs second half of window)

### API Response

```json
{
  "degradation": {
    "degrading": true,
    "reasons": [
      "Disk usage increasing (150.5 → 210.3 MB)",
      "High warn+critical rate (8/10)"
    ],
    "critical_count": 2,
    "warn_count": 6,
    "window_size": 10
  }
}
```

### Actions on Degradation

**If degrading = true:**
1. Review `reasons` array
2. Check recent health snapshots
3. Apply retention/cleanup
4. Investigate root cause (excessive logging, retention failure, etc.)

---

## 🛠️ Troubleshooting

### Problem 1: No Trends Data

**Symptom:** Dashboard shows "No health snapshots found"

**Solution:**
```bash
# Capture first snapshot
python3 scripts/telemetry_health_snapshot.py

# Verify file created
ls -lh logs/telemetry_health_snapshots.jsonl

# Refresh dashboard
```

### Problem 2: Trends API Returns Empty

**Symptom:** API returns `snapshots_found: 0`

**Solution:**
```bash
# Check if snapshots file exists
ls -lh logs/telemetry_health_snapshots.jsonl

# Check snapshot age (may be older than requested days)
python3 -c "
from pathlib import Path
from src.execution.telemetry_health_trends import load_snapshots

path = Path('logs/telemetry_health_snapshots.jsonl')
snapshots = load_snapshots(path)
if snapshots:
    print(f'Oldest: {snapshots[0].ts_utc}')
    print(f'Newest: {snapshots[-1].ts_utc}')
else:
    print('No snapshots found')
"
```

### Problem 3: Snapshots File Too Large

**Symptom:** Snapshots file > 100 MB

**Solution:**
```bash
# Check size
ls -lh logs/telemetry_health_snapshots.jsonl

# Prune old snapshots (keep last 30 days)
python3 -c "
from pathlib import Path
from src.execution.telemetry_health_trends import prune_old_snapshots

path = Path('logs/telemetry_health_snapshots.jsonl')
removed, kept = prune_old_snapshots(path, days=30)
print(f'Removed: {removed}, Kept: {kept}')
"
```

### Problem 4: Snapshot Capture Fails

**Symptom:** `scripts/telemetry_health_snapshot.py` exits with code 1

**Solution:**
```bash
# Run without --quiet to see error
python3 scripts/telemetry_health_snapshot.py

# Check permissions
ls -la logs/

# Check disk space
df -h

# Check telemetry root exists
ls -la logs/execution/
```

---

## 📋 Maintenance Checklist

### Daily
- [ ] Check dashboard for critical/warn trends (30s)
- [ ] Verify snapshot capture is running (cron)

### Weekly
- [ ] Review 7-day trends (5 min)
- [ ] Check disk usage trend (is it increasing?)
- [ ] Verify degradation indicators

### Monthly
- [ ] Review 30-day trends (10 min)
- [ ] Analyze seasonal patterns
- [ ] Plan capacity (if disk usage growing)
- [ ] Prune old snapshots (keep last 90 days)

---

## 🔗 Related Documentation

- **Phase 16F Health Check:** `docs/ops/TELEMETRY_HEALTH_RUNBOOK.md`
- **Phase 16E Retention:** `docs/ops/EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md` (Retention section)
- **Phase 16C Viewer:** `docs/execution/TELEMETRY_VIEWER.md`

---

## ✅ Quick Reference

**Capture Snapshot:**
```bash
python3 scripts/telemetry_health_snapshot.py
```

**View Trends (Dashboard):**
```bash
open http://127.0.0.1:8000/live/telemetry
```

**Query Trends (API):**
```bash
curl "http://127.0.0.1:8000/api/telemetry/health/trends?days=30"
```

**Prune Old Snapshots:**
```python
from pathlib import Path
from src.execution.telemetry_health_trends import prune_old_snapshots

prune_old_snapshots(Path("logs/telemetry_health_snapshots.jsonl"), days=90)
```

---

**Status:** ✅ **Phase 16H Complete** (Historical health trends)  
**Stack:** Phasen 16A-H (Logging → Viewer → QA → Retention → Health → Trends)
