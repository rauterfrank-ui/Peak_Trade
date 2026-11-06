# Market Dashboard MISSING_SOURCE / NOT_BOUND Inventory V1

Generated: 2026-08-04T18:30:57.619368Z
Base: `0a3df4827e675c41b8c51cea3d2baea34ef52eee`
Dashboard: http://127.0.0.1:8000/market

## Counts

- TOTAL_PRESENTATION_ELEMENTS_INVENTORIED=73
- TOTAL_MISSING_SOURCE_COUNT=50
- TOTAL_NOT_BOUND_COUNT=18
- SOURCE_FAMILY_COUNT=16
- RESOLVABLE_SOURCE_FAMILY_COUNT=1
- BLOCKED_SOURCE_FAMILY_COUNT=15

## Selected Source Family

`universe_selection_rail_facts`

Canonical source: `readmodels&#47;universe_selection_readmodel.v1.json` (PRESENT)

Members to bind from existing fields only:
- Watchlist ← universe row count
- Rank ← selected instrument rank
- Session ← source_run_id
- Selection Reason ← selected_future.selection_reason

## Source Families

- `universe_selection_rail_facts` [RESOLVABLE] count=4 category=existing_canonical_source_frontend_mapping_missing value=HIGH
- `canonical_decision` [BLOCKED] count=5 category=canonical_source_genuinely_unavailable value=HIGH
- `double_play` [BLOCKED] count=3 category=canonical_source_genuinely_unavailable value=HIGH
- `dynamic_scope` [BLOCKED] count=5 category=canonical_source_genuinely_unavailable value=HIGH
- `regime_bull_bear_switch` [BLOCKED] count=5 category=canonical_source_genuinely_unavailable value=HIGH
- `risk_sizing_capital` [BLOCKED] count=8 category=canonical_source_genuinely_unavailable value=HIGH
- `safety_authority` [BLOCKED] count=3 category=canonical_source_genuinely_unavailable value=HIGH
- `execution_reconciliation` [BLOCKED] count=7 category=canonical_source_genuinely_unavailable value=MEDIUM
- `economic_summary` [BLOCKED] count=13 category=canonical_source_genuinely_unavailable value=MEDIUM
- `diagnostics_summary_intentional_unbound` [BLOCKED] count=5 category=presentation_element_intentionally_unbound value=LOW
- `autonomy_stage_intentional_unbound` [BLOCKED] count=9 category=presentation_element_intentionally_unbound value=LOW
- `decision_strip_blockers_unbound` [BLOCKED] count=1 category=existing_endpoint_frontend_mapping_missing value=MEDIUM
- `decision_strip_confidence_intentional_unbound` [BLOCKED] count=1 category=presentation_element_intentionally_unbound value=LOW
- `source_health_aggregate` [BLOCKED] count=1 category=stale_or_malformed_source_fallback value=LOW
- `repository_sha_no_canonical_payload_field` [BLOCKED] count=1 category=canonical_source_genuinely_unavailable value=LOW
- `timeline_intentional_unbound` [BLOCKED] count=1 category=presentation_element_intentionally_unbound value=LOW
