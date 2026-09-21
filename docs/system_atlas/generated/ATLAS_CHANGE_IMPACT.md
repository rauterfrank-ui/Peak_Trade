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
ATLAS_CHANGED_RELATION_COUNT=5
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `FULL_CORE_P1_LIABILITY_GOVERNANCE_AND_MAX_CLOSEOUT_TO_NEXT_REAL_BLOCKER_V1`.

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
| `RUNTIME_COMPONENT:p1_liability_event_class_governance_and_ratified_query_class_set_v1` |
| `RUNTIME_COMPONENT:p1_bounded_query_traversal_completeness_witness_v1` |
| `RUNTIME_COMPONENT:p1_completeness_witness_foundation_v1` |
| `RUNTIME_COMPONENT:p1_negative_completeness_closeout_contract_v1` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:r_p1_liability_governance_witness_consumes_witness_foundation` |
| `REL:r_p1_bounded_traversal_witness_consumes_witness_foundation` |
| `REL:r_p1_negative_completeness_closeout_consumes_witness_foundation` |

## NEW_RELATIONS

| id |
| --- |
| `REL:r_p1_liability_governance_witness_consumes_witness_foundation` |
| `REL:r_p1_bounded_traversal_witness_consumes_witness_foundation` |

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
| `GET_&#47;api&#47;v5&#47;account&#47;interest-accrued` |

## AFFECTED_SAFETY_SURFACES

| id |
| --- |
| _(none)_ |

## AFFECTED_SCHEMAS

| id |
| --- |
| `DATA_CONTRACT:p1_liability_event_class_governance_and_ratified_query_class_set_v1` |
| `DATA_CONTRACT:p1_bounded_query_traversal_completeness_witness_v1` |
| `DATA_CONTRACT:p1_completeness_witness_foundation_v1` |

## REVIEW_REQUIRED_ITEMS

| item |
| --- |
| _(none)_ |

## Notes

- P1 liability event-class governance and bounded query traversal witnesses: offline ratified interest-accrued Market-loan query class without global EQUITY_STOCK kind-set uplift; pagination query-traversal and vacuous ordering for zero-row bound queries; #6666 root extensions; #6665 re-evaluation. Observation freshness and restart durability remain open. No trading semantics change. Atlas is not canonical authority.
- introduced_by=FULL_CORE_P1_LIABILITY_GOVERNANCE_AND_MAX_CLOSEOUT_TO_NEXT_REAL_BLOCKER_V1
- modified_by=FULL_CORE_P1_LIABILITY_GOVERNANCE_AND_MAX_CLOSEOUT_TO_NEXT_REAL_BLOCKER_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
