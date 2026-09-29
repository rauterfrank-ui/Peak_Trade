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
| `RUNTIME_COMPONENT:od_29p_fresh_trusted_numeric_venue_bind_canonical_adjudication_v1` |
| `RUNTIME_COMPONENT:od_u01_p01_29p_sizing_mint_canonical_adjudication_v1` |

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

- PR #6962: OD U01/P01 three-input 29P sizing-mint adjudication (CASE D); catalog entity for od_u01_p01; od_29p successor mint-precondition link; Law Map/CSIA navigation only; no GET/POST; AUTHORITY=NONE.
- introduced_by=ATLAS_LEGACY_ERADICATION_V1
- modified_by=OD_U01_P01_29P_SIZING_MINT_CANONICAL_ADJUDICATION_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
