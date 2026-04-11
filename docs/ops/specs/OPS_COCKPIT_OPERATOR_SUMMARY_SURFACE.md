# OPS Cockpit — Operator Summary Surface (vNext-aligned)

**status:** active  
**last_updated:** 2026-04-11  
**purpose:** Map OPS Suite / Dashboard vNext „Required Views“ (Teilmenge) to the JSON payload served at `GET &#47;api&#47;ops-cockpit` (same shape as the `/ops` HTML page) and HTML render helpers — read-only, no execution authority.

**docs_token:** `DOCS_TOKEN_OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE`

## Non-Goals

- No live unlock, no approval semantics, no gate weakening.
- No new API routes; payload semantics unchanged (presentation-only HTML).

## Required View ↔ Payload ↔ Render

| vNext Required View (Auszug) | Payload keys (observation) | HTML / helper |
|------------------------------|------------------------------|----------------|
| System State | `system_state.mode`, `system_state.execution_model`; optional Kurzbezug: `dependencies_state.summary`, `evidence_state.summary` | `src/webui/ops_cockpit.py` — `_render_operator_summary_surface`, section **System status (observation)** |
| Go / No-Go (observation, not approval) | `policy_state.action`, `policy_state.blocked`, `incident_state.summary`, `incident_state.requires_operator_attention`, kill-switch flags in payload | Same — section **Go / No-Go observation (not approval)** |
| Kompakte Rollups (Truth / Freshness / Sources) | `executive_summary` (nested levels/labels), top-level `truth_status` / `freshness_status` / `source_coverage_status`, `critical_flags`, `unknown_flags` | `_render_status_at_a_glance_inner` (Status-at-a-glance cards) |

## Related

- [`OPS_SUITE_DASHBOARD_VNEXT_SPEC.md`](OPS_SUITE_DASHBOARD_VNEXT_SPEC.md) — operator-facing target spec.
- [`RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](../runbooks/RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md) — phased plan; Folgeslice: Incident/Evidence-Freshness vertieft.

## Code references

- Payload builder: `build_ops_cockpit_payload` in `src/webui/ops_cockpit.py`
- HTML entry: `render_ops_cockpit_html` in `src/webui/ops_cockpit.py`
- Tests: `tests/webui/test_ops_cockpit.py`
