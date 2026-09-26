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
ATLAS_CHANGED_ENTITY_COUNT=4
ATLAS_CHANGED_RELATION_COUNT=2
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `UNIFIED_BLUEPRINT_PHASE_8_MI_TO_LEARNING_INTEGRATION_V1`.

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
| `RUNTIME_COMPONENT:unified_blueprint_d01_d02_topology_adjudication_v1` |
| `RUNTIME_COMPONENT:unified_blueprint_phase_8_mi_to_learning_integration_v1` |
| `CAPABILITY:market_intelligence_forecast_calibration_offline_stack_v1` |
| `NAVIGATION_INDEX:map_of_truth` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:s_map_navigates_unified_blueprint_d01_d02_topology_adjudication_v1` |
| `REL:s_map_navigates_unified_blueprint_phase_8_mi_to_learning_integration_v1` |

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

- Unified Blueprint Phase 8 closes d02_mi_to_learning typed MI→Learning export path; updates D02 adjudication and interaction map edge mi_offline_typed_export_to_learning_path. AUTHORITY=NONE.
- introduced_by=UNIFIED_BLUEPRINT_PHASE_8_MI_TO_LEARNING_INTEGRATION_V1
- modified_by=UNIFIED_BLUEPRINT_PHASE_8_MI_TO_LEARNING_INTEGRATION_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
