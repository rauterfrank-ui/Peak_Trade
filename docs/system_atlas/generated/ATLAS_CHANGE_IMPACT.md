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
ATLAS_CHANGED_ENTITY_COUNT=14
ATLAS_CHANGED_RELATION_COUNT=3
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `P5_10_PRODUCTIVE_ACTIVATION_AND_BINDING_V1`.

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
| `CONTRACT:p5_10_productive_activation_and_binding_v1` |
| `CONTRACT:current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1` |
| `CONTRACT:current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1` |
| `CONTRACT:current_mf_n5_isolated_lane_instance_topology_v1` |
| `CONTRACT:p5_10a_layered_tick_merge_epoch_orchestration_contract_v1` |
| `CONTRACT:p5_10b_layered_epoch_remaining_authority_closure_v1` |
| `CONTRACT:p5_1_layered_core_seal_cz4_delegated_replay_v1` |
| `CONTRACT:p5_2_productive_cycle_seam_invoke_and_authority_bind_v1` |
| `CONTRACT:p5_5_o_r2_semantic_authority_contracts_v1` |
| `CONTRACT:p5_7_regime_sidestate_projection_mapping_contract_v1` |
| `CONTRACT:p5_8b_regime_sidestate_projection_phase_authority_v1` |
| `CONTRACT:p5_9d_layered_mechanical_sidestate_fsm_contract_v1` |
| `RUNTIME_COMPONENT:elementary_direction_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:r_full_core_cycle_observes_elementary_direction` |
| `REL:s_fa_occupied_lane_mv2_dp_decision_state_addressing_depends_on_fa_mv2_dp_handoff` |
| `REL:s_fa_occupied_lane_mv2_dp_decision_state_addressing_depends_on_n5_lane_topology` |

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

- P5.10 productive bind wiring closure: productive_cycle_layered_core_bind_wiring_v1 (store + scope gate); governed cursor-backed callers and addressing join reuse explicit kwargs; bootstrap stays legacy until existing_scope; ATLAS_AUTHORITY=NONE.
- introduced_by=P5_10_PRODUCTIVE_ACTIVATION_AND_BINDING_V1
- modified_by=PRODUCTIVE_LAYERED_CORE_BIND_DEFAULT_OR_STORE_WIRING_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
