# RUNBOOK — OPS Suite Dashboard vNext — Phase E Governance Review

**status:** active  
**last_updated:** 2026-04-13  
**owner:** Peak_Trade  
**purpose:** Reviewable, traceable **Phase E** closure for the Ops Cockpit read-model line: operator interpretation, explicit non-authority, and canonical doc anchors — **no** new product authority.  
**docs_token:** `DOCS_TOKEN_RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW`

## Intent

Phase E in [`RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md) asks for governance validation without gate softening. This runbook **materializes** that phase as a **docs-first interpretation frame**: what operators should infer from the Cockpit, what they must **not** infer, and **which specifications and tests** are the canonical anchors.

## Scope

- Ops Cockpit payload from `build_ops_cockpit_payload` in `src&#47;webui&#47;ops_cockpit.py` and the read-only `&#47;ops` HTML bundle.  
- **Not** execution engines, **not** R&amp;D Dashboard, **not** Workflow Officer process control from the browser.

## Non-Goals

- No live-trading enablement, no unlock semantics, no compliance “pass” claim from the Cockpit.  
- No new API routes, POST actions, or Cockpit-side steering of officers or eligibility.  
- No replacement for external governance, LB-APR-001, or operator runbooks — only **local read-model visibility**.

---

## What Phase E records as achieved (read-model / interpretation)

The following are **in place** as bounded, additive read-only surfaces (see Ist-Stand in [`RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md)):

- **Top-level payload contract** — key set and grouping: [`OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md`](../specs/OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md); regression: `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py`.  
- **Operator summary ↔ HTML mapping** — [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](../specs/OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md); implementation: `src&#47;webui&#47;ops_cockpit.py`.  
- **Compact `*_observation` aggregates** — conservative rollups from existing payload fields; modules under `src&#47;ops&#47;*_observation.py` as referenced in the payload contract.  
- **Workflow Officer / Update Officer visibility** — `workflow_officer_state`, `update_officer_ui`; bounded handoff/preview language; no Cockpit start of Workflow Officer.  
- **Traceability registry** — [`DOCS_TRUTH_MAP.md`](../registry/DOCS_TRUTH_MAP.md) for doc drift awareness (not semantic proof).

---

## What Phase E explicitly does **not** claim

| Topic | Clarification |
|-------|----------------|
| **Broker / exchange truth** | Cockpit observations use local artifacts, config, and filesystem where documented — **not** live order books or balances from exchanges. |
| **Go / live approval** | `policy_go_no_go_observation` and inline policy lines are **observation**, not an external approval or unlock. |
| **Workflow handoff / preview** | Rows under `workflow_officer_state` (e.g. handoff/next-step preview) are **bounded excerpts** from officer artifacts — **not** a release go-signal; see operator summary surface. |
| **Audit / evidence “clearance”** | `evidence_audit_observation` and `evidence_state` do **not** assert compliance sign-off. |
| **Session enforcement** | e.g. `session_end_mismatch_state` is local observation; **not** broker-enforced session unlock. |

---

## How operators should read the Cockpit (three layers)

1. **Policy / guard posture (`policy_state`, `guard_state`, `operator_state`)** — Derived from config (when loadable) and kill-switch file observation in the builder; reflects **configuration and local state files** as wired in code, **not** a trading mandate. See payload contract and [`OPS_SUITE_OPERATOR_STATE_REAL_SIGNAL_REVIEW.md`](../specs/OPS_SUITE_OPERATOR_STATE_REAL_SIGNAL_REVIEW.md) (historical note at top).  
2. **Compact observations (`*_observation`)** — Rolled-up **visibility** with `data_source` and schema hints; **not** approvals.  
3. **Workflow / notifier tooling (`workflow_officer_state`, `update_officer_ui`)** — Artifact and notifier **visibility**; **not** policy substitute and **not** execution authority.

Separation rule: if two blocks disagree, **do not** treat the Cockpit as arbiter — resolve using external governance and runbooks.

---

## Canonical anchors (review checklist)

| Anchor | Role |
|--------|------|
| [`OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md`](../specs/OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md) | Top-level keys; observation semantics. |
| [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](../specs/OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md) | Required-view ↔ payload ↔ HTML. |
| [`RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md) | Phases A–E and Ist-Stand narrative. |
| [`DOCS_TRUTH_MAP.md`](../registry/DOCS_TRUTH_MAP.md) | Docs drift pairing for sensitive areas. |
| `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py` | Stable key-set regression (no value snapshots). |
| `tests&#47;webui&#47;test_ops_cockpit.py` | HTML/payload builder behavior coverage (wording/ids where asserted). |

**Human review (Phase E):** Confirm no PR in this line weakens gates, adds hidden write paths, or implies live approval from observation text alone.

---

## Related

- [`OPS_SUITE_DASHBOARD_VNEXT_SPEC.md`](../specs/OPS_SUITE_DASHBOARD_VNEXT_SPEC.md) — product vNext target (non-binding on implementation detail).  
- [`GOVERNANCE_AND_SAFETY_OVERVIEW.md`](../../GOVERNANCE_AND_SAFETY_OVERVIEW.md) — repo-wide governance context.
