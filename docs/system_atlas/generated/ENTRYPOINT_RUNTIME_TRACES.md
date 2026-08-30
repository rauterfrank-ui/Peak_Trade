<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Entrypoint Runtime Traces

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

### EP:cap23_policy — Single selected future policy

- path: `scripts/ops/run_single_selected_future_policy_v1.py`
- class: `PRODUCTIVE_OFFLINE_PRODUCER`
- epistemic: `STATUS=FORENSIC_RAW`
- network: `none_in_policy_producer`
- evidence: `docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md`

  1. `SCRIPT:run_cap23_policy` -> `CAPABILITY:cap_2_3_single_selected_future` gate=`OWNER_DECISION:cap23_exclusive_selection` fail=`fail-closed no selection`

### EP:flatten_execute — Flatten execute authority

- path: `src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_execute_authority_v1.py`
- class: `GATED_MUTATION_PATH`
- epistemic: `STATUS=FORENSIC_RAW`
- network: `may_exist_downstream_NOT_activated`
- evidence: `src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_execute_authority_v1.py`

  1. `GATE:flatten_execute_authority` -> `CAPABILITY:cap_11_13_5_live_canary` gate=`GATE:live_authorized_false` fail=`deny`

- missing_wiring: `OBSERVER:post_action_canary`

### EP:gfu_producer — Governed Futures Universe producer

- path: `scripts/ops/run_governed_futures_universe_producer_v1.py`
- class: `PRODUCTIVE_OFFLINE_PRODUCER`
- epistemic: `STATUS=FORENSIC_RAW`
- network: `Discovery is offline/injected payload in GFU producer itself; public MD client is a separate adapter`
- evidence: `docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md`

  1. `SCRIPT:run_gfu_producer` -> `CAPABILITY:cap_2_1_gfu` gate=`GATE:btc_exclusion` fail=`fail-closed eligibility reject`
  2. `CAPABILITY:cap_2_1_gfu` -> `RUNTIME_COMPONENT:gfu_eligibility` gate=`INVARIANT:missing_metadata_never_defaulted` fail=`MISSING_QUOTE_CURRENCY / exclusion codes`

