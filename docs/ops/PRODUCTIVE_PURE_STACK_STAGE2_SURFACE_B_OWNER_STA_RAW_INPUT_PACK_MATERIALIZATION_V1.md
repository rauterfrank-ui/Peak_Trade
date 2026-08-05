# Stage-2 Surface B — Owner/STA Raw Input Pack Materialization Execution v1

```text
DOCUMENT_TYPE=OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_EXECUTION
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION
STATUS=OWNER_STA_RAW_INPUT_PACK_MATERIALIZED_OBSERVATION_DIGEST_COMPUTED_REMAINING_NULL
DECISION_ID=DEC_RAW_INPUT_PACK_MATERIALIZATION
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
OWNER_GO=OWNER_STA_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION_V1
OWNER_GO_BASE_SHA=24da36c1b4ded14a376d9f73555a0cba28b41204
SCOPE=RAW_INPUT_PACK_MATERIALIZATION_ONLY
USE_RECORDED_INSTANCE_VALUES=true
PARENT_MATERIALIZATION_DECISION=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISION_V1.md
PARENT_OKX_TIP_PROOF=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF_V1.md
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISIONS_EXECUTION_V1.json
SCHEMA=docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_execution_v1.schema.json
VALIDATOR=src/ops/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_v1/
CYBERSECURITY_MIRROR=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_CYBERSECURITY_MIRROR_EXECUTION_V1.md
SEALED_ARTIFACTS=docs/ops/artifacts/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_v1/

AUTHORITY_SURFACE=B
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
O4_UNCHANGED=true
O4_PT1H_AS_PT1M_FORBIDDEN=true
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_ROLE=READ_ONLY_CONSUMER
NOTION_SSOT=false
REPOSITORY_IS_SSOT=true

PACK_MATERIALIZATION=true
RAW_INPUT_PACK_CREATED=true
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=true
CAMPAIGN_START=false
CAMPAIGN_START_AUTHORIZED=false
CAMPAIGN_STARTED=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
PRODUCTIVE_NUMERIC_VALUES_SET=0
PRODUCTIVE_THRESHOLDS_LOOKBACKS=false
TRADING_LOGIC_CHANGE=false
ORDERS_TESTNET_LIVE=false
INVENTED_VALUES=false
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
CAMPAIGN_ID_EXPLICIT_LEAVE_NULL=true
REGIME_COVERAGE_LEAVE_NULL_UNTIL_STA_PRODUCER_PROOF=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 0. Binding effect

This Owner/STA surface executes **raw input-pack materialization only** under
`DEC_RAW_INPUT_PACK_MATERIALIZATION`, bound to Owner-GO baseline
`24da36c1b4ded14a376d9f73555a0cba28b41204` (`origin&#47;main` after instance-values fill merge).

It:

1. reuses recorded Owner/STA instance values (`USE_RECORDED_INSTANCE_VALUES=true`);
2. rebuilds PT1M finalized bars from sealed OKX tip-proof candle/mark raw bytes
   (no network fetch in this GO);
3. materializes immutable `ObservationPackV1` via the existing Surface-B pack
   builder;
4. seals `observation_pack_digest=268b2e67b350bfa0cf2310a75b1d2710a45dca277b182205dfe12692131a0676`;
5. keeps `campaign_id` and regime-coverage slots explicitly null;
6. keeps campaign start, INPUT_AUTHORITY, RUNTIME_IMPLEMENTED, regime-coverage
   producer availability, productive thresholds/lookbacks, trading-logic change,
   Dashboard authority, and orders/testnet/live false or NONE.

It does **not**:

- invent `campaign_id`, regime coverage, purge/embargo/fold_sizes numerics;
- start a Surface-B campaign or evidence collector;
- flip `INPUT_AUTHORITY` or `RUNTIME_IMPLEMENTED`;
- authorize orders, credentials, testnet, live, or capital movement;
- make Dashboard or Notion an authority.

## 1. Recorded instance values used

| Field | Value |
|-------|-------|
| `dataset_id` | `surface_b_eth_usdt_swap_pt1m_okx_public_tip1785934680_v1` |
| `scenario_id` | `surface_b_regime_coverage_structural_partition_v1` |
| `seed` | `5745001` |
| `event_time_epoch_s` | `1785934680` |
| `raw_source_digest` | `9ea3edd6b0b7051a647ff3e6dd64da524b0bbb3ca6850a699c37936ad9541a57` |
| `partition_boundaries_event_time_epoch_s` | `[1785916740, 1785921240, 1785925740, 1785930240, 1785934680]` |
| `fold_ids` | `['train', 'calibration', 'validation', 'holdout']` |
| `bootstrap_seeds` | `[574500101, 574500102, 574500103, 574500104]` |
| `instrument_binding` | Owner-ratified InstrumentBindingV1 (ETH-USDT-SWAP) |
| `campaign_id` | `null` (explicit leave-null) |
| `regime_coverage_counts` | `null` |
| `regime_coverage_instance` | `null` |

## 2. Sealed materialization proof

| Slot | Value |
|------|-------|
| `observation_pack_digest` | `268b2e67b350bfa0cf2310a75b1d2710a45dca277b182205dfe12692131a0676` |
| `config_digest` | `577a327df1a7bcfc8be394cca6db370f7d33675c92c80432d7d069dae5c6c419` |
| `repository_sha` | `24da36c1b4ded14a376d9f73555a0cba28b41204` |
| `bar_count` | `299` |
| `first_bar_open_event_time_epoch_s` | `1785916740` |
| `last_bar_open_event_time_epoch_s` | `1785934620` |
| `exclusive_tip_event_time_epoch_s` | `1785934680` |
| `ingestion_timestamp` | `2026-08-05T12:58:48Z` |
| `finalization_timestamp` | `2026-08-05T12:58:49Z` |
| `observation_pack_canonical_json_sha256` | `af3ef5f70315e80f1b0e48769b02fbe1b479456526946405e972ef38908f6ff4` |

```text
PACK_MATERIALIZATION=true
RAW_INPUT_PACK_CREATED=true
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=true
CAMPAIGN_START=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
```

## 3. Remaining null (out of this scope)

```text
campaign_id
regime_coverage_counts
regime_coverage_instance
```

## 4. Explicit non-effects

```text
CAMPAIGN_START=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
PRODUCTIVE_THRESHOLDS_LOOKBACKS=false
TRADING_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
ORDERS_TESTNET_LIVE=false
INVENTED_VALUES=false
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
```

## 5. Next action

Regime-coverage STA producer proof and Surface-B pack input-gap closeout are
executed under a separate Owner GO:

`docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_REGIME_COVERAGE_AND_DASHBOARD_INPUT_GAP_CLOSEOUT_V1.md`

```text
NEXT_ACTION=AWAIT_OWNER_GO_FOR_COMMIT_PUSH_PR_OR_CAMPAIGN_ID_OR_DECISION_PACKET_SYNC
DO_NOT_MERGE_WITHOUT_OWNER_MERGE_GO=true
```
