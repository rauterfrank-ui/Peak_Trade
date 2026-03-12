# OPS Suite — Run State Real-Signal Review (Read-Only)

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Read-only review of run_state real-signal gaps and hardening options
docs_token: DOCS_TOKEN_OPS_SUITE_RUN_STATE_REVIEW

## Scope
This document is a **read-only review** of `run_state` in the Ops Cockpit. No code changes, no mutations. It identifies gaps and recommends real-signal mapping options for future implementation.

## Baseline
- **main@4eb57480**
- **Related:** OPS_SUITE_DASHBOARD_VNEXT_SPEC, exposure_state (live_runs), evidence_state (telemetry hardened)

---

## 1. Current run_state Implementation

### 1.1 Schema (ops_cockpit.py ~426–433)

| Field | Current Source | Real Signal? |
|-------|----------------|---------------|
| `status` | Hardcoded `"idle"` | **Placeholder** |
| `active` | Hardcoded `False` | **Placeholder** |
| `last_run_status` | Hardcoded `"unknown"` | **Placeholder** |
| `session_active` | Hardcoded `False` | **Placeholder** |
| `generated_at` | `truth_state["last_verified_utc"]` | **Partial** — payload generation time |
| `freshness_status` | `v3_summary["freshness_status"]` | **Partial** — truth docs only |

### 1.2 OPS_SUITE_DASHBOARD_VNEXT_SPEC Expectations

Session / Run State view should include:
- current run/session
- latest run outcome
- session start/end
- active operator context

---

## 2. Gap Analysis

### 2.1 last_run_status

| Aspect | Current | Gap |
|--------|---------|-----|
| Value | Always `"unknown"` | No derivation from execution/registry |
| Real signal candidate | `live_session_registry` | Most recent record has status: completed/failed/aborted |

**Data source:** `reports&#47;experiments&#47;live_sessions&#47;*.json` — populated by `register_live_session_run()` at end of session (scripts/run_execution_session.py).

**Recommendation:** When `live_session_registry` exists and has records:

- `list_session_records(limit=1)` → most recent record
- `last_run_status` = record.status (`completed` \| `failed` \| `aborted`)

**Fallback:** `unknown` when no registry or no records.

### 2.2 session_active / active / status

| Aspect | Current | Gap |
|--------|---------|-----|
| session_active | Always `False` | No real signal |
| active | Always `False` | Same |
| status | Always `"idle"` | No derivation |

**Constraint:** `live_session_registry` only writes records when a session **ends** (in `finally` block). There are no `"started"` records in the registry with the current flow. So `by_status.get("started", 0)` is always 0.

**Options for session_active:**

- **A (live_runs heuristic):** When `live_runs` exists and has `last_updated_utc`, treat as "active" if age < threshold (e.g. 5 min). Risky: a run that writes every 10 min would appear stale.
- **B (registry extension):** Future: register at session start with status=started, update to completed/failed at end. Then `session_active = by_status.get("started", 0) > 0`. Out of scope for this review.
- **C (keep placeholder):** Document that session_active is not derivable until registry or heartbeat is extended.

**Recommendation:** For this review, document Option C. Primary hardening: `last_run_status` from registry. `session_active` / `active` / `status` remain placeholders until registry or heartbeat extension.

### 2.3 Optional: run_count, last_run_id

| Optional field | Source | Notes |
|----------------|--------|-------|
| `run_count` | `live_session_registry` num_sessions or `live_runs` list_runs | Informational |
| `last_run_id` | Most recent record session_id | For audit trail |

---

## 3. Real-Signal Mapping Options

### 3.1 Existing Real Signals

| Source | Location | Writer | Relevance |
|--------|----------|--------|-----------|
| `live_session_registry` | `reports&#47;experiments&#47;live_sessions&#47;*.json` | run_execution_session.py (at end) | status, last_started_at |
| `get_session_summary` | list_session_records, get_session_summary | — | num_sessions, by_status |
| `live_runs` | `live_runs&#47;` | LiveRunLogger | run_count, last_updated (no status) |
| `get_live_sessions_stats` | live_panel_data.py | Wrapper over registry | total_sessions, active_sessions (always 0) |

### 3.2 Recommended Mapping (for future PR)

| run_state field | Option | Real signal | Fallback |
|-----------------|--------|-------------|----------|
| `last_run_status` | Primary | `list_session_records(limit=1)[0].status` | `"unknown"` |
| `session_active` | Deferred | — | `False` (no signal yet) |
| `active` | Deferred | — | `False` |
| `status` | Deferred | — | `"idle"` |
| `run_count` | Optional | `get_session_summary()["num_sessions"]` or live_runs count | omit |

### 3.3 Out of Scope (this review)

- Registry extension for "started" registration
- Heartbeat / process marker for active detection
- Prometheus session metrics
- Execution authority changes

---

## 4. Implementation Notes (for future PR)

### 4.1 Registry Path

- Default: `repo_root &#47; "reports" &#47; "experiments" &#47; "live_sessions"` when `repo_root` set
- Or: `live_session_registry.DEFAULT_LIVE_SESSION_DIR` relative to cwd

### 4.2 Order of Operations

- `run_state` is built before `exposure_state` and `evidence_state` in current flow.
- Add optional `live_sessions_root` param to `build_ops_cockpit_payload` (or derive from repo_root).
- Call `get_session_summary` / `list_session_records` only when path exists; fail-safe to `[]`.

### 4.3 Risk

- **Low:** Read-only addition; no execution authority.
- **Consistency:** Registry may be empty (sessions run without `--no-registry` or different base_dir). Fallback to placeholder is safe.

---

## 5. Summary

| Field | Current | Recommended Hardening |
|-------|---------|------------------------|
| `last_run_status` | `"unknown"` | Derive from `list_session_records(limit=1)` when registry has records |
| `session_active` | `False` | Keep placeholder (no signal until registry/heartbeat extension) |
| `active` | `False` | Keep placeholder |
| `status` | `"idle"` | Keep placeholder (or derive from session_active when available) |
| `run_count` | — | Optional: add when registry/live_runs available |

**Next step:** Explicit approval for implementation PR (read-model contract + code changes) when ready.
