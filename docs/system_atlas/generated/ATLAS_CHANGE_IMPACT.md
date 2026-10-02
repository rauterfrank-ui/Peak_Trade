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
ATLAS_CHANGED_ENTITY_COUNT=7
ATLAS_CHANGED_RELATION_COUNT=0
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
| `CONTRACT:current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1` |
| `RUNTIME_COMPONENT:current_productive_persistent_natural_enter_convergence_v1` |
| `RUNTIME_COMPONENT:current_productive_persistent_natural_enter_policy_governed_live_c1_continuous_run_v1` |
| `RUNTIME_COMPONENT:current_productive_synthetic_enter_forensic_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1` |
| `RUNTIME_COMPONENT:ghv_pre_external_continuation_harness_v1` |
| `RUNTIME_COMPONENT:ghv_pre_external_runtime_flight_recorder_v1` |

## CHANGED_RELATIONS

| id |
| --- |
| _(none)_ |

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

- PR #7014: default-off GHV PRE_EXTERNAL runtime flight recorder + continuation snapshot/harness; observation-only wiring at composition root, venue plan, synthetic overlay, and N5 join; capture failures do not change decisions; AUTHORITY=NONE; POST_COUNT=0.
- introduced_by=ATLAS_LEGACY_ERADICATION_V1
- modified_by=PR_7014_GHV_RUNTIME_FLIGHT_RECORDER_CONTINUATION_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
