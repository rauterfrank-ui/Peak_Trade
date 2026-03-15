# Bounded Pilot Telemetry Root Evidence Gap Note

status: DRAFT
last_updated: 2026-03-15
owner: Peak_Trade
purpose: Document the telemetry-root split between logs/execution and out/ops/execution_events, evidence_state limitation, and future unification path
docs_token: DOCS_TOKEN_BOUNDED_PILOT_TELEMETRY_ROOT_EVIDENCE_GAP_NOTE

## 1. Intent

This note documents the **split** between two telemetry-root paths and its impact on Ops Cockpit `evidence_state`. It does not change `run_health_checks`, `evidence_state` logic, or broader telemetry design. It establishes the canonical documentation before any future unification.

## 2. Current Telemetry-Root Split

| Path | Writer | Consumer |
|------|--------|----------|
| `logs&#47;execution` | Orchestrator, execution_pipeline, telemetry.py | Ops Cockpit, live_panel, execution_watch |
| `out&#47;ops&#47;execution_events&#47;` | execution_events (observability) | None (no Ops Cockpit consumer) |

Bounded-pilot `execution_events` write to:

- Global: `out&#47;ops&#47;execution_events&#47;execution_events.jsonl`
- Session-scoped: `out&#47;ops&#47;execution_events&#47;sessions&#47;&lt;session_id&gt;&#47;execution_events.jsonl`

## 3. evidence_state Limitation

Ops Cockpit `evidence_state` derives `audit_trail` and `telemetry_evidence` from `run_health_checks(telemetry_root)`. The default `telemetry_root` is `logs&#47;execution`.

| evidence_state field | Source | Reflects |
|-----------------------|--------|----------|
| audit_trail | run_health_checks(_tel_root).status | `logs&#47;execution` only |
| telemetry_evidence | _tel_status | `logs&#47;execution` only |
| summary | blend(truth, telemetry) | `logs&#47;execution` only |

**Limitation:** `evidence_state` does **not** reflect the health or presence of bounded-pilot execution events in `out&#47;ops&#47;execution_events&#47;`.

## 4. Bounded-Pilot Impact

| Aspect | Impact |
|--------|--------|
| Operator perception | Ops Cockpit may show evidence_state "ok" while bounded-pilot Evidence lives in a different path |
| Closeout verification | Operator must check `out&#47;ops&#47;execution_events&#47;sessions&#47;&lt;session_id&gt;&#47;` separately |
| run_health_checks | Scans `logs&#47;execution`; does not scan `out&#47;ops&#47;execution_events&#47;` |

## 5. Future Unification Path

When unification is desired (out of scope for this note):

- **Option B (recommended):** Extend `run_health_checks` to support a second root or recursive scan; pass `out&#47;ops&#47;execution_events&#47;` from Ops Cockpit and blend results.
- **Option A:** Ops Cockpit calls `run_health_checks` for both roots; use worst-of.
- **Option C (not recommended):** Move execution_events to `logs&#47;execution` — breaking change.

This note does **not** implement any of these options.

## 6. Relationship

- Source: `docs&#47;ops&#47;reviews&#47;telemetry_root_evidence_gap_review&#47;`
- Companion to: `OPS_SUITE_EVIDENCE_STATE_REAL_SIGNAL_REVIEW`
- Companion to: `docs&#47;ops&#47;runbooks&#47;execution_events_wiring.md`

## 7. Non-Goals

- No `run_health_checks` changes
- No `evidence_state` logic changes
- No broader telemetry redesign
- No code changes
