# RUNBOOK — OPS Suite / Dashboard vNext Plan

status: DRAFT
last_updated: 2026-04-13
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
- **Top-level Ops Cockpit payload (builder contract):** [`OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md`](../specs/OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md) — `build_ops_cockpit_payload` in `src&#47;webui&#47;ops_cockpit.py`; key-level, observation-only aggregates; no execution authority.

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

**Phase E closure (docs-first, reviewable):** [`RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md`](RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md) — what the read-model line **does and does not** claim, how to separate **policy/guard** vs **`*_observation`** vs **workflow tooling**, and **canonical anchors** (payload contract, operator summary surface, Truth-Map, tests). No Cockpit product authority is introduced by that document.

## Recommended Future Branch Sequence
1. feat/ops-suite-read-model-contract
2. feat/ops-suite-system-policy-surface
3. feat/ops-suite-incident-risk-surface
4. feat/ops-suite-operator-workflow-visibility
5. feat/ops-suite-phase-e-governance-review  
6. feat/ops-suite-vnext-coverage-matrix (docs-only: Required Views coverage matrix + dashboard checklist sync)

**Required Views ↔ Cockpit traceability (review):** [`OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`](../specs/OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md) — maps vNext §1–7 to payload keys, operator summary surface, and test anchors; **not** an approval or live-readiness claim.

**Ist-Stand (Ops Cockpit HTML):** read-only **Policy &#47; Governance observation (vNext RV6)** bündelt `policy_state`, `guard_state`, `ai_boundary_state`, `human_supervision_state` und einen Evidence-/Audit-Cross-Ref zu `evidence_state` — keine neue Autorität, Presentation-only (`src/webui/ops_cockpit.py`). **System / environment (read-only):** additives Payload-Feld `system_state_observation` aus `system_state`, optional Konsistenzcheck zu `policy_state.summary` (`build_system_state_observation` in `src/ops/system_state_observation.py`) — keine Broker-/Exchange-Garantie, keine Environment-Runtime-Garantie; getrennt von `health_drift_observation`, `safety_posture_observation`, `policy_go_no_go_observation`. **Safety / gating posture (read-only):** additives Payload-Feld `safety_posture_observation` aus bestehenden Rollups (`build_safety_posture_observation` in `src/ops/safety_posture_observation.py`) — Observation only, keine Gate-Abschwächung. **Policy / go-no-go (read-only):** additives Payload-Feld `policy_go_no_go_observation` aus `policy_state`, `incident_state`, `operator_state` (`build_policy_go_no_go_observation` in `src/ops/policy_go_no_go_observation.py`) — keine Live-Freigabe, kein Ersatz für externe Governance; getrennt von `safety_posture_observation`. **Governance / AI boundary (read-only):** additives Payload-Feld `governance_boundary_observation` aus `ai_boundary_state`, `human_supervision_state`, optional Hinweisen aus `guard_state` &#47; `evidence_state` (`build_governance_boundary_observation` in `src/ops/governance_boundary_observation.py`) — keine Governance-Freigabe, kein Supervision-Waiver; getrennt von `safety_posture_observation` und `evidence_audit_observation`. **Run / session (read-only):** additives Payload-Feld `run_session_observation` aus `run_state`, `session_end_mismatch_state`, `stale_state`, `operator_state` (`build_run_session_observation` in `src/ops/run_session_observation.py`) — keine Session-Garantie, keine Exchange-Wahrheit. **Health / Drift (read-only):** additives Payload-Feld `health_drift_observation` aus Truth-/Freshness-/Coverage-Rollups, Flags, `evidence_state`, `dependencies_state`, `stale_state` (`build_health_drift_observation` in `src/ops/health_drift_observation.py`) — keine Live-Service-Health-Garantie. **Exposure / Risk (read-only):** additives Payload-Feld `exposure_risk_observation` aus `exposure_state`, `transfer_ambiguity_state`, `stale_state`, `guard_state` (`build_exposure_risk_observation` in `src/ops/exposure_risk_observation.py`) — Observation only, keine Broker-Wahrheit, keine Risk-Freigabe. **Incident / Safety (read-only):** additives Payload-Feld `incident_safety_observation` aus `incident_state`, `dependencies_state`, optional Konsistenz-Hinweise aus `policy_state` &#47; `operator_state` (`build_incident_safety_observation` in `src/ops/incident_safety_observation.py`) — fokussiert auf Incident-/Dependency-Signale, nicht deckungsgleich mit `safety_posture_observation`; keine Incident-Freigabe. **Evidence / Audit (read-only):** additives Payload-Feld `evidence_audit_observation` aus `evidence_state`, optional Konsistenz-Hinweise aus Top-Level-`truth_status` &#47; `freshness_status` und `executive_summary` (`build_evidence_audit_observation` in `src/ops/evidence_audit_observation.py`) — nicht Audit-Freigabe, nicht Compliance-Urteil; getrennt von `health_drift_observation`. **Phase 4:** `workflow_officer_state` aus `out&#47;ops&#47;workflow_officer` (read-only, startet den Officer nicht); bounded **`handoff_observation`** &#47; **`next_chat_preview_observation`** aus demselben `report.json`-`summary`, wenn vorhanden; Cockpit-HTML (`id=operator-workflow-observation-surface`) und **`update_officer_ui`** (`id=update-officer-visibility-card`) nur Sichtbarkeit — kein Go-Signal, **`policy_go_no_go_observation`** bleibt separat. **Session-end mismatch (read model):** `session_end_mismatch_state` wird aus Live-Session-Registry-JSONs und `live_runs`-Metadaten/Events abgeleitet (`src/live/session_end_mismatch_reader.py`); kein Broker-Call, kein Enforcement. **Transfer-/Treasury-Ambiguity (read-only):** `transfer_ambiguity_state` aus lokalen Cockpit-Signalen (`src/live/transfer_ambiguity_reader.py`); keine Exchange-API, keine Freigabe-Semantik. **Dependencies / P85 (read-only):** `dependencies_state.p85_exchange_observation` aus `P85_RESULT.json` unter `out&#47;ops&#47;**` (`src/ops/p85_result_reader.py`); kein Netzwerk im Cockpit-Payload-Build, kein Live-Check durch die Seite selbst. **Dependencies / lokaler Market-Data-Cache (read-only):** `dependencies_state.market_data_cache_observation` aus offline `check_data_health_only` auf `real_market_smokes.base_path` (`src/ops/market_data_cache_observation_reader.py`); kein Live-Feed, kein Broker-Truth.

## Explicit Non-Goals
- no live-trading enablement
- no direct execution overrides
- no implicit broker authority
- no config or runtime gate weakening
