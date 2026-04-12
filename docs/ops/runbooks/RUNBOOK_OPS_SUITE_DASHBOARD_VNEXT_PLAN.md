# RUNBOOK — OPS Suite / Dashboard vNext Plan

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Phased implementation plan for OPS Suite / Dashboard vNext
docs_token: DOCS_TOKEN_RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN

## Intent
Create a safe, operator-facing OPS Suite / Dashboard expansion plan that improves visibility and control-plane clarity without mutating execution authority.

## Phase A — Discovery / Mapping
- map existing Ops Cockpit payloads
- map existing governance/risk state surfaces
- identify gaps for operator state visibility
- inventory current run/session/incident inputs

## Phase B — Read-Model Contract
- define canonical read-model contract for:
  - system_state
  - policy_state
  - safety_state
  - run_state
  - incident_state
  - exposure_state
  - evidence_state

## Phase C — UI Surface Design
- system status banner
- go/no-go summary
- incident panel
- exposure/risk panel
- evidence freshness panel
- operator action visibility panel

## Phase D — Safe Incremental Build
- ship read-only surfaces first
- avoid authority-bearing controls
- verify truth-first semantics
- add tests before operator action affordances

## Phase E — Governance Review
- validate no gate softening
- validate no hidden authority
- validate audit/evidence continuity
- validate operator interpretation clarity

## Recommended Future Branch Sequence
1. feat/ops-suite-read-model-contract
2. feat/ops-suite-system-policy-surface
3. feat/ops-suite-incident-risk-surface
4. feat/ops-suite-operator-workflow-visibility

**Ist-Stand (Ops Cockpit HTML):** read-only **Policy &#47; Governance observation (vNext RV6)** bündelt `policy_state`, `guard_state`, `ai_boundary_state`, `human_supervision_state` und einen Evidence-/Audit-Cross-Ref zu `evidence_state` — keine neue Autorität, Presentation-only (`src/webui/ops_cockpit.py`). **Phase 4:** `workflow_officer_state` aus `out&#47;ops&#47;workflow_officer` (read-only, startet den Officer nicht).

## Explicit Non-Goals
- no live-trading enablement
- no direct execution overrides
- no implicit broker authority
- no config or runtime gate weakening
