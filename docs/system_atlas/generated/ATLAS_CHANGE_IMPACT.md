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

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `CHANGE:pr_7099_phase7_evidence_binding_v1`.

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
| `RUNTIME_COMPONENT:full_core_exchange_reconciliation_integration_v1` |
| `RUNTIME_COMPONENT:full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1` |
| `RUNTIME_COMPONENT:full_core_orchestrated_post_submit_lifecycle_reconciliation_v1` |
| `RUNTIME_COMPONENT:full_core_post_completed_hook_evidence_v1` |
| `RUNTIME_COMPONENT:full_core_post_submit_exchange_reconciliation_lifecycle_join_v1` |
| `RUNTIME_COMPONENT:ghv_current_okx_phase7_readiness_adjudication_v1` |
| `RUNTIME_COMPONENT:ghv_current_okx_productive_read_only_reconciliation_get_validation_v1` |

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

- PR #7099: Phase-7 evidence-bound productive OKX GET validation gates (offline reproof + adversarial manifest/review); post-squash review baseline ancestor semantics; spec cross-references only for Full-Core reconciliation entities; no productive provider wiring; GHV_AUTHORITY=NONE; AUTHORITY=NONE; POST_COUNT=0; ATLAS_AUTHORITY=NONE.
- introduced_by=CHANGE:pr_7099_phase7_evidence_binding_v1
- modified_by=CHANGE:pr_7099_phase7_evidence_binding_v1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
