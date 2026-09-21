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
ATLAS_CHANGED_ENTITY_COUNT=3
ATLAS_CHANGED_RELATION_COUNT=3
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `FULL_CORE_P1_MAX_EVIDENCE_CAMPAIGN_TO_NEXT_REAL_BLOCKER_V1`.

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
| `RUNTIME_COMPONENT:p1_max_evidence_campaign_to_next_real_blocker_v1` |
| `RUNTIME_COMPONENT:p1_completeness_witness_foundation_v1` |
| `RUNTIME_COMPONENT:p1_negative_completeness_closeout_contract_v1` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:r_p1_max_evidence_campaign_consumes_witness_foundation` |
| `REL:r_p1_negative_completeness_closeout_consumes_witness_foundation` |

## NEW_RELATIONS

| id |
| --- |
| `REL:r_p1_max_evidence_campaign_consumes_witness_foundation` |

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
| `DATA_CONTRACT:p1_max_evidence_campaign_to_next_real_blocker_v1` |
| `DATA_CONTRACT:p1_completeness_witness_foundation_v1` |

## REVIEW_REQUIRED_ITEMS

| item |
| --- |
| _(none)_ |

## Notes

- P1 max evidence campaign: one bounded read-only interest-accrued GET, campaign witness adjudication pack, #6666 witness consumption extension, #6665 re-evaluation. No governance ratification; no trading semantics change. Atlas is not canonical authority.
- introduced_by=FULL_CORE_P1_MAX_EVIDENCE_CAMPAIGN_TO_NEXT_REAL_BLOCKER_V1
- modified_by=FULL_CORE_P1_MAX_EVIDENCE_CAMPAIGN_TO_NEXT_REAL_BLOCKER_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
