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
ATLAS_CHANGED_RELATION_COUNT=5
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `B11_OPERATOR_PROFILE_AND_EXPLAINABILITY_V1`.

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
| `CAPABILITY:cap_2_2_ranking` |
| `CAPABILITY:cap_2_3_single_selected_future` |
| `CAPABILITY:cap_2_4_runtime_binding` |
| `CAPABILITY:cap22_peak_trade_ranking_runtime_v1` |
| `CAPABILITY:future_profile_snapshot_v1` |
| `CAPABILITY:operator_profile_explainability_v1` |
| `SYSTEM:peak_trade` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:s_system_has_b11_operator_profile_explainability` |
| `REL:s_b11_operator_view_depends_on_b07_future_profile` |
| `REL:s_b11_operator_view_depends_on_b06_ranking_witness` |
| `REL:s_b11_operator_view_depends_on_cap23_selection` |
| `REL:s_b11_operator_view_depends_on_cap24_binding` |

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

- B11 records an operator-facing selected Future profile and explainability projection over existing authoritative upstream facts: B07 Future Profile, B06 ranking explainability witness, Cap 2.3 selection, and Cap 2.4 binding evidence. The view is observability only. It does not recompute features, rescore, rerank, reselect, promote PROFILE_ONLY or UNCLASSIFIED fields, create ranking/selection/binding/live/execution/multi-future/cross-universe authority, or start B12. Cap 2.3 remains sole selection owner; Cap 2.4 remains binding boundary; MAX_POSITIONS_EFFECTIVE remains 1. ATLAS_AUTHORITY=NONE.
- introduced_by=B11_OPERATOR_PROFILE_AND_EXPLAINABILITY_V1
- modified_by=B11_OPERATOR_PROFILE_AND_EXPLAINABILITY_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
