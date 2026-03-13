# OPS Suite — Live Session Registry Started-State Contract

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Contract for "started" state in live_session_registry to enable run_state.session_active
docs_token: DOCS_TOKEN_OPS_SUITE_LIVE_SESSION_REGISTRY_STARTED_STATE

## Scope
This document defines the contract for registering live sessions with `status="started"` at session start, and updating to a terminal status at session end. It enables `run_state.session_active` and `run_state.active` in the Ops Cockpit to derive from real signals.

**Docs-only.** No code changes in this PR. Implementation: `feat/live-session-registry-started-status`.

## Non-Goals
- No execution authority
- No change to session lifecycle
- No Prometheus/heartbeat extension (this contract uses registry only)

## Context
- **Confirmed gap (2026-03-13):** `run_state.session_active` and `run_state.active` are placeholders; no real signal.
- **Reason:** `live_session_registry` only writes records when a session **ends** (in `finally` block). There are no `status="started"` records.
- **Baseline:** main@4a472528
- **Related:** OPS_SUITE_RUN_STATE_REAL_SIGNAL_REVIEW, OPS_SUITE_DASHBOARD_VNEXT_SPEC

---

## 1. Current Flow (as-is)

| Phase | Location | Action |
|-------|----------|--------|
| Session start | `run_execution_session.py` | `status = "started"` (in-memory only) |
| Session end | `finally` block | `register_live_session_run(record)` with terminal status |

**Result:** All persisted records have `status` in `{completed, failed, aborted}`. `by_status.get("started", 0)` is always 0.

---

## 2. Contract: Started-State Flow

### 2.1 Lifecycle

| Phase | When | Action |
|-------|------|--------|
| **Register at start** | After warmup, before `run_n_steps` / `run_for_duration` / `run_forever` | `register_live_session_run(record)` with `status="started"` |
| **Update at end** | In `finally` block | Overwrite same file with `status` in `{completed, failed, aborted}` |

### 2.2 Filename Stability

Current filename: `{started_at}_{run_type}_{session_id}.json` (see `_build_session_filename`).

- **Session ID** and **started_at** are fixed at session start.
- Same record used at start and end → same filename → overwrite.

**No API change required.**

### 2.3 Writer: run_execution_session.py

| Insert point | Before | After |
|--------------|--------|-------|
| `runner.warmup()` | — | — |
| `runner.run_n_steps()` / `run_for_duration()` / `run_forever()` | — | **Register with status=started** (if not dry_run, not no_registry) |

**Exception handling:** Registry write at start must not abort the session. Use same try/except pattern as in `finally`.

### 2.4 Consumer: Ops Cockpit

| run_state field | Signal | Fallback |
|-----------------|--------|----------|
| `session_active` | `get_session_summary()["active_sessions"] > 0` | `False` |
| `active` | Same as `session_active` | `False` |
| `status` | `"active"` if session_active else `"idle"` | `"idle"` |

`get_session_summary()` returns `active_sessions = by_status.get("started", 0)`. No change needed.

---

## 3. Schema

### 3.1 LiveSessionRecord.status (unchanged)

| Value | Meaning |
|-------|---------|
| `started` | Session is running |
| `completed` | Session ended normally |
| `failed` | Session ended with exception |
| `aborted` | Session ended with KeyboardInterrupt |

### 3.2 run_state (ops_cockpit)

| Field | After contract | Notes |
|-------|----------------|-------|
| `session_active` | `bool` from registry | `active_sessions > 0` |
| `active` | Same as `session_active` | Alias |
| `status` | `"active"` \| `"idle"` | Derived from session_active |

---

## 4. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| **Orphaned "started"** | Process crash (SIGKILL, OOM) leaves record with status=started. No automatic cleanup. | Accept: rare; operator can manually clean or add heartbeat-based stale detection. |
| **Registry write fails at start** | Session continues; ops_cockpit shows session_active=False. | Accept: fail-safe; session still runs. |
| **Registry write fails at end** | Record stays "started" forever. | Same as orphaned; existing try/except in finally handles it. |

---

## 5. Implementation Order (future PR)

1. **run_execution_session.py:** Register with status=started after warmup, before run.
2. **ops_cockpit.py:** Derive `session_active`, `active`, `status` from `get_session_summary()`.
3. **Tests:** Add test for session_active=True when registry has started record.

---

## 6. Summary

| Aspect | Value |
|--------|-------|
| **Contract** | Register at start (status=started), overwrite at end (terminal status) |
| **Filename** | Same file; no new API |
| **Consumer** | ops_cockpit run_state.session_active, active, status |
| **Future branch** | `feat/live-session-registry-started-status` |
