<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Structural graph — what belongs to what?

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

Membership, hierarchy, supersession. Inverse edges are not inferred.

| id | source | type | target | epistemic | evidence |
| --- | --- | --- | --- | --- | --- |
| REL:s_binder_uses_schema | BINDER:bound_instrument_v1 | USES_SCHEMA | SCHEMA:runtime_binding_v1 | STATUS=FORENSIC_RAW | src/ops/single_selected_future_runtime_binding_v1/constants_v1.py |
| REL:s_cap21_governed_by_btc | CAPABILITY:cap_2_1_gfu | GOVERNED_BY | GATE:btc_exclusion | STATUS=CANONICAL_AUTHORITY | src/ops/governed_futures_universe_producer_v1/constants_v1.py |
| REL:s_cap21_governed_by_never_default | CAPABILITY:cap_2_1_gfu | GOVERNED_BY | INVARIANT:missing_metadata_never_defaulted | STATUS=CANONICAL_AUTHORITY | docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md |
| REL:s_cap21_tested_by | CAPABILITY:cap_2_1_gfu | TESTED_BY | TEST:gfu_producer | STATUS=FORENSIC_RAW | docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md |
| REL:s_cap22_depends_cap21 | CAPABILITY:cap_2_2_ranking | DEPENDS_ON | CAPABILITY:cap_2_1_gfu | STATUS=ADJUDICATED | docs/ops/specs/MASTER_V2_CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1.md |
| REL:s_cap23_depends_cap22 | CAPABILITY:cap_2_3_single_selected_future | DEPENDS_ON | CAPABILITY:cap_2_2_ranking | STATUS=ADJUDICATED | src/ops/single_selected_future_policy_v1/constants_v1.py |
| REL:s_cap23_governed_by_owner | CAPABILITY:cap_2_3_single_selected_future | GOVERNED_BY | OWNER_DECISION:cap23_exclusive_selection | STATUS=CANONICAL_AUTHORITY | docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md |
| REL:s_cap24_depends_cap23 | CAPABILITY:cap_2_4_runtime_binding | DEPENDS_ON | CAPABILITY:cap_2_3_single_selected_future | STATUS=ADJUDICATED | src/ops/single_selected_future_runtime_binding_v1/constants_v1.py |
| REL:s_cap31_depends_cap24 | CAPABILITY:cap_3_1_futures_accounting | DEPENDS_ON | CAPABILITY:cap_2_4_runtime_binding | STATUS=ADJUDICATED | docs/ops/specs/MASTER_V2_CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1.md |
| REL:s_cap41_depends_cap11 | CAPABILITY:cap_4_1_pre_activation_closure | DEPENDS_ON | CAPABILITY:cap_1_1_reconciliation | STATUS=ADJUDICATED | docs/ops/specs/MASTER_V2_CAPABILITY_4_1_SINGLE_FUTURE_CANONICAL_RUNTIME_PRE_ACTIVATION_CLOSURE_V1.md |
| REL:s_cap41_depends_cap24 | CAPABILITY:cap_4_1_pre_activation_closure | DEPENDS_ON | CAPABILITY:cap_2_4_runtime_binding | STATUS=ADJUDICATED | docs/ops/specs/MASTER_V2_CAPABILITY_4_1_SINGLE_FUTURE_CANONICAL_RUNTIME_PRE_ACTIVATION_CLOSURE_V1.md |
| REL:s_cap41_depends_cap31 | CAPABILITY:cap_4_1_pre_activation_closure | DEPENDS_ON | CAPABILITY:cap_3_1_futures_accounting | STATUS=ADJUDICATED | docs/ops/specs/MASTER_V2_CAPABILITY_4_1_SINGLE_FUTURE_CANONICAL_RUNTIME_PRE_ACTIVATION_CLOSURE_V1.md |
| REL:s_cap72_depends_cap24 | CAPABILITY:cap_7_2_stateful_no_order | DEPENDS_ON | CAPABILITY:cap_2_4_runtime_binding | STATUS=ADJUDICATED | src/ops/single_future_stateful_no_order_runtime_activation_v1/host_binding_v1.py |
| REL:s_ddo_experiment_identity_reference_of_canonical_owner | RUNTIME_COMPONENT:ddo_experiment_identity_binding | REFERENCE_OF | EXPERIMENT:canonical_experiment_identity_v1 | STATUS=FORENSIC_RAW | src/learning/deterministic_decision_outcome_v0/experiment_identity_binding_v0.py,src/experiments/canonical_experiment_identity_v1.py,src/learning/deterministic_decision_outcome_v0/authority_v0.py |
| REL:s_ddo_phase_contains_capture | PHASE:ddo_offline_foundation | CONTAINS | RUNTIME_COMPONENT:ddo_capture_v0 | STATUS=FORENSIC_RAW | src/learning/deterministic_decision_outcome_v0/capture_v0.py,src/learning/deterministic_decision_outcome_v0/authority_v0.py |
| REL:s_ddo_phase_contains_experiment_identity_binding | PHASE:ddo_offline_foundation | CONTAINS | RUNTIME_COMPONENT:ddo_experiment_identity_binding | STATUS=FORENSIC_RAW | src/learning/deterministic_decision_outcome_v0/experiment_identity_binding_v0.py |
| REL:s_ddo_phase_contains_ledger | PHASE:ddo_offline_foundation | CONTAINS | RUNTIME_COMPONENT:ddo_ledger_v0 | STATUS=FORENSIC_RAW | src/learning/deterministic_decision_outcome_v0/ledger_v0.py |
| REL:s_dp_contains_dp_capital_slot | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_capital_slot | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_composition | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_composition | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_core_wiring | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_core_wiring | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_futures_input | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_futures_input | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_state | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_state | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_suitability | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_suitability | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_survival | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_survival | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_forensic_has_nested_child | FORENSIC_REFERENCE:information_corpus_persistence_base | HAS_CHILD | CHILD:nested_structural_child | STATUS=HISTORICAL | forensic/lossless_working_runbook_structure_identity_method_v1/build_lossless_structure.py |
| REL:s_forensic_reference_of_corpus | FORENSIC_REFERENCE:information_corpus_persistence_base | REFERENCE_OF | SYSTEM:peak_trade | STATUS=FORENSIC_RAW | docs/forensics/persistence/PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md |
| REL:s_map_navigates_runbook | NAVIGATION_INDEX:map_of_truth | NAVIGATES_TO | RUNBOOK:canonical_master_runbook | STATUS=NAVIGATION_ONLY | docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md |
| REL:s_master_v2_has_dp | SUBSYSTEM:master_v2 | HAS_FUNCTIONAL_CORE | FUNCTIONAL_CORE:double_play | STATUS=ADJUDICATED | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md,docs/architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md |
| REL:s_mv2_contains_dp_capital_slot | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_capital_slot | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_composition | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_composition | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_core_wiring | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_core_wiring | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_dashboard_display | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_dashboard_display | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_entry_exit_policy | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_entry_exit_policy | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_evaluate_authority_boundary | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_evaluate_authority_boundary | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_futures_input | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_futures_input | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_offline_scenario_replay | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_offline_scenario_replay | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_sole_authority_quarantine | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_sole_authority_quarantine | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_state | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_state | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_suitability | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_suitability | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_survival | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_survival | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_volatility_presence_gate | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_volatility_presence_gate | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_arithmetic_decimal | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_arithmetic_decimal | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_canonical_market_context | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_canonical_market_context | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_canonical_scope | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_canonical_scope | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_canonical_trading_decision_evidence | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_canonical_trading_decision_evidence | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_canonical_volatility | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_canonical_volatility | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_capital_risk_sizing | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_capital_risk_sizing | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_decision_packet | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_decision_packet | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_directional_assessment | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_directional_assessment | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_input_happy_path | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_input_happy_path | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_integrated_replay | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_integrated_replay | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_local_evaluator | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_local_evaluator | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_offline_boundary_adapters | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_offline_boundary_adapters | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_package_init | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_package_init | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_parity_gap_assessment | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_parity_gap_assessment | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_post_confirmation_ssc | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_post_confirmation_ssc | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_pr4985_materiality_classifier | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_pr4985_materiality_classifier | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_regime_bull_bear_readmodel | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_regime_bull_bear_readmodel | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_runtime_bridge | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_runtime_bridge | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_scenario_matrix | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_scenario_matrix | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_scope_events | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_scope_events | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_strategy_identity | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_strategy_identity | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_surface_p | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_surface_p | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_runbook_has_closure_std | RUNBOOK:canonical_master_runbook | HAS_DOD | DOD:capability_closure_standard | STATUS=CANONICAL_AUTHORITY | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:s_runbook_has_program_dod | RUNBOOK:canonical_master_runbook | HAS_DOD | DOD:program_final | STATUS=CANONICAL_AUTHORITY | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:s_runbook_supersedes_vollautonomie | RUNBOOK:canonical_master_runbook | SUPERSEDES | RUNBOOK:vollautonomie_v4_4_12 | STATUS=CANONICAL_AUTHORITY | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:s_schema_binding_defines_dto | SCHEMA:bound_instrument_dataclass_v1 | DEFINES_SHAPE_OF | DATA_CONTRACT:bound_instrument_v1 | STATUS=FORENSIC_RAW | src/ops/single_selected_future_runtime_binding_v1/models_v1.py |
| REL:s_schema_gfu_defines_contract | SCHEMA:gfu_snapshot_v1 | DEFINES_SHAPE_OF | DATA_CONTRACT:governed_universe_instrument_v1 | STATUS=INTERPRETATION | src/ops/governed_futures_universe_producer_v1/models_v1.py |
| REL:s_selection_uses_schema | SELECTOR:single_selected_future_policy | USES_SCHEMA | SCHEMA:single_selected_future_selection_v1 | STATUS=FORENSIC_RAW | src/ops/single_selected_future_policy_v1/constants_v1.py |
| REL:s_system_contains_master_v2 | SYSTEM:peak_trade | CONTAINS | SUBSYSTEM:master_v2 | STATUS=CANONICAL_AUTHORITY | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:s_system_has_cap11 | SYSTEM:peak_trade | HAS_CAPABILITY | CAPABILITY:cap_1_1_reconciliation | STATUS=CANONICAL_AUTHORITY | docs/ops/specs/MASTER_V2_CAPABILITY_1_1_PRODUCTIVE_RECONCILIATION_RUNTIME_BINDING_V1.md |
| REL:s_system_has_cap11135 | SYSTEM:peak_trade | HAS_CAPABILITY | CAPABILITY:cap_11_13_5_live_canary | STATUS=CANONICAL_AUTHORITY | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:s_system_has_cap21 | SYSTEM:peak_trade | HAS_CAPABILITY | CAPABILITY:cap_2_1_gfu | STATUS=CANONICAL_AUTHORITY | docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md |
| REL:s_system_has_cap22 | SYSTEM:peak_trade | HAS_CAPABILITY | CAPABILITY:cap_2_2_ranking | STATUS=CANONICAL_AUTHORITY | docs/ops/specs/MASTER_V2_CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1.md |
| REL:s_system_has_cap23 | SYSTEM:peak_trade | HAS_CAPABILITY | CAPABILITY:cap_2_3_single_selected_future | STATUS=CANONICAL_AUTHORITY | docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md |
| REL:s_system_has_cap24 | SYSTEM:peak_trade | HAS_CAPABILITY | CAPABILITY:cap_2_4_runtime_binding | STATUS=CANONICAL_AUTHORITY | docs/ops/specs/MASTER_V2_CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1.md |
| REL:s_system_has_cap31 | SYSTEM:peak_trade | HAS_CAPABILITY | CAPABILITY:cap_3_1_futures_accounting | STATUS=CANONICAL_AUTHORITY | docs/ops/specs/MASTER_V2_CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1.md |
| REL:s_system_has_cap41 | SYSTEM:peak_trade | HAS_CAPABILITY | CAPABILITY:cap_4_1_pre_activation_closure | STATUS=CANONICAL_AUTHORITY | docs/ops/specs/MASTER_V2_CAPABILITY_4_1_SINGLE_FUTURE_CANONICAL_RUNTIME_PRE_ACTIVATION_CLOSURE_V1.md |
| REL:s_system_has_cap72 | SYSTEM:peak_trade | HAS_CAPABILITY | CAPABILITY:cap_7_2_stateful_no_order | STATUS=CANONICAL_AUTHORITY | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:s_universe_uses_gfu_schema | UNIVERSE:governed_futures_universe | USES_SCHEMA | SCHEMA:gfu_snapshot_v1 | STATUS=FORENSIC_RAW | src/ops/governed_futures_universe_producer_v1/constants_v1.py |
| REL:s_va_has_dod_econ | RUNBOOK:vollautonomie_v4_4_12 | HAS_DOD | DOD:vollautonomie_economic_validity | STATUS=HISTORICAL | docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md |
| REL:s_va_has_dod_safety | RUNBOOK:vollautonomie_v4_4_12 | HAS_DOD | DOD:vollautonomie_safety_runtime | STATUS=HISTORICAL | docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md |
| REL:s_va_has_dod_tl | RUNBOOK:vollautonomie_v4_4_12 | HAS_DOD | DOD:vollautonomie_trading_logic | STATUS=HISTORICAL | docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md |
| REL:s_venue_okx_contains_eea | VENUE:okx | CONTAINS | VENUE:okx_eea | STATUS=FORENSIC_RAW | config/config.toml |

