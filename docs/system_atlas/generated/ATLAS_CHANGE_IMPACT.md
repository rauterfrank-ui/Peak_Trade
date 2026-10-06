<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

# Atlas Change Impact

This view is topology change-coupling, not canonical authority.

```text
ATLAS_IMPACT=UPDATED
ATLAS_CHANGED_ENTITY_COUNT=12
ATLAS_CHANGED_RELATION_COUNT=8
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `CHANGE:pr_7077_monetary_normalization_implementation_v1`.

## Workflow

1. Implement the code.
2. Add/update machine-readable Atlas records (relations, evidence, closures).
3. Regenerate views (`generate_system_atlas_v1.py`).
4. Validate (`validate_system_atlas_v1.py`).
5. Run the impact checker.
6. Report `ATLAS_IMPACT=UPDATED` or `ATLAS_IMPACT=NONE_WITH_PROOF`.

Do not manually patch generated Markdown.

## CHANGED_ENTITIES

| id |
| --- |
| `RUNTIME_COMPONENT:governed_productive_monetary_normalization_v1` |
| `CAPABILITY:okx_eea_private_account_state_runtime_v1` |
| `CONTRACT:current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1` |
| `GATE:full_core_capital_admission_v1` |
| `GATE:full_core_fresh_pretrade_runtime_get_v1` |
| `GATE:full_core_live_account_bound_v1` |
| `GATE:full_core_owner_one_shot_permit_v1` |
| `GATE:portfolio_capital_reservation_budget_v1` |
| `RUNTIME_COMPONENT:current_productive_forensic_executable_quantity_override_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1` |
| `RUNTIME_COMPONENT:governed_productive_instrument_metadata_authority_producer_v1` |
| `RUNTIME_COMPONENT:governed_productive_reference_price_authority_producer_v1` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:r_enter_live_29p_join_consumes_portfolio_budget` |
| `REL:r_full_core_capital_admission_composes_live_account_bound` |
| `REL:r_full_core_fresh_pretrade_get_composes_permit` |
| `REL:r_full_core_live_account_bound_composes_fresh_get` |
| `REL:r_full_core_path_calls_fresh_pretrade_runtime_get` |
| `REL:r_full_core_path_calls_live_account_bound` |
| `REL:s_fa_occupied_lane_governed_cycle_n1_consumer_depends_on_portfolio_budget` |
| `REL:s_private_state_runtime_adapts_fresh_pretrade_get` |

## NEW_RELATIONS

| id |
| --- |
| _(none)_ |

## REMOVED_RELATIONS

| id |
| --- |
| _(none)_ |

## AFFECTED_DEPENDENCY_CLOSURES

| id |
| --- |
| _(none)_ |

## AFFECTED_OKX_SURFACES

| id |
| --- |
| _(none)_ |

## AFFECTED_SAFETY_SURFACES

| id |
| --- |
| _(none)_ |

## AFFECTED_SCHEMAS

| id |
| --- |
| _(none)_ |

## REVIEW_REQUIRED_ITEMS

| item |
| --- |
| _(none)_ |

## Notes

- PR #7077: productive monetary normalization (USDT→USDC via index-tickers GET) at Fresh Pretrade + Enter-Live-29P before CRS; no trading authority change; AUTHORITY=NONE; POST_COUNT=0.
- introduced_by=CHANGE:pr_7077_monetary_normalization_implementation_v1
- modified_by=CHANGE:pr_7077_monetary_normalization_implementation_v1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
