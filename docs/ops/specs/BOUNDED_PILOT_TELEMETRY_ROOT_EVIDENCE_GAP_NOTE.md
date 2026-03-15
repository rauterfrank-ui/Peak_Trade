# Bounded Pilot Telemetry Root Evidence Gap Note

status: DRAFT
last_updated: 2026-03-15
owner: Peak_Trade
purpose: Document the telemetry-root split between logs/execution and out/ops/execution_events, evidence_state coverage (both roots since PR #1829), and unification status
docs_token: DOCS_TOKEN_BOUNDED_PILOT_TELEMETRY_ROOT_EVIDENCE_GAP_NOTE

## 1. Intent

This note documents the **split** between two telemetry-root paths and their impact on Ops Cockpit `evidence_state`. As of PR #1829, Ops Cockpit runs `run_health_checks` for both roots and blends results (worst-of). This note establishes the canonical documentation.

## 2. Current Telemetry-Root Split

| Path | Writer | Consumer |
|------|--------|----------|
| `logs&#47;execution` | Orchestrator, execution_pipeline, telemetry.py | Ops Cockpit, live_panel, execution_watch |
| `out&#47;ops&#47;execution_events&#47;` | execution_events (observability) | Ops Cockpit (via run_health_checks, PR #1829) |

Bounded-pilot `execution_events` write to:

- Global: `out&#47;ops&#47;execution_events&#47;execution_events.jsonl`
- Session-scoped: `out&#47;ops&#47;execution_events&#47;sessions&#47;&lt;session_id&gt;&#47;execution_events.jsonl`

## 3. evidence_state Coverage

Ops Cockpit `evidence_state` derives `audit_trail` and `telemetry_evidence` from `run_health_checks` over **both** roots (since PR #1829). The blend uses worst-of status.

| evidence_state field | Source | Reflects |
|-----------------------|--------|----------|
| audit_trail | run_health_checks(_tel_root) + run_health_checks(_exec_events_root) → worst-of | `logs&#47;execution` and `out&#47;ops&#47;execution_events&#47;` |
| telemetry_evidence | _tel_status (worst-of blend) | both roots |
| summary | blend(truth, telemetry) | both roots |

**Status:** `evidence_state` reflects the health of bounded-pilot execution events in `out&#47;ops&#47;execution_events&#47;` (Option A, PR #1829).

## 4. Bounded-Pilot Impact

| Aspect | Impact |
|--------|--------|
| Operator perception | Ops Cockpit evidence_state reflects both roots (worst-of); bounded-pilot Evidence in `out&#47;ops&#47;execution_events&#47;` is included |
| Closeout verification | Operator may still check `out&#47;ops&#47;execution_events&#47;sessions&#47;&lt;session_id&gt;&#47;` for session-level detail |
| run_health_checks | Scans both `logs&#47;execution` and `out&#47;ops&#47;execution_events&#47;` (when present) |

## 5. Unification Status

- **Option A (implemented, PR #1829):** Ops Cockpit calls `run_health_checks` for both roots; uses worst-of blend. Current state.
- **Option B (future):** Extend `run_health_checks` API to support a second root or recursive scan — not required for current evidence_state coverage.
- **Option C (not recommended):** Move execution_events to `logs&#47;execution` — breaking change.

## 6. Relationship

- Source: `docs&#47;ops&#47;reviews&#47;telemetry_root_evidence_gap_review&#47;`
- Rebaseline: `docs&#47;ops&#47;reviews&#47;bounded_pilot_evidence_state_rebaseline_review&#47;` (post PR #1829)
- Companion to: `OPS_SUITE_EVIDENCE_STATE_REAL_SIGNAL_REVIEW`
- Companion to: `docs&#47;ops&#47;runbooks&#47;execution_events_wiring.md`

## 7. Non-Goals

- No `run_health_checks` changes
- No `evidence_state` logic changes
- No broader telemetry redesign
- No code changes
