# Execution Telemetry & Live-Track Bridge – Phase 16B

> **Observability für ExecutionPipeline: Events, Logging, Timeline-Integration**

---

## Überblick

Phase 16B erweitert die ExecutionPipeline um **strukturierte Telemetry** und eine **Live-Track Bridge** für Echtzeit-Observability.

**Features:**
- ✅ Structured Events (intent/order/fill/gate/error)
- ✅ JSONL-Logging (append-only, session-based)
- ✅ Live-Track Timeline Integration
- ✅ Dashboard Widget (FastAPI)
- ✅ Pluggable Emitter-System

---

## Architektur

### Event Flow

```text
┌─────────────────────────────────────────────────────────────┐
│                   EXECUTION PIPELINE                         │
└─────────────────────────────────────────────────────────────┘

Intent → Order → Fill
  │        │       │
  ├────────┼───────┼─────→ ExecutionEventEmitter
  │        │       │
  ▼        ▼       ▼
┌──────────────────────────────────────────────────────────┐
│              EVENT EMITTERS                               │
│  - JsonlExecutionLogger → logs/execution/<session>.jsonl │
│  - CompositeEmitter → Multiple Backends                  │
│  - NullEmitter → Disabled                                │
└──────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│              LIVE-TRACK BRIDGE                            │
│  - Read JSONL logs                                       │
│  - Map to Timeline Rows                                  │
│  - Aggregate Statistics                                  │
└──────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│              DASHBOARD (FastAPI)                          │
│  - GET /api/live/execution/{session_id}                  │
│  - GET /live/execution/{session_id} (HTML)               │
└──────────────────────────────────────────────────────────┘
```

---

## Event Schema

### ExecutionEvent

```python
from src.execution.events import ExecutionEvent

event = ExecutionEvent(
    ts=datetime.now(),
    session_id="session_123",
    symbol="BTC-USD",
    mode="paper",  # backtest/paper/live
    kind="intent",  # intent/order/fill/gate/error
    payload={
        "side": "buy",
        "quantity": 1.0,
        "current_price": 100000.0,
    },
)
```

### Event Kinds

| Kind | Emitted When | Payload Keys |
|------|--------------|--------------|
| `intent` | OrderIntent created | side, quantity, current_price, strategy_key |
| `order` | Validated Order created | client_id, side, quantity, order_type |
| `fill` | Fill returned (simulated/real) | client_id, filled_quantity, fill_price, fill_notional, fill_fee |
| `gate` | Gate decision made | gate_name, passed, reason |
| `error` | Error occurred | error, stacktrace |

---

## Usage

### 1. Enable Telemetry in Pipeline

```python
from src.execution import ExecutionPipeline
from src.execution.telemetry import JsonlExecutionLogger

# Create emitter
emitter = JsonlExecutionLogger("logs/execution")

# Create pipeline with emitter
pipeline = ExecutionPipeline(
    executor=executor,
    emitter=emitter,  # ← Enable telemetry
)

# Events are now automatically emitted
result = pipeline.submit_order(intent)
```

### 2. Read Timeline

```python
from src.live.execution_bridge import get_execution_timeline

# Load last 200 events
timeline = get_execution_timeline("session_123", limit=200)

for row in timeline:
    print(f"{row.ts} [{row.kind}] {row.description}")
```

**Output:**
```
2025-01-01 12:00:02 [fill] Fill: 1.000000 @ $100,020.00 (fee: $10.0000)
2025-01-01 12:00:01 [order] Order: BUY 1.000000 (market)
2025-01-01 12:00:00 [intent] Intent: BUY 1.000000 @ $100,000.00
```

### 3. Get Summary

```python
from src.live.execution_bridge import get_execution_summary

summary = get_execution_summary("session_123")

print(f"Total Events: {summary['event_count']}")
print(f"Intents: {summary['kind_counts']['intent']}")
print(f"Fills: {summary['kind_counts']['fill']}")
print(f"Symbols: {summary['symbols']}")
```

---

## JSONL Log Format

**Location:** `logs/execution/<session_id>.jsonl`

**Format:** One JSON object per line (newline-separated)

**Example:**
```jsonl
{"ts": "2025-01-01T12:00:00", "session_id": "session_123", "symbol": "BTC-USD", "mode": "paper", "kind": "intent", "payload": {"side": "buy", "quantity": 1.0, "current_price": 100000.0}}
{"ts": "2025-01-01T12:00:01", "session_id": "session_123", "symbol": "BTC-USD", "mode": "paper", "kind": "order", "payload": {"client_id": "ord_001", "side": "buy", "quantity": 1.0, "order_type": "market"}}
{"ts": "2025-01-01T12:00:02", "session_id": "session_123", "symbol": "BTC-USD", "mode": "paper", "kind": "fill", "payload": {"client_id": "ord_001", "filled_quantity": 1.0, "fill_price": 100020.0, "fill_notional": 100020.0, "fill_fee": 10.0}}
```

### Tail Logs

```bash
# View last 20 events
tail -n 20 logs/execution/<session_id>.jsonl

# Stream live events
tail -f logs/execution/<session_id>.jsonl | jq .

# Filter by kind
grep '"kind": "fill"' logs/execution/<session_id>.jsonl | jq .
```

---

## Dashboard Integration

### API Endpoints

**1. Timeline API**

```bash
GET /api/live/execution/{session_id}?limit=200&kind=fill
```

**Response:**
```json
{
  "session_id": "session_123",
  "timeline": [
    {
      "ts": "2025-01-01T12:00:02",
      "kind": "fill",
      "symbol": "BTC-USD",
      "description": "Fill: 1.000000 @ $100,020.00 (fee: $10.0000)",
      "details": {
        "filled_quantity": 1.0,
        "fill_price": 100020.0,
        "fill_fee": 10.0
      }
    }
  ],
  "summary": {
    "event_count": 150,
    "kind_counts": {
      "intent": 50,
      "order": 50,
      "fill": 50
    },
    "symbols": ["BTC-USD"]
  },
  "count": 1
}
```

**2. HTML View**

```bash
# Open in browser
open http://localhost:8000/live/execution/session_123

# With filters
open http://localhost:8000/live/execution/session_123?kind=fill&limit=100
```

**Features:**
- ✅ Summary Stats (Total Events, by Kind)
- ✅ Filterable Table (by Kind)
- ✅ Event Details (expandable)
- ✅ Newest First ordering

---

## Emitter Backends

### JsonlExecutionLogger

```python
from src.execution.telemetry import JsonlExecutionLogger

# Default path: logs/execution
logger = JsonlExecutionLogger()

# Custom path
logger = JsonlExecutionLogger("custom/path/logs")
```

**Features:**
- Append-only (safe for concurrent writes)
- Creates directories automatically
- Session-based files: `<session_id>.jsonl`
- JSON Lines format (one event per line)

### NullEmitter (Disabled)

```python
from src.execution.telemetry import NullEmitter

# Disable telemetry
emitter = NullEmitter()

pipeline = ExecutionPipeline(executor=executor, emitter=emitter)
```

### CompositeEmitter (Multiple Backends)

```python
from src.execution.telemetry import CompositeEmitter, JsonlExecutionLogger

# Emit to multiple backends
emitter = CompositeEmitter([
    JsonlExecutionLogger("logs/execution"),
    JsonlExecutionLogger("backups/execution"),
    # Add custom emitters...
])

pipeline = ExecutionPipeline(executor=executor, emitter=emitter)
```

---

## Custom Emitters

### Create Custom Emitter

```python
from src.execution.telemetry import ExecutionEventEmitter
from src.execution.events import ExecutionEvent

class PrometheusEmitter(ExecutionEventEmitter):
    """Emit events to Prometheus."""

    def emit(self, event: ExecutionEvent) -> None:
        # Emit to Prometheus
        counter = prometheus_client.Counter(
            f"execution_{event.kind}_total",
            f"Total {event.kind} events",
        )
        counter.inc()
```

### Register Custom Emitter

```python
emitter = CompositeEmitter([
    JsonlExecutionLogger(),
    PrometheusEmitter(),
])

pipeline = ExecutionPipeline(executor=executor, emitter=emitter)
```

---

## Performance

### JSONL Logger Performance

- **Append-only:** Safe for concurrent writes
- **Buffered I/O:** Uses Python's buffered file I/O
- **No locks:** Each session has separate file
- **Typical overhead:** ~0.5-1ms per event (local SSD)

### Event Volume Estimates

| Scenario | Events/Second | Daily Events |
|----------|---------------|--------------|
| Low Frequency (1 signal/min) | 3 | ~250K |
| Medium (1 signal/5s) | 12 | ~1M |
| High Frequency (1 signal/s) | 60 | ~5M |

**Storage:** ~500 bytes/event → 5M events = ~2.5GB/day

**Recommendation:**
- Rotate logs daily: `logs/execution/YYYY-MM-DD/<session_id>.jsonl`
- Archive old logs (compress with gzip: ~90% reduction)
- Keep last 30 days online

---

## Troubleshooting

### "No execution log found"

**Ursache:** Session hat noch keine Events emitted oder Log wurde gelöscht.

**Lösung:**
- Prüfe ob Emitter konfiguriert: `pipeline._emitter is not None`
- Prüfe Logs: `ls -la logs/execution/`
- Tail live: `tail -f logs/execution/<session_id>.jsonl`

### "Events missing in timeline"

**Ursache:** JSONL parse error oder ungültige Events.

**Lösung:**
```bash
# Check for invalid JSON lines
jq . logs/execution/<session_id>.jsonl > /dev/null

# Check logs
grep ERROR logs/app.log | grep execution_bridge
```

### "Timeline too slow"

**Ursache:** Zu viele Events (>1M), keine Pagination.

**Lösung:**
- Reduziere `limit`: `?limit=100`
- Filter by `kind`: `?kind=fill`
- Rotate logs (keep last N days only)

---

## Testing

### Unit Tests

```bash
# Telemetry Tests
pytest tests/execution/test_execution_telemetry.py -v

# Bridge Tests
pytest tests/live/test_execution_bridge.py -v

# All
pytest tests/execution/test_execution_telemetry.py tests/live/test_execution_bridge.py -v
```

**Coverage:**
- ✅ Event serialization (to_dict)
- ✅ JSONL logging (write, read, parse)
- ✅ Timeline mapping (intent/order/fill/gate)
- ✅ Summary aggregation
- ✅ Emitter composition

### Integration Test

```python
from src.execution import ExecutionPipeline
from src.execution.telemetry import JsonlExecutionLogger
from src.live.execution_bridge import get_execution_timeline

# 1. Setup
emitter = JsonlExecutionLogger("test_logs")
pipeline = ExecutionPipeline(executor=executor, emitter=emitter)

# 2. Execute
intent = OrderIntent(...)
result = pipeline.submit_order(intent)

# 3. Verify
timeline = get_execution_timeline(intent.session_id, base_path="test_logs")
assert len(timeline) >= 3  # intent + order + fill
assert timeline[0].kind == "fill"  # newest first
```

---

## Next Steps (Phase 16C)

1. **Real-time Streaming**
   - WebSocket endpoint for live event stream
   - Server-Sent Events (SSE) for timeline updates
   - Auto-refresh in dashboard

2. **Advanced Analytics**
   - Execution latency metrics (intent → fill time)
   - Fill price vs intent price analysis
   - Gate rejection rate by type

3. **Alerting**
   - Alert on high gate rejection rate
   - Alert on execution errors
   - Slack/Email notifications

4. **Export & Replay**
   - Export timeline as CSV/Excel
   - Replay events for debugging
   - Import events from other systems

---

## API Reference

### Events Module

```python
# src/execution/events.py
from src.execution.events import ExecutionEvent, event_to_dict

event = ExecutionEvent(...)
d = event.to_dict()  # For JSON serialization
```

### Telemetry Module

```python
# src/execution/telemetry.py
from src.execution.telemetry import (
    ExecutionEventEmitter,      # Base interface
    JsonlExecutionLogger,        # JSONL backend
    NullEmitter,                 # Disabled
    CompositeEmitter,            # Multiple backends
)
```

### Bridge Module

```python
# src/live/execution_bridge.py
from src.live.execution_bridge import (
    get_execution_timeline,      # Load timeline
    get_execution_summary,       # Get summary stats
    ExecutionTimelineRow,        # Timeline row type
)
```

---

## Config Example

```toml
# config/execution.toml

[execution]
# ... existing config ...

[execution.telemetry]
enabled = true
backend = "jsonl"
base_path = "logs/execution"
rotation = "daily"  # Future feature
compression = true  # Future feature
retention_days = 30  # Future feature

[execution.telemetry.filters]
# Filter events to reduce volume (future)
include_kinds = ["intent", "fill", "error"]  # Skip orders
min_severity = "info"  # Skip debug events
```

---

## Weiterführende Dokumentation

- ExecutionPipeline Overview (archived) – Production Pipeline
- [PEAK_TRADE_OVERVIEW.md](../PEAK_TRADE_OVERVIEW.md) – Gesamtarchitektur
- Live-Track Integration (archived) – Session Timeline

---

**Status:** ✅ Phase 16B Complete  
**Tests:** 17/17 passed  
**Next Phase:** 16C – Real-time Streaming & Advanced Analytics
