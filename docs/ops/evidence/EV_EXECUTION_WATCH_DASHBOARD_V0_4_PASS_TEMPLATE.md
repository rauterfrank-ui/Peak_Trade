# Evidence — Execution Watch Dashboard v0.4 — PASS (TEMPLATE)

**UTCSTAMP:** `YYYYMMDDTHHMMSSZ`  
**Result:** PASS  
**Scope:** Watch-only dashboard + read-only APIs (v0.4 health panel + health endpoint)

---

## Preconditions

- Branch/commit:

```bash
git rev-parse HEAD
git status -sb
```

---

## Start

```bash
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

---

## API checks (read-only)

Record outputs (redact secrets; do not paste tokens).

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
- Backward compatible: top-level `api_version` remains `v0.2`, v0.4 semantics are indicated via `meta.api_version`
- `meta.api_version` = `v0.4`
- `meta.read_errors` present (0 if none)
- `meta.dataset_stats` present (sessions_count may be null)
- `meta.last_event_utc` present when determinable (else null)
- `/api/execution/health` returns deterministic invariants (no network calls)
- Negative behavior:
  - Unknown `run_id` → HTTP 404 with `{"detail":"run_not_found"}`

---

## UI checks

Open:

```text
/execution_watch
```

Checklist:
- Polling toggle default is off (no auto polling)
- Tail mode still works (append-only via `since_cursor`)
- Health panel shows meta fields and dataset stats
- “Ping Health” calls `/api/execution/health` and displays status
- If `meta.read_errors > 0`, UI shows a badge

---

## Tests

```bash
python3 -m ruff check src/webui/execution_watch_api_v0_2.py tests/live/test_execution_watch_api_v0_2.py
python3 -m ruff format --check src/webui/execution_watch_api_v0_2.py tests/live/test_execution_watch_api_v0_2.py
python3 -m pytest -q tests/live/test_execution_watch_api_v0_2.py
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

---

## Notes / Risk

- NO-LIVE: watch-only, read-only APIs, no trading actions.
