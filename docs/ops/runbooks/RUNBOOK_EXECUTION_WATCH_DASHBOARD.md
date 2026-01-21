# RUNBOOK — Execution Watch Dashboard v0.2 (Watch-Only)

**Owner:** ops  
**Purpose:** Start and verify the Execution Watch Dashboard v0.2 (read-only) for recent execution pipeline events and live-session registry state.  
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

Open the dashboard page in your browser:

```text
/execution_watch
```

---

## Verify

### Verify APIs (read-only)

Run these requests (examples shown as paths only; use your preferred client):

```text
/api/healthz
/api/execution/runs
/api/execution/runs/<run_id>
/api/execution/runs/<run_id>/events?limit=200
/api/live/sessions
```

Expected:
- HTTP 200 for existing data
- Deterministic ordering (newest runs first, stable pagination cursor)
- `api_version` is `v0.2` in responses
- `generated_at_utc` present in responses
- Events pagination returns `next_cursor` + `has_more` consistently

### Verify UI

On the Execution Watch page:
- Runs list renders (newest first)
- Selecting a run updates Run Detail
- Events table paginates deterministically (“Load more”)
- Sessions table renders from the live-session registry (if present)
- Polling toggle defaults to **off**

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

### No sessions

- Check whether registry files exist:

```bash
ls -la reports/experiments/live_sessions
```

### 404 for a run_id

- The run id might not exist in the current JSONL file; refresh runs list and select a valid run.

---

## Risk / NO-LIVE Notes

- This dashboard is **read-only** (watch-only). It must not place orders or call broker/exchange APIs.
- Do not add mutating endpoints. Keep API methods to GET/HEAD/OPTIONS.

---

## Evidence

Use the evidence template:

```text
docs/ops/evidence/EV_EXECUTION_WATCH_DASHBOARD_V0_2_PASS_TEMPLATE.md
```

Create a stamped evidence file from the template (example):

```text
docs/ops/evidence/EV_EXECUTION_WATCH_DASHBOARD_V0_2_PASS_YYYYMMDDTHHMMSSZ.md
```
