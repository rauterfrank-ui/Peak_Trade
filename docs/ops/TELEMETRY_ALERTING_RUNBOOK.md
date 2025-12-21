# Telemetry Alerting Runbook – Phase 16I

**Purpose:** Real-time alerting and incident hooks on top of health + trend analysis (Phases 16F+16H).

**Tools:**
- Alert Runner: `scripts/telemetry_alerts.py`
- Alerts API: `/api/telemetry/alerts/latest?limit=50`
- Alerts Dashboard: `/live/telemetry` (Alerts section)

---

## 🎯 Quick Start

### 1. Enable Alerting (Required)

**Edit Config:** `config/telemetry_alerting.toml`

```toml
[telemetry.alerting]
enabled = true  # REQUIRED: Enable alerting system
dry_run = true  # Recommended: Test with dry-run first
```

### 2. Run Alerts (Dry-Run)

```bash
# Dry-run (prints alerts, doesn't send)
python scripts/telemetry_alerts.py

# Output:
# 🚨 2 alert(s) triggered:
#   🔴 CRITICAL: 1
#   ⚠️  WARN: 1
#
# ⚠️  [WARN] Telemetry Health Degradation Detected
#   Source: rule:degradation_detected
#   ...
```

**Exit Codes:**
- `0` = No critical alerts and health OK
- `2` = Critical alert(s) emitted OR health critical
- `1` = Partial failures (e.g., webhook send failed)

### 3. View Alerts (Dashboard)

```bash
# Start dashboard
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

# Open browser
open http://127.0.0.1:8000/live/telemetry
```

**Dashboard Features:**
- Recent alerts with severity badges
- Auto-refresh every 60 seconds
- Filter by severity (API supports)

---

## 📋 Alert Rules

### Built-in Rules (4)

**1. Health Check Critical**
- **Trigger:** Health status = CRITICAL
- **Severity:** CRITICAL
- **Cooldown:** 5 minutes
- **Action:** Investigate immediately

**2. Degradation Detected**
- **Trigger:** Degradation analysis flags system degrading
- **Severity:** WARN
- **Cooldown:** 10 minutes
- **Action:** Review health trends, apply retention/cleanup

**3. Leading Indicator: Disk Growth**
- **Trigger:** Disk usage increasing rapidly (>20%)
- **Severity:** WARN
- **Cooldown:** 1 hour (long-term trend)
- **Action:** Plan capacity expansion or adjust retention policy

**4. Parse Error Rate High**
- **Trigger:** Parse error rate > 5%
- **Severity:** WARN
- **Cooldown:** 10 minutes
- **Action:** Investigate telemetry log quality

### Rule Configuration

**Enable/Disable Rules:** Edit `config/telemetry_alerting.toml`

```toml
[telemetry.alerting.rules.health_critical]
enabled = true  # Set to false to disable
cooldown_seconds = 300
dedupe_window_seconds = 900
```

**Adjust Thresholds:**
- `cooldown_seconds`: Minimum time between same rule firing
- `dedupe_window_seconds`: Time window for deduplication (same alert)

---

## 🚨 Alert Workflow

### Development/Testing (Dry-Run)

```bash
# 1. Enable alerting + dry-run
# Edit config: telemetry.alerting.enabled = true, dry_run = true

# 2. Run alert evaluation
python scripts/telemetry_alerts.py

# 3. Review output (printed to console)
# Adjust rules/thresholds as needed

# 4. Check exit code
echo $?  # 0 = OK, 2 = Critical
```

### Production (Webhook)

```bash
# 1. Configure webhook
# Edit config: telemetry.alerting.webhook.enabled = true
# Set webhook.url = "https://your-webhook-url"

# 2. Test with dry-run first
python scripts/telemetry_alerts.py --no-dry-run --sink webhook

# 3. Deploy (schedule with cron)
# Crontab entry (every 10 minutes):
*/10 * * * * cd /path/to/Peak_Trade && python scripts/telemetry_alerts.py --no-dry-run --sink webhook >> logs/alerts.log 2>&1
```

### Troubleshooting

**Problem:** Alerting disabled warning

```bash
# Check config
grep "enabled" config/telemetry_alerting.toml

# Enable:
[telemetry.alerting]
enabled = true
```

**Problem:** No alerts triggered but health is critical

```bash
# Check health status
python scripts/telemetry_health_check.py

# Check trend data
python scripts/telemetry_health_snapshot.py
```

**Problem:** Webhook send fails

```bash
# Test webhook URL manually
curl -X POST "https://your-webhook-url" \
  -H "Content-Type: application/json" \
  -d '{"test": "alert"}'

# Check webhook config
grep -A 5 "webhook" config/telemetry_alerting.toml
```

---

## 🔧 Configuration Details

### Complete Config Template

```toml
# config/telemetry_alerting.toml

[telemetry.alerting]
enabled = false  # MUST be true to enable
dry_run = true   # Recommended: test first
default_sink = "console"  # or "webhook"
max_alerts_per_run = 20
cooldown_seconds_default = 300
dedupe_window_seconds_default = 900

[telemetry.alerting.webhook]
enabled = false
url = ""  # Required if webhook enabled
timeout = 10
headers = ""  # Optional: '{"Authorization": "Bearer TOKEN"}'

[telemetry.alerting.rules.health_critical]
enabled = true
severity = "critical"
cooldown_seconds = 300
dedupe_window_seconds = 900

[telemetry.alerting.rules.degradation_detected]
enabled = true
severity = "warn"
cooldown_seconds = 600
dedupe_window_seconds = 1800

[telemetry.alerting.rules.leading_indicator_disk_growth]
enabled = true
severity = "warn"
cooldown_seconds = 3600
dedupe_window_seconds = 7200

[telemetry.alerting.rules.parse_error_rate_high]
enabled = true
severity = "warn"
cooldown_seconds = 600
dedupe_window_seconds = 1800
```

### Sink Types

**Console (Default):**
- Prints alerts to stdout
- Color-coded by severity
- No external dependencies
- Ideal for dry-run

**Webhook:**
- POST JSON to URL
- Configurable timeout (default 10s)
- Optional custom headers (auth)
- Safe by default (disabled unless configured)

---

## 📊 API Reference

### Endpoint: `/api/telemetry/alerts/latest`

**Query Parameters:**
- `limit` (int, default 50): Maximum alerts to return
- `severity` (string, optional): Filter by severity (info/warn/critical)

**Response:**
```json
{
  "alerts": [
    {
      "id": "uuid",
      "timestamp_utc": "2025-12-20T10:00:00+00:00",
      "source": "rule:health_critical",
      "severity": "critical",
      "title": "Telemetry Health Check CRITICAL",
      "body": "Telemetry health check status is CRITICAL...",
      "labels": {
        "rule_id": "health_critical",
        "rule_type": "health_check",
        "category": "health"
      },
      "dedupe_key": "health_critical:Telemetry Health Check CRITICAL"
    }
  ],
  "count": 1,
  "severity_filter": null
}
```

**Example:**
```bash
# Get all alerts
curl http://127.0.0.1:8000/api/telemetry/alerts/latest?limit=50

# Get only critical alerts
curl "http://127.0.0.1:8000/api/telemetry/alerts/latest?severity=critical"
```

---

## 🎯 Incident Response

### Step 1: Alert Received

**Critical Alert:**
1. Check dashboard: `/live/telemetry`
2. Review health status (top section)
3. Check trends (degradation indicators)

**Warn Alert:**
1. Note alert details (source, body)
2. Review health trends (24h/7d)
3. Plan preventive action

### Step 2: Triage

**Health Critical:**
```bash
# Run health check manually
python scripts/telemetry_health_check.py

# Review specific checks
# - Disk usage (> 1.9 GB?)
# - Retention staleness (> 7 days?)
# - Parse error rate (> 15%?)
```

**Degradation:**
```bash
# Review trend data
curl "http://127.0.0.1:8000/api/telemetry/health/trends?days=7" | python -m json.tool

# Check degradation reasons
# - Disk usage increasing
# - High warn+critical rate
```

### Step 3: Remediate

**Disk Usage:**
```bash
# Check disk usage
du -sh logs/execution

# Apply retention
python scripts/ops/telemetry_retention.py --apply

# If critical, use aggressive policy
python scripts/ops/telemetry_retention.py --apply --max-age-days 7
```

**Parse Errors:**
```bash
# Find problematic sessions
python scripts/view_execution_telemetry.py --json 2>&1 | grep -i error

# Check disk space (may cause write failures)
df -h
```

**Degradation:**
```bash
# Review recent health snapshots
python -c "
from pathlib import Path
from src.execution.telemetry_health_trends import load_snapshots

snapshots = load_snapshots(Path('logs/telemetry_health_snapshots.jsonl'), limit=10)
for s in snapshots:
    print(f'{s.ts_utc.isoformat()}: {s.severity} (disk: {s.disk_usage_mb:.1f} MB)')
"
```

### Step 4: Verify Fix

```bash
# Run health check
python scripts/telemetry_health_check.py
# Exit code should be 0 (OK)

# Capture snapshot
python scripts/telemetry_health_snapshot.py

# Re-run alerts
python scripts/telemetry_alerts.py
# Should show no critical alerts
```

### Step 5: Document

**Incident Log Template:**
```markdown
## Incident: [Severity] [Title]
- **Time:** YYYY-MM-DD HH:MM UTC
- **Alert:** [Alert title]
- **Source:** [Alert source/rule]
- **Root Cause:** [Brief description]
- **Actions Taken:**
  1. [Action 1]
  2. [Action 2]
- **Resolution:** [How resolved]
- **Verified:** [Verification command + result]
- **Follow-up:** [Any follow-up tasks]
```

---

## 🔕 Disabling Noisy Rules

### Temporary Disable (Command Line)

**Not directly supported** - use config file

### Permanent Disable (Config)

Edit `config/telemetry_alerting.toml`:

```toml
[telemetry.alerting.rules.rule_id_here]
enabled = false
```

**Example: Disable disk growth alerts temporarily:**

```toml
[telemetry.alerting.rules.leading_indicator_disk_growth]
enabled = false  # Will be ignored until re-enabled
```

### Adjust Cooldown (Reduce Noise)

```toml
[telemetry.alerting.rules.degradation_detected]
cooldown_seconds = 3600  # 1 hour instead of 10 minutes
dedupe_window_seconds = 7200  # 2 hours instead of 30 minutes
```

---

## 📈 Alerting Metrics

### Dashboard Visibility

**Dashboard URL:** `/live/telemetry`

**Displays:**
- Recent alerts (last 10)
- Severity badges (color-coded)
- Alert source + timestamp
- Auto-refresh (every 60s)

### API Metrics

```bash
# Count by severity
curl "http://127.0.0.1:8000/api/telemetry/alerts/latest?limit=1000" | \
  python -m json.tool | grep '"severity"' | sort | uniq -c

# Critical alerts only
curl "http://127.0.0.1:8000/api/telemetry/alerts/latest?severity=critical&limit=50"
```

---

## ✅ Best Practices

### 1. Test with Dry-Run First

Always test alerting configuration with dry-run before going live:

```bash
python scripts/telemetry_alerts.py --dry-run
```

### 2. Start with Console Sink

Use console sink initially, then move to webhook when confident:

```toml
[telemetry.alerting]
enabled = true
dry_run = false
default_sink = "console"  # Start here
```

### 3. Monitor Webhook Failures

Check exit codes and logs:

```bash
python scripts/telemetry_alerts.py --no-dry-run --sink webhook
echo $?  # 1 = webhook failed, 2 = critical alert
```

### 4. Adjust Cooldowns Based on Urgency

- **Critical alerts:** Short cooldown (5 min)
- **Warning alerts:** Medium cooldown (10-30 min)
- **Info alerts:** Long cooldown (1+ hour)

### 5. Regular Rule Review

Review alert rules monthly:
- Are they still relevant?
- Are cooldowns appropriate?
- Are there false positives?

---

## 🔗 Related Documentation

- **Phase 16F Health Check:** `docs/ops/TELEMETRY_HEALTH_RUNBOOK.md`
- **Phase 16H Trends:** `docs/ops/TELEMETRY_HEALTH_TRENDS_RUNBOOK.md`
- **Phase 16E Retention:** `docs/ops/EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md` (Retention section)

---

## 🚀 Production Deployment Checklist

- [ ] Config: `telemetry.alerting.enabled = true`
- [ ] Config: Test with `dry_run = true` first
- [ ] Config: Webhook URL configured (if using webhook)
- [ ] Config: Webhook authentication headers set (if required)
- [ ] Test: Run `python scripts/telemetry_alerts.py --dry-run`
- [ ] Test: Verify exit codes (0/1/2)
- [ ] Test: Check dashboard alerts section
- [ ] Test: Send test webhook (if using webhook)
- [ ] Deploy: Schedule cron job (recommended: every 10-30 minutes)
- [ ] Monitor: Check alert logs for first 24 hours
- [ ] Tune: Adjust cooldowns/thresholds based on noise level

---

**Status:** ✅ **Phase 16I Complete** (Real-time alerting + incident hooks)  
**Stack:** Phasen 16A-I (Logging → Viewer → QA → Retention → Health → Trends → **Alerting**)
