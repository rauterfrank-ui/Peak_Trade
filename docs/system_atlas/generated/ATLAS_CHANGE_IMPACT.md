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
ATLAS_CHANGED_ENTITY_COUNT=13
ATLAS_CHANGED_RELATION_COUNT=3
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `PENDING_CHANGE`.

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
| `FORENSIC_REFERENCE:information_corpus_persistence_base` |
| `FUNCTIONAL_CORE:double_play` |
| `GUARD:economic_diagnostic_optimization_boundary` |
| `NAVIGATION_INDEX:map_of_truth` |
| `RUNBOOK:canonical_master_runbook` |
| `RUNBOOK:vollautonomie_v4_4_12` |
| `RUNTIME_COMPONENT:ddo_capture_v0` |
| `RUNTIME_COMPONENT:dp_offline_scenario_replay` |
| `RUNTIME_COMPONENT:dp_state` |
| `RUNTIME_COMPONENT:mv2_integrated_replay` |
| `SUBSYSTEM:master_v2` |
| `TERM:dynamic_scope` |
| `TERM:map_of_truth` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:a_map_documents_runbook` |
| `REL:r_ddo_capture_observes_integrated_replay` |
| `REL:s_map_navigates_runbook` |

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
| `CLOSURE:live_readiness` |

## AFFECTED_OKX_SURFACES

| id |
| --- |
| _(none)_ |

## AFFECTED_SAFETY_SURFACES

| id |
| --- |
| `GUARD:economic_diagnostic_optimization_boundary` |

## AFFECTED_SCHEMAS

| id |
| --- |
| _(none)_ |

## REVIEW_REQUIRED_ITEMS

| item |
| --- |
| _(none)_ |

## Notes

- Directional mapping runtime bind: SHORT reversal polarity and PENDING departing-side generator orientation now consume the §5 TARGET. Active fifth-class slice grant is digest-bound to the current diff base. Freeze exception unauthorized. MODEL_C runtime unauthorized. ARMED residual unresolved. last_active_side bind unauthorized. MODEL_B remains the productive baseline. CLOSURE:live_readiness is inspected because MOT documents the runbook; this pointer does not authorize Live. Atlas is not canonical authority.
- introduced_by=PENDING_CHANGE
- modified_by=PENDING_CHANGE

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
