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
<<<<<<< HEAD
ATLAS_CHANGED_ENTITY_COUNT=13
ATLAS_CHANGED_RELATION_COUNT=7
=======
ATLAS_CHANGED_ENTITY_COUNT=1
ATLAS_CHANGED_RELATION_COUNT=0
>>>>>>> origin/main
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `ATLAS_LEGACY_ERADICATION_V1`.

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
<<<<<<< HEAD
| `CAPABILITY:market_data_private_state_runtime_convergence_v1` |
| `CONTRACT:p5_10_productive_activation_and_binding_v1` |
| `HOST:wallclock_decision_economics_cycle` |
| `NAVIGATION_INDEX:map_of_truth` |
| `RUNTIME_COMPONENT:ddo_capture_v0` |
| `RUNTIME_COMPONENT:ddo_learning_outcome_ingest_v1` |
| `RUNTIME_COMPONENT:dp_volatility_presence_gate` |
| `RUNTIME_COMPONENT:elementary_direction_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1` |
| `RUNTIME_COMPONENT:m10_productive_parameter_lineage_closure_v1` |
| `RUNTIME_COMPONENT:mv2_canonical_scope` |
| `RUNTIME_COMPONENT:mv2_integrated_replay` |
| `SUBSYSTEM:master_v2` |
=======
| `RUNTIME_COMPONENT:current_productive_persistent_natural_enter_policy_governed_live_c1_continuous_run_v1` |
>>>>>>> origin/main

## CHANGED_RELATIONS

| id |
| --- |
<<<<<<< HEAD
| `REL:r_ddo_capture_observes_integrated_replay` |
| `REL:r_full_core_cycle_observes_elementary_direction` |
| `REL:r_wallclock_calls_ddo_cycle_capture` |
| `REL:r_wallclock_calls_learning_outcome_ingest` |
| `REL:r_wallclock_injects_ddo_capture_session` |
| `REL:r_wallclock_materializes_ddo_o4_via_wp_c_public_plane` |
| `REL:s_wp_c_o4_n_bars_learning_handoff_to_wallclock_ddo` |
=======
| _(none)_ |
>>>>>>> origin/main

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

<<<<<<< HEAD
- PR #6993: dynamic scope authority + productive bridge boundary atlas review; AUTHORITY=NONE; POST_COUNT=0.
- introduced_by=ATLAS_LEGACY_ERADICATION_V1
- modified_by=PR_6993_DYNAMIC_SCOPE_BRIDGE_CLOSURE_V1
=======
- PR #6992: Owner-GO baseline re-pin 959039aa + immutable-surface lineage gate (master_v2 only); productive Level-A re-proof path to S5/HOLD; no Natural Enter in bounded window; MV2/DP unchanged; AUTHORITY=NONE; POST_COUNT=0.
- introduced_by=ATLAS_LEGACY_ERADICATION_V1
- modified_by=PR_6992_GOLDEN_HAPPY_VECTOR_OWNER_GO_LINEAGE_CLOSURE_V1
>>>>>>> origin/main

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
