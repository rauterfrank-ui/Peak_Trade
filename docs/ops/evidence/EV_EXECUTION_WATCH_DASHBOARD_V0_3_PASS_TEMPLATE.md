# Evidence — Execution Watch Dashboard v0.3 — PASS (TEMPLATE)

**UTCSTAMP:** `YYYYMMDDTHHMMSSZ`  
**Result:** PASS  
**Scope:** Watch-only dashboard + read-only APIs (v0.3 meta + tail)

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
/api/execution/runs/<run_id>/events?limit=200&since_cursor=<cursor>
```

```text
/api/live/sessions
```

Expected:
- Backward compatible: top-level `api_version` remains `v0.2`, v0.3 semantics are indicated via `meta.api_version`
- `generated_at_utc` present
- `meta` present:
  - `meta.api_version` = `v0.3`
  - `meta.read_errors` is present (0 if none)
  - `meta.has_more` / `meta.next_cursor` consistent
  - `meta.source` = `fixture|local`
- Negative behavior:
  - Unknown `run_id` → HTTP 404 with `{"detail":"run_not_found"}`

---

## UI checks

Open:

```text
/execution_watch
```

Checklist:
- Runs list renders
- Selecting a run updates detail
- Events table renders (empty state ok)
- Sessions table renders (or empty state is clear)
- Polling toggle default is off
- Poll interval selector works (2s/5s/10s)
- Tail mode:
  - When enabled, events append-only via `since_cursor`
  - “Clear” resets tail cursor watermark
- If `meta.read_errors > 0`, UI shows a badge

---

## Tests

```bash
python3 -m pytest -q tests/live/test_execution_watch_api_v0_2.py
```

---

## Notes / Risk

- NO-LIVE: watch-only, read-only APIs, no trading actions.
