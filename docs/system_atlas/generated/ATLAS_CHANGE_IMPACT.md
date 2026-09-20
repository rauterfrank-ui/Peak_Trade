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
ATLAS_CHANGED_ENTITY_COUNT=1
ATLAS_CHANGED_RELATION_COUNT=4
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `PENDING_PR_DEPOSIT_TO_AVAILABLE_FOR_SIZING_E4_S1`.

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
| `RUNTIME_COMPONENT:treasury_capital_admission_to_account_equity_orchestration_v1` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:r_treasury_e4_consumes_phase2_capital_admission_join` |
| `REL:r_treasury_e4_feeds_account_equity_orchestration_ingress` |

## NEW_RELATIONS

| id |
| --- |
| `REL:r_treasury_e4_consumes_phase2_capital_admission_join` |
| `REL:r_treasury_e4_feeds_account_equity_orchestration_ingress` |

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

- WP DEPOSIT_TO_AVAILABLE_FOR_SIZING_FIRST_MISSING_EDGE_V1: E4 binding from TreasuryCapitalAdmissionJoinV1 to AccountEquityOrchestrationIngressV1. No STEP-29P, sizing, or execution authority. Atlas is not canonical authority.
- introduced_by=PENDING_PR_DEPOSIT_TO_AVAILABLE_FOR_SIZING_E4_S1
- modified_by=PENDING_PR_DEPOSIT_TO_AVAILABLE_FOR_SIZING_E4_S1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
