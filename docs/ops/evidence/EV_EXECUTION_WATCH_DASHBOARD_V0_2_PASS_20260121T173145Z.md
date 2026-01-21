# Evidence — Execution Watch Dashboard v0.2 — PASS

**UTCSTAMP:** `20260121T173145Z`  
**Result:** PASS  
**Scope:** Watch-only dashboard + read-only APIs

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
```

```text
/api/execution/runs
```

```text
/api/execution/runs/<run_id>
```

```text
/api/execution/runs/<run_id>/events?limit=200
```

```text
/api/live/sessions
```

Expected:
- `api_version` is `v0.2`
- `generated_at_utc` present
- Runs newest-first, deterministic
- Events pagination stable (`next_cursor`, `has_more`)

---

## UI checks

Open:

```text
/execution_watch
```

Checklist:
- Runs list renders
- Selecting a run updates detail
- Events table paginates (“Load more”)
- Sessions table renders (or empty state is clear)
- Polling toggle default is off

---

## Tests

```bash
python3 -m pytest -q tests/live/test_execution_watch_api_v0_2.py
python3 -m ruff check src/webui/execution_watch_api_v0_2.py tests/live/test_execution_watch_api_v0_2.py
```

---

## Notes / Risk

- NO-LIVE: watch-only, read-only APIs, no trading actions.
