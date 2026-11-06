# OPS Suite — Incident State Real-Signal Review (Read-Only)

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Read-only review of incident_state real-signal gaps and hardening options
docs_token: DOCS_TOKEN_OPS_SUITE_INCIDENT_STATE_REVIEW

## Scope
This document is a **read-only review** of `incident_state` in the Ops Cockpit. No code changes, no mutations. It identifies gaps and recommends real-signal mapping options for future implementation.

## Baseline
- **main@201a697b**
- **Related:** OPS_SUITE_DASHBOARD_VNEXT_SPEC, PILOT_EXECUTION_EDGE_CASE_MATRIX, dependencies_state (telemetry hardened)

---

## 1. Current incident_state Implementation

### 1.1 Schema (ops_cockpit.py ~450–461)

| Field | Current Source | Real Signal? |
|-------|----------------|---------------|
| `status` | blocked if operator_state.blocked \| kill_switch_active else normal | **Partial** — operator/kill_switch hardcoded |
| `blocked` | operator_state.blocked | **Placeholder** — hardcoded |
| `kill_switch_active` | guard_state.kill_switch_active | **Placeholder** — always False |
| `degraded` | `not freshness_ok` (truth doc freshness) | **Partial** — truth only |
| `requires_operator_attention` | blocked \| kill_switch \| not freshness_ok | **Partial** |
| `summary` | blocked / degraded / normal | **Partial** |

### 1.2 OPS_SUITE_DASHBOARD_VNEXT_SPEC Expectations

Incident / Safety view should include:
- incidents
- degraded dependencies
- kill-switch posture
- operator-required action

### 1.3 PILOT_EXECUTION_EDGE_CASE_MATRIX

| Incident | Expected | Evidence |
|----------|----------|---------|
| Telemetry degraded | operator warning, prefer NO_TRADE | evidence freshness + degraded mode |
| Kill-switch active | no trade action, surface blocked state | explicit kill-switch visibility |

---

## 2. Gap Analysis

### 2.1 degraded

| Aspect | Current | Gap |
|--------|---------|-----|
| Source | Truth doc freshness only | No dependency/telemetry signal |
| dependencies_state | Has telemetry status (run_health_checks) | Not used for incident_state |

**Recommendation:** Blend `degraded` with `dependencies_state.telemetry`:
- `degraded` = truth stale **or** telemetry warn/critical
- Reuse `_tel_status` (already computed for dependencies_state)

### 2.2 kill_switch_active

| Aspect | Current | Gap |
|--------|---------|-----|
| Value | Always `False` | No derivation from runtime state |
| Real signal candidate | `StatePersistence` state file | `data&#47;kill_switch&#47;state.json` |

**Data source:** `src&#47;risk_layer&#47;kill_switch&#47;persistence.py` — `StatePersistence.load()` returns dict with `state` (ACTIVE, KILLED, RECOVERING).

**Recommendation:** When state file exists and is readable:
- `kill_switch_active` = (loaded state == "KILLED" or "RECOVERING")
- Fallback: `False` when file missing or unreadable

**Path:** `repo_root &#47; "data" &#47; "kill_switch" &#47; "state.json"` or config-driven.

### 2.3 incidents (list)

| Aspect | Current | Gap |
|--------|---------|-----|
| incident_state | No `incidents` field | OPS spec expects "incidents" |
| Alert system | AlertHistory, AlertEngine | Could surface recent unacked alerts |

**Recommendation:** Optional future addition. Out of scope for minimal hardening. Document as deferred.

### 2.4 summary / requires_operator_attention

| Aspect | Current | Gap |
|--------|---------|-----|
| Derivation | From blocked, kill_switch, freshness | Correct logic, but inputs are placeholders |

Once `kill_switch_active` and `degraded` are hardened, `summary` and `requires_operator_attention` improve automatically.

---

## 3. Real-Signal Mapping Options

### 3.1 Existing Real Signals

| Source | Location | Relevance |
|--------|----------|-----------|
| `run_health_checks` | telemetry_root | _tel_status already in payload (dependencies_state) |
| `StatePersistence.load()` | `data&#47;kill_switch&#47;state.json` | kill_switch state |
| `PEAK_KILL_SWITCH` env | live/safety.py | Alternative signal (session-scoped) |

### 3.2 Recommended Mapping (for future PR)

| incident_state field | Option | Real signal | Fallback |
|----------------------|--------|-------------|----------|
| `degraded` | Primary | truth stale **or** _tel_status in (warn, critical) | current (truth only) |
| `kill_switch_active` | Primary | StatePersistence.load() state in (KILLED, RECOVERING) | `False` |
| `incidents` | Deferred | — | omit |

### 3.3 Out of Scope (this review)

- AlertHistory / AlertEngine integration for incidents list
- Session-dependent kill-switch (PEAK_KILL_SWITCH env)
- Execution authority changes

---

## 4. Implementation Notes (for future PR)

### 4.1 Order of Operations

- `incident_state` is built after `_tel_status` is computed (telemetry block runs before evidence_state).
- `degraded` blend: add `or _tel_status in ("warn", "critical")` to current `not freshness_ok`.
- `kill_switch_active`: add block to read state file when path exists; use StatePersistence or minimal JSON read to avoid heavy imports.

### 4.2 Kill-Switch State File

- Default path: `repo_root &#47; "data" &#47; "kill_switch" &#47; "state.json"`
- Format: `{"state": "KILLED"|"ACTIVE"|"RECOVERING", ...}`
- Fail-safe: if file missing or parse error, assume `False`.

### 4.3 Risk

- **Low:** Read-only addition; no execution authority.
- **Consistency:** Kill-switch state file may not exist (e.g. first run). Fallback to False is safe.

---

## 5. Summary

| Field | Current | Recommended Hardening |
|-------|---------|------------------------|
| `degraded` | Truth freshness only | Blend with telemetry status (warn/critical) |
| `kill_switch_active` | `False` (hardcoded) | Read from StatePersistence file when exists |
| `incidents` | — | Deferred (optional future) |
| `summary` / `requires_operator_attention` | — | Improve automatically when inputs hardened |

**Next step:** Explicit approval for implementation PR (read-model contract + code changes) when ready.
