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
ATLAS_CHANGED_ENTITY_COUNT=2
ATLAS_CHANGED_RELATION_COUNT=0
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
| `RUNTIME_COMPONENT:f1_m9_prospective_candidate_selection_campaign_execution_v1` |
| `RUNTIME_COMPONENT:f1_m9_governed_productive_apply_preparation_and_selection_policy_stack_v1` |

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

- F1/M9 prospective candidate-selection campaign execution owner max-build (PR #6797): EXECUTION_PROOF and authorized-path gates; runtime authorization schema; no terminal REAL-MD orchestration; CAMPAIGN_EXECUTED=false; REAL_PRODUCTIVE_APPLY_AUTHORIZED=false. EXTERNAL_EFFECT_COUNT=0. ATLAS_AUTHORITY=NONE.
- F1/M9 authorized campaign run orchestration owner: terminal lifecycle owner `authorized_run_orchestration_v1`; hermetic terminal proof in tests; build-slice binds without REAL effects; CAMPAIGN_EXECUTED=false. ATLAS_AUTHORITY=NONE.
- introduced_by=F1_M9_R1_S01_FAILURE_RECOVERY_REPAIR_V1
- modified_by=F1_M9_PROSPECTIVE_CAMPAIGN_AUTHORIZED_RUN_ORCHESTRATION_OWNER_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
