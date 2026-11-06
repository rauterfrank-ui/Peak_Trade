# Stage-2 Surface B — Owner/STA Raw PT1M Observation Input and Exclusive Tip Proof v1

```text
DOCUMENT_TYPE=OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF
STATUS=OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_CONTRACT_READY_NUMERIC_PROOFS_STILL_UNRESOLVED
DECISION_ID=DEC_RAW_INPUT_PACK_MATERIALIZATION
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
OWNER_GO=OWNER_STA_SURFACE_B_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_V1
OWNER_GO_BASE_SHA=86d5eb3893647c8a77233569cccbd106245e5e09
SCOPE=STA_INPUT_PROOF_DOCS_MANIFEST_SCHEMA_VALIDATOR_EVIDENCE_ONLY
PARENT_MATERIALIZATION=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISION_V1.md
PARENT_RAW_INPUT_PACK=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md
PARENT_TRIAD=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_DECISIONS_V1.json
SCHEMA=docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_raw_pt1m_observation_input_and_exclusive_tip_proof_decisions_v1.schema.json
VALIDATOR=src/ops/productive_pure_stack_stage2_surface_b_owner_sta_raw_pt1m_observation_input_and_exclusive_tip_proof_v1/
CYBERSECURITY_MIRROR=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_CYBERSECURITY_MIRROR_V1.md

AUTHORITY_SURFACE=B
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
O4_UNCHANGED=true
O4_PT1H_AS_PT1M_FORBIDDEN=true
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_ROLE=READ_ONLY_CONSUMER
NOTION_SSOT=false
REPOSITORY_IS_SSOT=true

BAR_INTERVAL=PT1M
CANDLE_EVENT_TIME_SEMANTICS=PT1M_BUCKET_OPEN_EVENT_TIME
MARK_EVENT_TIME_SEMANTICS=PT1M_BUCKET_OPEN_EVENT_TIME
EXCLUSIVE_TIP_FORMULA=last_finalized_bar_open_event_time_epoch_s+60
DOWNLOAD_OR_NETWORK_FETCH_POLICY=STA_EXPLICITLY_AUTHORIZED_ONLY
DOWNLOAD_OR_NETWORK_FETCH=false
PROOF_CONTRACT_READY=true
STA_EXTERNAL_INPUT_FIELDS_READY=false
OWNER_PARTITION_SELECTION_READY=false
NUMERIC_PROOFS_RESOLVED=false

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
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 0. Binding effect

This Owner/STA surface publishes the **observation-input and exclusive-tip proof
contract** under `DEC_RAW_INPUT_PACK_MATERIALIZATION` after Owner authorize-value
`AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION`.

It:

1. classifies authorized vs forbidden venue-native PT1M input sources;
2. binds the Owner-ratified InstrumentBindingV1 for ETH-USDT-SWAP;
3. freezes exclusive-tip derivation as
   `last_finalized_bar_open_event_time_epoch_s+60` with PT1M alignment;
4. records all required finalize/join/contiguity/digest proof rules;
5. keeps every concrete numeric proof slot `null` because
   `DOWNLOAD_OR_NETWORK_FETCH=false` and no Surface-B raw PT1M pack exists;
6. keeps pack materialization, campaign start, partition fill, and authority
   flips false.

It does **not**:

- download or network-fetch venue rows;
- invent tip, digests, row counts, or observation windows;
- create a raw input pack;
- fill Owner partition boundaries;
- flip `RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED`, `INPUT_AUTHORITY`, or
  `RUNTIME_IMPLEMENTED`;
- authorize orders, credentials, testnet, live, or capital movement;
- make Dashboard, Notion, OKX archive, fixture/demo, or O4/PT1H an authority.

```text
PROOF_CONTRACT_READY=true
STA_EXTERNAL_INPUT_FIELDS_READY=false
OWNER_PARTITION_SELECTION_READY=false
NUMERIC_PROOFS_RESOLVED=false
PACK_MATERIALIZATION=false
RAW_INPUT_PACK_CREATED=false
DOWNLOAD_OR_NETWORK_FETCH=false
```

## 1. Authorized source classification

Authorized only:

```text
VENUE_NATIVE_OKX_PUBLIC_HISTORY_CANDLES_PT1M_CONFIRM_1
  = venue://okx/public/rest/v5/market/history-candles?bar=1m&confirm=1
VENUE_NATIVE_OKX_PUBLIC_HISTORY_MARK_PRICE_CANDLES_PT1M_CONFIRM_1
  = venue://okx/public/rest/v5/market/history-mark-price-candles?bar=1m&confirm=1
```

Forbidden:

```text
DASHBOARD_SOURCE
OKX_ARCHIVE_AS_AUTHORITY
FIXTURE_DEMO_SYNTHETIC_SOURCE
O4_PT1H_AS_PT1M_AUTHORITY
CANDLE_CLOSE_AS_MARK
NOTION_AS_AUTHORITY
```

## 2. InstrumentBindingV1

```text
venue=okx
canonical_instrument_id=inst-eth-usdt-perp
venue_instrument_id=ETH-USDT-SWAP
contract_type=perpetual
market_type=futures
quote_currency=USDT
settlement_currency=USDT
```

Exact field match required. String-name similarity inference is forbidden.

## 3. Exclusive tip and event-time rules

```text
BAR_INTERVAL=PT1M
CANDLE_EVENT_TIME_SEMANTICS=PT1M_BUCKET_OPEN_EVENT_TIME
MARK_EVENT_TIME_SEMANTICS=PT1M_BUCKET_OPEN_EVENT_TIME
REQUIRE_FINALIZED_CANDLES=true
REQUIRE_FINALIZED_MARKS=true
REQUIRE_CANDLE_MARK_BUCKET_JOIN=true
OPEN_BUCKET_AT_AS_OF_FORBIDDEN=true
BAR_AFTER_AS_OF_FORBIDDEN=true
DERIVE_EXCLUSIVE_TIP=true
EXCLUSIVE_TIP_FORMULA=last_finalized_bar_open_event_time_epoch_s+60
REQUIRE_EXCLUSIVE_TIP_PT1M_ALIGNMENT=true
REQUIRE_CONTIGUITY_PROOF=true
REQUIRE_DUPLICATE_FREE_EVENT_TIME_KEYS=true
REQUIRE_MONOTONIC_EVENT_TIME=true
REQUIRE_INSTRUMENT_CONSISTENCY=true
REQUIRE_OBSERVATION_PACK_DIGEST=true
REQUIRE_RAW_SOURCE_DIGEST=true
REQUIRE_DIGEST_BOUND_ROW_COUNTS=true
REQUIRE_FIRST_AND_LAST_EVENT_TIME_PROOF=true
```

Rule proofs on this surface are `true`. Concrete epoch/row/digest proofs remain
`false` / `null` until a separate STA-explicitly-authorized fetch or immutable
pack bytes are supplied.

## 4. Numeric proof slots (still null)

| Slot | Value |
|------|-------|
| `candle_row_count` | `null` |
| `mark_row_count` | `null` |
| `first_finalized_bucket_open_event_time_epoch_s` | `null` |
| `last_finalized_bucket_open_event_time_epoch_s` | `null` |
| `exclusive_tip_event_time_epoch_s` | `null` |
| `observation_pack_digest` | `null` |
| `raw_source_digest` | `null` |

```text
DIGEST_PROVENANCE_STATUS=UNRESOLVED_NO_AUTHORIZED_PACK_OR_RAW_BYTES
INVENTED_VALUES=false
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
```

## 5. Readiness

```text
PROOF_CONTRACT_READY=true
STA_EXTERNAL_INPUT_FIELDS_READY=false
OWNER_PARTITION_SELECTION_READY=false
NUMERIC_PROOFS_RESOLVED=false
```

`STA_EXTERNAL_INPUT_FIELDS_READY=false` because tip/digest/row-count values are
still unresolved. Owner partition selection remains not ready until an
authorized exclusive tip and observation window exist.

## 6. Non-negotiable invariants

```text
INV_AUTHORIZED_SOURCE_ONLY=true
INV_INSTRUMENTBINDINGV1_EXACT=true
INV_EXCLUSIVE_TIP_FORMULA_FROZEN=true
INV_NUMERIC_PROOF_SLOTS_NULL_WITHOUT_AUTHORIZED_FETCH_OR_PACK=true
INV_NO_DOWNLOAD_ON_THIS_SURFACE=true
INV_NO_INVENTED_TIP_OR_DIGEST=true
INV_PACK_MATERIALIZATION_REMAINS_FALSE=true
INV_CAMPAIGN_START_REMAINS_FALSE=true
INV_INPUT_AUTHORITY_REMAINS_FALSE=true
INV_RUNTIME_IMPLEMENTED_REMAINS_FALSE=true
INV_NO_PARTITION_FILL=true
INV_ORDERS_TESTNET_LIVE_REMAINS_FALSE=true
INV_DASHBOARD_CONSUMER_ONLY=true
```

## 7. Next action

A later Owner/STA GO must explicitly authorize download/network fetch
(`DOWNLOAD_OR_NETWORK_FETCH` policy remains `STA_EXPLICITLY_AUTHORIZED_ONLY`)
or supply digest-bound immutable pack/raw bytes from an already authorized path
before concrete tip/row/digest proofs may be filled. Until then:

```text
NEXT_ACTION=AWAIT_STA_EXPLICIT_DOWNLOAD_OR_AUTHORIZED_PACK_BYTES_FOR_NUMERIC_TIP_PROOF
DO_NOT_MERGE_WITHOUT_OWNER_MERGE_GO=true
```
