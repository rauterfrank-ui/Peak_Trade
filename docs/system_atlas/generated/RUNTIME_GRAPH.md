<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Runtime graph — what calls/consumes/produces what?

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

Control/data/network edges are typed. A CALLS edge does not imply a data dependency.

| id | source | type | target | epistemic | evidence |
| --- | --- | --- | --- | --- | --- |
| REL:r_cap21_produces_universe | CAPABILITY:cap_2_1_gfu | PRODUCES | UNIVERSE:governed_futures_universe | STATUS=ADJUDICATED | src/ops/governed_futures_universe_producer_v1/producer_v1.py |
| REL:r_cap22_ranks_universe | SELECTOR:productive_futures_ranking | RANKS | UNIVERSE:governed_futures_universe | STATUS=ADJUDICATED | src/ops/productive_futures_ranking_producer_v1/policy_v1.py |
| REL:r_cap23_selects | SELECTOR:single_selected_future_policy | SELECTS | SELECTOR:productive_futures_ranking | STATUS=ADJUDICATED | src/ops/single_selected_future_policy_v1/producer_v1.py |
| REL:r_cap24_binds | BINDER:bound_instrument_v1 | BINDS | SELECTOR:single_selected_future_policy | STATUS=ADJUDICATED | src/ops/single_selected_future_runtime_binding_v1/binding_gate_v1.py |
| REL:r_dp_composition_consumes_capital_slot | RUNTIME_COMPONENT:dp_composition | CONSUMES | RUNTIME_COMPONENT:dp_capital_slot | STATUS=FORENSIC_RAW | src/trading/master_v2/double_play_composition.py |
| REL:r_dp_composition_consumes_suitability | RUNTIME_COMPONENT:dp_composition | CONSUMES | RUNTIME_COMPONENT:dp_suitability | STATUS=FORENSIC_RAW | src/trading/master_v2/double_play_composition.py |
| REL:r_dp_composition_consumes_survival | RUNTIME_COMPONENT:dp_composition | CONSUMES | RUNTIME_COMPONENT:dp_survival | STATUS=FORENSIC_RAW | src/trading/master_v2/double_play_composition.py,docs/ops/specs/MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md |
| REL:r_dp_core_wiring_calls_decision_packet | RUNTIME_COMPONENT:dp_core_wiring | CALLS | RUNTIME_COMPONENT:mv2_decision_packet | STATUS=FORENSIC_RAW | src&#47;trading&#47;master_v2&#47;double_play_core_wiring_v1.py |
| REL:r_dp_core_wiring_calls_integrated_replay | RUNTIME_COMPONENT:dp_core_wiring | CALLS | RUNTIME_COMPONENT:mv2_integrated_replay | STATUS=FORENSIC_RAW | src&#47;trading&#47;master_v2&#47;double_play_core_wiring_v1.py |
| REL:r_dp_core_wiring_calls_quarantine | RUNTIME_COMPONENT:dp_core_wiring | CALLS | RUNTIME_COMPONENT:dp_sole_authority_quarantine | STATUS=FORENSIC_RAW | src&#47;trading&#47;master_v2&#47;double_play_core_wiring_v1.py |
| REL:r_dp_state_calls | RUNTIME_COMPONENT:dp_composition | READS | RUNTIME_COMPONENT:dp_state | STATUS=FORENSIC_RAW | src/trading/master_v2/double_play_composition.py |
| REL:r_flatten_gates | GATE:flatten_execute_authority | GATES | CAPABILITY:cap_11_13_5_live_canary | STATUS=FORENSIC_RAW | src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_execute_authority_v1.py |
| REL:r_gfu_eligibility_filters | RUNTIME_COMPONENT:gfu_eligibility | FILTERS | UNIVERSE:governed_futures_universe | STATUS=FORENSIC_RAW | src/ops/governed_futures_universe_producer_v1/eligibility_v1.py |
| REL:r_host72_consumes_binding | HOST:cap72_stateful_host | CONSUMES | BINDER:bound_instrument_v1 | STATUS=ADJUDICATED | src/ops/single_future_stateful_no_order_runtime_activation_v1/host_binding_v1.py |
| REL:r_live_auth_denies | GATE:live_authorized_false | DENIES | CAPABILITY:cap_11_13_5_live_canary | STATUS=CANONICAL_AUTHORITY | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:r_md_client_fetches_instruments | ADAPTER:okx_public_md_client | FETCHES | VENUE_ENDPOINT:okx_public_instruments | STATUS=FORENSIC_RAW | src/ops/okx_public_market_data_client_v1.py |
| REL:r_post_action_observes | OBSERVER:post_action_canary | OBSERVES | GATE:flatten_execute_authority | STATUS=OPEN (not proven) | docs/forensics/persistence/registries/INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md |
| REL:r_script_cap23_calls | SCRIPT:run_cap23_policy | CALLS | CAPABILITY:cap_2_3_single_selected_future | STATUS=FORENSIC_RAW | docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md |
| REL:r_script_gfu_calls_cap21 | SCRIPT:run_gfu_producer | CALLS | CAPABILITY:cap_2_1_gfu | STATUS=FORENSIC_RAW | docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md |
| REL:r_transport_signs | TRANSPORT:bound_okx_testnet_http | SIGNS | AUTH_PRIMITIVE:okx_hmac_sign | STATUS=FORENSIC_RAW | src/ops/section_11_12_8_real_productive_testnet_execute_path_unlock_v1/bound_testnet_http_client_v1.py |

