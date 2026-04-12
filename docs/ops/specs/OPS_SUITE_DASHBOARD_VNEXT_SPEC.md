# OPS Suite / Dashboard vNext Spec

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Canonical vNext specification for operator-facing OPS Suite / Dashboard expansion
docs_token: DOCS_TOKEN_OPS_SUITE_DASHBOARD_VNEXT_SPEC

## Scope
This document defines the operator-facing vNext target for the OPS Suite / Dashboard. It is a control-plane and observability specification, not an execution-authority document.

## Non-Goals
- no direct trading authority
- no bypass of enabled / armed / confirm-token / dry-run / kill-switch controls
- no implicit live-readiness claim
- no execution-engine redesign in this document

## Operator States
- disabled
- enabled
- armed
- dry-run
- blocked
- kill-switch active

## Required Views
### 1. System State
- current mode
- environment
- active safety state
- current gating posture

### 2. Go / No-Go
- policy outcome
- gating blockers
- readiness summary
- escalation signals

### 3. Session / Run State
- current run/session
- latest run outcome
- session start/end
- active operator context

### 4. Incident / Safety
- incidents
- degraded dependencies
- kill-switch posture
- operator-required action

### 5. Exposure / Risk
- current exposure summary
- strategy-level caps
- treasury separation status
- transfer/balance anomalies

### 6. Policy / Governance
- critic/proposer boundary summary
- current policy action
- confirm-token requirement
- audit/evidence status

**Ops Cockpit (read-only HTML):** observation bundle for RV6 is implemented as presentation-only (`_render_policy_governance_observation_surface` in `src/webui/ops_cockpit.py`); see [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md).

### 7. Health / Drift
- service health
- stale data
- feed/runtime drift indicators
- evidence freshness

## Data Model Expectations
The future implementation should prefer read-model payloads that are:
- explicit
- audit-friendly
- reproducible
- decoupled from execution authority

Suggested top-level payload sections:
- system_state
- policy_state
- safety_state
- run_state
- incident_state
- exposure_state
- evidence_state
- dependencies_state

## UX Principles
- truth-first before visual polish
- operator clarity over density
- visible blockers before actions
- explicit red/yellow/green semantics only when grounded by evidence
- no hidden inferred authority

## Delivery Phases
### Phase 1 — Read Model + Status Surfaces
Expose canonical system/policy/safety/run state in the dashboard.

### Phase 2 — Incident + Kill-Switch Surface
Expose operator-relevant incidents and kill-switch posture.

### Phase 3 — Exposure / Treasury / Reconciliation Surface
Expose capital separation, exposure, and anomaly summaries.

### Phase 4 — Operator Workflow Surface
Expose explicit go/no-go and acknowledgement flows without changing execution authority.

**Ops Cockpit (read-only HTML):** latest Workflow Officer dashboard view is exposed as `workflow_officer_state` (observation only; does not run the officer) — see [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md).

## Dependencies / Inputs
- existing Ops Cockpit truth-first model
- existing governance docs and runbooks
- existing risk-gate and activation-gate posture
- existing audit/evidence model

## Exit Criteria for Future Implementation
A future implementation should only be considered complete when:
- operator states are visible and unambiguous
- no execution authority is silently introduced
- audit trail remains intact
- gating and safety posture are visible and testable
