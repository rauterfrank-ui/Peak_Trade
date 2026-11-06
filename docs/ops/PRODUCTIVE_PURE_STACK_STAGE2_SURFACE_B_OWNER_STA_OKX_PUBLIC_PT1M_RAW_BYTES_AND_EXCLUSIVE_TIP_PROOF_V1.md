# Stage-2 Surface B — Owner/STA OKX Public PT1M Raw Bytes and Exclusive Tip Proof v1

```text
DOCUMENT_TYPE=OWNER_STA_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF
STATUS=OWNER_STA_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF_NUMERIC_TIP_DIGEST_PROOF_RESOLVED
DECISION_ID=DEC_RAW_INPUT_PACK_MATERIALIZATION
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
OWNER_GO=OWNER_STA_SURFACE_B_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF_V1
OWNER_GO_BASE_SHA=54642d8250bb59ba58d98da7ce7b6ab52558e43b
SCOPE=STA_AUTHORIZED_DOWNLOAD_RAW_BYTES_DIGEST_AND_NUMERIC_PROOF_ONLY
PARENT_CONTRACT=OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_CONTRACT_READY_NUMERIC_PROOFS_STILL_UNRESOLVED
PARENT_OBSERVATION_PROOF=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_V1.md
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF_DECISIONS_V1.json
SCHEMA=docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_decisions_v1.schema.json
VALIDATOR=src/ops/productive_pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1/
CYBERSECURITY_MIRROR=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF_CYBERSECURITY_MIRROR_V1.md
SEALED_ARTIFACTS=docs/ops/artifacts/productive_pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1/

AUTHORITY_SURFACE=B
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
O4_UNCHANGED=true
O4_PT1H_AS_PT1M_FORBIDDEN=true
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_ROLE=READ_ONLY_CONSUMER
NOTION_SSOT=false
REPOSITORY_IS_SSOT=true

BAR_INTERVAL=PT1M
EXCLUSIVE_TIP_FORMULA=last_finalized_common_bucket_open_event_time_epoch_s+60
AUTHORIZED_NETWORK_FETCH=true
DOWNLOAD_OR_NETWORK_FETCH=true
PROOF_CONTRACT_READY=true
STA_EXTERNAL_INPUT_FIELDS_READY=true
OWNER_PARTITION_SELECTION_READY=false
NUMERIC_PROOFS_RESOLVED=true

PACK_MATERIALIZATION=false
RAW_INPUT_PACK_CREATED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
CAMPAIGN_START=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
PRODUCTIVE_THRESHOLDS_LOOKBACKS=false
TRADING_LOGIC_CHANGE=false
ORDERS_TESTNET_LIVE=false
FILL_PARTITION_BOUNDARIES=false
OWNER_PARTITION_SELECTION=false
INVENTED_VALUES=false
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
WALLCLOCK_AS_DATA_AUTHORITY=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 0. Binding effect

This Owner/STA surface executes the **authorized public OKX download** that the
parent observation-input / exclusive-tip proof contract deferred
(`DOWNLOAD_OR_NETWORK_FETCH=false` there; numeric slots null).

It:

1. fetches venue-native PT1M history candles and mark-price candles for
   `ETH-USDT-SWAP` under Owner-ratified InstrumentBindingV1;
2. captures exact raw HTTP response bytes and request metadata;
3. digests candle, mark, and composed raw-source bytes;
4. keeps only `confirm=1` / venue-finalized rows;
5. joins candle and mark on common PT1M bucket-open event times;
6. proves contiguity, monotonicity, duplicate-freedom, and PT1M alignment;
7. derives
   `exclusive_tip_event_time_epoch_s = last_finalized_common_bucket_open + 60`;
8. publishes an authorized observation-window **candidate** (not a pack).

It does **not**:

- create a raw input pack or flip materialization authorization;
- fill Owner partition boundaries;
- start a campaign;
- flip `INPUT_AUTHORITY` or `RUNTIME_IMPLEMENTED`;
- authorize orders, credentials, testnet, live, or capital movement;
- treat Dashboard, Notion, local OKX archive, fixtures/demo, or O4/PT1H as
  authority;
- use wallclock as tip / observation-window data authority.

```text
AUTHORIZED_NETWORK_FETCH=true
NUMERIC_PROOFS_RESOLVED=true
STA_EXTERNAL_INPUT_FIELDS_READY=true
OWNER_PARTITION_SELECTION_READY=false
PACK_MATERIALIZATION=false
RAW_INPUT_PACK_CREATED=false
```

## 1. Authorized endpoints and request window

```text
AUTHORIZED_ENDPOINTS=
  /api/v5/market/history-candles
  /api/v5/market/history-mark-price-candles
REQUEST_PARAMETERS=instId=ETH-USDT-SWAP&bar=1m&limit=300
REQUEST_LIMITS=CANONICAL_OKX_ENDPOINT_LIMITS_ONLY
PAGE_LIMIT=300
PAGE_LIMIT_SOURCE=scripts/ops/ingest_okx_futures_public_market_data_canonical_dataset_staging_v1.py:PAGE_LIMIT
REQUEST_WINDOW_SOURCE=CANONICAL_OKX_PUBLIC_INGEST_V1_PAGE_LIMIT_300_SINGLE_PAGE_MOST_RECENT_HISTORY_COMMON_FINALIZED_CONTIGUOUS_WINDOW
PAGINATION=SINGLE_PAGE_NO_AFTER_CURSOR_REQUIRED
```

`confirm=1` is enforced as a **row finality filter** (not treated as a silent
server-side substitution). Open tip rows (`confirm=0`) are excluded.

## 2. Sealed numeric tip / digest proof

| Slot | Value |
|------|-------|
| `candle_raw_byte_count` | `29172` |
| `mark_raw_byte_count` | `18436` |
| `candle_raw_digest` | `e1da39436377d5c9eeae2470b7b21041e7894276e0fb32d9e96e2a60b826c739` |
| `mark_raw_digest` | `1a2a9d48dea7fe44663cc9b3f7a422a0ade9e9f19ca4ae6c0c5effab23aec610` |
| `raw_source_digest` | `9ea3edd6b0b7051a647ff3e6dd64da524b0bbb3ca6850a699c37936ad9541a57` |
| `candle_row_count` | `299` |
| `mark_row_count` | `299` |
| `first_finalized_common_bucket_open_event_time_epoch_s` | `1785916740` |
| `last_finalized_common_bucket_open_event_time_epoch_s` | `1785934620` |
| `exclusive_tip_event_time_epoch_s` | `1785934680` |
| `observation_pack_digest` | `null` |

```text
PT1M_ALIGNMENT_PROOF=true
CANDLE_MARK_JOIN_PROOF=true
CONTIGUITY_PROOF=true
DUPLICATE_FREE_PROOF=true
MONOTONICITY_PROOF=true
DIGEST_BOUND_ROW_COUNT_PROOF=true
```

Authorized observation-window candidate:

```text
[1785916740, 1785934680)  # half-open event-time seconds; PT1M bucket opens
```

## 3. Unresolved (out of this scope)

```text
observation_pack_digest
owner_partition_selection
partition_boundaries_event_time_epoch_s
campaign_id
dataset_id
scenario_id
```

## 4. Next action

```text
NEXT_ACTION=AWAIT_OWNER_GO_FOR_RAW_INPUT_PACK_MATERIALIZATION_OR_PARTITION_SELECTION
DO_NOT_MERGE_WITHOUT_OWNER_MERGE_GO=true
```
