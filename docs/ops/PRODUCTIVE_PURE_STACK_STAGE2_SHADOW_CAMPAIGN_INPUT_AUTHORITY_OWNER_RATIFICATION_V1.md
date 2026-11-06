# Stage-2 Shadow Campaign Input Authority — Owner Ratification v1

```text
DOCUMENT_TYPE=OWNER_AUTHORITY_RATIFICATION
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY
STATUS=OWNER_RATIFIED_BOUNDED_IMPLEMENTATION_AUTHORIZED
BASELINE_ORIGIN_MAIN_SHA=55922609182a3166320c0a66a3a0b7cda5c13090
PARENT_TWO_STAGE=docs/ops/PRODUCTIVE_PURE_STACK_OWNER_VALUES_TWO_STAGE_RATIFICATION_V1.md
CALIBRATION_PROTOCOL=docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md
SHADOW_CAMPAIGN=docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_SHADOW_CAMPAIGN_V1.md
IMPLEMENTATION_PLAN=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_IMPLEMENTATION_PLAN_V1.md
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_DECISIONS_V1.json

SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
AUTHORITY_SURFACE=B
O4_UNCHANGED=true
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_ROLE=READ_ONLY_CONSUMER
RESULTV1_MAPPING_AUTHORIZED=false
NEW_TRADING_AUTHORITY_AUTHORIZED=false
INPUT_AUTHORITY=false
INPUT_AUTHORITY_FUTURES_INPUT_SNAPSHOT=false
INPUT_AUTHORITY_SURVIVAL_ENVELOPE=false
INPUT_AUTHORITY_SUITABILITY_PROJECTION=false
INPUT_AUTHORITY_CAPITAL_SLOT_CONFIG=false
INPUT_AUTHORITY_CAPITAL_SLOT_STATE_INIT=false
RUNTIME_IMPLEMENTED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
PRODUCTIVE_NUMERIC_VALUES_SET=0
PRODUCTIVE_CALIBRATION_AUTHORIZED=false
STAGE1_PRODUCERS_PRODUCTIVE_ACTIVATION=false
LIVE_ORDERS=false
TESTNET_ORDERS=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
ARCHIVE_MUTATIONS=false
CORE_LOGIC_CHANGE=false
OWNER_MERGE_REQUIRED=true
```

## 0. Binding effect

This document is the Owner ratification of the Stage-2 Shadow Campaign Input
Authority decisions required before a dedicated PT1M
`PUBLIC_MARKET_FINALIZED_BARS` export, Campaign binder, and structural
manifest builders may be implemented.

It:

1. ratifies Authority Surface **B** (dedicated PT1M finalized-OHLCV shadow
   calibration producer under the sole trading authority);
2. ratifies price semantics, instrument binding, dataset identity, finality,
   partition, walk-forward, bootstrap, stress, and sequence/layer authorities
   exactly as listed below;
3. authorizes one bounded implementation scope matching §11;
4. keeps all `INPUT_AUTHORITY_*` flags false and sets zero productive numeric
   values.

It does **not**:

- authorize productive calibration or threshold promotion;
- flip runtime or input authority;
- mutate trading logic, O4, dashboards, or archives;
- authorize orders, paper exchange, testnet, live trading, or credentials;
- ratify numeric Owner magnitudes (purge/embargo sizes, fold sizes, bootstrap
  block length/path count, stress magnitudes).

```text
OWNERSHIP_MODEL_RATIFIED=true
BOUNDED_IMPLEMENTATION_AUTHORIZED=true
PRODUCTIVE_EMISSION_AUTHORIZED=false
PRODUCTIVE_BINDING_AUTHORIZED=false
NUMERIC_OWNER_VALUE_RATIFICATION=false
```

## 1. Non-negotiable invariants

```text
INV_AUTHORITY_SURFACE_B_ONLY=true
INV_O4_UNCHANGED=true
INV_DASHBOARD_NOT_SOURCE_AUTHORITY=true
INV_SOLE_TRADING_AUTHORITY_ONLY=true
INV_INPUT_AUTHORITY_REMAINS_FALSE=true
INV_NO_PRODUCTIVE_NUMERIC_VALUES=true
INV_NO_RESULTV1_MAPPING=true
INV_NO_CMC_VOLATILITY_AS_REALIZED_VOLATILITY=true
INV_NO_PARALLEL_KERNELS=true
INV_NO_ORDERS_TESTNET_LIVE=true
INV_CANDLE_MARK_TRADE_EQUIVALENCE_FORBIDDEN=true
INV_OPEN_TIP_BARS_FORBIDDEN=true
INV_SILENT_REWRITES_FORBIDDEN=true
INV_SNAPSHOTS_IMMUTABLE=true
INV_EVIDENCE_NO_FUTURE_MUTATION=true
INV_RANDOM_BAR_SPLIT_FORBIDDEN=true
INV_IID_BOOTSTRAP_FORBIDDEN_DEFAULT=true
INV_MULTI_INSTRUMENT_POOLING_FORBIDDEN=true
```

## 2. Decision 1 — AUTHORITY_SURFACE=B

```text
AUTHORITY_SURFACE=B
PRODUCER_CLASS=sole_trading_authority_shadow_calibration_producer
PRODUCER_SURFACE=DEDICATED_PT1M_FINALIZED_OHLCV_SHADOW_CALIBRATION_PRODUCER
O4_CANONICAL_PUBLIC_MD_BAR_PRODUCER=UNCHANGED
DASHBOARD_READMODEL_AS_SOURCE_AUTHORITY=FORBIDDEN
```

Authorize a **new dedicated** PT1M finalized-OHLCV shadow-calibration producer
under the sole trading authority
`run_integrated_offline_trading_logic_replay_v1`.

O4 (`CanonicalPublicMdBarProducerV1` / PT1H public-MD bar authority) remains
unchanged. No dashboard or read-model surface may act as source authority.

## 3. Decision 2 — PRICE_SEMANTICS

```text
OHLCV_SOURCE=VENUE_NATIVE_FINALIZED_CANDLES
MARK_PRICE=REQUIRED_SEPARATE_FIELD
CANDLE_MARK_TRADE_EQUIVALENCE=FORBIDDEN
MISSING_OR_INCONSISTENT_OHLCV_OR_MARK=FAIL_CLOSED
VENUE_CANDLES_ROLE=RAW_OHLCV_INPUT_BEHIND_DEDICATED_PRODUCER_ONLY
```

Venue-native finalized candles may supply O/H/L/C/Volume only as raw input
behind the dedicated Surface-B producer. `mark_price` is a required separate
field on the same finalized bar. Silent equality of candle close, mark, last,
or trade is forbidden. Missing or inconsistent OHLCV/mark inputs fail closed.

## 4. Decision 3 — INSTRUMENT_BINDING

```text
BINDING_MODE=SINGLE_SELECTED_FUTURE_VENUE_NATIVE
MULTI_INSTRUMENT_POOLING=FORBIDDEN
INSTRUMENT_CHANGE_POLICY=NEW_DATASET_ID_OR_SEGMENT_SPLIT
```

Bind exactly one venue-native instrument to the canonical
Single-Selected-Future authority. Required explicit fields:

- `venue`
- `canonical_instrument_id`
- `venue_instrument_id`
- `contract_type` / `market_type`
- `quote_currency`
- `settlement_currency`

Instrument changes require a new `dataset_id` or segment split. Multi-instrument
pooling is not authorized.

## 5. Decision 4 — DATASET_IDENTITY

Require immutable snapshot identity and provenance containing:

```text
dataset_id
source_id
venue
instrument_id
timeframe=PT1M
event_time_range
ingestion_timestamp
finalization_timestamp
repository_sha
config_digest
producer_version
raw_source_digest
correction_revision_policy
```

Compute the observation-pack digest from canonical JSON of bars plus provenance
and bind it into `ReproducibilityRecordV1.observation_pack_digest`.

## 6. Decision 5 — FINALITY_CORRECTIONS

```text
PT1M_FINAL_ONLY_AFTER_BUCKET_CLOSED_AND_AUTHORIZED_FINALIZER=true
OPEN_TIP_BARS=FORBIDDEN
LATE_EVENTS=EXPLICIT_CORRECTED_REVISION_OR_REJECT_INVALIDATE_SEGMENT
SILENT_REWRITES=FORBIDDEN
SNAPSHOTS=IMMUTABLE
REBUILD_POLICY=NEW_DATASET_ID_AND_DIGEST
EVIDENCE_PACK_FUTURE_MUTATION=FORBIDDEN
```

A PT1M bar is final only after the event-time bucket is closed and the
authorized finalizer rule confirms finality. Late events must produce an
explicit corrected revision or reject/invalidate the affected segment.

## 7. Decision 6 — PARTITION_PROTOCOL

```text
SPLIT_TYPE=CHRONOLOGICAL_POINT_IN_TIME
SEGMENTS=train|calibration|validation|holdout
RANDOM_BAR_SPLITTING=FORBIDDEN
PURGE_AND_EMBARGO=MANDATORY
PURGE_EMBARGO_NUMERIC_MAGNITUDES=UNSET
ATR_RV_WARMUP_HISTORY=PRESERVE_REQUIRED
REGIME_COVERAGE=RECORD_low|mid|high|unknown_AND_missing_WITHOUT_INVENTING
INSTRUMENT_CONTINUITY_BREAK=NEW_DATASET
```

## 8. Decision 7 — WALK_FORWARD_PROTOCOL

```text
MODE=EXPANDING_CALIBRATION_WINDOWS
FORWARD_VALIDATION=LOCKED
FORWARD_HOLDOUT=AT_LEAST_ONE_ISOLATED
STABLE_FOLD_IDS_AND_DIGESTS=REQUIRED
REBALANCE_BOUNDARIES=EVENT_TIME_BASED
CALIBRATION_MAY_NOT_ACCESS_VALIDATION_OR_HOLDOUT_LABELS=true
FOLD_SIZES_AND_CADENCE_NUMBERS=UNSET
```

## 9. Decision 8 — BOOTSTRAP_PROTOCOL

```text
METHOD=BLOCK_BOOTSTRAP
PRESERVE_TEMPORAL_STRUCTURE=true
IID_RESAMPLING=FORBIDDEN_BY_DEFAULT
DETERMINISTIC_RECORDED_SEEDS=REQUIRED
BLOCK_LENGTH=UNSET
RESAMPLING_UNIT_CHOICE=UNSET
PATH_COUNT=UNSET
PATH_ENSEMBLE_OWNERSHIP=SOLE_TRADING_AUTHORITY_SHADOW_CALIBRATION
PARALLEL_SURVIVAL_KERNEL=FORBIDDEN
```

## 10. Decision 9 — STRESS_PROTOCOL

Ratify structural stress scenario families only (no numeric magnitudes):

```text
gaps_missing_bars
staleness
spread_expansion_crossed_book
volatility_shocks
liquidation_near_miss_paths
chop_switch_clusters
fees
slippage
latency
sequence_path_disruption
```

```text
STRESS_NUMERIC_MAGNITUDES_RATIFIED=false
```

## 11. Decision 10 — SEQUENCE_LAYER_AUTHORITY

```text
SEQUENCE_SURVIVAL_METRICS_PRODUCER=SequenceSurvivalMetricsProducerV1_FUTURE_BOUNDED_UNDER_STA
SEQUENCE_SURVIVAL_METRICS_SHAPE=trading.master_v2.double_play_survival.SequenceSurvivalMetrics
PATH_SURVIVAL_METRICS_SOURCE=VERSIONED_DIGESTED_STA_OWNED_PATH_ENSEMBLE
LAYER_LEVERAGE_BUFFER_ADVERSE_FILL_PROJECTION=EXISTING_futures_accounting.py_ARITHMETIC_KERNEL_ONLY
```

Authorize the future bounded implementation of an STA-owned
`SequenceSurvivalMetricsProducerV1` using the existing
`SequenceSurvivalMetrics` shape. Authorize path-survival metrics only from a
versioned, digested STA-owned path ensemble. Authorize layer
leverage/buffer/adverse-fill projection only from the existing
`src&#47;execution&#47;paper&#47;futures_accounting.py` arithmetic kernel.

Forbidden as authority:

```text
ResultV1 objects
fixtures
dashboard_WebUI_values
CMC_volatility
research_panels
parallel_arithmetic_volatility_opportunity_survival_kernels
```

## 12. Decision 11 — IMPLEMENTATION_BOUNDARY

Authorize **one** bounded implementation scope containing only:

1. dedicated PT1M producer/export;
2. immutable observation packs and digests;
3. semantic-free binding to `FinalizedBarV1` and `ShadowCampaignRequestV1`;
4. complete structural dataset/partition/walk-forward/bootstrap/stress
   manifest builders **without** numeric policy values;
5. worktree-safe CLI/API loader with repository-SHA binding;
6. tests and explicit boundary guards.

Explicitly forbidden in this implementation:

```text
productive_calibration_or_thresholds
INPUT_AUTHORITY_or_runtime_activation_flips
trading_logic_mutation
O4_authority_expansion
dashboard_authority
parallel_kernels
orders_paper_execution_testnet_live_trading
numeric_Owner_value_ratification
```

## 13. Machine-readable pointer

Canonical machine decisions:
`docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_DECISIONS_V1.json`.

Bounded implementation plan:
`docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_IMPLEMENTATION_PLAN_V1.md`.

## 14. Forbidden effects (must remain false)

```text
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
PRODUCTIVE_CALIBRATION_AUTHORIZED=false
O4_MUTATED=false
DASHBOARD_AUTHORITY_EFFECT=NONE
RESULTV1_MAPPING_AUTHORIZED=false
PARALLEL_KERNEL_INTRODUCED=false
ORDERS_AUTHORIZED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
CORE_LOGIC_CHANGE=false
OWNER_MERGE_WITHOUT_OWNER_MERGE_GO=false
```
