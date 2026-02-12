# RUNBOOK — Execution Watch Dashboard v0.5 (Watch-Only)

**Owner:** ops  
**Purpose:** Start and verify the Execution Watch Dashboard v0.5 (read-only) for recent execution pipeline events and live-session registry state.  
**Policy:** NO-LIVE (read-only). No broker connectivity. No trading actions.

---

## Purpose

This runbook helps you:
- Start the dashboard locally (dev-only, watch-only)
- Verify API responses and UI rendering deterministically
- Capture evidence for a PASS result

---

## Preconditions

- Repo checkout is clean and on the expected branch (usually `main`)
- Python environment is set up (uv/venv per your local standard)
- You have **no need** to connect to broker/exchange (this dashboard is read-only)

Optional data sources:
- Execution pipeline JSONL exists (default location shown below)
- Live session registry files exist (default location shown below)

---

## Start

Start the WebUI server:

```bash
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

If `uvicorn` is not on your PATH, start via `uv` (same stack, no new services):
```bash
python3 -m uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

Open the dashboard page in your browser:

```text
/execution_watch
```

---

## Verify

### Verify APIs (read-only, v0.5 semantics)

Run these requests (examples shown as paths only; use your preferred client):

```text
/api/healthz
/api/execution/health
/api/execution/runs
/api/execution/runs/<run_id>
/api/execution/runs/<run_id>/events?limit=200
/api/execution/runs/<run_id>/events?limit=200&since_cursor=<cursor>
/api/live/sessions
```

Expected:
- HTTP 200 for existing data
- Deterministic ordering (newest runs first, stable pagination cursor)
- Backward compatible: top-level `api_version` remains `v0.2`, v0.5 semantics are indicated via `meta.api_version`
- `generated_at_utc` present in responses
- `meta` present (backward-compatible):
  - `meta.api_version` = `v0.5`
  - `meta.generated_at_utc` mirrors top-level `generated_at_utc`
  - `meta.has_more`, `meta.next_cursor` (paging/tail)
  - `meta.read_errors` (count of malformed JSONL lines skipped)
  - `meta.source` = `fixture|local`
  - `meta.last_event_utc` (falls bestimmbar, sonst null)
  - `meta.dataset_stats` (runs/events/sessions counts; sessions_count kann null sein)
- Events pagination returns `next_cursor` + `has_more` consistently
- Tail semantics:
  - `since_cursor` returns events strictly **after** the provided cursor
  - `next_cursor` is a watermark cursor you can feed back into `since_cursor`
 - Health endpoint:
   - `/api/execution/health` liefert Meta-Summary + deterministische Invariants

v0.5 notes:
- `meta.last_event_utc` is derived via strict timestamp precedence when possible and normalized to UTC (Z suffix).
- `invariants` includes a richer deterministic set (plus explanatory notes):
  - `cursor_monotonicity_ok`
  - `dataset_nonempty_ok` + `dataset_nonempty_note`
  - `events_sorted_by_time_ok` + `events_sorted_by_time_note`
  - `runs_sessions_consistency_ok` + `runs_sessions_consistency_note`
- Runtime metrics are still opt-in and non-deterministic; default health is deterministic.

Expected negative/edge behavior:
- Unknown `run_id` → HTTP 404 with `{"detail":"run_not_found"}`
- Empty dataset:
  - `/api/execution/runs` → `runs=[]`
  - `/api/live/sessions` → `sessions=[]`
  - `has_more=false`, `next_cursor=null`, `read_errors=0`
- Malformed JSONL line:
  - Line is skipped deterministically
  - `meta.read_errors` increments accordingly

### Verify UI

On the Execution Watch page:
- Runs list renders (newest first)
- Selecting a run updates Run Detail
- Events table paginates deterministically (“Load more”)
- Sessions table renders from the live-session registry (if present)
- Polling toggle defaults to **off**
- Tail mode (optional):
  - Enable “Tail mode” to follow new events (append-only, no full refresh)
  - Polling interval selector (2s/5s/10s) controls refresh cadence
  - “Clear” resets the tail cursor watermark
- Health panel (v0.5):
  - Zeigt `meta.api_version`, `meta.source`, `meta.read_errors`, `meta.dataset_stats`, `meta.last_event_utc`
  - Zeigt Invariants Summary + Details (expand/collapse) inkl. Notes
  - “Ping Health” ruft `/api/execution/health` ab und zeigt den Snapshot (kein Auto-Polling)

---

## Stop

Stop the server with:

```bash
Ctrl-C
```

---

## Troubleshooting

### No runs / empty events

- Check whether the JSONL file exists:

```bash
ls -la logs/execution
```

- If no JSONL exists, the dashboard will show empty state. This is expected in a clean environment.

### read_errors > 0 (malformed JSONL)

- The API skips malformed JSONL lines deterministically and exposes a counter:

```text
meta.read_errors
```

- If `read_errors` increases unexpectedly:
  - Inspect the JSONL generator / upstream pipeline for partial writes
  - Confirm the file is not being edited concurrently during inspection

### Optional metrics hook (v0.5)

- Execution Watch kann optional Requests/Latency/Read-Errors mitzählen (best-effort).
- Aktivierung:
  - Prometheus (wenn verfügbar) folgt dem Flag `PEAK_TRADE_PROMETHEUS_ENABLED=1`
  - In-memory Runtime-Metriken sind opt-in via `PEAK_TRADE_EXECUTION_WATCH_METRICS_ENABLED=1`
- Hinweis: Runtime-Metriken sind **nicht deterministisch**. Der Health-Endpoint ist deterministisch **ohne** Runtime-Metriken; Runtime-Metriken nur via explizitem Opt-in:

```text
/api/execution/health?include_runtime_metrics=true
```

### No sessions

- Check whether registry files exist:

```bash
ls -la reports/experiments/live_sessions
```

### 404 for a run_id

- The run id might not exist in the current JSONL file; refresh runs list and select a valid run.

---

## CI semantics note (snapshot-only)

- In GitHub UI, `mergeStateStatus` / required check rollups may appear **UNSTABLE** until checks have registered.
- The merge process is snapshot-only: treat CI signals as a point-in-time snapshot; do not assume real-time convergence.

---

## Risk / NO-LIVE Notes

- This dashboard is **read-only** (watch-only). It must not place orders or call broker/exchange APIs.
- Do not add mutating endpoints. Keep API methods to GET/HEAD/OPTIONS.

---

## Evidence

Use the evidence template:

```text
docs/ops/evidence/EV_EXECUTION_WATCH_DASHBOARD_V0_4_PASS_TEMPLATE.md
```

Create a stamped evidence file from the template (example):

```text
docs/ops/evidence/EV_EXECUTION_WATCH_DASHBOARD_V0_4_PASS_YYYYMMDDTHHMMSSZ.md
```
