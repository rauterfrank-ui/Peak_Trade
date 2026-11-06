# OPS Suite — Exposure Data Source Decision

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Canonical decision for exposure_state real-signal data source in OPS Suite / Ops Cockpit
docs_token: DOCS_TOKEN_OPS_SUITE_EXPOSURE_DATA_SOURCE_DECISION

## Scope
This document records the decision for the primary data source for `exposure_state` observed exposure in the Ops Cockpit. It is a decision record only. No implementation is implied until explicitly approved.

## Non-Goals
- no implementation in this document
- no execution authority
- no bypass of risk gates or caps

## Decision

**Primary data source:** Option B — `live_runs&#47;` (file-based)

**Secondary:** Option A (Prometheus) may be added later when Live Web and runs are active.

---

## Rationale

| Criterion | Option B (live_runs) | Option A (Prometheus) |
|-----------|----------------------|------------------------|
| Stateless Ops Cockpit | ✅ | ✅ (with scrape) |
| Audit-friendly | ✅ File-based | ⚠️ Scrape |
| Available without Live Web | ✅ | ❌ |
| RUNBOOK alignment | ✅ | ✅ |
| Implementation effort | Medium | Medium |

**Reason:** Stateless, audit-friendly, and available without requiring the Live Web process to be running.

---

## Data Source Details

### live_runs/ (primary)

| Aspect | Value |
|--------|-------|
| **Location** | `live_runs&#47;&lt;run_id&gt;&#47;` |
| **Format** | Parquet or CSV (per `ShadowPaperLoggingConfig`) |
| **Schema** | `LiveRunEvent` with `position_size`, `price`, `close` |
| **Exposure derivation** | `abs(position_size) * (price or close)` per run |
| **Aggregation** | Latest event per run → sum over all runs |
| **Freshness** | `mtime` of Parquet/CSV files |

### Existing infrastructure

- `src&#47;live&#47;run_logging.py` — `LiveRunEvent` schema
- `src&#47;live&#47;monitoring.py` — `load_run_events`, `get_run_timeseries` (exposure from `position_size`)
- `live_runs&#47;` base dir configurable via `shadow_paper_logging.base_dir`

---

## Implementation Prerequisites (when approved)

1. **Reader:** Read `live_runs&#47;` for latest `position_size` and `price` per run.
2. **Aggregation:** Sum `abs(position_size) * price` across runs.
3. **Freshness:** Derive from file mtime; treat stale (>24h) as `unknown`.
4. **Fallback:** When no runs or `live_runs&#47;` empty → `summary: no_live_context` (unchanged).
5. **Contract:** Align with `OPS_SUITE_EXPOSURE_READ_MODEL_CONTRACT.md` schema.

---

## Do Not Implement Yet

This decision is recorded for future implementation. No implementation branch should be opened until:

- Explicit operator approval
- Read-model contract stable
- Tests defined for exposure derivation

---

## References

- `docs&#47;ops&#47;specs&#47;OPS_SUITE_EXPOSURE_READ_MODEL_CONTRACT.md` — Schema and mapping rules
- `docs&#47;ops&#47;runbooks&#47;RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md` — Runbook requirements
- `src&#47;live&#47;run_logging.py` — LiveRunEvent schema
- `src&#47;live&#47;monitoring.py` — Run loading and exposure derivation
