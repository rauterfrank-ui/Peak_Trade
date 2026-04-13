# OPS Cockpit — vNext Required Views Coverage (Traceability)

**status:** active  
**last_updated:** 2026-04-13  
**purpose:** Review-friendly **mapping** from [`OPS_SUITE_DASHBOARD_VNEXT_SPEC.md`](OPS_SUITE_DASHBOARD_VNEXT_SPEC.md) **Required Views §1–7** to Ops Cockpit **payload keys**, **operator summary / HTML surface** (see [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md)), and **test anchors**. **Not** a completeness guarantee for every bullet under each view; **not** an execution or approval claim.

**docs_token:** `DOCS_TOKEN_OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE`

## Non-Goals

- **Not** broker, exchange, or reconciliation truth — same semantics as [`OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md`](OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md) and [`RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md`](../runbooks/RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md).  
- **Not** a substitute for [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md) (detailed row-level mapping).  
- **Not** coverage of **R&amp;D Dashboard** (Phase 76) or non-Cockpit UIs.

## Canonical anchors

| Anchor | Role |
|--------|------|
| [`OPS_SUITE_DASHBOARD_VNEXT_SPEC.md`](OPS_SUITE_DASHBOARD_VNEXT_SPEC.md) | Product vNext Required Views §1–7 (target). |
| [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md) | Payload ↔ operator-summary HTML (primary detail). |
| [`OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md`](OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md) | Top-level payload keys for `build_ops_cockpit_payload`. |
| `tests&#47;webui&#47;test_ops_cockpit.py` | Cockpit HTML &#47; payload builder regression (representative). |
| `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py` | Stable top-level key set (no value snapshots). |
| `tests&#47;ops&#47;test_*_observation.py` | Per-aggregate tests for compact `*_observation` builders (where present). |

## Required Views §1–7 ↔ Cockpit read-model (summary)

| RV | vNext Required View (headline) | Primary payload / observation keys (indicative) | Operator summary / HTML (indicative) | Test / doc anchors |
|----|----------------------------------|-------------------------------------------------|--------------------------------------|---------------------|
| **1** | System State | `system_state`, `system_state_observation` | `_render_operator_summary_surface` — **System status**, **System &#47; environment (observation)**; hero **Config environment (observation)** | `test_system_state_observation.py`; operator summary surface table |
| **2** | Go &#47; No-Go | `policy_state`, `guard_state`, `operator_state`, `policy_go_no_go_observation` | **Go &#47; No-Go observation**, **Policy &#47; go-no-go (observation)** | `test_policy_go_no_go_observation.py`; `test_ops_cockpit_payload_top_level_contract.py` |
| **3** | Session &#47; Run State | `run_state`, `session_end_mismatch_state`, `stale_state` (in part), `run_session_observation`, `operator_state` (inputs) | **Run &#47; session (observation)**; cards **Run state**, **Stale State**; **Session End Mismatch** | `test_run_session_observation.py`; `tests&#47;webui&#47;test_ops_cockpit.py` (session &#47; run cases) |
| **4** | Incident &#47; Safety | `incident_state`, `dependencies_state`, `incident_safety_observation` | **Incident &#47; safety (observation)**; **Incident observation (read-only)** | `test_incident_safety_observation.py` |
| **5** | Exposure &#47; Risk | `exposure_state`, `transfer_ambiguity_state`, `stale_state`, `balance_semantics_state`, `exposure_risk_observation` | **Exposure &#47; risk (observation)**; **Exposure State**, **Transfer &#47; Treasury ambiguity**, **Stale State** | `test_exposure_risk_observation.py`; exposure contract refs in operator summary surface |
| **6** | Policy &#47; Governance | `policy_state`, `guard_state`, `ai_boundary_state`, `human_supervision_state`, `evidence_state` (cross-ref), `governance_boundary_observation` | `_render_policy_governance_observation_surface` — **Policy &#47; Governance observation (vNext RV6)** | `test_governance_boundary_observation.py` |
| **7** | Health &#47; Drift | `health_drift_observation`, `truth_status`, `freshness_status`, `source_coverage_status`, `executive_summary`, `evidence_state`, `dependencies_state`, `stale_state` | **Health &#47; drift (observation)**; **Status-at-a-glance**; **Evidence** blocks as linked in summary surface | `test_health_drift_observation.py`; `test_evidence_audit_observation.py` |

**Notes:** `safety_posture_observation` spans gating posture (related to RV2 &#47; RV4); see operator summary surface ordering. **Additional** Cockpit keys not named in vNext §1–7 but shipped read-only include e.g. `workflow_officer_state`, `update_officer_ui`, `phase83_eligibility_snapshot` — see payload contract and operator summary surface; they **do not** replace Required View semantics.

## Related

- [`RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](../runbooks/RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md) — phased plan and Ist-Stand.  
- [`RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md`](../runbooks/RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md) — interpretation vs authority.  
- [`docs/ops/registry/DOCS_TRUTH_MAP.md`](../registry/DOCS_TRUTH_MAP.md) — docs drift registry.
