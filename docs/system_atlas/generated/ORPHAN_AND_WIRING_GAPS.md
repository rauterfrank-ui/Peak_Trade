<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Orphan and Wiring Gaps

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

| id | class | entity | epistemic | notes |
| --- | --- | --- | --- | --- |
| GAP:architectural_mmr | TERM_WITHOUT_FORMAL_KIND | TERM:mmr_polyvalent | STATUS=OPEN (not proven) | Architectural MMR unproven; OKX mmr is a venue field |
| GAP:cap23_not_wired_to_canary | PARALLEL_INSTRUMENT_AUTHORITY | CAPABILITY:cap_2_3_single_selected_future | STATUS=ADJUDICATED | Section 11.13.5 canary hardcoded SUI-USD_UM_XPERP-310404; no Cap 2.3 import on origin/main |
| GAP:ddo_declared_seams_without_host_decorator | DECLARED_SEAM_WITHOUT_PROVEN_HOST_EDGE | RUNTIME_COMPONENT:ddo_capture_v0 | STATUS=ADJUDICATED | Host-decorator gap closed by WP-FS-B1. Gap id retained for Atlas membership. Not WP-FA-08. Supervisor host activation re |
| GAP:flatten_live_wire_disabled | IMPLEMENTED_BUT_UNREACHABLE | GATE:flatten_live_wire | STATUS=FORENSIC_RAW | DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false; LIVE_FLATTEN_PROVABILITY not PROVEN |
| GAP:live_ws_client | CONFIGURED_BUT_NO_CLIENT | OKX_FEATURE:websocket_hosts_configured | STATUS=OPEN (not proven) | WS hosts configured; no proven live WS client; src/data/feeds/live_feed.py is a stub |
| GAP:no_family_ontology_projection | TERM_WITHOUT_FORMAL_KIND | TERM:family_polyvalent | STATUS=OPEN (not proven) | CBK-FAMILY-PROJECTION KIND=NO_FAMILY_ONTOLOGY blocks 5-family projection completeness only |
| GAP:okx_historical_removals | CENSUS_INCOMPLETE | VENUE:okx | STATUS=OPEN (not proven) | Unshallow complete. Named-path removals searched. Do not equate remaining non-named callers with missing history. |
| GAP:post_action_not_wired | DEFINED_BUT_NO_CONSUMER | OBSERVER:post_action_canary | STATUS=OPEN (not proven) | Forensic registry records POST_ACTION_NOT_WIRED_IN_FLATTEN_EXECUTE |
| GAP:schema_field_enumeration | CENSUS_CLOSED_FOR_DECLARED_SCOPE | SCHEMA:pure_stack_numeric_policy_evidence_pack_v1 | STATUS=ADJUDICATED | JSON Schema field inventory plus src schema-like classification closed; remaining VERSION_TOKEN payloads are not SCHEMA  |
| GAP:ssot_child_undefined | TERM_WITHOUT_FORMAL_KIND | TERM:ssot_child_unproven | STATUS=OPEN (not proven) | Owner-requested SSOT child has no formal in-repo definition |
| GAP:sui_xperp_gfu_membership | PRODUCTIVE_MEMBERSHIP_UNPROVEN | UNIVERSE:governed_futures_universe | STATUS=OPEN (not proven) | GAP-U-CAN-006 SUI XPERP blocked by missing quote and source_event_time. NO XPERP REPAIR in this workpackage. |
| GAP_AUTO:NO_CONSUMER:ADAPTER:kraken_live_client | DEFINED_BUT_NO_CONSUMER | ADAPTER:kraken_live_client | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:ADAPTER:okx_europe_lifecycle_contract | DEFINED_BUT_NO_CONSUMER | ADAPTER:okx_europe_lifecycle_contract | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:ADAPTER:okx_execution_mock_v1 | DEFINED_BUT_NO_CONSUMER | ADAPTER:okx_execution_mock_v1 | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:CAPABILITY:cap_11_13_5_live_canary | DEFINED_BUT_NO_CONSUMER | CAPABILITY:cap_11_13_5_live_canary | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:CAPABILITY:cap_1_1_reconciliation | DEFINED_BUT_NO_CONSUMER | CAPABILITY:cap_1_1_reconciliation | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:CAPABILITY:cap_2_2_ranking | DEFINED_BUT_NO_CONSUMER | CAPABILITY:cap_2_2_ranking | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:CAPABILITY:cap_2_4_runtime_binding | DEFINED_BUT_NO_CONSUMER | CAPABILITY:cap_2_4_runtime_binding | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:CAPABILITY:cap_3_1_futures_accounting | DEFINED_BUT_NO_CONSUMER | CAPABILITY:cap_3_1_futures_accounting | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:CAPABILITY:cap_4_1_pre_activation_closure | DEFINED_BUT_NO_CONSUMER | CAPABILITY:cap_4_1_pre_activation_closure | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:CAPABILITY:cap_7_2_stateful_no_order | DEFINED_BUT_NO_CONSUMER | CAPABILITY:cap_7_2_stateful_no_order | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:ddo_experiment_identity_binding | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:ddo_experiment_identity_binding | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:dp_capital_slot | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:dp_capital_slot | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:dp_dashboard_display | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:dp_dashboard_display | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:dp_entry_exit_policy | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:dp_entry_exit_policy | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:dp_evaluate_authority_boundary | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:dp_evaluate_authority_boundary | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:dp_futures_input | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:dp_futures_input | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:dp_offline_scenario_replay | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:dp_offline_scenario_replay | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:dp_state | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:dp_state | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:dp_suitability | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:dp_suitability | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:dp_survival | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:dp_survival | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:dp_volatility_presence_gate | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:dp_volatility_presence_gate | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:gfu_eligibility | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:gfu_eligibility | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_arithmetic_decimal | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_arithmetic_decimal | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_canonical_market_context | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_canonical_market_context | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_canonical_scope | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_canonical_scope | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_canonical_trading_decision_evidence | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_canonical_trading_decision_evidence | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_canonical_volatility | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_canonical_volatility | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_capital_risk_sizing | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_capital_risk_sizing | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_directional_assessment | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_directional_assessment | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_input_happy_path | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_input_happy_path | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_local_evaluator | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_local_evaluator | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_offline_boundary_adapters | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_offline_boundary_adapters | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_package_init | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_package_init | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_parity_gap_assessment | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_parity_gap_assessment | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_post_confirmation_ssc | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_post_confirmation_ssc | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_pr4985_materiality_classifier | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_pr4985_materiality_classifier | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_regime_bull_bear_readmodel | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_regime_bull_bear_readmodel | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_runtime_bridge | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_runtime_bridge | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_scenario_matrix | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_scenario_matrix | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_scope_events | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_scope_events | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_strategy_identity | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_strategy_identity | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:mv2_surface_p | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:mv2_surface_p | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:offline_execution_permission_and_position_creation_producer_wiring_v1 | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:offline_execution_permission_and_position_creation_producer_wiring_v1 | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:offline_funding_balance_read_producer_v1 | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:offline_funding_balance_read_producer_v1 | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:offline_observation_proposal_contract_fences_v1 | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:offline_observation_proposal_contract_fences_v1 | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:operative_venue_boundary_v1 | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:operative_venue_boundary_v1 | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:ops_evaluate_double_play | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:ops_evaluate_double_play | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:ops_failclosed_venue_cleanup_surfaces | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:ops_failclosed_venue_cleanup_surfaces | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:promotion_loop_safety | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:promotion_loop_safety | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:recon_startup_gate_v1 | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:recon_startup_gate_v1 | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:simulated_execution_port_v1 | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:simulated_execution_port_v1 | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:z2dg_single_actual_read_only_funding_balance_get_v1 | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:z2dg_single_actual_read_only_funding_balance_get_v1 | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:z2dh_single_actual_read_only_funding_balance_get_v1 | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:z2dh_single_actual_read_only_funding_balance_get_v1 | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:RUNTIME_COMPONENT:z2dl_post_remediation_single_private_auth_get_v1 | DEFINED_BUT_NO_CONSUMER | RUNTIME_COMPONENT:z2dl_post_remediation_single_private_auth_get_v1 | STATUS=OPEN (not proven) |  |
| GAP_AUTO:NO_CONSUMER:TRANSPORT:bound_okx_testnet_http | DEFINED_BUT_NO_CONSUMER | TRANSPORT:bound_okx_testnet_http | STATUS=OPEN (not proven) |  |

