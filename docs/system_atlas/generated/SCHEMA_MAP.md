<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Schema Map

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

SCHEMA is not automatically DATA_CONTRACT or dataclass. Relations recorded only if proven.

```text
SRC_SCHEMA_CANDIDATE_COUNT=1626
SRC_ACCEPTED_SCHEMA_COUNT=5
SRC_DATA_CONTRACT_COUNT=2
SRC_TYPE_ONLY_COUNT=1618
SRC_UNADJUDICATED_SCHEMA_CANDIDATE_COUNT=0
SCHEMA_CENSUS_COMPLETE=true
```

Drill-down census: `docs/system_atlas/census/schema_like_src.yaml`, `docs/system_atlas/census/schema_field_inventory.yaml`.

| id | name | schema_kind | status | epistemic | evidence |
| --- | --- | --- | --- | --- | --- |
| SCHEMA:atlas_v1 | system_atlas.v1 | atlas_record_schema | CURRENT_NONCANONICAL | STATUS=ADJUDICATED | ['scripts/ops/system_atlas_v1/constants_v1.py', 'scripts/ops/system_atlas_v1/val |
| SCHEMA:bound_instrument_dataclass_v1 | BoundInstrumentV1 dataclass shape | python_dataclass_implicit_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['src/ops/single_selected_future_runtime_binding_v1/models_v1.py'] |
| SCHEMA:forensic_document_class | DOCUMENT_CLASS forensic header | forensic_document_marker | FORENSIC_REFERENCE_ONLY | STATUS=FORENSIC_RAW | ['docs/forensics/persistence/PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md'] |
| SCHEMA:gfu_snapshot_v1 | governed_futures_universe_snapshot.v1 | evidence_snapshot_serialization | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['src/ops/governed_futures_universe_producer_v1/constants_v1.py', 'src/ops/gover |
| SCHEMA:okx_public_get_envelope | OKX public GET source envelope (forensic) | forensic_raw_http_envelope | FORENSIC_REFERENCE_ONLY | STATUS=FORENSIC_RAW | ['docs/forensics/persistence/PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md'] |
| SCHEMA:pure_stack_numeric_policy_evidence_pack_v1 | productive_pure_stack_numeric_policy_evidence_pack/v1 | json_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['docs/ops/schemas/productive_pure_stack_numeric_policy_evidence_pack_v1.schema. |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority | productive_pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority_decisions/v1 | json_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_candle_mark_ |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m | productive_pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_decisions/v1 | json_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_okx_public_p |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decisions | productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decisions/v1 | json_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pa |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_execution | productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_execution/v1 | json_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pa |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_raw_pt1m_observation | productive_pure_stack_stage2_surface_b_owner_sta_raw_pt1m_observation_input_and_exclusive_tip_proof_decisions/v1 | json_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_raw_pt1m_obs |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer | productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decisions/v1 | json_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_regime_cover |
| SCHEMA:pure_stack_stage2_surface_b_owner_sta_regime_coverage_sta_open_inputs_closeout | productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_sta_open_inputs_closeout_decisions/v1 | json_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_regime_cover |
| SCHEMA:pure_stack_stage2_surface_b_raw_pt1m_input_pack | productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_decisions/v1 | json_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['docs/ops/schemas/productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_de |
| SCHEMA:pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout | productive_pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout/v1 | json_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['docs/ops/schemas/productive_pure_stack_stage2_surface_b_regime_coverage_and_da |
| SCHEMA:ranking_snapshot_v1 | productive_futures_ranking_snapshot.v1 | evidence_snapshot_serialization | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['src/ops/productive_futures_ranking_producer_v1/constants_v1.py', 'src/ops/prod |
| SCHEMA:runtime_binding_v1 | single_selected_future_runtime_binding.v1 | runtime_binding_serialization | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['src/ops/single_selected_future_runtime_binding_v1/constants_v1.py', 'src/ops/s |
| SCHEMA:single_selected_future_selection_v1 | single_selected_future_selection.v1 | selection_snapshot_serialization | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['src/ops/single_selected_future_policy_v1/constants_v1.py'] |

