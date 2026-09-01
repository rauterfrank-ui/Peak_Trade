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
ATLAS_CHANGED_ENTITY_COUNT=16
ATLAS_CHANGED_RELATION_COUNT=2
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
| `BINDER:bound_instrument_v1` |
| `CAPABILITY:cap_2_1_gfu` |
| `CAPABILITY:cap_2_4_runtime_binding` |
| `PHASE:ddo_offline_foundation` |
| `PHASE:z2da` |
| `SELECTOR:single_selected_future_policy` |
| `TERM:ddo_non_semantic_capture` |
| `TERM:ddo_offline_contract_and_ledger` |
| `TERM:ddo_offline_control_plane` |
| `TERM:ddo_offline_evaluation_engine` |
| `TERM:ddo_offline_learning_validation_shadow` |
| `TERM:ddo_offline_owner_bindings_and_drift` |
| `TERM:document_class` |
| `TERM:focused_full_noop` |
| `TERM:information_corpus` |
| `UNIVERSE:governed_futures_universe` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:r_cap21_produces_universe` |
| `REL:r_cap24_binds` |

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
| `CLOSURE:native_instrument_binding` |
| `CLOSURE:productive_selection` |
| `CLOSURE:productive_universe` |

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

- Navigation-only census SHA rebind to current origin/main after WP-FA-01..07, plus TERM:ddo_offline_contract_and_ledger and PHASE:ddo_offline_foundation catalog binding of the already-present offline DDO contract foundation. Parallel to live CURRENT_CANONICAL_SECTION=11.13.5.Z2DA. No Atlas trading, promotion, risk, safety, or execution semantics. Atlas is not canonical authority. Census discovery does not create authority.
- introduced_by=PENDING_CHANGE
- modified_by=PENDING_CHANGE

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
