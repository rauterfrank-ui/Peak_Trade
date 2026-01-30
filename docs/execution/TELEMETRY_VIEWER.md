# Telemetry Viewer - Execution Event Logs (Phase 16C)

**Status:** ✅ Implemented  
**Module:** `src/execution/telemetry_viewer.py`  
**CLI:** `scripts/view_execution_telemetry.py`  
**API:** `/api/telemetry`

---

## Overview

Der **Telemetry Viewer** ist ein read-only Tool zum Abfragen, Filtern und Analysieren von Execution Telemetry Logs (JSONL format).

**Key Features:**
- ✅ Read-only (keine Änderungen an Logs)
- ✅ Flexibles Filtern (session, type, symbol, timestamp)
- ✅ Robustes Parsing (überspringt invalide Zeilen)
- ✅ Latency-Analyse (intent→order timing)
- ✅ CLI + API Interface
- ✅ Keine externe Dependencies

---

## Log Location

**Default Path:**
```
logs/execution/<session_id>.jsonl
```

**Format:** JSONL (one JSON object per line)

**Example Event:**
```json
{
  "ts": "2025-12-20T09:30:45.123456+00:00",
  "session_id": "session_123",
  "symbol": "BTC-USD",
  "mode": "paper",
  "kind": "fill",
  "payload": {
    "filled_quantity": 1.0,
    "fill_price": 100020.0,
    "fill_fee": 10.0
  }
}
```

---

## CLI Usage

### Basic Commands

**1. View all events from a session:**
```bash
python3 scripts/view_execution_telemetry.py --session session_123
```

**2. Filter by event type:**
```bash
python3 scripts/view_execution_telemetry.py --type fill --limit 50
```

**3. Filter by symbol:**
```bash
python3 scripts/view_execution_telemetry.py --symbol BTC-USD --limit 100
```

**4. Time range filter:**
```bash
python3 scripts/view_execution_telemetry.py \
  --session session_123 \
  --from 2025-01-01T12:00:00 \
  --to 2025-01-01T13:00:00
```

**5. Export as JSON:**
```bash
python3 scripts/view_execution_telemetry.py --session session_123 --json > events.json
```

**6. Summary only (no timeline):**
```bash
python3 scripts/view_execution_telemetry.py --session session_123 --timeline 0
```

### Command Line Options

```
--path PATH           Base path for telemetry logs (default: logs/execution)
--session SESSION_ID  Filter by session ID
--type TYPE           Filter by event type (intent|order|fill|gate|error)
--symbol SYMBOL       Filter by trading symbol
--from ISO_TIMESTAMP  Filter events after this timestamp
--to ISO_TIMESTAMP    Filter events before this timestamp
--limit N             Maximum events to load (default: 2000)
--json                Output raw events as JSON lines
--summary             Show summary statistics (default: true)
--no-summary          Skip summary
--timeline N          Show last N events as timeline (default: 20, 0 to skip)
```

### Exit Codes

- `0` - Success
- `2` - No logs found
- `3` - Parse errors > 5%

---

## Dashboard Usage

### API Endpoint

**GET `/api/telemetry`**

**Query Parameters:**
- `session_id` (optional) - Filter by session
- `type` (optional) - Filter by event type
- `symbol` (optional) - Filter by symbol
- `from` (optional) - ISO timestamp (events after)
- `to` (optional) - ISO timestamp (events before)
- `limit` (optional, default: 200, max: 2000) - Max events

**Response:**
```json
{
  "summary": {
    "total_events": 150,
    "counts_by_type": {
      "intent": 50,
      "order": 50,
      "fill": 50
    },
    "unique_symbols": ["BTC-USD", "ETH-USD"],
    "unique_sessions": ["session_123"],
    "first_ts": "2025-01-01T12:00:00+00:00",
    "last_ts": "2025-01-01T12:30:00+00:00",
    "latency_ms": {
      "min": 0.5,
      "median": 2.1,
      "max": 15.3,
      "p95": 10.2
    }
  },
  "timeline": [
    {
      "ts": "2025-01-01T12:00:00+00:00",
      "type": "fill",
      "symbol": "BTC-USD",
      "session_id": "session_123",
      "filled_quantity": 1.0,
      "fill_price": 100000.0,
      "fill_fee": 10.0
    }
  ],
  "query": {
    "session_id": "session_123",
    "type": "fill",
    "symbol": null,
    "from": null,
    "to": null,
    "limit": 200
  },
  "stats": {
    "total_lines": 150,
    "valid_events": 150,
    "invalid_lines": 0,
    "error_rate": 0.0
  }
}
```

### Examples

**1. Query via curl:**
```bash
curl "http://localhost:8000/api/telemetry?session_id=session_123&limit=50"
```

**2. Filter by type:**
```bash
curl "http://localhost:8000/api/telemetry?type=fill&limit=100"
```

**3. Time range:**
```bash
curl "http://localhost:8000/api/telemetry?from=2025-01-01T12:00:00&to=2025-01-01T13:00:00"
```

---

## Python API

### Basic Usage

```python
from pathlib import Path
from src.execution.telemetry_viewer import (
    TelemetryQuery,
    iter_events,
    summarize_events,
    build_timeline,
    find_session_logs,
)

# Find all session logs
logs = find_session_logs(Path("logs/execution"))
print(f"Found {len(logs)} session logs")

# Query events
query = TelemetryQuery(
    session_id="session_123",
    event_type="fill",
    limit=100,
)
events, stats = iter_events(logs, query)

# Summarize
events_list = list(events)
summary = summarize_events(events_list)
print(f"Total events: {summary['total_events']}")
print(f"By type: {summary['counts_by_type']}")

# Build timeline
timeline = build_timeline(events_list, max_items=20)
for entry in timeline:
    print(f"{entry['ts']} | {entry['type']} | {entry['symbol']}")
```

### Advanced Filtering

```python
from datetime import datetime, timezone

# Time range filter
query = TelemetryQuery(
    symbol="BTC-USD",
    ts_from="2025-01-01T12:00:00+00:00",
    ts_to="2025-01-01T13:00:00+00:00",
    limit=1000,
)

# Multiple sessions
logs = [
    Path("logs/execution/session_1.jsonl"),
    Path("logs/execution/session_2.jsonl"),
]
events, stats = iter_events(logs, query)

# Check parse errors
if stats.error_rate > 0.05:
    print(f"⚠️  High error rate: {stats.error_rate:.1%}")
    print(f"   Invalid lines: {stats.invalid_lines}/{stats.total_lines}")
```

---

## Troubleshooting

### Invalid Lines

**Symptom:** High error rate (>5%)

**Causes:**
- Corrupted JSONL files
- Incomplete writes (process killed mid-write)
- Mixed formats (old schema)

**Fix:**
```bash
# Check for invalid lines
python3 scripts/view_execution_telemetry.py --session session_123 --summary

# Parse Stats:
#   Total Lines: 1000
#   Valid Events: 950
#   Invalid Lines: 50
#   Error Rate: 5.0%

# View problematic file
tail -n 100 logs/execution/session_123.jsonl | jq . || echo "Invalid JSON detected"
```

### Missing Fields

**Symptom:** Timeline shows "(unknown event type)" or empty values

**Cause:** Event schema mismatch (old events, incomplete payload)

**Fix:**
- Viewer is tolerant: uses `.get()` with defaults
- Missing fields → empty string or 0
- No action needed (viewer handles gracefully)

### No Logs Found

**Symptom:** `❌ Error: No telemetry logs found`

**Causes:**
- Wrong path (default: `logs/execution`)
- Telemetry not enabled (emitter=None)
- No sessions run yet

**Fix:**
```bash
# Check path
ls -la logs/execution/

# Enable telemetry (if not already)
# See: docs/execution/EXECUTION_TELEMETRY_LIVE_TRACK_V1.md

# Run a session with telemetry
python3 scripts/run_execution_session.py --mode paper --session test_demo
```

### Schema Version Mismatch

**Symptom:** `schema_version="unknown"` in warnings

**Cause:** Events don't have `schema_version` field (Phase 16B events)

**Fix:**
- Not an error (Phase 16B events don't have version field)
- Viewer assumes current schema
- No action needed

---

## Performance

### Benchmarks (typical)

| Operation | Events | Time | Notes |
|-----------|--------|------|-------|
| Parse JSONL | 10,000 | ~50ms | Single session file |
| Filter by type | 10,000 → 3,000 | ~60ms | No re-parse |
| Summarize | 10,000 | ~20ms | In-memory |
| Build timeline | 10,000 → 200 | ~10ms | Truncates to limit |

### Large Files

**Recommendation:** Use filters to reduce load

```bash
# Instead of loading all 100k events:
python3 scripts/view_execution_telemetry.py --session huge_session --limit 10000

# Better: Filter by type or time range
python3 scripts/view_execution_telemetry.py \
  --session huge_session \
  --type fill \
  --from 2025-01-01T12:00:00 \
  --limit 1000
```

### Memory Usage

- ~500 bytes/event in memory
- 10,000 events ≈ 5MB RAM
- 100,000 events ≈ 50MB RAM
- Limit param prevents OOM

---

## Integration Examples

### 1. Daily Ops Check

```bash
#!/bin/bash
# Daily telemetry check for all sessions

for session in $(ls logs/execution/*.jsonl | xargs -n1 basename | sed 's/.jsonl//'); do
  echo "=== $session ==="
  python3 scripts/view_execution_telemetry.py \
    --session $session \
    --summary \
    --timeline 5
done
```

### 2. Error Alert

```bash
#!/bin/bash
# Alert on high error rate

output=$(python3 scripts/view_execution_telemetry.py --session $SESSION_ID --summary 2>&1)
error_rate=$(echo "$output" | grep "Error Rate" | awk '{print $3}' | tr -d '%')

if (( $(echo "$error_rate > 5.0" | bc -l) )); then
  echo "⚠️  Alert: High telemetry error rate: ${error_rate}%"
  # Send alert...
fi
```

### 3. Latency Monitoring

```python
from src.execution.telemetry_viewer import iter_events, summarize_events, TelemetryQuery
from pathlib import Path

# Daily latency check
logs = find_session_logs(Path("logs/execution"))
query = TelemetryQuery(limit=10000)
events, stats = iter_events(logs, query)

summary = summarize_events(list(events))
if "latency_ms" in summary:
    p95 = summary["latency_ms"]["p95"]
    if p95 and p95 > 100.0:  # >100ms
        print(f"⚠️  Alert: High P95 latency: {p95:.1f}ms")
```

---

## Configuration (Optional)

### Retention Policy

**Manual Cleanup (Recommended for v1):**
```bash
# Remove logs older than 14 days
find logs/execution -name "*.jsonl" -mtime +14 -delete
```

**Cron Job:**
```cron
# Daily cleanup at 3am
0 3 * * * find /path/to/Peak_Trade/logs/execution -name "*.jsonl" -mtime +14 -delete
```

### Rotation (Future)

**Not implemented in Phase 16C** (add-on feature for Phase 16D)

**Workaround:** Use date-based session IDs
```python
from datetime import datetime
session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
```

---

## Related Documentation

- [EXECUTION_TELEMETRY_LIVE_TRACK_V1.md](EXECUTION_TELEMETRY_LIVE_TRACK_V1.md) - Telemetry basics (Phase 16B)
- [EXECUTION_SIMPLE_V1.md](EXECUTION_SIMPLE_V1.md) - Simplified pipeline (Phase 16A)
- [PR_183_MERGE_LOG.md](../ops/PR_183_MERGE_LOG.md) - Phase 16A+B merge log

---

## FAQ

**Q: Can I modify logs?**  
A: No. Viewer is read-only. Modifying JSONL logs can break parsing.

**Q: What if I delete a log file?**  
A: Safe. Viewer skips missing files with warning. No side effects.

**Q: How do I enable telemetry?**  
A: See [EXECUTION_TELEMETRY_LIVE_TRACK_V1.md](EXECUTION_TELEMETRY_LIVE_TRACK_V1.md) - opt-in via `emitter=JsonlExecutionLogger()`.

**Q: Can I query multiple sessions at once?**  
A: Yes. Omit `--session` param in CLI, or pass multiple paths to `iter_events()` in Python.

**Q: What's the difference between CLI and API?**  
A: CLI is for ops/debugging (shell), API is for programmatic access (dashboard, scripts).

**Q: Is UTC timezone enforced?**  
A: Yes (since PR #183). All timestamps are UTC with `+00:00` suffix.

---

**Phase 16C Status:** ✅ **COMPLETE**  
**Production Ready:** ✅ **YES**  
**Breaking Changes:** ❌ **NONE** (read-only add-on)
