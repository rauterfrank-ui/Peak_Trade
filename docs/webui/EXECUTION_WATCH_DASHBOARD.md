## Execution Watch Dashboard (v0) — Watch-only

### Scope / Governance
- **Read-only**: keine Actions, keine Order-Platzierung, keine Secrets.
- Datenquelle ist **append-only JSONL** (schema `execution_event_v0`).

### Endpoints (v0)

#### Health
- `GET /api/v0/execution/health`
- Query:
  - `root` (default: `logs&#47;execution`)
  - `filename` (default: `execution_pipeline_events_v0.jsonl`)
- Response (JSON):
  - `status`: "ok"
  - `watch_only`: true
  - `schema`: "execution_event_v0"
  - `exists`: bool

#### Runs (List)
- `GET /api/v0/execution/runs`
- Query:
  - `limit` (1..2000)
  - `root`, `filename` (wie oben)
- Response (JSON):
  - `count`: int
  - `runs`: Array
    - `run_id`
    - `correlation_id`
    - `started_at`
    - `last_event_at`
    - `status` ("success"|"failed"|"canceled"|"unknown")
    - `counts` (map event_type -> count)

#### Run Detail (Timeline)
- `GET /api/v0/execution/runs/{run_id}`
- Query:
  - `limit` (1..50000)
  - `root`, `filename` (wie oben)
- Response (JSON):
  - `run_id`
  - `correlation_id`
  - `summary` (started_at, last_event_at, status, counts)
  - `events`: Array (raw v0 events)

#### HTML Visual Surface
- `GET /watch/execution`
- Query:
  - `run_id` (optional)
  - `root`, `filename`
- Output:
  - Runs table (linkable run_id)
  - Timeline table (wenn run_id gesetzt)
  - **Cache-Control: no-store**

### Data Source Contract
- Die UI/API lesen aus:
  - `logs&#47;execution&#47;execution_pipeline_events_v0.jsonl`
- Jede Zeile ist ein JSON-Objekt mit:
  - `schema="execution_event_v0"`
  - `ts`, `run_id`, `correlation_id`, `event_type`, `payload`, optional `order_id`, `idempotency_key`
