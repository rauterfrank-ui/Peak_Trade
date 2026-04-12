# RUNBOOK — OPS Suite / Dashboard vNext Plan

status: DRAFT
last_updated: 2026-04-12
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
  - system_state (config-derived environment / load-status observation; no broker guarantee)
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

**Ist-Stand (Ops Cockpit HTML):** read-only **Policy &#47; Governance observation (vNext RV6)** bündelt `policy_state`, `guard_state`, `ai_boundary_state`, `human_supervision_state` und einen Evidence-/Audit-Cross-Ref zu `evidence_state` — keine neue Autorität, Presentation-only (`src/webui/ops_cockpit.py`). **Safety / gating posture (read-only):** additives Payload-Feld `safety_posture_observation` aus bestehenden Rollups (`build_safety_posture_observation` in `src/ops/safety_posture_observation.py`) — Observation only, keine Gate-Abschwächung. **Phase 4:** `workflow_officer_state` aus `out&#47;ops&#47;workflow_officer` (read-only, startet den Officer nicht); bounded **`handoff_observation`** &#47; **`next_chat_preview_observation`** aus demselben `report.json`-`summary`, wenn vorhanden. **Session-end mismatch (read model):** `session_end_mismatch_state` wird aus Live-Session-Registry-JSONs und `live_runs`-Metadaten/Events abgeleitet (`src/live/session_end_mismatch_reader.py`); kein Broker-Call, kein Enforcement. **Transfer-/Treasury-Ambiguity (read-only):** `transfer_ambiguity_state` aus lokalen Cockpit-Signalen (`src/live/transfer_ambiguity_reader.py`); keine Exchange-API, keine Freigabe-Semantik. **Dependencies / P85 (read-only):** `dependencies_state.p85_exchange_observation` aus `P85_RESULT.json` unter `out&#47;ops&#47;**` (`src/ops/p85_result_reader.py`); kein Netzwerk im Cockpit-Payload-Build, kein Live-Check durch die Seite selbst. **Dependencies / lokaler Market-Data-Cache (read-only):** `dependencies_state.market_data_cache_observation` aus offline `check_data_health_only` auf `real_market_smokes.base_path` (`src/ops/market_data_cache_observation_reader.py`); kein Live-Feed, kein Broker-Truth.

## Explicit Non-Goals
- no live-trading enablement
- no direct execution overrides
- no implicit broker authority
- no config or runtime gate weakening
