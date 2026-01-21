## ExecutionPipeline Contract (Beta) — RUNBOOK B / Slice 1

### Objects (Contract Fields)

- **OrderIntent**
  - `run_id: str`
  - `session_id: str`
  - `intent_id: str`
  - `symbol: str`
  - `side: "BUY" | "SELL"`
  - `quantity: Decimal`
  - `order_type: "MARKET" | "LIMIT"`
  - `limit_price: Decimal | None`

- **ExecutionEvent (JSONL line)**
  - `schema_version: "BETA_EXEC_V1"`
  - `event_id: str`
  - `run_id: str`
  - `session_id: str`
  - `intent_id: str`
  - `symbol: str`
  - `event_type: "INTENT" | "VALIDATION_REJECT" | "RISK_REJECT" | "SUBMIT" | "ACK" | "REJECT" | "FILL" | "ERROR"`
  - `ts_sim: int` (monotonisch; Start 0; +1 pro Event)
  - `ts_utc: str` (ISO8601; nicht Teil der Determinism-Assertions)
  - Optional: `request_id`, `client_order_id`, `reason_code`, `reason_detail`, `payload`

### Determinism Contract

- **seed_u64**: `int.from_bytes(sha256(f"{run_id}|{symbol}|{intent_id}")[:8], "big")`
- **ts_sim**: monotonic counter pro `(run_id, session_id)`, Start `0`, `+1` pro emittiertem Event.
- **Event Ordering Keys**: `(run_id, session_id, ts_sim, event_type, event_id)`
- **event_id (stable_id)**: `sha256(canonical_json({ "kind": "execution_event", **canonical_fields }))`
  - canonical_fields (Slice 1): `run_id, session_id, intent_id, symbol, event_type, ts_sim, request_id, client_order_id, reason_code, payload`

### JSONL Log Contract

- **Pfad**: `logs&#47;execution&#47;execution_events.jsonl`
- **Format**: 1 JSON object pro Zeile, **append-only** (kein Rewrite/Sort).

### Reject Codes (MVP)

- `VALIDATION_REJECT_BAD_QTY`
- `RISK_REJECT_KILL_SWITCH`
- `RISK_REJECT_MAX_POSITION`

### Minimal How-To (NO-LIVE)

```python
from decimal import Decimal
from src.execution.orchestrator import ExecutionOrchestrator, ExecutionMode, OrderIntent
from src.execution.contracts import OrderSide
from src.execution.venue_adapters.simulated import SimulatedVenueAdapter

orch = ExecutionOrchestrator(
    adapter=SimulatedVenueAdapter(),
    execution_mode=ExecutionMode.PAPER,
)

intent = OrderIntent(
    run_id="run_001",
    session_id="sess_001",
    intent_id="intent_001",
    symbol="BTC/EUR",
    side=OrderSide.BUY,
    quantity=Decimal("0.01"),
)

result = orch.submit_intent(intent)
print(result.success, result.order)
```
