# Telemetry Alerting Lifecycle Runbook – Phase 16J

**Purpose:** Alert lifecycle management with history, operator actions (ACK/SNOOZE), and noise control.

**Tools:**
- Lifecycle CLI: `scripts/telemetry_alerts_lifecycle.py`
- Main Runner: `scripts/telemetry_alerts.py` (integrated with Phase 16J)

---

## 🎯 Quick Start

### 1. Enable Alert History (Optional)

**Edit Config:** `config/telemetry_alerting.toml`

```toml
[telemetry.alerting.history]
enabled = true
path = "data/telemetry/alerts/alerts_history.jsonl"
retain_days = 14
```

### 2. Enable Operator Actions (Optional)

```toml
[telemetry.alerting.operator_actions]
enabled = true
state_path = "data/telemetry/alerts/alerts_state.json"
require_flag = true
suppress_critical_on_ack = false  # CRITICAL bypasses ACK by default
```

### 3. View Alert History

```bash
# Last 50 alerts
python scripts/telemetry_alerts_lifecycle.py history --limit 50

# Last 24 hours
python scripts/telemetry_alerts_lifecycle.py history --since 24h

# Filter by severity
python scripts/telemetry_alerts_lifecycle.py history --severity critical --limit 20
```

### 4. Acknowledge Alert (Suppress Future Occurrences)

```bash
# ACK with 2-hour TTL
python scripts/telemetry_alerts_lifecycle.py ack \
  --dedupe-key "health_critical:Telemetry Health Check CRITICAL" \
  --ttl 2h \
  --enable-operator-actions

# Permanent ACK (no TTL)
python scripts/telemetry_alerts_lifecycle.py ack \
  --dedupe-key "degradation_detected:..." \
  --enable-operator-actions
```

### 5. Snooze Rule (Suppress All Alerts from Rule)

```bash
# Snooze for 30 minutes
python scripts/telemetry_alerts_lifecycle.py snooze \
  --rule-id degradation_detected \
  --ttl 30m \
  --enable-operator-actions \
  --reason "Under maintenance"

# Unsnooze
python scripts/telemetry_alerts_lifecycle.py unsnooze \
  --rule-id degradation_detected \
  --enable-operator-actions
```

### 6. View Statistics

```bash
# Last 7 days
python scripts/telemetry_alerts_lifecycle.py stats --since 7d

# All time
python scripts/telemetry_alerts_lifecycle.py stats
```

---

## 📊 Features

### Alert History

**Storage:** JSONL append-only file (`data/telemetry/alerts/alerts_history.jsonl`)

**Includes:**
- All alert metadata (timestamp, severity, rule_id, dedupe_key, labels)
- Delivery status (sent/failed/skipped)
- Automatic retention cleanup (14 days default)

**Query Capabilities:**
- Time-based filtering (`--since`)
- Severity filtering (`--severity`)
- Rule filtering (`--rule-id`)
- Limit results (`--limit`)

### Operator Actions

**ACK (Acknowledge):**
- Suppresses future alerts with same `dedupe_key`
- Optional TTL (e.g., `2h`, `30m`, permanent if omitted)
- CRITICAL alerts bypass ACK by default (configurable)
- Stored in: `data/telemetry/alerts/alerts_state.json`

**SNOOZE:**
- Suppresses ALL alerts from a rule
- Requires TTL (no permanent snooze)
- Applies to all severities
- Automatic expiry and cleanup

**Behavior:**
- Alert engine checks operator state before emitting alerts
- Snoozed rules → skipped evaluation
- Acked dedupe_keys → suppressed (unless CRITICAL)

### Statistics

**Provides:**
- Total alert count
- By severity (info/warn/critical)
- By rule (top 10 noisy rules)
- By delivery status (sent/failed)

---

## 🔧 Configuration

### Complete Config

```toml
# config/telemetry_alerting.toml

[telemetry.alerting]
enabled = true
dry_run = true

[telemetry.alerting.history]
enabled = true
path = "data/telemetry/alerts/alerts_history.jsonl"
retain_days = 14

[telemetry.alerting.operator_actions]
enabled = true
state_path = "data/telemetry/alerts/alerts_state.json"
require_flag = true
suppress_critical_on_ack = false
```

**Safety Defaults:**
- History: `enabled = false` (opt-in)
- Operator actions: `enabled = false` (opt-in)
- Suppress CRITICAL on ACK: `false` (CRITICAL bypasses)

---

## 📈 Workflow Examples

### Example 1: Noisy Rule Mitigation

**Problem:** `degradation_detected` firing every 10 minutes during known maintenance.

**Solution:**
```bash
# Snooze for 4 hours
python scripts/telemetry_alerts_lifecycle.py snooze \
  --rule-id degradation_detected \
  --ttl 4h \
  --enable-operator-actions \
  --reason "Maintenance: retention cleanup"

# After maintenance, verify unsnooze (or wait for TTL expiry)
python scripts/telemetry_alerts_lifecycle.py unsnooze \
  --rule-id degradation_detected \
  --enable-operator-actions
```

### Example 2: Acknowledged Incident

**Problem:** Critical health alert acknowledged, incident resolved, don't want duplicate alerts for 2 hours.

**Solution:**
```bash
# ACK with 2-hour TTL
python scripts/telemetry_alerts_lifecycle.py ack \
  --dedupe-key "health_critical:Telemetry Health Check CRITICAL" \
  --ttl 2h \
  --enable-operator-actions \
  --reason "Incident resolved: disk cleanup applied"
```

### Example 3: Post-Incident Analysis

**Problem:** Review what alerts fired during incident window.

**Solution:**
```bash
# View last 6 hours of critical alerts
python scripts/telemetry_alerts_lifecycle.py history \
  --since 6h \
  --severity critical

# Get stats for last 24h
python scripts/telemetry_alerts_lifecycle.py stats --since 24h
```

---

## 🚨 Best Practices

### 1. Use TTLs for Temporary Suppressions

Always use TTL for snooze/ACK unless permanent suppression is intended:

```bash
# Good: 30-minute snooze during maintenance
--ttl 30m

# Bad: No TTL (permanent suppression)
# (omit --ttl only if you're sure)
```

### 2. CRITICAL Alerts Should Not Be Suppressed

Default config prevents CRITICAL suppression on ACK. Only override if necessary:

```toml
# Only enable if you understand implications
suppress_critical_on_ack = false  # Default: CRITICAL bypasses ACK
```

### 3. Review History Regularly

Weekly review of alert statistics:

```bash
python scripts/telemetry_alerts_lifecycle.py stats --since 7d
```

### 4. Clean Up Expired State

Operator state auto-cleans expired entries, but manual cleanup if needed:

```python
from pathlib import Path
from src.execution.alerting.operator_state import OperatorState

state = OperatorState(Path("data/telemetry/alerts/alerts_state.json"), enabled=True)
state._cleanup_expired()
```

---

## ❓ Troubleshooting

### Problem 1: Operator Actions Not Working

**Symptom:** ACK/SNOOZE returns "Operator actions disabled"

**Solution:**
1. Check config: `telemetry.alerting.operator_actions.enabled = true`
2. Use `--enable-operator-actions` flag in CLI
3. Verify state file path is writable

### Problem 2: History Not Recording

**Symptom:** `history` command returns no results

**Solution:**
1. Check config: `telemetry.alerting.history.enabled = true`
2. Run main alert runner: `python scripts&#47;telemetry_alerts.py`
3. Verify history file exists: `ls -la data/telemetry/alerts/alerts_history.jsonl`

### Problem 3: ACK Not Suppressing Alerts

**Symptom:** Alerts still firing after ACK

**Solution:**
1. Verify dedupe_key matches: Check alert output for exact dedupe_key
2. Check TTL expiry: May have expired
3. Check severity: CRITICAL bypasses ACK by default

### Problem 4: Stats Show Wrong Counts

**Symptom:** Statistics don't match expected alert counts

**Solution:**
1. Verify time window: Use `--since` to filter correctly
2. Check history retention: Old alerts may be cleaned up
3. Re-run main alert runner to populate history

---

## 📊 Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Invalid args or operator actions disabled |
| `2` | Operation failed (write error, etc.) |

---

## 🔗 Related Documentation

- **Phase 16I Alerting:** `docs/ops/TELEMETRY_ALERTING_RUNBOOK.md`
- **Phase 16F Health:** `docs/ops/TELEMETRY_HEALTH_RUNBOOK.md`
- **Phase 16H Trends:** `docs/ops/TELEMETRY_HEALTH_TRENDS_RUNBOOK.md`

---

**Status:** ✅ **Phase 16J Complete** (Alert lifecycle + noise control)  
**Stack:** Phases 16A-J (Logging → Viewer → QA → Retention → Health → Trends → Alerting → **Lifecycle**)
