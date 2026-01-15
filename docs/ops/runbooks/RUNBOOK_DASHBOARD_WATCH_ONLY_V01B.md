# RUNBOOK — Dashboard Watch-Only UI v0.1B (Observability)

**Status:** READY  
**Owner:** ops  
**Risk:** LOW (read-only, watch-only)  
**Scope:** `src/live/web/app.py` (Live Dashboard v0, Phase 67) — Watch-Only UI routes + read-only API v0

---

## 1) Purpose
Provide a **watch-only** observability UI for:
- System health (reachable, latency, contract version)
- Run list (active/inactive, last update)
- Run detail panels (signals, positions, orders — read-only counters)

---

## 2) Non-Goals (Governance)
- No POST/PUT/PATCH/DELETE endpoints
- No action buttons that mutate state (no cancel, no submit, no start/stop)
- No secrets or API keys in frontend code
- No CI “watch loops” (all verification is snapshot-only)

---

## 3) Preconditions (Data Source)
This UI reads run artifacts from a **runs directory** (default: `live_runs/`).

Required per run:
- `meta.json`
- `events.parquet` or `events.csv`

Optional:
- `alerts.jsonl`

See contracts:
- `docs/webui/DASHBOARD_DATA_CONTRACT_v0.md`
- `docs/webui/DASHBOARD_API_CONTRACT_v0.md`

---

## 4) Start (Local)
Start the live dashboard server (read-only):

```bash
python scripts/live_web_server.py --host 127.0.0.1 --port 8000
```

Optional: override run artifacts directory:

```bash
python scripts/live_web_server.py --host 127.0.0.1 --port 8000 --base-runs-dir live_runs --auto-refresh-seconds 5
```

---

## 5) UI Routes (Watch-Only)

Open in browser:

```text
/watch
/watch/runs/{run_id}
/sessions/{run_id}   (alias)
```

Notes:
- Polling is **client-side** (default ~3s) with exponential backoff up to 30s.
- Pages are **server-rendered first** (usable without JS).
- “WATCH-ONLY” banner is always visible.

---

## 6) API Routes (Read-Only)

```text
/api/v0/health
/api/v0/runs
/api/v0/runs/{run_id}
/api/v0/runs/{run_id}/metrics
/api/v0/runs/{run_id}/equity
/api/v0/runs/{run_id}/signals
/api/v0/runs/{run_id}/positions
/api/v0/runs/{run_id}/orders
```

---

## 7) Debug Checklist (Snapshot-Only)
- Health responds and includes `contract_version` + `server_time`
- Runs list loads (may be empty if no artifacts exist)
- Run detail loads (signals/positions/orders may be empty depending on logged columns)

---

## 8) Evidence Commands (Snapshot-Only)

```bash
python3 -m ruff check .
python3 -m ruff format --check .
pytest -q
```

---

## 9) Rollback
Revert the PR commit(s) that introduced the watch-only v0.1B additions in `src/live/web/app.py`.
