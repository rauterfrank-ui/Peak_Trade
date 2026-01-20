## Phase 16A — ExecutionPipeline MVP (Package & Contracts)

### Ziel
- **ExecutionPipeline v0** als eigenstaendiges Paket `src&#47;execution_pipeline&#47;` (keine Breaking Changes an `src&#47;execution&#47;*`).
- **Deterministisch + CI-friendly**: injected clock, keine Sleeps, keine externen Calls.
- **Governance-safe / NO-LIVE**: Adapter sind explizit NO-LIVE; Watch/UI ist read-only.

### Package Tree (v0)
- `src&#47;execution_pipeline&#47;__init__.py`
- `src&#47;execution_pipeline&#47;contracts.py` (ExecutionContext/Plan/Result + ExecutionError)
- `src&#47;execution_pipeline&#47;events_v0.py` (ExecutionEventV0 + EventType)
- `src&#47;execution_pipeline&#47;policies.py` (RetryPolicy, TimeoutPolicy, IdempotencyKey)
- `src&#47;execution_pipeline&#47;adapter.py` (ExecutionAdapter + Null/InMemory)
- `src&#47;execution_pipeline&#47;telemetry.py` (TelemetryEmitter + JSONL)
- `src&#47;execution_pipeline&#47;store.py` (read-only JSONL store fuer Watch-API)
- `src&#47;execution_pipeline&#47;pipeline.py` (ExecutionPipeline MVP)

### Core Contracts (v0)
- **ExecutionContext**
  - `run_id`: str
  - `correlation_id`: str (stabil ueber alle Events)
  - `idempotency_key`: IdempotencyKey (run-level; order-level derived)
  - `created_at`: datetime (aus injected clock)
- **ExecutionPlan**
  - `orders`: List[OrderPlan]
  - `retry`: RetryPolicy (default max_attempts=1)
  - `timeout`: TimeoutPolicy (deadline_seconds)
- **ExecutionResult**
  - `status`: "success" | "failed" | "canceled"
  - `orders`: List[Dict] (per-order result)
  - `error`: ExecutionError|None

### Adapter Contract (v0)
- **ExecutionAdapter** (Interface)
  - `submit(req: SubmitRequest) -> SubmitAck`
  - `cancel(run_id, correlation_id, order_id) -> None`
  - `status(run_id, correlation_id, order_id) -> OrderStatus`
- **NO-LIVE**: `NullExecutionAdapter` + `InMemoryExecutionAdapter` sind deterministic und side-effect-free.

### Event Schema (stable, versioned v0)
- **Schema name**: `execution_event_v0`
- **Required fields**:
  - `schema`: "execution_event_v0"
  - `ts`: ISO-8601 string
  - `run_id`: str
  - `correlation_id`: str
  - `event_type`: one of `created|validated|submitted|acked|filled|canceled|failed`
  - `payload`: object
- **Optional fields**:
  - `order_id`: str|null
  - `idempotency_key`: str|null

### Errors (typed + stable codes)
- Pipeline errors werden als `ExecutionError(error_code, message, details)` modelliert.
- Failures muessen ein **finales** `failed` Event emitten (`payload.final=true`).

### Idempotency / Retries / Timeout
- **Idempotency**: order-level idempotency wird deterministisch aus `ctx.idempotency_key + order_id` abgeleitet.
- **Retries**: keine Sleeps; jeder Versuch emit `submitted` und bei Reject/Failure ein `failed` mit `payload.final=false` (bis final).
- **Timeout**: run-level deadline via injected clock; bei Ueberschreitung: `ExecutionError(error_code="timeout")` + final `failed`.

### Telemetry Output (JSONL)
- Default: `logs&#47;execution&#47;execution_pipeline_events_v0.jsonl` (append-only).
- Ziel ist Watch-only Observability via `src&#47;webui&#47;execution_watch_api_v0.py`.
