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
ATLAS_CHANGED_RELATION_COUNT=4
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `MARKET_DATA_PRIVATE_STATE_RUNTIME_CONVERGENCE_V1`.

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
| `CAPABILITY:market_data_private_state_runtime_convergence_v1` |
| `SYSTEM:peak_trade` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:s_system_has_md_private_runtime_convergence_v1` |
| `REL:s_wp_c_convergence_depends_on_public_md_runtime` |
| `REL:s_wp_c_convergence_depends_on_private_state_runtime` |
| `REL:s_wp_c_preserves_cap23_selection_owner` |

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

- WP-C adds runtime convergence / consumer closure capability: forensic census, governed public/private handoffs onto WP-A/WP-B canonical facts/state, restart/reconciliation closure proofs, and effective authorization readmodel (observation capability distinct from send authority). No selection, rerank, execution, wire, multi-future, or account-equity sizing authority acquired. Cap 2.3 sole selection owner unchanged. ATLAS_AUTHORITY=NONE.
- introduced_by=MARKET_DATA_PRIVATE_STATE_RUNTIME_CONVERGENCE_V1
- modified_by=MARKET_DATA_PRIVATE_STATE_RUNTIME_CONVERGENCE_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
