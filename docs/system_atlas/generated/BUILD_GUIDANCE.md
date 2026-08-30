<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Build Guidance

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

If you change X, inspect the listed contracts and invariants.

### CLOSURE:canary — CANARY

- inspect: `CAPABILITY:cap_11_13_5_live_canary, GATE:live_authorized_false`
- upstream: `GATE:flatten_execute_authority`
- downstream: `OBSERVER:post_action_canary`
- evidence: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`

  - `CAPABILITY:cap_11_13_5_live_canary` transitive upstream: `(none)`
  - `GATE:live_authorized_false` transitive upstream: `(none)`

### CLOSURE:flatten — FLATTEN

- inspect: `GATE:flatten_execute_authority, CAPABILITY:cap_11_13_5_live_canary`
- upstream: ``
- downstream: `OBSERVER:post_action_canary`
- evidence: `src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_execute_authority_v1.py`

  - `GATE:flatten_execute_authority` transitive upstream: `(none)`
  - `CAPABILITY:cap_11_13_5_live_canary` transitive upstream: `(none)`

### CLOSURE:live_readiness — LIVE_READINESS

- inspect: `GATE:live_authorized_false, DOD:program_final, RUNBOOK:canonical_master_runbook`
- upstream: ``
- downstream: ``
- evidence: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`

  - `GATE:live_authorized_false` transitive upstream: `(none)`
  - `DOD:program_final` transitive upstream: `(none)`
  - `RUNBOOK:canonical_master_runbook` transitive upstream: `(none)`

### CLOSURE:native_instrument_binding — NATIVE_INSTRUMENT_BINDING

- inspect: `CAPABILITY:cap_2_4_runtime_binding, BINDER:bound_instrument_v1, DATA_CONTRACT:bound_instrument_v1, SCHEMA:runtime_binding_v1`
- upstream: `CAPABILITY:cap_2_3_single_selected_future`
- downstream: `HOST:cap72_stateful_host`
- evidence: `docs/ops/specs/MASTER_V2_CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1.md`

  - `CAPABILITY:cap_2_4_runtime_binding` transitive upstream: `CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, CAPABILITY:cap_2_3_single_selected_future, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted, OWNER_DECISION:cap23_exclusive_selection`
  - `BINDER:bound_instrument_v1` transitive upstream: `SELECTOR:single_selected_future_policy`
  - `DATA_CONTRACT:bound_instrument_v1` transitive upstream: `(none)`
  - `SCHEMA:runtime_binding_v1` transitive upstream: `(none)`

### CLOSURE:order_submit — ORDER_SUBMIT

- inspect: `TRANSPORT:bound_okx_testnet_http, VENUE_ENDPOINT:okx_trade_order, GATE:live_authorized_false`
- upstream: `AUTH_PRIMITIVE:okx_hmac_sign`
- downstream: ``
- evidence: `src/ops/section_11_12_8_real_productive_testnet_execute_path_unlock_v1/bound_testnet_http_client_v1.py`

  - `TRANSPORT:bound_okx_testnet_http` transitive upstream: `(none)`
  - `VENUE_ENDPOINT:okx_trade_order` transitive upstream: `(none)`
  - `GATE:live_authorized_false` transitive upstream: `(none)`

### CLOSURE:position_observation — POSITION_OBSERVATION

- inspect: `TRANSPORT:bound_okx_testnet_http, VENUE_ENDPOINT:okx_account_positions`
- upstream: `AUTH_PRIMITIVE:okx_hmac_sign`
- downstream: ``
- evidence: `src/ops/section_11_12_8_real_productive_testnet_execute_path_unlock_v1/bound_testnet_http_client_v1.py`

  - `TRANSPORT:bound_okx_testnet_http` transitive upstream: `(none)`
  - `VENUE_ENDPOINT:okx_account_positions` transitive upstream: `(none)`

### CLOSURE:post_action_success — POST_ACTION_SUCCESS

- inspect: `OBSERVER:post_action_canary, GATE:flatten_execute_authority`
- upstream: ``
- downstream: ``
- evidence: `docs/forensics/persistence/registries/INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md`

  - `OBSERVER:post_action_canary` transitive upstream: `(none)`
  - `GATE:flatten_execute_authority` transitive upstream: `(none)`

### CLOSURE:productive_selection — PRODUCTIVE_SELECTION

- inspect: `CAPABILITY:cap_2_3_single_selected_future, SELECTOR:single_selected_future_policy, OWNER_DECISION:cap23_exclusive_selection, SCHEMA:single_selected_future_selection_v1`
- upstream: `CAPABILITY:cap_2_2_ranking, SELECTOR:productive_futures_ranking`
- downstream: `CAPABILITY:cap_2_4_runtime_binding`
- evidence: `docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md`

  - `CAPABILITY:cap_2_3_single_selected_future` transitive upstream: `CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted, OWNER_DECISION:cap23_exclusive_selection`
  - `SELECTOR:single_selected_future_policy` transitive upstream: `(none)`
  - `OWNER_DECISION:cap23_exclusive_selection` transitive upstream: `CAPABILITY:cap_2_1_gfu, CAPABILITY:cap_2_2_ranking, CAPABILITY:cap_2_3_single_selected_future, GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted`
  - `SCHEMA:single_selected_future_selection_v1` transitive upstream: `(none)`

### CLOSURE:productive_universe — PRODUCTIVE_UNIVERSE

- inspect: `CAPABILITY:cap_2_1_gfu, UNIVERSE:governed_futures_universe, INVARIANT:missing_metadata_never_defaulted, GATE:btc_exclusion, SCHEMA:gfu_snapshot_v1`
- upstream: `ADAPTER:okx_public_md_client, VENUE:okx_eea`
- downstream: `CAPABILITY:cap_2_2_ranking`
- evidence: `docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md`

  - `CAPABILITY:cap_2_1_gfu` transitive upstream: `GATE:btc_exclusion, INVARIANT:missing_metadata_never_defaulted`
  - `UNIVERSE:governed_futures_universe` transitive upstream: `(none)`
  - `INVARIANT:missing_metadata_never_defaulted` transitive upstream: `(none)`
  - `GATE:btc_exclusion` transitive upstream: `(none)`
  - `SCHEMA:gfu_snapshot_v1` transitive upstream: `(none)`

