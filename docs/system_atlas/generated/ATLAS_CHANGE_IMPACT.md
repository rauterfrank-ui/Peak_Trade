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
ATLAS_CHANGED_RELATION_COUNT=0
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `CHANGE:ghv_current_pilot_post_guarded_enter_admission_v1`.

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
| `CONTRACT:current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1` |
| `CONTRACT:current_productive_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_boundary_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1` |
| `RUNTIME_COMPONENT:full_core_pre_post_capital_guard_join_v1` |

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

- GHV pilot guarded Enter-POST admission stack on productive actual-venue one-shot join: mandatory NEW-RISK enter-post admission, pilot capital-guard binding, one-shot post-admission seal before permit mint, reduce-only envelope provenance guard on send seam; offline adversarial tests; no Live/Testnet activation; standing Owner-GO pins unchanged; GHV_AUTHORITY=NONE; AUTHORITY=NONE; POST_COUNT=0; ATLAS_AUTHORITY=NONE.
- introduced_by=CHANGE:ghv_current_pilot_post_guarded_enter_admission_v1
- modified_by=CHANGE:ghv_current_pilot_post_guarded_enter_admission_v1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
