# OPS Cockpit — Payload Read-Model Contract

**status:** active  
**last_updated:** 2026-04-13  
**purpose:** Canonical, review-friendly **top-level contract** for the JSON object returned by `build_ops_cockpit_payload` in `src&#47;webui&#47;ops_cockpit.py` (same shape as `GET &#47;api&#47;ops-cockpit` and the `&#47;ops` HTML page payload). **Contract level:** top-level keys and grouping — **not** a guarantee of nested field values, enums, or snapshot stability of rollups.

**docs_token:** `DOCS_TOKEN_OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT`

## Scope

- Describes **which top-level keys** the builder is intended to surface and how they group by concern.
- Points to **builder / reader modules** where aggregates are produced.
- Clarifies **observation-only** semantics for `*_observation` keys.

## Non-Goals

- **Not** an execution-authority or live-trading enablement document.
- **Not** broker, exchange, or reconciliation truth; cockpit payloads are **read-model observations** from local artifacts and config where applicable.
- **Not** a promise that nested shapes or string values stay byte-stable across releases — only **top-level keys** are treated as the stable contract surface unless explicitly called out.
- **Not** a substitute for [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md) (HTML &#47; operator-summary mapping) or [`OPS_SUITE_DASHBOARD_VNEXT_SPEC.md`](OPS_SUITE_DASHBOARD_VNEXT_SPEC.md) (product vNext target).

## Contract boundary

**Source of truth for the top-level key set:** `build_ops_cockpit_payload` → `return { ... }` in `src&#47;webui&#47;ops_cockpit.py`.

Additive changes may introduce **new** top-level keys; removals or renames are **breaking** for consumers and should update this document and any key-stability test together.

## Top-level key groups

### System / environment

| Key | Role |
|-----|------|
| `system_state` | Config-derived environment and cockpit mode labels (observation; not broker guarantee). |
| `system_state_observation` | Compact aggregate — `src&#47;ops&#47;system_state_observation.py` (`build_system_state_observation`). Observation only. |

### Policy / go–no-go

| Key | Role |
|-----|------|
| `policy_state` | Policy rollup (action, blocked, kill-switch flags, etc.). |
| `guard_state` | Guard rails subset exposed in payload (presentation). |
| `operator_state` | Operator enablement / blocked rollup. |
| `policy_go_no_go_observation` | Compact aggregate — `src&#47;ops&#47;policy_go_no_go_observation.py`. Observation only. |

### Safety / gating

| Key | Role |
|-----|------|
| `safety_posture_observation` | Holistic gating posture aggregate — `src&#47;ops&#47;safety_posture_observation.py`. Observation only. |
| `safety_state` | vNext-aligned **top-level projection** — `src&#47;ops&#47;safety_state.py` (`build_safety_state`). Bundles references and a small scalar subset from existing `safety_posture_observation`, `incident_safety_observation`, and `incident_state` only — **not** new gating logic, **not** approval or unlock. |

### Run / session

| Key | Role |
|-----|------|
| `run_state` | Run &#47; session rollup from registry &#47; metadata where present. |
| `session_end_mismatch_state` | Read model — `src&#47;live&#47;session_end_mismatch_reader.py`. |
| `stale_state` | Stale signals (balance, orders, exposure, etc.). |
| `balance_semantics_state` | Balance semantics **observation** from local portfolio snapshot when config allows — **not** exchange reconciliation truth. Drives `stale_state.balance` and feeds session &#47; transfer readers where wired; supplementary traceability: [`OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`](OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md) — **§ Supplementary Cockpit surfaces**. Operator Summary HTML: [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md) — **Balance semantics (observation)** (`id=operator-summary-balance-semantics`). |
| `run_session_observation` | Compact aggregate — `src&#47;ops&#47;run_session_observation.py`. Observation only. |

### Health / drift

| Key | Role |
|-----|------|
| `truth_status`, `freshness_status`, `source_coverage_status` | Executive rollup levels. |
| `critical_flags`, `unknown_flags` | Flag lists from truth pipeline. |
| `executive_summary` | Nested executive summary (v3). |
| `health_drift_observation` | Compact aggregate — `src&#47;ops&#47;health_drift_observation.py`. Observation only. |

### Exposure / risk

| Key | Role |
|-----|------|
| `exposure_state` | Exposure card payload. |
| `transfer_ambiguity_state` | Read model — `src&#47;live&#47;transfer_ambiguity_reader.py`. |
| `exposure_risk_observation` | Compact aggregate — `src&#47;ops&#47;exposure_risk_observation.py`. Observation only. |

### Incident / safety

| Key | Role |
|-----|------|
| `incident_state` | Incident rollup. |
| `incident_safety_observation` | Compact aggregate — `src&#47;ops&#47;incident_safety_observation.py`. Observation only. |

### Evidence / audit

| Key | Role |
|-----|------|
| `evidence_state` | Evidence freshness and audit trail rollup. |
| `evidence_audit_observation` | Compact aggregate — `src&#47;ops&#47;evidence_audit_observation.py`. Observation only. |

### Governance / AI boundary

| Key | Role |
|-----|------|
| `ai_boundary_state` | AI boundary labels from canonical docs &#47; builders in cockpit. |
| `human_supervision_state` | Human supervision rollup. |
| `governance_boundary_observation` | Compact aggregate — `src&#47;ops&#47;governance_boundary_observation.py`. Observation only. |

### Dependencies / specialized observations

| Key | Role |
|-----|------|
| `dependencies_state` | Dependencies rollup; may include `p85_exchange_observation`, `market_data_cache_observation` (see `src&#47;ops&#47;p85_result_reader.py`, `src&#47;ops&#47;market_data_cache_observation_reader.py`). |

### Truth sources / runtime

| Key | Role |
|-----|------|
| `truth_state` | Truth doc pipeline state. |
| `canonical_sources`, `source_groups`, `source_group_summary` | Grouped sources for cockpit. |
| `runtime_unknown_state` | Runtime unknown bucket. |

### Operator tooling (read-only artifacts)

| Key | Role |
|-----|------|
| `workflow_officer_state` | Latest Workflow Officer panel context — does **not** start the officer; `src&#47;ops&#47;workflow_officer.py` (panel builders). Surfaces in HTML as **Operator workflow observation** (`id=operator-workflow-observation-surface`, `_render_workflow_officer_observation_surface`) — visibility and bounded **handoff** &#47; **next-step preview** rows from the same `report.json` `summary` when present; **not** approval, **not** unlock, **not** execution authority, **not** a substitute for `policy_go_no_go_observation`. Supplementary traceability: [`OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`](OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md) — **§ Supplementary Cockpit surfaces**. |
| `update_officer_ui` | Update-officer GET-only UI model for cockpit forms (`build_update_officer_ui_model`). Surfaces in HTML as **Update Officer** (`id=update-officer-visibility-card`, `_render_update_officer_card`) with GET-only source ergonomics on the same page — **not** Workflow Officer control, **not** POST write actions. Supplementary traceability: [`OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`](OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md) — **§ Supplementary Cockpit surfaces**. |

**Non-Goals (operator tooling):** No Cockpit-side start of Workflow Officer; no reconciliation or gate authority; no semantic expansion of other `*_observation` aggregates beyond their existing builders.

### Other snapshots

| Key | Role |
|-----|------|
| `phase83_eligibility_snapshot` | Read-only **observation** snapshot from the existing Phase 83 eligibility check (`check_strategy_live_eligibility`); **not** live approval or gate weakening. Traceability (payload &#47; HTML &#47; tests): [`OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`](OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md) — **§ Supplementary Cockpit surfaces**. |

## Observation-only aggregates (`*_observation`)

Keys ending with `_observation` are **cockpit observations**: conservative rollups for operator visibility. They are **not** approvals, unlocks, compliance verdicts, broker truth, or substitutes for external governance. Each aggregate typically includes `reader_schema_version` and `data_source` (e.g. `cockpit_payload_aggregate`). See individual modules under `src&#47;ops&#47;*_observation.py` and [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md).

## UI surface

Rendering and section order are **not** part of this key-level contract. For HTML mapping, use [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md).

## Governance interpretation (Phase E)

This contract lists **keys and roles**, not operator procedure. For **read-only interpretation** — what the payload **does not** authorize, and how `policy_state` &#47; `*_observation` &#47; workflow tooling differ — use:

- [`RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md`](../runbooks/RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md) — Phase E closure; canonical anchors and non-claims.  
- [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md) — section **Phase E — Operator interpretation**.  
- [`docs/ops/registry/DOCS_TRUTH_MAP.md`](../registry/DOCS_TRUTH_MAP.md) — docs drift registry (pairing sensitive edits with canonical docs).

## Related

- [`OPS_SUITE_DASHBOARD_VNEXT_SPEC.md`](OPS_SUITE_DASHBOARD_VNEXT_SPEC.md) — vNext operator-facing target.
- [`OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md`](OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md) — Required Views §1–7 ↔ keys / summary surface / tests.
- [`RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](../runbooks/RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md) — phased plan; Phase B read-model alignment.
- [`RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md`](../runbooks/RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md) — Phase E governance review and traceability.
- [`docs/ops/registry/DOCS_TRUTH_MAP.md`](../registry/DOCS_TRUTH_MAP.md) — docs drift and canonical references.

## Tests

- Top-level key subset regression: `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py` (no value snapshots).

## Stable top-level key set (reference)

The following **39** top-level keys are **intended** to be present when `build_ops_cockpit_payload` completes successfully on a minimal repo layout (the set may grow **additively**; new keys should be documented here):

`ai_boundary_state`, `balance_semantics_state`, `canonical_sources`, `critical_flags`, `dependencies_state`, `evidence_audit_observation`, `evidence_state`, `executive_summary`, `exposure_risk_observation`, `exposure_state`, `freshness_status`, `governance_boundary_observation`, `guard_state`, `health_drift_observation`, `human_supervision_state`, `incident_safety_observation`, `incident_state`, `operator_state`, `phase83_eligibility_snapshot`, `policy_go_no_go_observation`, `policy_state`, `runtime_unknown_state`, `run_session_observation`, `run_state`, `safety_posture_observation`, `safety_state`, `session_end_mismatch_state`, `source_coverage_status`, `source_group_summary`, `source_groups`, `stale_state`, `system_state`, `system_state_observation`, `transfer_ambiguity_state`, `truth_state`, `truth_status`, `unknown_flags`, `update_officer_ui`, `workflow_officer_state`.

**Note:** Nested object shapes and enum-like strings inside these keys are **evolving**; consumers should not rely on undocumented inner fields without checking the builder implementation.
