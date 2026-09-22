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
ATLAS_CHANGED_ENTITY_COUNT=3
ATLAS_CHANGED_RELATION_COUNT=2
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `OWNER_GO_FULL_CORE_RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_V1`.

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
| `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1` |
| `GATE:portfolio_capital_reservation_budget_v1` |
| `CONTRACT:current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1` |

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

- PR_6744 MV2 capital context rebind for ENTER Live-29P success path from typed 29P equity (no historical fixture literals); navigation/provenance only; ATLAS_AUTHORITY=NONE.
- introduced_by=OWNER_GO_FULL_CORE_RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_V1
- modified_by=CURRENT_PRODUCTIVE_29P_TO_NEXT_REAL_BLOCKER_REPAIR_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
