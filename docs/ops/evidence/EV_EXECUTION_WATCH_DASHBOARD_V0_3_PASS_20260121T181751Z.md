# Evidence — Execution Watch Dashboard v0.3 — PASS

**UTCSTAMP:** `20260121T181751Z`  
**Result:** PASS  
**Scope:** Watch-only dashboard + read-only APIs (v0.3 meta + tail)

---

## Preconditions

- Branch/commit:

```bash
git rev-parse HEAD
git status -sb
```

Recorded:
- `git rev-parse HEAD` → `595d53bcf97061c6751d0363093247448c100845`
- `git status -sb` → `## main...origin&#47;main` (working tree modified; see PR diff)

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
/api/execution/runs
/api/execution/runs/<run_id>
/api/execution/runs/<run_id>/events?limit=200
/api/execution/runs/<run_id>/events?limit=200&since_cursor=<cursor>
/api/live/sessions
```

Expected (verified via tests + contract inspection):
- Backward compatible: top-level `api_version` remains `v0.2`, v0.3 semantics are indicated via `meta.api_version`
- `meta.api_version` = `v0.3`
- `meta.read_errors` present (0 if none)
- `meta.has_more` / `meta.next_cursor` consistent
- Unknown `run_id` → HTTP 404 with `{"detail":"run_not_found"}`
- Empty dataset list endpoints render empty arrays with `has_more=false`, `next_cursor=null`
- Malformed JSONL line: skipped deterministically, `meta.read_errors` increments
- Tail: `since_cursor` returns events strictly after cursor; `next_cursor` is watermark

---

## UI checks

Open:

```text
/execution_watch
```

Checklist (v0.3 operator UX):
- Polling toggle default is off
- Poll interval selector present (2s/5s/10s)
- Tail mode toggle present (append-only via `since_cursor`)
- Tail “Clear” resets watermark cursor
- Empty state for events is clear
- If `meta.read_errors > 0`, UI shows a badge

---

## Tests

```bash
python3 -m pytest -q tests/live/test_execution_watch_api_v0_2.py
```

Recorded:
- `7 passed`

---

## Notes / Risk

- NO-LIVE: watch-only, read-only APIs, no trading actions.
