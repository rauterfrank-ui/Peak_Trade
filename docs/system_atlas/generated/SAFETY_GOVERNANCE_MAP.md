<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Safety / Governance Map

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

## Mechanisms

| id | kind | fail | status |
| --- | --- | --- | --- |
| GATE:btc_exclusion | GATE | True | CURRENT_CANONICAL |
| GATE:flatten_execute_authority | GATE | True | CURRENT_NONCANONICAL |
| GATE:flatten_live_wire | GATE | True | CURRENT_NONCANONICAL |
| GATE:full_core_durable_filegate_join_v1 | GATE | True | CURRENT_NONCANONICAL |
| GATE:full_core_live_path_execution_boundary_halt_before_wire_v1 | GATE | True | CURRENT_NONCANONICAL |
| GATE:full_core_live_path_frozen_pretrade_conjunction_v1 | GATE | True | CURRENT_NONCANONICAL |
| GATE:full_core_live_path_identity_v1 | GATE | True | CURRENT_NONCANONICAL |
| GATE:full_core_live_path_restart_gate_v1 | GATE | True | CURRENT_NONCANONICAL |
| GATE:full_core_live_path_standing_live_gates_v1 | GATE | True | CURRENT_NONCANONICAL |
| GATE:full_core_owner_one_shot_permit_v1 | GATE | True | CURRENT_NONCANONICAL |
| GATE:kill_switch_durable_filegate_v1 | GATE | True | CURRENT_NONCANONICAL |
| GATE:live_authorized_false | GATE | True | CURRENT_CANONICAL |
| GATE:max_positions_1 | GATE | True | CURRENT_CANONICAL |
| GATE:position_observation_freshness | GATE | True | CURRENT_NONCANONICAL |
| GATE:target_position_state | GATE | True | CURRENT_NONCANONICAL |
| GUARD:economic_diagnostic_optimization_boundary | GUARD | True | CURRENT_NONCANONICAL |

## Mutation-path chains (actual wiring; missing edges explicit)

### CHAIN:canary_flatten

- epistemic: `STATUS=OPEN (not proven)`
- chain: `GATE:live_authorized_false -> GATE:flatten_execute_authority -> CAPABILITY:cap_11_13_5_live_canary -> OBSERVER:post_action_canary`
- missing: `OBSERVER:post_action_canary`
- evidence: `docs/forensics/persistence/registries/INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md`

### CHAIN:full_core_live_path_halt_before_wire

- epistemic: `STATUS=FORENSIC_RAW`
- chain: `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1 -> RUNTIME_COMPONENT:full_core_live_path_venue_translation_v1 -> GATE:full_core_live_path_frozen_pretrade_conjunction_v1 -> GATE:full_core_live_path_execution_boundary_halt_before_wire_v1 -> GATE:full_core_durable_filegate_join_v1 -> GATE:full_core_owner_one_shot_permit_v1 -> GATE:full_core_live_path_standing_live_gates_v1 -> GATE:full_core_live_path_identity_v1 -> GATE:live_authorized_false`
- missing: `(none recorded)`
- evidence: `src/ops/full_core_live_path_composition_root_v1/execution_boundary_v1.py`

### CHAIN:gfu_eligibility

- epistemic: `STATUS=FORENSIC_RAW`
- chain: `ADAPTER:okx_public_md_client -> RUNTIME_COMPONENT:gfu_eligibility -> GATE:btc_exclusion -> UNIVERSE:governed_futures_universe`
- missing: `(none recorded)`
- evidence: `src/ops/governed_futures_universe_producer_v1/eligibility_v1.py`

### CHAIN:order_submit_standing_deny

- epistemic: `STATUS=ADJUDICATED`
- chain: `GATE:live_authorized_false -> TRANSPORT:bound_okx_testnet_http -> VENUE_ENDPOINT:okx_trade_order`
- missing: `(none recorded)`
- evidence: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`

