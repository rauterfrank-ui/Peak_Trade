# OPS Suite — Evidence State Real-Signal Review (Read-Only)

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Read-only review of evidence_state real-signal gaps and hardening options
docs_token: DOCS_TOKEN_OPS_SUITE_EVIDENCE_STATE_REVIEW

## Scope
This document is a **read-only review** of `evidence_state` in the Ops Cockpit. No code changes, no mutations. It identifies gaps and recommends real-signal mapping options for future implementation.

## Baseline
- **main@d43b840e**
- **Related:** OPS_SUITE_DASHBOARD_VNEXT_SPEC, RECONCILIATION_FLOW_SPEC, exposure_state (live_runs + caps hardened)

---

## 1. Current evidence_state Implementation

### 1.1 Schema (ops_cockpit.py ~517–524)

| Field | Current Source | Real Signal? |
|-------|----------------|---------------|
| `summary` | `_ev_summary` = map(`v3_summary["freshness_status"]` → ok/partial/stale) | **Partial** — derived from truth doc freshness only |
| `last_verified_utc` | `truth_state["last_verified_utc"]` = `_utc_now()` | **Placeholder** — always now, not from evidence |
| `freshness_status` | `v3_summary["freshness_status"]` (truth doc mtimes) | **Partial** — truth docs only |
| `source_freshness` | `group_summaries` (fresh/stale/older counts) | **Partial** — truth docs only |
| `audit_trail` | Hardcoded `"intact"` | **Placeholder** — no real signal |

### 1.2 Data Flow (Current)

```
truth_docs (discover_truth_docs)
  → group_summaries (_group_summary)
  → v3_summary (_build_v3_executive_summary)
  → _fs_level = v3_summary["freshness_status"]
  → _ev_summary = map(ok→ok, warn→partial, critical→stale)
  → evidence_state
```

**Not used for evidence_state:**
- `run_health_checks(telemetry_root)` — used only for `dependencies_state.telemetry`
- `logs&#47;execution` content (JSONL events)
- `get_telemetry_summary()`
- Prometheus / session metrics

---

## 2. Gap Analysis

### 2.1 audit_trail

| Aspect | Current | Gap |
|--------|---------|-----|
| Value | Always `"intact"` | No derivation from execution/telemetry |
| RECONCILIATION_FLOW_SPEC | "evidence trail is intact" is a resume criterion | Operator cannot verify from Ops Cockpit |
| Real signal candidate | `run_health_checks(logs&#47;execution)` | Parse error rate, compression failures indicate degraded trail |

**Recommendation:** Derive `audit_trail` from telemetry health when `logs&#47;execution` exists:
- `run_health_checks` status `ok` → `"intact"`
- `warn` → `"degraded"` or `"partial"`
- `critical` → `"degraded"`
- No telemetry root / not exists → `"unknown"` (or keep `"intact"` as conservative default for no-data case)

### 2.2 summary / freshness_status

| Aspect | Current | Gap |
|--------|---------|-----|
| Source | Truth doc file mtimes only | No execution/telemetry evidence |
| OPS_SUITE_DASHBOARD_VNEXT_SPEC | "evidence freshness" in Health/Drift view | Truth freshness ≠ execution evidence freshness |

**Options:**
- **A (minimal):** Keep current; document that evidence_state = truth-doc evidence only.
- **B (blend):** When telemetry exists, blend: `summary` = worst of (truth freshness, telemetry status). E.g. truth ok + telemetry critical → partial/stale.
- **C (separate):** Add `telemetry_evidence` field: `ok`/`warn`/`critical`/`unknown` from `run_health_checks`, leave `summary` truth-only.

### 2.3 last_verified_utc

| Aspect | Current | Gap |
|--------|---------|-----|
| Value | Always `now()` | Not evidence-based |
| Meaning | "When was evidence last verified?" | Could mean: last truth scan, or last telemetry read |

**Options:**
- **A:** Keep as payload generation time (current).
- **B:** Use `max(truth last_modified, telemetry last_event)` when available.
- **C:** Add `last_evidence_scan_utc` = now, `last_telemetry_read_utc` = from telemetry health/recent log mtime.

---

## 3. Real-Signal Mapping Options

### 3.1 Existing Real Signals

| Source | Location | Writer | Relevance |
|-------|----------|--------|-----------|
| `run_health_checks` | `src/execution/telemetry_health.py` | Telemetry health | disk, retention, compression, parse errors |
| `get_telemetry_summary` | `src/webui/services/live_panel_data.py` | Wrapper over run_health_checks | status, total_sessions, disk_usage_mb, recent_errors |
| `logs&#47;execution` | `*.jsonl`, `*.jsonl.gz` | Execution pipeline | Execution events, append-only |
| Truth docs | `docs&#47;governance&#47;ai&#47;*.md` | Manual/CI | File mtimes (current source) |

### 3.2 Recommended Mapping (for future PR)

| evidence_state field | Option | Real signal | Fallback |
|----------------------|--------|-------------|----------|
| `audit_trail` | Primary | `run_health_checks(telemetry_root).status` → intact/degraded/unknown | `"unknown"` when no telemetry |
| `summary` | Optional blend | worst of (truth freshness, telemetry status) | Current (truth-only) |
| `telemetry_evidence` | Optional new | `run_health_checks` status | omit when no telemetry |

### 3.3 Out of Scope (this review)

- Prometheus evidence metrics
- Session-dependent `get_risk_status`
- Execution authority changes
- New telemetry writers or schemas

---

## 4. Implementation Notes (for future PR)

### 4.1 Reuse

- `telemetry_root` and `run_health_checks` are already used for `dependencies_state`.
- `evidence_state` can call `run_health_checks` in the same block (or receive `_tel_status` from a shared call) to avoid duplicate I/O.

### 4.2 Order of Operations

Current order in `build_ops_cockpit_payload`:
1. Build truth_state, v3_summary, exposure_state
2. Build evidence_state (truth-only)
3. Resolve _tel_root, run run_health_checks for dependencies_state

Suggested: Move telemetry health call earlier (or pass result) so both `dependencies_state` and `evidence_state` can use it.

### 4.3 Risk

- **Low:** Read-only addition; no execution authority.
- **Consistency:** `audit_trail` derived from telemetry may differ from operator expectation if "audit" is interpreted as governance docs only. Document clearly.

---

## 5. Summary

| Field | Current | Recommended Hardening |
|-------|---------|------------------------|
| `audit_trail` | `"intact"` (hardcoded) | Derive from `run_health_checks` → intact/degraded/unknown |
| `summary` | Truth freshness only | Optional: blend with telemetry status |
| `last_verified_utc` | now() | Optional: add telemetry-based timestamp |
| `source_freshness` | Truth docs | Keep as-is (truth-specific) |
| `freshness_status` | Truth docs | Keep or blend (see summary) |

**Next step:** Explicit approval for implementation PR (read-model contract + code changes) when ready.
