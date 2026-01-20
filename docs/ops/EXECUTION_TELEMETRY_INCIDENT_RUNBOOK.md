# Execution Telemetry - Incident Runbook

**Phase 16D - Ops Pack**

Quick reference guide for diagnosing and responding to execution telemetry incidents.

**Audience:** Operators, DevOps, SRE  
**Scope:** Read-only diagnostics (no system changes)  
**Prerequisites:** Access to `logs/execution/` directory and CLI tools

---

## 📋 Quick Reference

### Common Symptoms → Actions

| Symptom | Likely Cause | First Action |
|---------|--------------|--------------|
| Missing fills after orders | Order execution failed | [Check missing fills](#3-missing-fills-after-orders) |
| High error rate in logs | Invalid JSON / corrupted lines | [Check parse errors](#5-high-error-rate-invalid-lines) |
| Latency spikes | Network/broker delays | [Analyze latency](#4-latency-spikes-summary) |
| No events for session | Wrong session_id / logs not created | [Find session logs](#6-find-session-logs) |
| Timestamps out of order | Clock skew / concurrency | [Check monotonicity](#7-timestamp-ordering-issues) |

---

## 🔍 Diagnostic Commands (Copy/Paste Ready)

### 1. Show Last 50 Fills for Session

**Use case:** Quick check if fills are being recorded.

```bash
# Replace SESSION_ID with actual session ID
python scripts/view_execution_telemetry.py \
  --session SESSION_ID \
  --type fill \
  --limit 50 \
  --timeline 50
```

**Expected output:** List of fill events with timestamps, symbols, prices, quantities.

**Red flags:**
- No fills despite orders → execution issue
- Fill prices wildly different from market → slippage problem
- Gaps in timestamps → intermittent connectivity

---

### 2. Filter by Symbol

**Use case:** Isolate issues to specific trading pairs.

```bash
# Check all BTC-USD events
python scripts/view_execution_telemetry.py \
  --symbol BTC-USD \
  --limit 200 \
  --summary
```

**Expected output:** Summary stats + timeline for symbol.

**Red flags:**
- High error rate for specific symbol → data feed issue
- No fills for high-volume symbol → exchange API issue
- Orders but no fills → order rejection / insufficient balance

---

### 3. Missing Fills After Orders

**Use case:** Detect orders that didn't result in fills.

```bash
# Export full session to JSON for analysis
python scripts/view_execution_telemetry.py \
  --session SESSION_ID \
  --json > /tmp/session_events.jsonl

# Count orders vs fills
grep '"kind": "order"' /tmp/session_events.jsonl | wc -l
grep '"kind": "fill"' /tmp/session_events.jsonl | wc -l
```

**Analysis:**
- If `orders > fills`: Check for rejections, insufficient balance, order cancellations
- If `orders == fills`: Normal (1:1 mapping expected for market orders)
- If `fills > orders`: Unexpected (possible duplicate logging)

**Next steps:**
1. Check order payloads for `order_id`
2. Search for corresponding fills with same `order_id`
3. If missing: Check broker logs / exchange API status
4. Escalate if systematic pattern

---

### 4. Latency Spikes Summary

**Use case:** Identify slow execution paths.

```bash
# Get summary with latency stats
python scripts/view_execution_telemetry.py \
  --session SESSION_ID \
  --summary
```

**Expected output:**
```
=== Execution Telemetry Summary ===
Total events: 1250
Time range: 2025-12-20T10:00:00Z to 2025-12-20T11:30:00Z
...
Latency (intent->order): avg 45ms, p50 42ms, p95 89ms, max 250ms
Latency (order->fill): avg 120ms, p50 110ms, p95 280ms, max 1500ms
```

**Red flags:**
- p95 > 500ms → Network/broker latency issues
- max > 5000ms → Possible timeouts / retries
- Sudden spikes in avg → Investigate at that time window

**Drill down:**
```bash
# Check events around spike time
python scripts/view_execution_telemetry.py \
  --session SESSION_ID \
  --from "2025-12-20T10:15:00Z" \
  --to "2025-12-20T10:20:00Z" \
  --timeline 100
```

---

### 5. High Error Rate (Invalid Lines)

**Use case:** Detect log corruption or parser issues.

```bash
# Check error rate
python scripts/view_execution_telemetry.py \
  --path logs/execution \
  --summary
```

**Expected output:**
```
Parse Statistics:
  Total lines: 10000
  Valid events: 9987
  Invalid lines: 13
  Error rate: 0.13%
```

**Red flags:**
- Error rate > 1% → Investigate log corruption
- Error rate > 5% → Critical: Possible disk/write issues

**Drill down:**
```bash
# Find invalid lines manually
cd logs/execution
for file in *.jsonl; do
  echo "Checking $file..."
  python -c "
import json
import sys
with open('$file') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except:
            print(f'Line {i}: {line[:80]}...')
  "
done
```

---

### 6. Find Session Logs

**Use case:** Locate logs when session_id is unknown.

```bash
# List all session log files
ls -lht logs/execution/*.jsonl | head -20

# Search for sessions by time
find logs/execution -name "*.jsonl" -mtime -1  # Last 24h

# Search for sessions by symbol (content grep)
grep -l "BTC-USD" logs/execution/*.jsonl
```

**Next:** Use discovered session_id with other commands.

---

### 7. Timestamp Ordering Issues

**Use case:** Detect clock skew or out-of-order events.

```bash
# Export events and check timestamps
python scripts/view_execution_telemetry.py \
  --session SESSION_ID \
  --json | jq -r '.ts' | sort -c

# If sort complains, timestamps are not monotonic
```

**Red flags:**
- Non-monotonic timestamps → Clock skew / multi-threaded logging issue
- Large backward jumps (> 1 second) → Investigate source of events

**Mitigation:**
- Verify all servers use NTP / synchronized clocks
- Check if events from multiple sources are being mixed
- Review telemetry emitter concurrency guards

---

## 🎯 Dashboard Quick Access

### Live Execution Timeline

**URL:** `http://localhost:8000/live/execution/{session_id}`

**Features:**
- Visual timeline of all events
- Filter by event type (intent/order/fill/gate/error)
- Adjustable limit (last N events)
- Expandable JSON payloads

**Use case:** Real-time monitoring during live trading sessions.

---

### Telemetry API (JSON)

**URL:** `http://localhost:8000/api/telemetry?session_id={session_id}`

**Query params:**
- `session_id` (optional)
- `type` (intent|order|fill|gate|error)
- `symbol` (e.g., BTC-USD)
- `from` (ISO timestamp)
- `to` (ISO timestamp)
- `limit` (default: 2000)

**Use case:** Programmatic queries, dashboards, alerting.

**Example:**
```bash
curl "http://localhost:8000/api/telemetry?session_id=session_123&type=fill&limit=100" | jq .
```

---

## 🚨 When to Escalate

**Escalate immediately if:**

1. **Systematic missing fills:**
   - Orders placed but 0% fill rate across multiple sessions
   - Loss of execution capability

2. **Critical error rate:**
   - Error rate > 10% sustained for > 5 minutes
   - Possible disk failure or logger crash

3. **Extreme latency:**
   - p95 latency > 10 seconds for market orders
   - May indicate broker API outage

4. **Data corruption:**
   - Large portions of logs unreadable
   - Timestamps jumping backward by hours/days

5. **No events being logged:**
   - New sessions starting but no logs created
   - Telemetry emitter may be disabled/crashed

**How to escalate:**
- Create incident ticket with priority: P1 (critical) or P2 (high)
- Include: session_id, time range, commands run, output snippets
- Attach: relevant log files or export (`--json` output)

---

## 📊 What Info to Include in Incident Ticket

### Checklist

```markdown
## Incident: [Brief Description]

**Time Detected:** YYYY-MM-DD HH:MM:SS UTC

**Session ID(s):** session_123, session_456

**Symptom:**
- [ ] Missing fills
- [ ] High error rate
- [ ] Latency spikes
- [ ] No logs created
- [ ] Other: ___________

**Commands Run:**
```bash
# Paste commands here
python scripts/view_execution_telemetry.py --session session_123 --summary
```

**Output Snippet:**
```
# Paste relevant output (first 50 lines max)
```

**Impact:**
- [ ] Production trading affected
- [ ] Paper trading only
- [ ] Observability degraded

**Tried:**
- [ ] Checked session logs exist
- [ ] Verified correct session_id
- [ ] Checked dashboard
- [ ] Reviewed error rates
- [ ] Analyzed latency

**Next Steps / Questions:**
- [ ] Needs deeper investigation
- [ ] Requires code changes
- [ ] Configuration issue
```

---

## 🗄️ Retention & Rotation (Phase 16E)

**Purpose:** Manage telemetry log lifecycle (compression + deletion).

**Default Policy:**
```bash
# Recommended defaults (can override via CLI flags)
Max age: 30 days
Keep last N sessions: 200 (protected even if old)
Max total size: 2048 MB (2 GB)
Compress after: 7 days (gzip, ~80% size reduction)
```

### Dry-Run (Safe, Default)

**Check what would be deleted/compressed:**
```bash
python scripts/ops/telemetry_retention.py
```

**Output:**
- Summary stats (sessions, size before/after)
- Actions planned (compress/delete with reasons)
- No files modified (dry-run)

### Apply Retention

**Execute cleanup (requires --apply):**
```bash
python scripts/ops/telemetry_retention.py --apply
```

**Custom policy:**
```bash
# Keep only last 14 days, compress after 3 days
python scripts/ops/telemetry_retention.py --apply \
  --max-age-days 14 \
  --compress-after-days 3 \
  --keep-last-n 100
```

**Check results:**
```bash
# Before
du -sh logs/execution
# 850M logs/execution

# After (compression + deletion)
du -sh logs/execution
# 180M logs/execution
```

### Manual Cleanup Scenarios

**Scenario 1: Disk Almost Full (Aggressive)**
```bash
# Keep only last 7 days, no compression (delete immediately)
python scripts/ops/telemetry_retention.py --apply \
  --max-age-days 7 \
  --compress-after-days 0 \
  --keep-last-n 50
```

**Scenario 2: Archive Old Sessions (Compress Only)**
```bash
# Don't delete, just compress everything > 3 days
python scripts/ops/telemetry_retention.py --apply \
  --max-age-days 365 \
  --compress-after-days 3 \
  --max-total-mb 0  # Disable size limit
```

**Scenario 3: Size Limit Enforcement**
```bash
# Keep total size under 500 MB
python scripts/ops/telemetry_retention.py --apply \
  --max-total-mb 500 \
  --keep-last-n 100
```

### View Compressed Logs

**Compressed logs (.jsonl.gz) are still queryable:**
```bash
# Viewer auto-detects compressed files
python scripts/view_execution_telemetry.py \
  --path logs/execution \
  --summary

# Manual inspection
zcat logs/execution/session_123.jsonl.gz | head -20
```

### Safety Features

- ✅ **Dry-run default** (--apply required to modify)
- ✅ **Session-count protection** (keeps last N sessions even if old)
- ✅ **Root directory validation** (must contain "execution"/"telemetry"/"logs")
- ✅ **Deterministic sorting** (oldest deleted first)
- ✅ **Compression preserves mtime** (age calculation stays correct)

### Troubleshooting

**Problem:** "Unsafe or invalid telemetry root"
```bash
# Solution: Use correct path with "execution" or "telemetry" in name
python scripts/ops/telemetry_retention.py --root logs/execution
```

**Problem:** Not enough space freed
```bash
# Check actual file sizes
ls -lh logs/execution/*.jsonl

# More aggressive cleanup
python scripts/ops/telemetry_retention.py --apply \
  --max-age-days 3 \
  --keep-last-n 20
```

**Problem:** Need to restore compressed log
```bash
# Decompress manually
gunzip logs/execution/session_123.jsonl.gz
# Creates: logs/execution/session_123.jsonl
```

### Recommended Maintenance Schedule

| Frequency | Task | Command |
|-----------|------|---------|
| **Daily** | Dry-run check | `python scripts&#47;ops&#47;telemetry_retention.py` |
| **Weekly** | Apply retention | `python scripts&#47;ops&#47;telemetry_retention.py --apply` |
| **Monthly** | Verify size | `du -sh logs/execution` |

**Or:** Set up a cron job (optional)
```bash
# Example: Daily at 3 AM
0 3 * * * cd /path/to/Peak_Trade && python scripts/ops/telemetry_retention.py --apply
```

---

## 🔗 Related Documentation

- **Telemetry Viewer Guide:** `docs/execution/TELEMETRY_VIEWER.md`
- **Phase 16B Telemetry & Bridge:** `docs/execution/EXECUTION_TELEMETRY_LIVE_TRACK_V1.md`
- **Execution Pipeline V1:** `docs/execution/EXECUTION_SIMPLE_V1.md`
- **Merge Logs:** `docs/ops/PR_183_MERGE_LOG.md`

---

## 📝 Quick Tips

1. **Always use UTC timestamps** when filtering (`--from`, `--to`)
2. **Start with `--summary`** to get overview before drilling down
3. **Export to JSON** (`--json`) for external analysis (jq, pandas)
4. **Check dashboard first** for visual context
5. **Limit scope** with `--symbol` or `--session` to reduce noise

---

## 🧪 Testing This Runbook

To verify commands work in your environment:

```bash
# 1. Check CLI is available
python scripts/view_execution_telemetry.py --help

# 2. Test with golden fixtures (dev only)
python scripts/view_execution_telemetry.py \
  --path tests/fixtures/execution_telemetry \
  --summary

# 3. Verify dashboard is running
curl http://localhost:8000/api/telemetry?limit=1
```

---

**Last Updated:** 2025-12-20 (Phase 16D)  
**Maintainer:** Ops Team  
**Status:** Active
