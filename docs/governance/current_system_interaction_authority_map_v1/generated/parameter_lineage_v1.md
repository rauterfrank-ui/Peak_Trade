<!-- GENERATED FILE. DO NOT EDIT BY HAND. SOURCE=config/governance/current_system_interaction_authority_map_v1/source_v1.json VIEW=parameter_lineage AUTHORITY=NONE -->

# Parameter Lineage View

AUTHORITY=NONE

Historical defaults stay historical. Model semantics are not aged into history.

## harness_parallel_distance_literals

- semantic_class=LEGACY_TECHNICAL
- source_ref=src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py
- canonical_owner_ref=not the TOML owner
- current_consumer_ref=harness builder
- current_decision_effect=Parallel literal. Not promoted to owner.
- authority_status=NOT_OWNER
- historical_default_status=NOT_HISTORICAL_DEFAULT
- lifecycle=LEGACY_TECHNICAL
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=NOT_THE_PRODUCTIVE_OWNER
- conflicts=second literal site beside the TOML owner
- evidence=`src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py`, `config/ops/canonical_decision_runtime_config_v1.toml`

## historical_crs_limits_25_500

- semantic_class=HISTORICAL_DEFAULT
- source_ref=src/trading/master_v2/capital_risk_sizing_historical_default_deauthorization_v1.py
- canonical_owner_ref=fixture module, not current authority
- current_consumer_ref=isolated_offline_replay_fixture_capital_context_v0
- current_decision_effect=No substitution on the productive enter rebind.
- authority_status=NONE
- historical_default_status=HISTORICAL_DEFAULT
- lifecycle=RESEARCH_ONLY
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=NOT_A_PRODUCTIVE_SEAM
- conflicts=(none)
- evidence=`src/trading/master_v2/capital_risk_sizing_historical_default_deauthorization_v1.py`, `src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py`

## historical_equity_sentinel_10000

- semantic_class=HISTORICAL_DEFAULT
- source_ref=src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py
- canonical_owner_ref=fixture constant alias _DEFAULT_ACCOUNT_EQUITY
- current_consumer_ref=src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py
- current_decision_effect=Sentinel comparison only. Not a productive sizing source. Producer output of exactly 10000 passes the inequality check.
- authority_status=NONE
- historical_default_status=HISTORICAL_DEFAULT
- lifecycle=SENTINEL_ON_ENTER_JOIN
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=LEAK_DENY_SENTINEL
- conflicts=(none)
- evidence=`src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py`, `src/trading/master_v2/capital_risk_sizing_historical_default_deauthorization_v1.py`

## historical_fixture_prices_3500_3400

- semantic_class=HISTORICAL_DEFAULT
- source_ref=src/trading/master_v2/capital_risk_sizing_historical_default_deauthorization_v1.py
- canonical_owner_ref=fixture capital context
- current_consumer_ref=isolated offline replay fixture
- current_decision_effect=Enter-path stop derivation does not use these fixture literals.
- authority_status=NONE
- historical_default_status=HISTORICAL_DEFAULT
- lifecycle=RESEARCH_ONLY
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=NOT_A_PRODUCTIVE_SEAM
- conflicts=(none)
- evidence=`src/trading/master_v2/capital_risk_sizing_historical_default_deauthorization_v1.py`

## historical_maximum_quantity_100

- semantic_class=HISTORICAL_DEFAULT
- source_ref=src/trading/master_v2/capital_risk_sizing_historical_default_deauthorization_v1.py
- canonical_owner_ref=isolated_offline_replay_fixture_instrument_v0
- current_consumer_ref=fixture instrument builder
- current_decision_effect=Not the productive helper, which sets maximum_quantity None.
- authority_status=NONE
- historical_default_status=HISTORICAL_DEFAULT
- lifecycle=RESEARCH_ONLY
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=NOT_A_PRODUCTIVE_SEAM
- conflicts=(none)
- evidence=`src/trading/master_v2/capital_risk_sizing_historical_default_deauthorization_v1.py`, `src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py`

## m9_numeric_max_age_seconds

- semantic_class=UNKNOWN
- source_ref=config/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1_decision_v1.json
- canonical_owner_ref=m9 target decision
- current_consumer_ref=evaluate_canonical_volatility_estimate_age_policy_v1
- current_decision_effect=No current decision effect through enforcement. Threshold not ratified.
- authority_status=NONE
- historical_default_status=NOT_HISTORICAL_DEFAULT
- lifecycle=REGISTERED_NOT_ENFORCED
- optimization_surface_status=TARGET_REGISTERED_APPLY_NONE
- learning_evidence_status=NOT_LEARNING_AUTHORITY
- productive_seam_status=PARTIAL
- conflicts=(none)
- evidence=`src/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1.py`, `config/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1_decision_v1.json`

## model_adverse_exit_distance_80

- semantic_class=CANONICAL_MODEL_SEMANTIC
- source_ref=config/ops/canonical_decision_runtime_config_v1.toml
- canonical_owner_ref=ops.decision_config_ownership_and_consumer_closure_v1
- current_consumer_ref=src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py
- current_decision_effect=Distance enters replay input and protective stop derivation.
- authority_status=CONFIG_OWNER_PIN
- historical_default_status=NOT_HISTORICAL_DEFAULT
- lifecycle=CURRENT_MODEL_WIRING
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=MODEL_INPUT
- conflicts=harness parallel literal is not the owner
- evidence=`config/ops/canonical_decision_runtime_config_v1.toml`, `src/ops/decision_config_ownership_and_consumer_closure_v1/constants_v1.py`, `src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py`, `src/ops/exit_policy_producer_binding_v1/parity_v1.py`

## model_confirmation_epochs_2

- semantic_class=CANONICAL_MODEL_SEMANTIC
- source_ref=config/ops/canonical_decision_runtime_config_v1.toml
- canonical_owner_ref=ops.decision_config_ownership_and_consumer_closure_v1
- current_consumer_ref=src/ops/decision_config_ownership_and_consumer_closure_v1/constants_v1.py
- current_decision_effect=Confirmation-epoch model input via the same loader.
- authority_status=CONFIG_OWNER_PIN
- historical_default_status=NOT_HISTORICAL_DEFAULT
- lifecycle=CURRENT_MODEL_WIRING
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=MODEL_INPUT
- conflicts=(none)
- evidence=`config/ops/canonical_decision_runtime_config_v1.toml`, `src/ops/decision_config_ownership_and_consumer_closure_v1/constants_v1.py`

## model_reversal_distance_120

- semantic_class=CANONICAL_MODEL_SEMANTIC
- source_ref=config/ops/canonical_decision_runtime_config_v1.toml
- canonical_owner_ref=ops.decision_config_ownership_and_consumer_closure_v1
- current_consumer_ref=src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py
- current_decision_effect=Scope distance input of the replay.
- authority_status=CONFIG_OWNER_PIN
- historical_default_status=NOT_HISTORICAL_DEFAULT
- lifecycle=CURRENT_MODEL_WIRING
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=MODEL_INPUT
- conflicts=(none)
- evidence=`config/ops/canonical_decision_runtime_config_v1.toml`, `src/ops/decision_config_ownership_and_consumer_closure_v1/constants_v1.py`, `src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py`

## model_up_distance_200

- semantic_class=CANONICAL_MODEL_SEMANTIC
- source_ref=config/ops/canonical_decision_runtime_config_v1.toml
- canonical_owner_ref=ops.decision_config_ownership_and_consumer_closure_v1
- current_consumer_ref=src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py
- current_decision_effect=Scope distance input of the replay.
- authority_status=CONFIG_OWNER_PIN
- historical_default_status=NOT_HISTORICAL_DEFAULT
- lifecycle=CURRENT_MODEL_WIRING
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=MODEL_INPUT
- conflicts=(none)
- evidence=`config/ops/canonical_decision_runtime_config_v1.toml`, `src/ops/decision_config_ownership_and_consumer_closure_v1/constants_v1.py`, `src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py`

## offline_instrument_literals_on_productive_context

- semantic_class=UNKNOWN
- source_ref=src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py
- canonical_owner_ref=ops.governed_productive_instrument_metadata_authority_producer_v1
- current_consumer_ref=src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py
- current_decision_effect=LIVE_ACCOUNT_BOUND path requires governed instruments-row producer; offline literals remain non-CURRENT on productive enter-live join.
- authority_status=PARTIAL
- historical_default_status=NOT_CURRENT_AUTHORITY
- lifecycle=WIRING_PRESENT_EFFECT_UNKNOWN
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=CONDITIONAL_CRS_BRANCH
- conflicts=INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=true on Full-Core B05 path (#6817); Companion C2 handoff still absent
- evidence=`src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py`, `src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py`, `config/governance/risk_sizing_authority_decision_contract_freeze_v1.json`

## typed_29p_equity_to_four_crs_limits

- semantic_class=CONFLICTING
- source_ref=src/ops/full_core_live_path_composition_root_v1/current_productive_mv2_capital_context_rebind_v1.py
- canonical_owner_ref=UNRESOLVED
- current_consumer_ref=src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py
- current_decision_effect=Formula wires four CRS limits to typed 29P equity. The scalar is not CURRENT_AUTHORITY while the equity owner is unresolved.
- authority_status=UNRESOLVED
- historical_default_status=NOT_HISTORICAL_DEFAULT
- lifecycle=CURRENT_WIRING_AUTHORITY_UNRESOLVED
- optimization_surface_status=NOT_AN_OPTIMIZATION_SURFACE
- learning_evidence_status=NOT_LEARNING_EVIDENCE
- productive_seam_status=ENTER_JOIN_CALL
- conflicts=ACCOUNT_EQUITY_AUTHORITY_OWNER unresolved, limit names versus equity collapse
- evidence=`src/ops/full_core_live_path_composition_root_v1/current_productive_mv2_capital_context_rebind_v1.py`, `src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py`, `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`, `config/governance/risk_sizing_authority_decision_contract_freeze_v1.json`
