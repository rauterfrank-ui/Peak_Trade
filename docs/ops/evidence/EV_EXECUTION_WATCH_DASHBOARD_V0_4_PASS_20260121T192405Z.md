# Evidence — Execution Watch Dashboard v0.4 — PASS

**UTCSTAMP:** `20260121T192405Z`  
**Result:** PASS  
**Scope:** Watch-only dashboard + read-only APIs (v0.4 health panel + health endpoint)

---

## Preconditions

- Branch/commit:

```bash
git rev-parse HEAD
git status -sb
```

Recorded:
- `git rev-parse HEAD` → `01fa040925225fd1a7c67301e1eafae4d4a23b42`
- `git status -sb` → `## main...origin&#47;main` (working tree modified; see PR diff)

---

## Start

```bash
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

---

## API checks (read-only)

```text
/api/healthz
/api/execution/health
/api/execution/runs
/api/execution/runs/<run_id>
/api/execution/runs/<run_id>/events?limit=200
/api/execution/runs/<run_id>/events?limit=200&since_cursor=<cursor>
/api/live/sessions
```

Expected (verified via tests + contract inspection):
- Backward compatible: top-level `api_version` remains `v0.2`, v0.4 semantics are indicated via `meta.api_version`
- `meta.api_version` = `v0.4`
- `meta.read_errors` present (0 if none)
- `meta.dataset_stats` present (sessions_count may be null)
- `meta.last_event_utc` present when determinable (else null)
- `/api/execution/health` returns deterministic invariants (no network calls)

---

## UI checks

```text
/execution_watch
```

Checklist (v0.4 operator UX):
- Polling toggle default is off
- Tail mode works (append-only via `since_cursor`)
- Health panel shows meta fields and dataset stats
- “Ping Health” calls `/api/execution/health` and shows status
- If `meta.read_errors > 0`, UI shows a badge

---

## Tests

```bash
python3 -m ruff check src/webui/execution_watch_api_v0_2.py tests/live/test_execution_watch_api_v0_2.py
python3 -m ruff format --check src/webui/execution_watch_api_v0_2.py tests/live/test_execution_watch_api_v0_2.py
python3 -m pytest -q tests/live/test_execution_watch_api_v0_2.py
```

Recorded:
- `9 passed`

---

## Notes / Risk

- NO-LIVE: watch-only, read-only APIs, no trading actions.
