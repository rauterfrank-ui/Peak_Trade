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
ATLAS_CHANGED_ENTITY_COUNT=157
ATLAS_CHANGED_RELATION_COUNT=23
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
| `ACRONYM:C1` |
| `ACRONYM:C2` |
| `ACRONYM:C3` |
| `ACRONYM:CAP` |
| `ACRONYM:CAP23` |
| `ACRONYM:DOD` |
| `ACRONYM:MMR` |
| `ACRONYM:PENDING` |
| `ACRONYM:SSOT` |
| `ADAPTER:kraken_live_client` |
| `CAPABILITY:cap_11_13_5_live_canary` |
| `CAPABILITY:cap_7_2_stateful_no_order` |
| `CFG:live_authorized` |
| `CFG:max_positions` |
| `CFG:testnet_authorized` |
| `DATA_CONTRACT:full_core_live_path_models_v1` |
| `DOD:capability_closure_standard` |
| `DOD:cybersecurity_runbook` |
| `DOD:program_final` |
| `DOD:vollautonomie_economic_validity` |
| `DOD:vollautonomie_safety_runtime` |
| `DOD:vollautonomie_trading_logic` |
| `EP:full_core_live_path_offline` |
| `FUNCTIONAL_CORE:double_play` |
| `GATE:full_core_live_path_execution_boundary_halt_before_wire_v1` |
| `GATE:full_core_live_path_frozen_pretrade_conjunction_v1` |
| `GATE:full_core_live_path_identity_v1` |
| `GATE:full_core_live_path_restart_gate_v1` |
| `GATE:full_core_live_path_standing_live_gates_v1` |
| `GATE:full_core_owner_one_shot_permit_v1` |
| `GATE:treasury_phase_1_offline_contracts_v1` |
| `GATE:live_authorized_false` |
| `GATE:max_positions_1` |
| `HOST:cap72_stateful_host` |
| `KIND:ACRONYM` |
| `KIND:DOD` |
| `KIND:FUNCTIONAL_CORE` |
| `KIND:MMR` |
| `KIND:SYSTEM` |
| `NAVIGATION_INDEX:map_of_truth` |
| `OWNER_DECISION:cap23_exclusive_selection` |
| `PHASE:authenticated_private_runtime_read_and_runtime_permit_issuance` |
| `PHASE:authenticated_productive_transport` |
| `PHASE:ddo_offline_foundation` |
| `PHASE:g12_canonical_delayed_zero_persist_and_pending_related_observations` |
| `PHASE:g12_delayed_posid_zero_row_full_conjunction_proof_contract` |
| `PHASE:p08_distinct_first_party_evidence` |
| `PHASE:p08_empty_data_not_zero` |
| `PHASE:p08_nonzero_position_adjudication_persist_close` |
| `PHASE:p08_position_observation` |
| `PHASE:p08_post_read_only_exhaustion_authority_boundary` |
| `PHASE:p08_read_only_closure` |
| `PHASE:p10_target_position_qty_unit_forensic_adjudicate_persist` |
| `PHASE:p11_pos_to_sz_unit_identity_independent_proof` |
| `PHASE:p12_execution_prerequisite_11_position_side_posside` |
| `PHASE:p13_execution_prerequisite_12_exact_flatten_payload` |
| `PHASE:p16_execution_prerequisite_16_bounded_activation` |
| `PHASE:p20_execution_prerequisite_20_mutation_limited_to_proven_position` |
| `PHASE:p25_execution_prerequisite_25_no_additional_owner_decision` |
| `PHASE:post_z2ds_50110_egress_capture` |
| `PHASE:post_z2ds_50110_whitelist_add_from_capture` |
| `PHASE:post_z2ds_post_whitelist_private_auth_attestation` |
| `PHASE:pr_6252_merge_closeout` |
| `PHASE:productive_flatten_post_and_reconciliation` |
| `PHASE:remaining_execution_path_end_to_end_census` |
| `PHASE:section_11_14_live_accounting_reconstructed_adjudication` |
| `PHASE:section_11_14_live_execution_code_exists_adjudication` |
| `PHASE:section_11_14_live_execution_path_reachable_adjudication` |
| `PHASE:section_11_14_live_fee_observed_adjudication` |
| `PHASE:section_11_14_live_fill_observed_adjudication` |
| `PHASE:section_11_14_live_order_plan_observed_adjudication` |
| `PHASE:section_11_14_live_position_reconciled_adjudication` |
| `PHASE:section_11_14_live_private_read_only_proven_adjudication` |
| `PHASE:section_11_14_live_restart_reconstructed_adjudication` |
| `PHASE:section_11_14_live_submit_ack_contract_and_mutation_boundary_forensic_adjudication` |
| `PHASE:section_11_14_live_submit_ack_observed_adjudication` |
| `PHASE:section_11_14_live_submit_ack_observed_proof_criterion` |
| `PHASE:section_11_14_offline_evidence_ladder_surface` |
| `PHASE:send_time_pass_18_19_21_24` |
| `PHASE:send_time_position_reobservation` |
| `PHASE:z2cn` |
| `PHASE:z2co` |
| `PHASE:z2cp` |
| `PHASE:z2cq` |
| `PHASE:z2cr` |
| `PHASE:z2cs` |
| `PHASE:z2ct` |
| `PHASE:z2cu` |
| `PHASE:z2cv` |
| `PHASE:z2cw` |
| `PHASE:z2cx` |
| `PHASE:z2cy` |
| `PHASE:z2cz` |
| `PHASE:z2da` |
| `PHASE:z2dn` |
| `PHASE:z2do` |
| `PHASE:z2dp` |
| `PHASE:z2dq` |
| `PHASE:z2dr` |
| `PHASE:z2ds` |
| `RUNBOOK:canonical_master_runbook` |
| `RUNBOOK:vollautonomie_v4_4_12` |
| `RUNTIME_COMPONENT:authenticated_private_runtime_read_and_runtime_permit_issuance_v1` |
| `RUNTIME_COMPONENT:authenticated_productive_transport_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_canary_isolation_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_venue_translation_v1` |
| `RUNTIME_COMPONENT:g12_canonical_delayed_zero_persist_and_pending_related_observations_v1` |
| `RUNTIME_COMPONENT:g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1` |
| `RUNTIME_COMPONENT:offline_execution_permission_and_position_creation_producer_wiring_v1` |
| `RUNTIME_COMPONENT:offline_funding_balance_read_producer_v1` |
| `RUNTIME_COMPONENT:p08_distinct_first_party_evidence_v1` |
| `RUNTIME_COMPONENT:p08_empty_data_not_zero_v1` |
| `RUNTIME_COMPONENT:p08_nonzero_position_adjudication_persist_close_v1` |
| `RUNTIME_COMPONENT:p08_position_observation_v1` |
| `RUNTIME_COMPONENT:p08_post_read_only_exhaustion_authority_boundary_v1` |
| `RUNTIME_COMPONENT:p08_read_only_closure_v1` |
| `RUNTIME_COMPONENT:p10_target_position_qty_unit_forensic_adjudicate_persist_v1` |
| `RUNTIME_COMPONENT:p11_pos_to_sz_unit_identity_independent_proof_v1` |
| `RUNTIME_COMPONENT:p12_execution_prerequisite_11_position_side_posside_v1` |
| `RUNTIME_COMPONENT:p13_execution_prerequisite_12_exact_flatten_payload_v1` |
| `RUNTIME_COMPONENT:p16_execution_prerequisite_16_bounded_activation_v1` |
| `RUNTIME_COMPONENT:p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1` |
| `RUNTIME_COMPONENT:p25_execution_prerequisite_25_no_additional_owner_decision_v1` |
| `RUNTIME_COMPONENT:post_z2do_fresh_create_readiness_evidence_v1` |
| `RUNTIME_COMPONENT:post_z2dr_runtime_read_only_evidence_max_leverage_v1` |
| `RUNTIME_COMPONENT:post_z2ds_post_whitelist_private_auth_attestation_v1` |
| `RUNTIME_COMPONENT:post_z2ds_private_get_current_50110_egress_capture_v1` |
| `RUNTIME_COMPONENT:pr_6252_merge_closeout_v1` |
| `RUNTIME_COMPONENT:prerequisite_08_position_source_policy_rebind_v1` |
| `RUNTIME_COMPONENT:productive_flatten_post_and_reconciliation_v1` |
| `RUNTIME_COMPONENT:remaining_execution_path_end_to_end_census_v1` |
| `RUNTIME_COMPONENT:route_c_create_path_blocker_census_v1` |
| `RUNTIME_COMPONENT:route_c_net_mode_posside_first_party_contract_evidence_v1` |
| `RUNTIME_COMPONENT:route_c_offline_gated_productive_submit_composition_v1` |
| `RUNTIME_COMPONENT:section_11_14_live_order_and_economic_evidence_ladder_v1` |
| `RUNTIME_COMPONENT:send_time_pass_18_19_21_24_v1` |
| `RUNTIME_COMPONENT:send_time_position_reobservation_v1` |
| `RUNTIME_COMPONENT:z2dg_single_actual_read_only_funding_balance_get_v1` |
| `RUNTIME_COMPONENT:z2dh_single_actual_read_only_funding_balance_get_v1` |
| `RUNTIME_COMPONENT:z2dl_post_remediation_single_private_auth_get_v1` |
| `SUBSYSTEM:master_v2` |
| `SUBSYSTEM:trading_decision_core` |
| `SYSTEM:peak_trade` |
| `TERM:btc_productive_proof_do_not_run` |
| `TERM:canary` |
| `TERM:cap23` |
| `TERM:capability_closure_standard` |
| `TERM:document_class` |
| `TERM:double_play` |
| `TERM:fail_closed` |
| `TERM:live_authorized` |
| `TERM:map_of_truth` |
| `TERM:master_v2` |
| `TERM:mmr_polyvalent` |
| `TERM:owner_go` |
| `TERM:shadow` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:a_map_documents_runbook` |
| `REL:a_runbook_does_not_authorize_live` |
| `REL:a_runbook_governs_system` |
| `REL:r_live_auth_denies` |
| `REL:s_map_navigates_runbook` |
| `REL:s_master_v2_has_dp` |
| `REL:s_runbook_has_closure_std` |
| `REL:s_runbook_has_program_dod` |
| `REL:s_runbook_supersedes_vollautonomie` |
| `REL:s_system_contains_master_v2` |
| `REL:s_system_has_cap11135` |
| `REL:s_system_has_cap72` |

## NEW_RELATIONS

| id |
| --- |
| `REL:s_system_contains_full_core_live_path_composition_root` |
| `REL:r_full_core_path_calls_venue_translation` |
| `REL:r_full_core_path_calls_frozen_pretrade` |
| `REL:r_full_core_path_calls_execution_boundary` |
| `REL:r_full_core_path_calls_restart_gate` |
| `REL:r_full_core_path_calls_canary_isolation` |
| `REL:r_full_core_path_consumes_models` |
| `REL:r_full_core_path_calls_standing_live_gates` |
| `REL:r_full_core_path_calls_owner_one_shot_permit` |
| `REL:r_full_core_owner_one_shot_permit_composes_filegate` |
| `REL:r_full_core_path_calls_path_identity` |

## REMOVED_RELATIONS

| id |
| --- |
| _(none)_ |

## AFFECTED_DEPENDENCY_CLOSURES

| id |
| --- |
| `CLOSURE:canary` |
| `CLOSURE:flatten` |
| `CLOSURE:live_readiness` |
| `CLOSURE:native_instrument_binding` |
| `CLOSURE:order_submit` |
| `CLOSURE:productive_selection` |

## AFFECTED_OKX_SURFACES

| id |
| --- |
| _(none)_ |

## AFFECTED_SAFETY_SURFACES

| id |
| --- |
| `CHAIN:order_submit_standing_deny` |
| `CHAIN:full_core_live_path_halt_before_wire` |
| `GATE:live_authorized_false` |
| `GATE:max_positions_1` |
| `GATE:full_core_live_path_execution_boundary_halt_before_wire_v1` |
| `GATE:full_core_live_path_frozen_pretrade_conjunction_v1` |
| `GATE:full_core_live_path_identity_v1` |
| `GATE:full_core_live_path_restart_gate_v1` |
| `GATE:full_core_live_path_standing_live_gates_v1` |
| `GATE:full_core_owner_one_shot_permit_v1` |

## AFFECTED_SCHEMAS

| id |
| --- |
| `DATA_CONTRACT:full_core_live_path_models_v1` |

## REVIEW_REQUIRED_ITEMS

| item |
| --- |
| _(none)_ |

## Notes

- Offline Core-to-Live composition root inventory plus Full-Core productive Live-path identity and live-admission gap DAG. Canary / §11.14 remain evidence-domain only. No Live GET/POST. Atlas is not canonical authority.
- introduced_by=PENDING_CHANGE
- modified_by=PENDING_CHANGE

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
