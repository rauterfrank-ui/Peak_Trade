# Stage-2 Surface B — Owner/STA Raw Input Pack Materialization Decision v1

```text
DOCUMENT_TYPE=OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISION
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISION
STATUS=OWNER_STA_NON_PROVABLE_INSTANCE_VALUES_OWNER_AND_STA_FILL_RECORDED_REMAINING_NULL
DECISION_ID=DEC_RAW_INPUT_PACK_MATERIALIZATION
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
OWNER_GO_BASE_SHA=037b48fb75f77dbec34468f8de189473d1849568
BASELINE_ORIGIN_MAIN_SHA=56721ad0666fac5627d2dedbf33a22b59cd5996e
SCOPE=FILL_NON_PROVABLE_INSTANCE_VALUES_ONLY
PARENT_RAW_INPUT_PACK=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md
PARENT_TRIAD=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md
PARENT_REGIME_COVERAGE=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1.md
PARENT_STA_OPEN_INPUTS_CLOSEOUT=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1.md
PARENT_SURFACE_B=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISIONS_V1.json
SCHEMA=docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decisions_v1.schema.json
VALIDATOR=src/ops/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1/
CYBERSECURITY_MIRROR=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_CYBERSECURITY_MIRROR_V1.md
DECISION_PACKET_ID=OWNER_STA_SURFACE_B_RAW_INPUT_PACK_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_V1

AUTHORITY_SURFACE=B
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
O4_UNCHANGED=true
O4_PT1H_AS_PT1M_FORBIDDEN=true
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_ROLE=READ_ONLY_CONSUMER
NOTION_SSOT=false
REPOSITORY_IS_SSOT=true

PRODUCER_REIMPLEMENTATION=false
CONSUMER_WIRING=false
PT1M_ADAPTER=false
PACK_MATERIALIZATION=false
CAMPAIGN_START=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
CAMPAIGN_START_AUTHORIZED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
PRODUCTIVE_THRESHOLDS_LOOKBACKS=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
TRADING_LOGIC_CHANGE=false
ORDERS_TESTNET_LIVE=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED=true
AUTHORIZE_DETAIL_FIELDS_COMPLETE=false
PROVABLE_INSTANCE_FIELDS_CLOSED=true
NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY=true
NON_PROVABLE_INSTANCE_VALUES_STILL_NULL=false
NON_PROVABLE_INSTANCE_VALUES_PARTIALLY_FILLED=true
CAMPAIGN_ID_EXPLICIT_LEAVE_NULL=true
OBSERVATION_PACK_DIGEST_LEAVE_NULL_UNTIL_COMPUTED=true
REGIME_COVERAGE_LEAVE_NULL_UNTIL_STA_PRODUCER_PROOF=true
PURGE_EXPLICIT_NULL_RATIFICATION=true
EMBARGO_EXPLICIT_NULL_RATIFICATION=true
FOLD_SIZES_EXPLICIT_NULL_RATIFICATION=true
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
INVENTED_VALUES=false
```

## 0. Binding effect

This document is the Owner/STA **decision surface** for exactly one decision:

`DEC_RAW_INPUT_PACK_MATERIALIZATION`

The Owner has recorded:

```text
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
DECISION_STATUS=RATIFIED
OWNER_GO_BASE_SHA=037b48fb75f77dbec34468f8de189473d1849568
STATUS=OWNER_STA_NON_PROVABLE_INSTANCE_VALUES_OWNER_AND_STA_FILL_RECORDED_REMAINING_NULL
AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED=true
AUTHORIZE_DETAIL_FIELDS_COMPLETE=false
PROVABLE_INSTANCE_FIELDS_CLOSED=true
NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY=true
NON_PROVABLE_INSTANCE_VALUES_STILL_NULL=false
NON_PROVABLE_INSTANCE_VALUES_PARTIALLY_FILLED=true
CAMPAIGN_ID_EXPLICIT_LEAVE_NULL=true
OBSERVATION_PACK_DIGEST_LEAVE_NULL_UNTIL_COMPUTED=true
REGIME_COVERAGE_LEAVE_NULL_UNTIL_STA_PRODUCER_PROOF=true
PURGE_EXPLICIT_NULL_RATIFICATION=true
EMBARGO_EXPLICIT_NULL_RATIFICATION=true
FOLD_SIZES_EXPLICIT_NULL_RATIFICATION=true
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
INVENTED_VALUES=false
```

The only allowed alternatives remain:

1. `AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION`
2. `EXPLICITLY_REJECT_RAW_INPUT_PACK_MATERIALIZATION`

It:

1. records the Owner authorize choice;
2. keeps authorize-detail provable refs closed from parent triad and
   regime-coverage authorities;
3. closes only the provable, non-invented instance field
   `instrument_binding` from the Owner-ratified InstrumentBindingV1;
4. closes STA venue-native candle/mark source-identity inputs proven by
   already-closed authorize-detail refs;
5. publishes an explicit fillable Owner/STA decision packet that
   enumerates every remaining null non-provable field, classifies each
   as `OWNER_VALUE` or `STA_EXTERNAL_INPUT`, and records allowed formats,
   constraints, and provenance requirements;
6. keeps all fillable packet value slots null (`PROPOSED_VALUES=false`,
   `SILENT_DEFAULTS=false`, `INVENTED_VALUES=false`);
7. keeps `RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false`,
   `PACK_MATERIALIZATION=false`, `RAW_INPUT_PACK_CREATED=false`,
   `CAMPAIGN_START_AUTHORIZED=false`, `INPUT_AUTHORITY=false`, and
   `RUNTIME_IMPLEMENTED=false`.

It does **not**:

- invent campaign/instance identity, digests, seeds, partitions, folds, or
  bootstrap seeds;
- propose or silently default any non-provable field;
- authorize or execute pack materialization;
- start a Surface-B campaign;
- reimplement producers, wire consumers, or bind a PT1M adapter;
- flip input authority or runtime implementation;
- set productive thresholds/lookbacks or productive numeric Owner values;
- authorize orders, credentials, testnet, live, paper exchange, or capital
  movement;
- change trading logic;
- make Dashboard or Notion an authority.

```text
OWNER_STA_NON_PROVABLE_INSTANCE_VALUES_OWNER_AND_STA_FILL_RECORDED_REMAINING_NULL=true
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED=true
AUTHORIZE_DETAIL_FIELDS_COMPLETE=false
PROVABLE_INSTANCE_FIELDS_CLOSED=true
NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY=true
NON_PROVABLE_INSTANCE_VALUES_STILL_NULL=false
NON_PROVABLE_INSTANCE_VALUES_PARTIALLY_FILLED=true
CAMPAIGN_ID_EXPLICIT_LEAVE_NULL=true
OBSERVATION_PACK_DIGEST_LEAVE_NULL_UNTIL_COMPUTED=true
REGIME_COVERAGE_LEAVE_NULL_UNTIL_STA_PRODUCER_PROOF=true
PURGE_EXPLICIT_NULL_RATIFICATION=true
EMBARGO_EXPLICIT_NULL_RATIFICATION=true
FOLD_SIZES_EXPLICIT_NULL_RATIFICATION=true
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
INVENTED_VALUES=false
PACK_MATERIALIZATION=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
```

## 1. Non-negotiable invariants

```text
INV_AUTHORITY_SURFACE_B_ONLY=true
INV_ONLY_TWO_OWNER_ALTERNATIVES=true
INV_OWNER_VALUE_RECORDED_AUTHORIZE=true
INV_AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED=true
INV_PROVABLE_INSTANCE_FIELDS_CLOSED=true
INV_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY=true
INV_NON_PROVABLE_INSTANCE_FIELDS_REQUIRE_EXPLICIT_OWNER_VALUES=true
INV_SILENT_DEFAULTS_FORBIDDEN=true
INV_PROPOSED_VALUES_FORBIDDEN=true
INV_NO_INVENTED_INSTANCE_OR_PACK_VALUES=true
INV_NO_FIXTURE_DEMO_DASHBOARD_SUBSTITUTION=true
INV_PACK_MATERIALIZATION_REMAINS_FALSE=true
INV_RAW_PACK_MATERIALIZATION_UNAUTHORIZED=true
INV_INPUT_AUTHORITY_REMAINS_FALSE=true
INV_RUNTIME_IMPLEMENTED_REMAINS_FALSE=true
INV_CAMPAIGN_START_UNAUTHORIZED=true
INV_NO_ORDERS_TESTNET_LIVE=true
INV_DASHBOARD_CONSUMER_ONLY=true
```

## 2. Decision identity

| Field | Value |
|-------|-------|
| `decision_id` | `DEC_RAW_INPUT_PACK_MATERIALIZATION` |
| `status` | `OWNER_STA_NON_PROVABLE_INSTANCE_VALUES_OWNER_AND_STA_FILL_RECORDED_REMAINING_NULL` |
| `decision_status` | `RATIFIED` |
| `owner_value` | `AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION` |
| Allowed owner values | exactly the two alternatives below |
| Decision packet id | `OWNER_STA_SURFACE_B_RAW_INPUT_PACK_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_V1` |

### Allowed owner values

```text
AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
EXPLICITLY_REJECT_RAW_INPUT_PACK_MATERIALIZATION
```

No other owner value is accepted by the fail-closed validator.

## 3. Authorize detail fields (provable refs closed; non-provable instance null)

Provable, non-invented authorize-detail refs remain closed from parent authorities:

```text
instrument_binding_ref=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#instrument_binding
candle_authority_source_ref=venue://okx/public/rest/v5/market/history-candles?bar=1m&confirm=1
mark_price_authority_source_ref=venue://okx/public/rest/v5/market/history-mark-price-candles?bar=1m&confirm=1
regime_coverage_binding_ref=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1.md
```

Authorize-detail instance / pack identity fields remain `null`:

```text
campaign_id=null
dataset_id=surface_b_eth_usdt_swap_pt1m_okx_public_tip1785934680_v1
scenario_id=surface_b_regime_coverage_structural_partition_v1
observation_pack_digest=null
raw_source_digest=9ea3edd6b0b7051a647ff3e6dd64da524b0bbb3ca6850a699c37936ad9541a57
seed=5745001
event_time_epoch_s=1785934680
partition_boundaries_event_time_epoch_s=[1785916740, 1785921240, 1785925740, 1785930240, 1785934680]
fold_ids=['train', 'calibration', 'validation', 'holdout']
bootstrap_seeds=[574500101, 574500102, 574500103, 574500104]
```

## 4. Provable instance field closed

Exactly one open-null instance field is closed from Owner-ratified parent
InstrumentBindingV1 (exact field match; no invention; no silent default):

```text
instrument_binding:
venue=okx
canonical_instrument_id=inst-eth-usdt-perp
venue_instrument_id=ETH-USDT-SWAP
contract_type=perpetual
market_type=futures
quote_currency=USDT
settlement_currency=USDT
```

Authority refs for this binding:

```text
instrument_binding_authority_ref=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#instrument_binding
sta_open_inputs_closeout_ref=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1.md
compatibility_mode=EXACT_OWNER_RATIFIED_INSTRUMENTBINDINGV1_FIELD_MATCH
```

## 5. Explicit fillable Owner/STA decision packet

Machine-readable fillable packet:

`docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISIONS_V1.json`
→ `non_provable_instance_values_decision_packet`

```text
PACKET_ID=OWNER_STA_SURFACE_B_RAW_INPUT_PACK_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_V1
PACKET_STATUS=PACKET_OWNER_AND_STA_VALUES_FILLED_REMAINING_NULL
ENUMERATED_REMAINING_NULL_FIELD_COUNT=4
PROPOSED_VALUES=false
SILENT_DEFAULTS=false
INVENTED_VALUES=false
```

Each row records:

- `field`
- `input_class` (`OWNER_VALUE` or `STA_EXTERNAL_INPUT`)
- `related_sta_open_input`
- `manifest_locations`
- `allowed_format`
- `constraints`
- `provenance_requirements`
- `fillable_owner_value=null`
- `fillable_sta_value=null`
- `proposed_value=null`
- `status=OPEN_FILLABLE`

### 5.1 Enumerated remaining null fields

| Field | Class | Related STA open input | Allowed format |
|-------|-------|------------------------|----------------|
| `campaign_id` | `OWNER_VALUE` | `non_invented_campaign_instance_identity` | `NON_EMPTY_ASCII_SLUG_STRING` |
| `dataset_id` | `OWNER_VALUE` | `non_invented_campaign_instance_identity` | `NON_EMPTY_ASCII_DATASET_ID_STRING` |
| `scenario_id` | `OWNER_VALUE` | `non_invented_campaign_instance_identity` | `NON_EMPTY_ASCII_SCENARIO_ID_STRING` |
| `observation_pack_digest` | `STA_EXTERNAL_INPUT` | `immutable_pack_provenance_digests` | `SHA256_HEX_64` |
| `raw_source_digest` | `STA_EXTERNAL_INPUT` | `immutable_pack_provenance_digests` | `SHA256_HEX_64` |
| `seed` | `OWNER_VALUE` | `deterministic_campaign_seed` | `DETERMINISTIC_NON_NEGATIVE_INTEGER_OR_EXPLICIT_SEED_STRING` |
| `event_time_epoch_s` | `STA_EXTERNAL_INPUT` | `exclusive_tip_event_time_epoch_s` | `UNIX_EPOCH_SECONDS_INTEGER` |
| `partition_boundaries` | `OWNER_VALUE` | `partition_fold_bootstrap_structure` | `ORDERED_LIST_OF_EVENT_TIME_BOUNDARIES` |
| `partition_boundaries_event_time_epoch_s` | `OWNER_VALUE` | `partition_fold_bootstrap_structure` | `ORDERED_LIST_OF_UNIX_EPOCH_SECONDS_INTEGERS` |
| `fold_ids` | `OWNER_VALUE` | `partition_fold_bootstrap_structure` | `ORDERED_LIST_OF_NON_EMPTY_FOLD_ID_STRINGS` |
| `bootstrap_seeds` | `OWNER_VALUE` | `partition_fold_bootstrap_structure` | `ORDERED_LIST_OF_DETERMINISTIC_SEEDS` |
| `purge` | `OWNER_VALUE` | `partition_fold_bootstrap_structure` | `EXPLICIT_OWNER_NUMERIC_OR_EXPLICIT_NULL_RATIFICATION` |
| `embargo` | `OWNER_VALUE` | `partition_fold_bootstrap_structure` | `EXPLICIT_OWNER_NUMERIC_OR_EXPLICIT_NULL_RATIFICATION` |
| `fold_sizes` | `OWNER_VALUE` | `partition_fold_bootstrap_structure` | `EXPLICIT_OWNER_LIST_OF_POSITIVE_INTEGERS_OR_EXPLICIT_NULL_RATIFICATION` |
| `regime_coverage_counts` | `STA_EXTERNAL_INPUT` | `regime_coverage_materialization_readiness` | `OBSERVATION_DERIVED_COUNT_OBJECT_FROM_AUTHORIZED_PRODUCER_ONLY` |
| `regime_coverage_instance` | `STA_EXTERNAL_INPUT` | `regime_coverage_materialization_readiness` | `PRODUCER_BOUND_REGIME_COVERAGE_INSTANCE_OBJECT` |

All listed fields remain `null` in authorize-detail / open-null instance
locations. Fillable packet slots remain null until a **separate** explicit
Owner fill GO supplies real values (and STA proofs where classified
`STA_EXTERNAL_INPUT`).

```text
campaign_id=null  # CAMPAIGN_ID_EXPLICIT_LEAVE_NULL=true
dataset_id=surface_b_eth_usdt_swap_pt1m_okx_public_tip1785934680_v1
scenario_id=surface_b_regime_coverage_structural_partition_v1
seed=5745001
event_time_epoch_s=1785934680
partition_boundaries={'train': [1785916740, 1785921240], 'calibration': [1785921240, 1785925740], 'validation': [1785925740, 1785930240], 'holdout': [1785930240, 1785934680]}
fold_ids=['train', 'calibration', 'validation', 'holdout']
bootstrap_seeds=[574500101, 574500102, 574500103, 574500104]
purge=null  # PURGE_EXPLICIT_NULL_RATIFICATION=true
embargo=null  # EMBARGO_EXPLICIT_NULL_RATIFICATION=true
fold_sizes=null  # FOLD_SIZES_EXPLICIT_NULL_RATIFICATION=true
regime_coverage_counts=null  # leave until STA producer proof
regime_coverage_instance=null  # leave until STA producer proof
observation_pack_digest=null  # leave until materialize/compute
raw_source_digest=9ea3edd6b0b7051a647ff3e6dd64da524b0bbb3ca6850a699c37936ad9541a57
partition_boundaries_event_time_epoch_s=[1785916740, 1785921240, 1785925740, 1785930240, 1785934680]
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
INVENTED_VALUES=false
NON_PROVABLE_INSTANCE_VALUES_PARTIALLY_FILLED=true
REMAINING_NULL_FIELDS=campaign_id,observation_pack_digest,regime_coverage_counts,regime_coverage_instance
```

## 6. STA external inputs

Closed by prior closeout (proven by authorize-detail venue-native refs):

```text
venue_native_candle_source_identity
venue_native_mark_source_identity
```

Remaining open external STA inputs (not satisfied by this packet surface):

```text
non_invented_campaign_instance_identity
immutable_pack_provenance_digests
deterministic_campaign_seed
exclusive_tip_event_time_epoch_s
partition_fold_bootstrap_structure
regime_coverage_materialization_readiness
```

## 7. REJECT semantics

If Owner chooses `EXPLICITLY_REJECT_RAW_INPUT_PACK_MATERIALIZATION`:

```text
raw input pack remains not materializable
Surface-B campaign remains not startable
no fixture/demo/dashboard/Notion component may become substitute authority
non-provable instance fields remain null or absent
```

## 8. AUTHORIZE semantics

Even after Owner chooses `AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION`,
closes provable refs, closes the provable instance binding, and publishes
the fillable decision packet:

```text
AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED=true
PROVABLE_INSTANCE_FIELDS_CLOSED=true
NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY=true
NON_PROVABLE_INSTANCE_VALUES_STILL_NULL=false
NON_PROVABLE_INSTANCE_VALUES_PARTIALLY_FILLED=true
CAMPAIGN_ID_EXPLICIT_LEAVE_NULL=true
OBSERVATION_PACK_DIGEST_LEAVE_NULL_UNTIL_COMPUTED=true
REGIME_COVERAGE_LEAVE_NULL_UNTIL_STA_PRODUCER_PROOF=true
PURGE_EXPLICIT_NULL_RATIFICATION=true
EMBARGO_EXPLICIT_NULL_RATIFICATION=true
FOLD_SIZES_EXPLICIT_NULL_RATIFICATION=true
AUTHORIZE_DETAIL_FIELDS_COMPLETE=false
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
INVENTED_VALUES=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false until remaining instance fields and STA proofs are fully ratified
PACK_MATERIALIZATION=false until a separate explicit materialization-execution Owner GO
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
separate explicit pack-materialization execution order required later
```

## 9. Fail-closed guards

Validator package
`src/ops/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1/`
rejects:

- any owner value outside the two allowed alternatives;
- invented instance/pack values or productive numeric policy values;
- any authorize-detail value outside the exact provable parent refs or null;
- any instrument_binding value outside the exact Owner-ratified InstrumentBindingV1;
- any non-null fillable packet value / proposed value;
- silent defaults for non-provable fields;
- incomplete decision-packet enumeration, classification, format, constraint,
  or provenance rows;
- fixture / demo / dashboard / Notion / candle-close-as-mark sources;
- Dashboard authority other than `NONE`;
- pack materialization, campaign start, input-authority or runtime flips from
  this surface alone.

## 9b. Owner/STA non-provable instance values fill (this GO)

```text
OWNER_GO=OWNER_STA_SURFACE_B_RAW_INPUT_PACK_INSTANCE_VALUES_FILL_V1
OWNER_GO_BASE_SHA=037b48fb75f77dbec34468f8de189473d1849568
SCOPE=FILL_NON_PROVABLE_INSTANCE_VALUES_ONLY
DATASET_ID=surface_b_eth_usdt_swap_pt1m_okx_public_tip1785934680_v1
SCENARIO_ID=surface_b_regime_coverage_structural_partition_v1
CAMPAIGN_ID_EXPLICIT_LEAVE_NULL=true
SEED=5745001
OWNER_PARTITION_SELECTION=FULL_AUTHORIZED_OBSERVATION_WINDOW_FOUR_CANONICAL_SEGMENTS
PARTITION_BOUNDARIES_EVENT_TIME_EPOCH_S=[1785916740, 1785921240, 1785925740, 1785930240, 1785934680]
PARTITION_COUNT=4
PARTITION_SEGMENTS_RESOLUTION=EXPLICIT_FOUR_SEGMENT_BOUNDARIES_NO_EXCEPTION
FOLD_IDS=['train', 'calibration', 'validation', 'holdout']
BOOTSTRAP_SEEDS=[574500101, 574500102, 574500103, 574500104]
PURGE_EXPLICIT_NULL_RATIFICATION=true
EMBARGO_EXPLICIT_NULL_RATIFICATION=true
FOLD_SIZES_EXPLICIT_NULL_RATIFICATION=true
RAW_SOURCE_DIGEST=9ea3edd6b0b7051a647ff3e6dd64da524b0bbb3ca6850a699c37936ad9541a57
EVENT_TIME_EPOCH_S=1785934680
OBSERVATION_PACK_DIGEST=null
REGIME_COVERAGE_COUNTS=null
REGIME_COVERAGE_INSTANCE=null
MATERIALIZE_RAW_INPUT_PACK=false
COMPUTE_OBSERVATION_PACK_DIGEST=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
CAMPAIGN_START=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
```

instrument_binding_ref=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#instrument_binding
candle_authority_source_ref=venue://okx/public/rest/v5/market/history-candles?bar=1m&confirm=1
mark_price_authority_source_ref=venue://okx/public/rest/v5/market/history-mark-price-candles?bar=1m&confirm=1
regime_coverage_binding_ref=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1.md

Remaining open for later GOs:

```text
campaign_id (explicit leave null)
observation_pack_digest (compute on materialize)
regime_coverage_counts / regime_coverage_instance (STA producer proof)
```

## 10. Explicit non-effects

```text
PRODUCER_REIMPLEMENTATION=false
CONSUMER_WIRING=false
PT1M_ADAPTER=false
PACK_MATERIALIZATION=false
CAMPAIGN_START=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
CAMPAIGN_START_AUTHORIZED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
PRODUCTIVE_THRESHOLDS_LOOKBACKS=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
TRADING_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
NOTION_SSOT=false
ORDERS_TESTNET_LIVE=false
EXCHANGE_CREDENTIAL_EFFECTS=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
AUTHORIZE_DETAIL_FIELDS_COMPLETE=false
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
INVENTED_VALUES=false
```

## 11. Canonical next step

The fillable decision packet
`OWNER_STA_SURFACE_B_RAW_INPUT_PACK_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_V1`
is ready under
`OWNER_STA_NON_PROVABLE_INSTANCE_VALUES_OWNER_AND_STA_FILL_RECORDED_REMAINING_NULL`.
All enumerated non-provable instance fields remain null. A **separate**
explicit Owner fill GO remains required before remaining instance fields may
be set; separate later GOs remain required for pack materialization execution
(`PACK_MATERIALIZATION` / `RAW_INPUT_PACK_CREATED`), campaign start,
input-authority/runtime flips, consumer wiring, PT1M adapter binding, or
productive threshold/lookback ratification.
