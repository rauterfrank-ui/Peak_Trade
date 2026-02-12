# Telemetry Health Runbook – Phase 16F

**Purpose:** Monitor and maintain telemetry observability stack health.

**Tools:**
- Health Check CLI: `scripts/telemetry_health_check.py`
- Telemetry Console Dashboard: `/live/telemetry`
- Health API: `/api/telemetry/health`

---

## 🎯 Quick Start

### 1. Check Overall Health (CLI)

```bash
# Human-readable output
python3 scripts/telemetry_health_check.py

# JSON output (for automation)
python3 scripts/telemetry_health_check.py --json
```

**Exit Codes:**
- `0` = OK (all checks pass)
- `2` = WARNING (non-critical threshold exceeded)
- `3` = CRITICAL (critical threshold exceeded)

### 2. Check Health (Dashboard)

```bash
# Start dashboard
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

# Open browser
open http://127.0.0.1:8000/live/telemetry
```

**Dashboard Features:**
- ✅ Real-time health status (OK/WARN/CRITICAL)
- 📊 Disk usage summary
- 🗄️ Retention policy overview
- 📋 Recent sessions table (last 50)
- 🔧 Copy/paste CLI commands

### 3. Check Health (API)

```bash
curl http://127.0.0.1:8000/api/telemetry/health
```

---

## 🔍 Health Checks Explained

### 1. Disk Usage

**What:** Total size of telemetry logs directory.

**Thresholds (Default):**
- ⚠️  WARNING: 1500 MB (1.5 GB)
- 🔴 CRITICAL: 1900 MB (1.9 GB, near 2 GB default retention limit)

**Troubleshooting:**

```bash
# Check disk usage
du -sh logs/execution

# Apply retention cleanup
python3 scripts/ops/telemetry_retention.py --apply

# Aggressive cleanup (if critical)
python3 scripts/ops/telemetry_retention.py --apply \
  --max-age-days 7 \
  --keep-last-n 50
```

### 2. Retention Staleness

**What:** Time since last retention/compression run.

**Thresholds (Default):**
- ⚠️  WARNING: 48 hours
- 🔴 CRITICAL: 168 hours (7 days)

**Troubleshooting:**

```bash
# Check when retention last ran
ls -lh logs/execution/.last_retention_run  # (marker file)
ls -lht logs/execution/*.gz | head -5       # (recent compressed files)

# Run retention now
python3 scripts/ops/telemetry_retention.py --apply

# Add to cron (recommended)
# Run daily at 2 AM:
# 0 2 * * * cd /path/to/Peak_Trade && python3 scripts/ops/telemetry_retention.py --apply
```

### 3. Compression Failures

**What:** Percentage of compression operations that failed (indicated by orphaned `.tmp` files).

**Thresholds (Default):**
- ⚠️  WARNING: 10% failure rate
- 🔴 CRITICAL: 25% failure rate

**Troubleshooting:**

```bash
# Check for orphaned temp files
ls -lh logs/execution/*.tmp

# Remove orphaned files (manual cleanup)
rm logs/execution/*.tmp

# Check disk space (compression failures often caused by full disk)
df -h
```

### 4. Parse Error Rate

**What:** Percentage of invalid JSON lines in telemetry logs (samples recent logs).

**Thresholds (Default):**
- ⚠️  WARNING: 5% invalid lines
- 🔴 CRITICAL: 15% invalid lines

**Troubleshooting:**

```bash
# Check for invalid lines
python3 scripts/view_execution_telemetry.py --session <SESSION_ID>

# Manually inspect log file
cat logs/execution/<SESSION_ID>.jsonl | head -20

# Check for truncated/corrupted files
python3 -c "
import json
import sys
with open('logs/execution/<SESSION_ID>.jsonl') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line.strip())
        except json.JSONDecodeError as e:
            print(f'Line {i}: {e}')
            print(f'Content: {line[:100]}')
"
```

---

## 🚨 Common Scenarios

### Scenario 1: Disk Almost Full (CRITICAL)

**Symptoms:**
- Health check shows CRITICAL for disk usage
- Dashboard shows > 1900 MB

**Actions:**

```bash
# 1. Immediate cleanup (aggressive)
python3 scripts/ops/telemetry_retention.py --apply \
  --max-age-days 7 \
  --keep-last-n 50 \
  --compress-after-days 0  # Delete immediately, no compression

# 2. Verify cleanup
du -sh logs/execution

# 3. If still critical, manually delete old logs
rm logs/execution/<OLD_SESSION_ID>.jsonl
rm logs/execution/<OLD_SESSION_ID>.jsonl.gz
```

**Prevention:**
- Schedule automated retention (cron)
- Lower `max_total_mb` in config
- Increase retention frequency

### Scenario 2: Retention Not Running (WARNING)

**Symptoms:**
- Health check shows WARNING for retention staleness
- No `.last_retention_run` marker or very old

**Actions:**

```bash
# 1. Run retention manually
python3 scripts/ops/telemetry_retention.py --apply

# 2. Check cron/scheduler
crontab -l | grep retention

# 3. Add to cron if missing
crontab -e
# Add: 0 2 * * * cd /path/to/Peak_Trade && python3 scripts/ops/telemetry_retention.py --apply
```

### Scenario 3: High Parse Error Rate (WARNING)

**Symptoms:**
- Health check shows WARNING for parse error rate
- Dashboard shows > 5% invalid lines

**Root Causes:**
- Partial writes (interrupted process)
- Disk full during logging
- Corrupted/truncated files

**Actions:**

```bash
# 1. Identify problematic sessions
python3 scripts/view_execution_telemetry.py --json 2>&1 | grep -i error

# 2. Manually inspect
cat logs/execution/<SESSION_ID>.jsonl | tail -50

# 3. If file is corrupted, move to quarantine
mkdir -p logs/execution/quarantine
mv logs/execution/<SESSION_ID>.jsonl logs/execution/quarantine/

# 4. Check for disk space issues
df -h
```

**Prevention:**
- Ensure adequate disk space
- Use atomic writes (telemetry logger already does this)
- Monitor disk usage proactively

### Scenario 4: Compression Failures (WARNING)

**Symptoms:**
- Health check shows WARNING for compression failures
- Many `.tmp` files in telemetry dir

**Actions:**

```bash
# 1. Check disk space
df -h

# 2. Remove orphaned temp files
rm logs/execution/*.tmp

# 3. Re-run retention (will retry compression)
python3 scripts/ops/telemetry_retention.py --apply

# 4. Check permissions
ls -la logs/execution/
```

---

## 🔧 Custom Thresholds

### CLI Override

```bash
# Custom disk thresholds
python3 scripts/telemetry_health_check.py \
  --disk-warn-mb 1000 \
  --disk-critical-mb 1800

# Custom retention thresholds
python3 scripts/telemetry_health_check.py \
  --retention-warn-hours 24 \
  --retention-critical-hours 72
```

### API Override

```bash
# Custom root directory
curl "http://127.0.0.1:8000/api/telemetry/health?root=logs/custom_execution"
```

---

## 📊 Monitoring Integration

### Prometheus/Grafana (Future)

```bash
# Export metrics (example)
python3 scripts/telemetry_health_check.py --json | jq '.checks[] | {name, status, value}'
```

### Slack/PagerDuty Alerts (Future)

```bash
# Run health check in cron, alert on non-zero exit
python3 scripts/telemetry_health_check.py || \
  curl -X POST https://hooks.slack.com/... -d '{"text": "Telemetry health check failed"}'
```

---

## 🎯 Maintenance Schedule (Recommended)

| Frequency | Task | Command |
|-----------|------|---------|
| **Daily** | Retention cleanup | `python3 scripts/ops/telemetry_retention.py --apply` |
| **Daily** | Health check | `python3 scripts/telemetry_health_check.py` |
| **Weekly** | Review dashboard | Open `/live/telemetry` |
| **Monthly** | Manual audit | Review old sessions, disk trends |

---

## 🔗 Related Documentation

- **Phase 16E Retention:** `docs/ops/EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md` (Retention & Rotation section)
- **Phase 16C Viewer:** `docs/execution/TELEMETRY_VIEWER.md`
- **Phase 16D Incident Runbook:** `docs/ops/EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md`
- **PR #186 Merge Log:** `docs/ops/PR_186_MERGE_LOG.md`

---

## ✅ Quick Reference

**Health Check:**
```bash
python3 scripts/telemetry_health_check.py
```

**Dashboard:**
```bash
open http://127.0.0.1:8000/live/telemetry
```

**Retention:**
```bash
python3 scripts/ops/telemetry_retention.py --apply
```

**Disk Usage:**
```bash
du -sh logs/execution
```

**Exit Codes:**
- `0` = OK
- `2` = WARNING
- `3` = CRITICAL
