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
ATLAS_CHANGED_RELATION_COUNT=7
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `B03_GOVERNANCE_PERSISTENCE_V1`.

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
| `CAPABILITY:cap_2_1_gfu` |
| `CAPABILITY:cap_2_2_ranking` |
| `CAPABILITY:cap_economic_md_input` |
| `CONTRACT:cap22_economic_md_dual_input_v1` |
| `CONTRACT:cap22_offline_policy_candidates_and_evidence_v1` |
| `CONTRACT:peak_trade_ranking_matrix_policy_v1` |
| `SYSTEM:peak_trade` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:s_cap22_depends_cap21` |
| `REL:s_cap22_governed_by_economic_md_dual_input` |
| `REL:s_cap22_governed_by_offline_policy_candidates_and_evidence` |
| `REL:s_cap22_governed_by_peak_trade_ranking_matrix_policy_v1` |
| `REL:s_economic_md_governed_by_dual_input` |
| `REL:s_system_has_cap22` |
| `REL:s_system_has_economic_md_input` |

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

- B03 Peak Trade ranking matrix policy v1 governance persist (PR #6833): CONTRACT:peak_trade_ranking_matrix_policy_v1; Cap 2.2 policy ratified; CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false; PRODUCTIVE_ECONOMIC_RANK_ACTIVATION=false; ECONOMIC_RANK_ACTIVATED=false; INPUT2_MAX_AGE_SECONDS_RATIFIED=false; Cap 2.3 sole selection owner unchanged; no B04/B05/B06 runtime; TRADING_SEMANTICS_CHANGED=false; ATLAS_AUTHORITY=NONE.
- introduced_by=B03_GOVERNANCE_PERSISTENCE_V1
- modified_by=B03_GOVERNANCE_PERSISTENCE_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
