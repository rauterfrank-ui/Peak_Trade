<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Project Terminology

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

Seed vocabulary is not complete. Status OPEN means expansion/definition is unproven.

| id | kind | name | status | epistemic | do_not_confuse |
| --- | --- | --- | --- | --- | --- |
| ACRONYM:C1 | ACRONYM | C1 | OPEN | STATUS=CONTRADICTED (both sides preserved) | C2; C3; C4_NAMED_MASTER_SSOT_POINTER; Cap 1 |
| ACRONYM:C2 | ACRONYM | C2 | OPEN | STATUS=CONTRADICTED (both sides preserved) |  |
| ACRONYM:C3 | ACRONYM | C3 | OPEN | STATUS=OPEN (not proven) |  |
| ACRONYM:CAP | ACRONYM | CAP | CURRENT_NONCANONICAL | STATUS=ADJUDICATED | capital; CAPM |
| ACRONYM:CAP23 | ACRONYM | CAP23 | CURRENT_CANONICAL | STATUS=CANONICAL_AUTHORITY | Cap 2.1 GFU; Cap 2.2 ranking; Cap 2.4 binding |
| ACRONYM:DOD | ACRONYM | DoD | CURRENT_NONCANONICAL | STATUS=ADJUDICATED | Mandatory Capability Closure Standard; pytest; PR checklist DoD |
| ACRONYM:EEA | ACRONYM | EEA | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| ACRONYM:FND | ACRONYM | FND | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| ACRONYM:GFU | ACRONYM | GFU | CURRENT_NONCANONICAL | STATUS=ADJUDICATED | OKX instruments listing; ranking snapshot |
| ACRONYM:MMR | ACRONYM | MMR | CURRENT_NONCANONICAL | STATUS=ADJUDICATED | instFamily; Family; unproven architectural MMR kind |
| ACRONYM:OKX | ACRONYM | OKX | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| ACRONYM:PENDING | ACRONYM | PENDING | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | PRE; OPEN |
| ACRONYM:PIT | ACRONYM | PIT | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | PRE; PENDING |
| ACRONYM:PRE | ACRONYM | PRE | OPEN | STATUS=OPEN (not proven) |  |
| ACRONYM:SSOT | ACRONYM | SSOT | CURRENT_NONCANONICAL | STATUS=ADJUDICATED | SSOT child (unproven kind); dashboard as SSOT (forbidden) |
| ACRONYM:XPERP | ACRONYM | XPERP | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| CHILD:nested_structural_child | CHILD | NestedStructuralChild forensic structural type | FORENSIC_REFERENCE_ONLY | STATUS=HISTORICAL |  |
| DOD:capability_closure_standard | DOD | Mandatory Capability Closure Standard | CURRENT_CANONICAL | STATUS=CANONICAL_AUTHORITY |  |
| DOD:cybersecurity_runbook | DOD | Cybersecurity Runbook Definition of Done | CURRENT_NONCANONICAL | STATUS=ADJUDICATED |  |
| DOD:pr_queue_per_pr | DOD | Definition of Done pro PR | CURRENT_NONCANONICAL | STATUS=HISTORICAL |  |
| DOD:program_final | DOD | Program Definition of Done | CURRENT_CANONICAL | STATUS=CANONICAL_AUTHORITY |  |
| DOD:roadmap_phase_generic | DOD | Historical phase/roadmap Definition of Done headings | OPEN | STATUS=OPEN (not proven) |  |
| DOD:vollautonomie_economic_validity | DOD | Definition of Done — Economic Validity | SUPERSEDED | STATUS=HISTORICAL |  |
| DOD:vollautonomie_safety_runtime | DOD | Definition of Done — Safety and Runtime | SUPERSEDED | STATUS=HISTORICAL |  |
| DOD:vollautonomie_trading_logic | DOD | Definition of Done — Trading Logic | SUPERSEDED | STATUS=HISTORICAL |  |
| FAMILY:dashboard_canonical_decision | FAMILY | dashboard family_id canonical_decision | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | strategy visual-map Family; confirm-token FAMILY_*; OKX instFamily |
| FAMILY:dashboard_double_play | FAMILY | dashboard family_id double_play | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| FAMILY:dashboard_dynamic_scope | FAMILY | dashboard family_id dynamic_scope | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | Master V2 architectural Family; OKX instFamily |
| FAMILY:dashboard_economic_summary | FAMILY | dashboard family_id economic_summary | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| FAMILY:dashboard_execution_reconciliation | FAMILY | dashboard family_id execution_reconciliation | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| FAMILY:dashboard_regime_bull_bear | FAMILY | dashboard family_id regime_bull_bear_switch | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| FAMILY:dashboard_risk_sizing_capital | FAMILY | dashboard family_id risk_sizing_capital | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| FAMILY:dashboard_safety_authority | FAMILY | dashboard family_id safety_authority | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| KIND:ACRONYM | TERM | ACRONYM | OPEN | STATUS=ADJUDICATED |  |
| KIND:CHILD | TERM | CHILD | OPEN | STATUS=OPEN (not proven) | SSOT_CHILD; HISTORICAL_CHILD_LEDGER; NestedStructuralChild; Falls-Parent/Child |
| KIND:DOD | TERM | DOD | OPEN | STATUS=ADJUDICATED | Mandatory Capability Closure Standard; tests; acceptance criteria |
| KIND:FAMILY | TERM | FAMILY | OPEN | STATUS=OPEN (not proven) | OKX instFamily; dashboard family_id; research signal family; confirm-token famil |
| KIND:FUNCTIONAL_CORE | TERM | FUNCTIONAL_CORE | OPEN | STATUS=ADJUDICATED |  |
| KIND:MMR | TERM | MMR | OPEN | STATUS=OPEN (not proven) | OKX public/position-tiers mmr maintenance-margin-ratio |
| KIND:SCHEMA | TERM | SCHEMA | OPEN | STATUS=ADJUDICATED | DATA_CONTRACT; dataclass; CONFIG; PROTOCOL |
| KIND:SSOT_CHILD | TERM | SSOT_CHILD | OPEN | STATUS=OPEN (not proven) |  |
| KIND:SYSTEM | TERM | SYSTEM | OPEN | STATUS=ADJUDICATED |  |
| SCHEMA:atlas_v1 | SCHEMA | system_atlas.v1 | CURRENT_NONCANONICAL | STATUS=ADJUDICATED |  |
| SCHEMA:bound_instrument_dataclass_v1 | SCHEMA | BoundInstrumentV1 dataclass shape | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:forensic_document_class | SCHEMA | DOCUMENT_CLASS forensic header | FORENSIC_REFERENCE_ONLY | STATUS=FORENSIC_RAW |  |
| SCHEMA:gfu_snapshot_v1 | SCHEMA | governed_futures_universe_snapshot.v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:okx_public_get_envelope | SCHEMA | OKX public GET source envelope (forensic) | FORENSIC_REFERENCE_ONLY | STATUS=FORENSIC_RAW |  |
| SCHEMA:pure_stack_numeric_policy_evidence_pack_v1 | SCHEMA | productive_pure_stack_numeric_policy_evidence_pack/v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority | SCHEMA | productive_pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority_decisions/v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m | SCHEMA | productive_pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_decisions/v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decisions | SCHEMA | productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decisions/v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_execution | SCHEMA | productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_execution/v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_raw_pt1m_observation | SCHEMA | productive_pure_stack_stage2_surface_b_owner_sta_raw_pt1m_observation_input_and_exclusive_tip_proof_decisions/v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer | SCHEMA | productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decisions/v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_regime_coverage_sta_open_inputs_closeout | SCHEMA | productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_sta_open_inputs_closeout_decisions/v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:pure_stack_stage2_surface_b_raw_pt1m_input_pack | SCHEMA | productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_decisions/v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout | SCHEMA | productive_pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout/v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:ranking_snapshot_v1 | SCHEMA | productive_futures_ranking_snapshot.v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:runtime_binding_v1 | SCHEMA | single_selected_future_runtime_binding.v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| SCHEMA:single_selected_future_selection_v1 | SCHEMA | single_selected_future_selection.v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:bound_instrument | TERM | BoundInstrumentV1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | SCHEMA:runtime_binding_v1 version string; OKX instId |
| TERM:btc_productive_proof_do_not_run | TERM | BTC_PRODUCTIVE_PROOF=DO_NOT_RUN | CURRENT_CANONICAL | STATUS=CANONICAL_AUTHORITY | GATE:btc_exclusion; superseded canary id BTC-USD_UM_XPERP-310404 |
| TERM:canary | TERM | Canary | CURRENT_CANONICAL | STATUS=CANONICAL_AUTHORITY |  |
| TERM:cap23 | TERM | CAP23 | CURRENT_CANONICAL | STATUS=CANONICAL_AUTHORITY |  |
| TERM:capability_closure_standard | TERM | Mandatory Capability Closure Standard | CURRENT_CANONICAL | STATUS=CANONICAL_AUTHORITY | Program Definition of Done; pytest |
| TERM:child_unproven_kind | TERM | Child | OPEN | STATUS=OPEN (not proven) |  |
| TERM:confirm_token | TERM | confirm-token | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:confirm_token_family_matrix | TERM | confirm-token FAMILY_* matrix | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | projection octet family_id; strategy Family; Gate-Familien F1-F6 |
| TERM:ddo_non_semantic_capture | TERM | DDO non-semantic decision-spine capture | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:ddo_offline_contract_and_ledger | TERM | DDO offline contract and ledger foundation | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:ddo_offline_control_plane | TERM | DDO offline control plane | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:ddo_offline_evaluation_engine | TERM | DDO offline evaluation engine | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:ddo_offline_learning_validation_shadow | TERM | DDO offline learning validation shadow | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:ddo_offline_owner_bindings_and_drift | TERM | DDO offline owner bindings and drift contracts | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:document_class | TERM | DOCUMENT_CLASS | FORENSIC_REFERENCE_ONLY | STATUS=FORENSIC_RAW |  |
| TERM:double_play | TERM | Double Play | STILL_CURRENT_AND_CANONICALLY_SUPPORTED | STATUS=CANONICAL_AUTHORITY | ops.double_play.evaluate_double_play (quarantined projection); dashboard family_ |
| TERM:dynamic_scope | TERM | Dynamic Scope | CURRENT_IMPLEMENTATION_WITHOUT_PROVEN_CANONICAL_SUPPORT | STATUS=ADJUDICATED | dashboard family_id dynamic_scope |
| TERM:fail_closed | TERM | fail-closed | CURRENT_CANONICAL | STATUS=CANONICAL_AUTHORITY |  |
| TERM:falls_parent_child | TERM | Falls-Parent/Child forensic coupling | FORENSIC_REFERENCE_ONLY | STATUS=HISTORICAL |  |
| TERM:family_polyvalent | TERM | Family | OPEN | STATUS=CONTRADICTED (both sides preserved) | Child; SSOT child; OKX instFamily; OKX mmr |
| TERM:flatten | TERM | Flatten | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:focused_full_noop | TERM | FOCUSED / FULL / NO_OP | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:gate_families_f1_f6 | TERM | Gate-Familien F1–F6 | FORENSIC_REFERENCE_ONLY | STATUS=HISTORICAL |  |
| TERM:historical_child_ledger | TERM | HISTORICAL_CHILD_LEDGER child_id | FORENSIC_REFERENCE_ONLY | STATUS=HISTORICAL |  |
| TERM:information_corpus | TERM | Information Corpus | FORENSIC_REFERENCE_ONLY | STATUS=FORENSIC_RAW |  |
| TERM:levelup | TERM | LevelUp | OPEN | STATUS=OPEN (not proven) |  |
| TERM:live_authorized | TERM | LIVE_AUTHORIZED | CURRENT_CANONICAL | STATUS=CANONICAL_AUTHORITY | implementation presence; HMAC signer existence |
| TERM:map_of_truth | TERM | Map of Truth | CURRENT_NONCANONICAL | STATUS=NAVIGATION_ONLY |  |
| TERM:master_v2 | TERM | Master V2 | STILL_CURRENT_AND_CANONICALLY_SUPPORTED | STATUS=CANONICAL_AUTHORITY |  |
| TERM:mmr_polyvalent | TERM | MMR | OPEN | STATUS=CONTRADICTED (both sides preserved) | Family; instFamily |
| TERM:nested_structural_child | TERM | NestedStructuralChild | FORENSIC_REFERENCE_ONLY | STATUS=HISTORICAL |  |
| TERM:no_family_ontology | TERM | NO_FAMILY_ONTOLOGY | OPEN | STATUS=FORENSIC_RAW |  |
| TERM:owner_go | TERM | Owner-GO | CURRENT_CANONICAL | STATUS=CANONICAL_AUTHORITY |  |
| TERM:pure_stack | TERM | Pure Stack | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | Family/Child hierarchy (unproven) |
| TERM:quoteCcy | TERM | quoteCcy | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |  |
| TERM:schema_version | TERM | SCHEMA_VERSION | CURRENT_NONCANONICAL | STATUS=ADJUDICATED | JSON Schema files under docs/ops/schemas; dataclass TYPE_ONLY |
| TERM:settleCcy | TERM | settleCcy | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | quoteCcy; uly; baseCcy |
| TERM:shadow | TERM | Shadow | CURRENT_NONCANONICAL | STATUS=ADJUDICATED | TESTNET; LIVE; INTERNAL_SIMULATED_EXECUTION |
| TERM:sign_okx_request_v1 | TERM | sign_okx_request_v1 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | July-17 audit claimed absence; C-OKX-AUDIT-SIGNED-REST-001 |
| TERM:ssot_child_unproven | TERM | SSOT child | OPEN | STATUS=OPEN (not proven) |  |
| TERM:trading_decision_core | TERM | TRADING_DECISION_CORE | SUPERSEDED | STATUS=HISTORICAL |  |
| TERM:uly | TERM | uly | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | quoteCcy; instId; instFamily |
| TERM:x_simulated_trading | TERM | x-simulated-trading | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | LIVE_AUTHORIZED; TESTNET_AUTHORIZED |

## Historical origin/main archaeology (scoped)

SSOT_CHILD literal remains absent from origin/main history. OPEN expansions remain OPEN.

| term | spelling | expansion | status | first_commit |
| --- | --- | --- | --- | --- |
| X-Perp | X-Perp | OPEN | CURRENT_NONCANONICAL | 8457850cbf10a4ec040d320ac9bb84d2fc63c844 |
| SSOT_CHILD | SSOT_CHILD | OPEN | SEARCHED_BUT_NO_EVIDENCE_FOUND | none |
| Gate-Familien | Gate-Familien | OPEN | HISTORICAL_ONLY | e94ff20c8ffb6f7e69152bcb9e2972165897cc43 |
| NestedStructuralChild | NestedStructuralChild | OPEN | FORENSIC_REFERENCE_ONLY | b81d5181c04c2a3dc156d089fc8790ed4419782b |

