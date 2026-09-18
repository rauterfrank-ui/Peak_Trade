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
| `GATE:full_core_fresh_pretrade_runtime_get_v1` |
| `GATE:full_core_live_account_bound_v1` |
| `GATE:full_core_owner_one_shot_permit_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:r_full_core_fresh_pretrade_get_composes_permit` |
| `REL:r_full_core_live_account_bound_composes_fresh_get` |
| `REL:r_full_core_path_calls_fresh_pretrade_runtime_get` |

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
| `GATE:full_core_fresh_pretrade_runtime_get_v1` |

## AFFECTED_SCHEMAS

| id |
| --- |
| _(none)_ |

## REVIEW_REQUIRED_ITEMS

| item |
| --- |
| _(none)_ |

## Notes

- S1 DataSafety source_kind stamp at productive venue GET (PR 6584). FreshPretradeGetTransportResultV1.data_safety_source_kind default None. REAL only from FullCoreProductiveReadOnlyGetTransportV1.get with direct eea.okx.com acquisition evidence. Injected/failed remain unbound. No DataSafetyGate join, no usage_context, no V5/C1 carrier, no activation. Atlas is not canonical authority.
- introduced_by=PENDING_CHANGE
- modified_by=PENDING_CHANGE

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
