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
| Incident / Safety (compact observation) | `incident_state.status`, `incident_state.degraded`, `incident_state.requires_operator_attention`, `incident_state.incident_stop_invoked`, `incident_state.entry_permitted`, `incident_state.operator_authoritative_state`; `dependencies_state.summary`, `dependencies_state.telemetry`, `dependencies_state.exchange`, `dependencies_state.degraded` | Same — section **Incident observation (read-only)** |
| Evidence / Freshness (compact observation) | `evidence_state.summary`, `evidence_state.freshness_status`, `evidence_state.audit_trail`, `evidence_state.last_verified_utc`, `evidence_state.source_freshness`, optional `evidence_state.telemetry_evidence` | Same — section **Evidence freshness observation (read-only)** |
| Kompakte Rollups (Truth / Freshness / Sources) | `executive_summary` (nested levels/labels), top-level `truth_status` / `freshness_status` / `source_coverage_status`, `critical_flags`, `unknown_flags` | `_render_status_at_a_glance_inner` (Status-at-a-glance cards) |

### Exposure / Risk (separate card, read-only)

Presentation-only **Exposure State** card in `render_ops_cockpit_html` — observation of existing keys; not approval, not unlock. Cross-check: [`OPS_SUITE_EXPOSURE_READ_MODEL_CONTRACT.md`](OPS_SUITE_EXPOSURE_READ_MODEL_CONTRACT.md).

| Observation | Payload keys (read from `exposure_state` unless noted) |
|-------------|--------------------------------------------------------|
| Summary, treasury, risk | `summary`, `treasury_separation`, `risk_status` |
| Observed values | `observed_exposure`, `observed_ccy`, `data_source`, `last_updated_utc`, `stale` |
| Cross-surface context | `stale_state.exposure` (from `stale_state`), `dependencies_state.summary` (from `dependencies_state`) |
| Caps & breakdown | `caps_configured`, `exposure_by_symbol` (preview) |

### Dependencies / Health-Drift (separate card, read-only)

Presentation-only **Dependencies State** card — `_render_dependencies_state_card_body` in `render_ops_cockpit_html`; existing keys only; not approval, not unlock. Data-quality context: [`OPS_SUITE_DEPENDENCIES_STATE_DATA_QUALITY_REVIEW.md`](OPS_SUITE_DEPENDENCIES_STATE_DATA_QUALITY_REVIEW.md).

| Observation | Payload keys (`dependencies_state`) |
|-------------|--------------------------------------|
| Rollup | `summary`, `exchange`, `telemetry` |
| Optional feed health | `market_data_cache` (shown as `n&#47;a` when absent) |
| Degraded checklist | `degraded` (list preview) |

### Evidence / Audit (separate card, read-only)

Presentation-only **Evidence State** card — `_render_evidence_state_card_body` in `render_ops_cockpit_html`; same payload keys as the compact operator-summary block; not approval, not unlock.

| Observation | Payload keys (`evidence_state`) |
|---------------|----------------------------------|
| Rollup | `summary`, `freshness_status`, `audit_trail`, `last_verified_utc` |
| Source counts | `source_freshness` (`fresh` / `stale` / `older`) |
| Optional | `telemetry_evidence` (shown as `n&#47;a` when absent in payload) |

## Related

- [`OPS_SUITE_DASHBOARD_VNEXT_SPEC.md`](OPS_SUITE_DASHBOARD_VNEXT_SPEC.md) — operator-facing target spec.
- [`RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`](../runbooks/RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md) — phased plan; Folgeslice: Incident/Evidence-Freshness vertieft.

## Code references

- Payload builder: `build_ops_cockpit_payload` in `src/webui/ops_cockpit.py`
- HTML entry: `render_ops_cockpit_html` in `src/webui/ops_cockpit.py`
- Tests: `tests/webui/test_ops_cockpit.py`
