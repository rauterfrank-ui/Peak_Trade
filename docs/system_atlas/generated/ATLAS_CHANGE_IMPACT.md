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
ATLAS_CHANGED_ENTITY_COUNT=6
ATLAS_CHANGED_RELATION_COUNT=19
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
| `CONTRACT:current_mf_n5_instrument_runtime_identity_closure_v1` |
| `CONTRACT:current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1` |
| `CONTRACT:current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1` |
| `CONTRACT:current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1` |
| `CONTRACT:current_mf_n5_isolated_lane_instance_topology_v1` |
| `CONTRACT:current_mf_n5_recovered_topology_consumer_join_v1` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:r_current_mf_n5_lane_topology_calls_pinned_cap23_adapter` |
| `REL:r_current_mf_n5_lane_topology_consumes_mf_membership_semantics` |
| `REL:r_durable_lane_assignment_persistence_loads_n5_lane_topology` |
| `REL:r_durable_lane_assignment_persistence_persists_n5_lane_topology` |
| `REL:r_occupied_lane_pin_consumer_calls_n5_lane_topology` |
| `REL:r_occupied_lane_pin_consumer_calls_recovered_topology_consumer` |
| `REL:r_recovered_topology_consumer_calls_durable_lane_assignment` |
| `REL:r_recovered_topology_consumer_calls_n5_lane_topology` |
| `REL:s_current_mf_n5_lane_topology_depends_on_mf_membership_semantics` |
| `REL:s_current_mf_n5_lane_topology_optionally_uses_pinned_cap23_adapter` |
| `REL:s_fa_occupied_lane_governed_cycle_n1_consumer_depends_on_portfolio_budget` |
| `REL:s_fa_occupied_lane_governed_cycle_n1_consumer_depends_on_s8_addressing` |
| `REL:s_fa_occupied_lane_mv2_dp_decision_state_addressing_depends_on_fa_mv2_dp_handoff` |
| `REL:s_fa_occupied_lane_mv2_dp_decision_state_addressing_depends_on_n5_lane_topology` |
| `REL:s_fa_productive_runtime_orchestrator_depends_on_mv2_dp_handoff` |
| `REL:s_fa_productive_runtime_orchestrator_depends_on_n1_host_join_readiness` |
| `REL:s_fa_productive_runtime_orchestrator_depends_on_portfolio_budget` |
| `REL:s_recovered_topology_consumer_depends_on_durable_lane_assignment` |
| `REL:s_recovered_topology_consumer_depends_on_n5_lane_topology` |

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

- PR #6990 N5 instrument runtime identity closure: new CONTRACT closure package, orchestrator bind-only ingress, topology/recovered/N1 consumer threading; reviewed productive_selection closure coupling and dependent N5 lane relations; no Cap23/Cap24/POST authority; AUTHORITY=NONE; POST_COUNT=0.
- introduced_by=ATLAS_LEGACY_ERADICATION_V1
- modified_by=PR_6990_N5_INSTRUMENT_RUNTIME_IDENTITY_CLOSURE_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
