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
ATLAS_CHANGED_RELATION_COUNT=2
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `F1_M9_R1_S01_FAILURE_RECOVERY_REPAIR_V1`.

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
| `CONTRACT:current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1` |
| `GATE:portfolio_capital_reservation_budget_v1` |
| `GATE:treasury_productive_read_only_venue_observation_v1` |
| `NAVIGATION_INDEX:map_of_truth` |
| `RUNTIME_COMPONENT:c08_treasury_observed_or_reconciled_capital_productive_sizing_source_binding_v1` |
| `RUNTIME_COMPONENT:c08_treasury_observed_or_reconciled_capital_semantic_authority_closeout_contract_v1` |
| `RUNTIME_COMPONENT:current_productive_available_for_sizing_base_binding_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1` |
| `RUNTIME_COMPONENT:governed_productive_instrument_metadata_authority_producer_v1` |
| `RUNTIME_COMPONENT:governed_productive_reference_price_authority_producer_v1` |
| `RUNTIME_COMPONENT:treasury_phase_2_read_only_venue_observation_binding_v1` |
| `TERM:map_of_truth` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:r_enter_live_29p_join_consumes_portfolio_budget` |
| `REL:s_fa_occupied_lane_governed_cycle_n1_consumer_depends_on_portfolio_budget` |

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

- Treasury Full-Core C08 single-source capital handoff (PR_6827): enter-live delegates one trusted GET through Treasury/E4/C08 to B05 Q0; bounded Full-Core reachability; C08 productive transport authorized; AVAILABLE_FOR_SIZING BASE bound; Q3 unchanged; map partial treasury_full_core_c08_single_source_handoff_v1; TRADING_SEMANTICS_CHANGED=false; LIVE_ENABLED=false; ATLAS_AUTHORITY=NONE.
- introduced_by=F1_M9_R1_S01_FAILURE_RECOVERY_REPAIR_V1
- modified_by=TREASURY_FULL_CORE_C08_SINGLE_SOURCE_HANDOFF_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
