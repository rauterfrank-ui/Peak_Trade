<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Full Dependency Graph

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

Inverse CALLS edges are derived as CALLED_BY for downstream listing only; they are not stored as independent facts.

### ADAPTER:okx_public_md_client

- direct_upstream: `VENUE_ENDPOINT:okx_public_instruments`
- transitive_upstream: `VENUE_ENDPOINT:okx_public_instruments`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### BINDER:bound_instrument_v1

- direct_upstream: `SELECTOR:single_selected_future_policy`
- transitive_upstream: `SELECTOR:single_selected_future_policy`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### CAPABILITY:cap_2_1_gfu

- direct_upstream: `GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted`
- transitive_upstream: `GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted`
- direct_downstream: `SCRIPT:run_gfu_producer, UNIVERSE:governed_futures_universe`
- transitive_downstream: `UNIVERSE:governed_futures_universe`

### CAPABILITY:cap_2_2_ranking

- direct_upstream: `CAPABILITY:cap_2_1_gfu`
- transitive_upstream: `CAPABILITY:cap_2_1_gfu, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### CAPABILITY:cap_2_3_single_selected_future

- direct_upstream: `CAPABILITY:cap_2_2_ranking, OWNER_DECISION:cap23_exclusive_selection`
- transitive_upstream: `CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted, OWNER_DECISION:cap23_exclusive_selection`
- direct_downstream: `SCRIPT:run_cap23_policy`
- transitive_downstream: `(none)`

### CAPABILITY:cap_2_4_runtime_binding

- direct_upstream: `CAPABILITY:cap_2_3_single_selected_future`
- transitive_upstream: `CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, CAPABILITY:cap_2_3_single_selected_future, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted, OWNER_DECISION:cap23_exclusive_selection`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### CAPABILITY:cap_3_1_futures_accounting

- direct_upstream: `CAPABILITY:cap_2_4_runtime_binding`
- transitive_upstream: `CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, CAPABILITY:cap_2_3_single_selected_future, CAPABILITY:cap_2_4_runtime_binding, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted, OWNER_DECISION:cap23_exclusive_selection`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### CAPABILITY:cap_4_1_pre_activation_closure

- direct_upstream: `CAPABILITY:cap_1_1_reconciliation, CAPABILITY:cap_2_4_runtime_binding, CAPABILITY:cap_3_1_futures_accounting`
- transitive_upstream: `CAPABILITY:cap_1_1_reconciliation, CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, CAPABILITY:cap_2_3_single_selected_future, CAPABILITY:cap_2_4_runtime_binding, CAPABILITY:cap_3_1_futures_accounting, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted, OWNER_DECISION:cap23_exclusive_selection`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### CAPABILITY:cap_7_2_stateful_no_order

- direct_upstream: `CAPABILITY:cap_2_4_runtime_binding`
- transitive_upstream: `CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, CAPABILITY:cap_2_3_single_selected_future, CAPABILITY:cap_2_4_runtime_binding, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted, OWNER_DECISION:cap23_exclusive_selection`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### FORENSIC_REFERENCE:information_corpus_persistence_base

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `CHILD:nested_structural_child`
- transitive_downstream: `CHILD:nested_structural_child`

### FUNCTIONAL_CORE:double_play

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `RUNTIME_COMPONENT:dp_capital_slot, RUNTIME_COMPONENT:dp_composition, RUNTIME_COMPONENT:dp_core_wiring, RUNTIME_COMPONENT:dp_futures_input, RUNTIME_COMPONENT:dp_state, RUNTIME_COMPONENT:dp_suitability, RUNTIME_COMPONENT:dp_survival`
- transitive_downstream: `RUNTIME_COMPONENT:dp_capital_slot, RUNTIME_COMPONENT:dp_composition, RUNTIME_COMPONENT:dp_core_wiring, RUNTIME_COMPONENT:dp_futures_input, RUNTIME_COMPONENT:dp_state, RUNTIME_COMPONENT:dp_suitability, RUNTIME_COMPONENT:dp_survival`

### HOST:cap72_stateful_host

- direct_upstream: `BINDER:bound_instrument_v1`
- transitive_upstream: `BINDER:bound_instrument_v1, SELECTOR:single_selected_future_policy`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### HOST:wallclock_decision_economics_cycle

- direct_upstream: `RUNTIME_COMPONENT:ddo_capture_v0`
- transitive_upstream: `RUNTIME_COMPONENT:ddo_capture_v0`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### OWNER_DECISION:btc_excluded

- direct_upstream: `GATE:btc_exclusion`
- transitive_upstream: `GATE:btc_exclusion`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### OWNER_DECISION:cap23_exclusive_selection

- direct_upstream: `CAPABILITY:cap_2_3_single_selected_future`
- transitive_upstream: `CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, CAPABILITY:cap_2_3_single_selected_future, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### PHASE:ddo_offline_foundation

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `RUNTIME_COMPONENT:ddo_capture_v0, RUNTIME_COMPONENT:ddo_experiment_identity_binding, RUNTIME_COMPONENT:ddo_ledger_v0`
- transitive_downstream: `RUNTIME_COMPONENT:ddo_capture_v0, RUNTIME_COMPONENT:ddo_experiment_identity_binding, RUNTIME_COMPONENT:ddo_ledger_v0`

### RUNBOOK:canonical_master_runbook

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `DOD:capability_closure_standard, DOD:program_final`
- transitive_downstream: `DOD:capability_closure_standard, DOD:program_final`

### RUNBOOK:vollautonomie_v4_4_12

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `DOD:vollautonomie_economic_validity, DOD:vollautonomie_safety_runtime, DOD:vollautonomie_trading_logic`
- transitive_downstream: `DOD:vollautonomie_economic_validity, DOD:vollautonomie_safety_runtime, DOD:vollautonomie_trading_logic`

### RUNTIME_COMPONENT:ddo_capture_v0

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `HOST:wallclock_decision_economics_cycle, RUNTIME_COMPONENT:ddo_ledger_v0`
- transitive_downstream: `RUNTIME_COMPONENT:ddo_ledger_v0`

### RUNTIME_COMPONENT:dp_composition

- direct_upstream: `RUNTIME_COMPONENT:dp_capital_slot, RUNTIME_COMPONENT:dp_state, RUNTIME_COMPONENT:dp_suitability, RUNTIME_COMPONENT:dp_survival`
- transitive_upstream: `RUNTIME_COMPONENT:dp_capital_slot, RUNTIME_COMPONENT:dp_state, RUNTIME_COMPONENT:dp_suitability, RUNTIME_COMPONENT:dp_survival`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### RUNTIME_COMPONENT:dp_core_wiring

- direct_upstream: `RUNTIME_COMPONENT:dp_sole_authority_quarantine, RUNTIME_COMPONENT:mv2_decision_packet, RUNTIME_COMPONENT:mv2_integrated_replay`
- transitive_upstream: `RUNTIME_COMPONENT:dp_sole_authority_quarantine, RUNTIME_COMPONENT:mv2_decision_packet, RUNTIME_COMPONENT:mv2_integrated_replay`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### RUNTIME_COMPONENT:dp_sole_authority_quarantine

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `RUNTIME_COMPONENT:dp_core_wiring`
- transitive_downstream: `(none)`

### RUNTIME_COMPONENT:g12_canonical_delayed_zero_persist_and_pending_related_observations_v1

- direct_upstream: `RUNTIME_COMPONENT:g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1`
- transitive_upstream: `GATE:target_position_state, RUNTIME_COMPONENT:g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### RUNTIME_COMPONENT:g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1

- direct_upstream: `GATE:target_position_state`
- transitive_upstream: `GATE:target_position_state`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### RUNTIME_COMPONENT:mv2_decision_packet

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `RUNTIME_COMPONENT:dp_core_wiring`
- transitive_downstream: `(none)`

### RUNTIME_COMPONENT:mv2_integrated_replay

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `RUNTIME_COMPONENT:dp_core_wiring`
- transitive_downstream: `(none)`

### RUNTIME_COMPONENT:section_11_14_live_order_and_economic_evidence_ladder_v1

- direct_upstream: `PHASE:section_11_14_live_execution_code_exists_adjudication, PHASE:section_11_14_offline_evidence_ladder_surface, RUNTIME_COMPONENT:g12_canonical_delayed_zero_persist_and_pending_related_observations_v1`
- transitive_upstream: `GATE:target_position_state, PHASE:section_11_14_live_execution_code_exists_adjudication, PHASE:section_11_14_offline_evidence_ladder_surface, RUNTIME_COMPONENT:g12_canonical_delayed_zero_persist_and_pending_related_observations_v1, RUNTIME_COMPONENT:g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### SCRIPT:run_cap23_policy

- direct_upstream: `CAPABILITY:cap_2_3_single_selected_future`
- transitive_upstream: `CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, CAPABILITY:cap_2_3_single_selected_future, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted, OWNER_DECISION:cap23_exclusive_selection`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### SCRIPT:run_gfu_producer

- direct_upstream: `CAPABILITY:cap_2_1_gfu`
- transitive_upstream: `CAPABILITY:cap_2_1_gfu, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted`
- direct_downstream: `(none)`
- transitive_downstream: `(none)`

### SUBSYSTEM:master_v2

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `FUNCTIONAL_CORE:double_play, RUNTIME_COMPONENT:dp_capital_slot, RUNTIME_COMPONENT:dp_composition, RUNTIME_COMPONENT:dp_core_wiring, RUNTIME_COMPONENT:dp_dashboard_display, RUNTIME_COMPONENT:dp_entry_exit_policy, RUNTIME_COMPONENT:dp_evaluate_authority_boundary, RUNTIME_COMPONENT:dp_futures_input, RUNTIME_COMPONENT:dp_offline_scenario_replay, RUNTIME_COMPONENT:dp_sole_authority_quarantine, RUNTIME_COMPONENT:dp_state, RUNTIME_COMPONENT:dp_suitability, RUNTIME_COMPONENT:dp_survival, RUNTIME_COMPONENT:dp_volatility_presence_gate, RUNTIME_COMPONENT:mv2_arithmetic_decimal, RUNTIME_COMPONENT:mv2_canonical_market_context, RUNTIME_COMPONENT:mv2_canonical_scope, RUNTIME_COMPONENT:mv2_canonical_trading_decision_evidence, RUNTIME_COMPONENT:mv2_canonical_volatility, RUNTIME_COMPONENT:mv2_capital_risk_sizing, RUNTIME_COMPONENT:mv2_decision_packet, RUNTIME_COMPONENT:mv2_directional_assessment, RUNTIME_COMPONENT:mv2_input_happy_path, RUNTIME_COMPONENT:mv2_integrated_replay, RUNTIME_COMPONENT:mv2_local_evaluator, RUNTIME_COMPONENT:mv2_offline_boundary_adapters, RUNTIME_COMPONENT:mv2_package_init, RUNTIME_COMPONENT:mv2_parity_gap_assessment, RUNTIME_COMPONENT:mv2_post_confirmation_ssc, RUNTIME_COMPONENT:mv2_pr4985_materiality_classifier, RUNTIME_COMPONENT:mv2_regime_bull_bear_readmodel, RUNTIME_COMPONENT:mv2_runtime_bridge, RUNTIME_COMPONENT:mv2_scenario_matrix, RUNTIME_COMPONENT:mv2_scope_events, RUNTIME_COMPONENT:mv2_strategy_identity, RUNTIME_COMPONENT:mv2_surface_p`
- transitive_downstream: `FUNCTIONAL_CORE:double_play, RUNTIME_COMPONENT:dp_capital_slot, RUNTIME_COMPONENT:dp_composition, RUNTIME_COMPONENT:dp_core_wiring, RUNTIME_COMPONENT:dp_dashboard_display, RUNTIME_COMPONENT:dp_entry_exit_policy, RUNTIME_COMPONENT:dp_evaluate_authority_boundary, RUNTIME_COMPONENT:dp_futures_input, RUNTIME_COMPONENT:dp_offline_scenario_replay, RUNTIME_COMPONENT:dp_sole_authority_quarantine, RUNTIME_COMPONENT:dp_state, RUNTIME_COMPONENT:dp_suitability, RUNTIME_COMPONENT:dp_survival, RUNTIME_COMPONENT:dp_volatility_presence_gate, RUNTIME_COMPONENT:mv2_arithmetic_decimal, RUNTIME_COMPONENT:mv2_canonical_market_context, RUNTIME_COMPONENT:mv2_canonical_scope, RUNTIME_COMPONENT:mv2_canonical_trading_decision_evidence, RUNTIME_COMPONENT:mv2_canonical_volatility, RUNTIME_COMPONENT:mv2_capital_risk_sizing, RUNTIME_COMPONENT:mv2_decision_packet, RUNTIME_COMPONENT:mv2_directional_assessment, RUNTIME_COMPONENT:mv2_input_happy_path, RUNTIME_COMPONENT:mv2_integrated_replay, RUNTIME_COMPONENT:mv2_local_evaluator, RUNTIME_COMPONENT:mv2_offline_boundary_adapters, RUNTIME_COMPONENT:mv2_package_init, RUNTIME_COMPONENT:mv2_parity_gap_assessment, RUNTIME_COMPONENT:mv2_post_confirmation_ssc, RUNTIME_COMPONENT:mv2_pr4985_materiality_classifier, RUNTIME_COMPONENT:mv2_regime_bull_bear_readmodel, RUNTIME_COMPONENT:mv2_runtime_bridge, RUNTIME_COMPONENT:mv2_scenario_matrix, RUNTIME_COMPONENT:mv2_scope_events, RUNTIME_COMPONENT:mv2_strategy_identity, RUNTIME_COMPONENT:mv2_surface_p`

### SYSTEM:peak_trade

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `CAPABILITY:cap_11_13_5_live_canary, CAPABILITY:cap_1_1_reconciliation, CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, CAPABILITY:cap_2_3_single_selected_future, CAPABILITY:cap_2_4_runtime_binding, CAPABILITY:cap_3_1_futures_accounting, CAPABILITY:cap_4_1_pre_activation_closure, CAPABILITY:cap_7_2_stateful_no_order, SUBSYSTEM:master_v2`
- transitive_downstream: `CAPABILITY:cap_11_13_5_live_canary, CAPABILITY:cap_1_1_reconciliation, CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, CAPABILITY:cap_2_3_single_selected_future, CAPABILITY:cap_2_4_runtime_binding, CAPABILITY:cap_3_1_futures_accounting, CAPABILITY:cap_4_1_pre_activation_closure, CAPABILITY:cap_7_2_stateful_no_order, FUNCTIONAL_CORE:double_play, RUNTIME_COMPONENT:dp_capital_slot, RUNTIME_COMPONENT:dp_composition, RUNTIME_COMPONENT:dp_core_wiring, RUNTIME_COMPONENT:dp_dashboard_display, RUNTIME_COMPONENT:dp_entry_exit_policy, RUNTIME_COMPONENT:dp_evaluate_authority_boundary, RUNTIME_COMPONENT:dp_futures_input, RUNTIME_COMPONENT:dp_offline_scenario_replay, RUNTIME_COMPONENT:dp_sole_authority_quarantine, RUNTIME_COMPONENT:dp_state, RUNTIME_COMPONENT:dp_suitability, RUNTIME_COMPONENT:dp_survival, RUNTIME_COMPONENT:dp_volatility_presence_gate, RUNTIME_COMPONENT:mv2_arithmetic_decimal, RUNTIME_COMPONENT:mv2_canonical_market_context, RUNTIME_COMPONENT:mv2_canonical_scope, RUNTIME_COMPONENT:mv2_canonical_trading_decision_evidence, RUNTIME_COMPONENT:mv2_canonical_volatility, RUNTIME_COMPONENT:mv2_capital_risk_sizing, RUNTIME_COMPONENT:mv2_decision_packet, RUNTIME_COMPONENT:mv2_directional_assessment, RUNTIME_COMPONENT:mv2_input_happy_path, RUNTIME_COMPONENT:mv2_integrated_replay, RUNTIME_COMPONENT:mv2_local_evaluator, RUNTIME_COMPONENT:mv2_offline_boundary_adapters, RUNTIME_COMPONENT:mv2_package_init, RUNTIME_COMPONENT:mv2_parity_gap_assessment, RUNTIME_COMPONENT:mv2_post_confirmation_ssc, RUNTIME_COMPONENT:mv2_pr4985_materiality_classifier, RUNTIME_COMPONENT:mv2_regime_bull_bear_readmodel, RUNTIME_COMPONENT:mv2_runtime_bridge, RUNTIME_COMPONENT:mv2_scenario_matrix, RUNTIME_COMPONENT:mv2_scope_events, RUNTIME_COMPONENT:mv2_strategy_identity, RUNTIME_COMPONENT:mv2_surface_p, SUBSYSTEM:master_v2, UNIVERSE:governed_futures_universe`

### VENUE:okx

- direct_upstream: `(none)`
- transitive_upstream: `(none)`
- direct_downstream: `VENUE:okx_eea`
- transitive_downstream: `VENUE:okx_eea`

## Historical wiring (time-bounded; origin/main git)

| id | source | relation | target | from | to | epistemic |
| --- | --- | --- | --- | --- | --- | --- |
| HW:ops_dp_specialists_introduced | src/ops/double_play | INTRODUCED | bull/bear specialists scaffold | 2026-02-20 | still present (quarantined) | STATUS=FORENSIC_RAW |
| HW:master_v2_contains_dp_pure_stack | src/trading/master_v2 | CONTAINS | double_play_{state,survival,suitability,composition} | 2026-04-25 | current | STATUS=FORENSIC_RAW |
| HW:webui_dp_dashboard_removed | src&#47;webui&#47;market_dashboard_readmodels_v1&#47;adapters&#47;double_play.py | REMOVED_CONSUMER | Double Play display | OPEN | 2026-07-17 | STATUS=FORENSIC_RAW |
| HW:kraken_deactivated_okx_staged | config | SUPERSEDED_BY | disabled OKX target staging | 2026-06-27 | current (Kraken deactivated) | STATUS=FORENSIC_RAW |
| HW:dp_core_wiring_restored | src&#47;trading&#47;master_v2&#47;double_play_core_wiring_v1.py | RESTORED | FUNCTIONAL_CORE:double_play facade | 2026-08-29 | current | STATUS=FORENSIC_RAW |

