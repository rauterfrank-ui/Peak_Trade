# Stage-2 Surface B — Raw PT1M Candle/Mark Input Pack & Campaign Instance Binding

## Owner Decision v1

```text
DOCUMENT_TYPE=OWNER_AUTHORITY_DECISION
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_RAW_PT1M_CANDLE_MARK_INPUT_PACK_AND_CAMPAIGN_INSTANCE_BINDING
STATUS=OWNER_DECISION_STRUCTURE_RATIFIED_INSTANCE_FIELDS_OPEN
BASELINE_ORIGIN_MAIN_SHA=81315806a9501ab7872b9fc0c54bafa82eff5920
PARENT_SURFACE_B=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md
PARENT_DECISIONS=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_DECISIONS_V1.json
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_DECISIONS_V1.json
SCHEMA=docs/ops/schemas/productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_decisions_v1.schema.json
VALIDATOR=src/ops/productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_owner_decision_v1/
SHADOW_CAMPAIGN=docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_SHADOW_CAMPAIGN_V1.md

AUTHORITY_SURFACE=B
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
O4_UNCHANGED=true
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_ROLE=READ_ONLY_CONSUMER
NOTION_SSOT=false
REPOSITORY_IS_SSOT=true

INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
CAMPAIGN_START_AUTHORIZED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
PRODUCTIVE_CALIBRATION_AUTHORIZED=false
PURGE_VALUE=null
EMBARGO_VALUE=null
FOLD_SIZES_VALUE=null

LIVE_ORDERS=false
TESTNET_ORDERS=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
CORE_LOGIC_CHANGE=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 0. Binding effect

This document is the Owner Decision that closes the **governance /
authority specification gap** between:

1. the already-ratified Surface-B PT1M producer / observation-pack /
   collector path; and
2. a future, immutable Surface-B raw candle+mark input pack bound to
   exactly one Stage-2 Shadow Campaign instance.

It:

1. ratifies the decision surface
   `SURFACE_B_RAW_PT1M_CANDLE_MARK_INPUT_PACK_AND_CAMPAIGN_INSTANCE_BINDING`;
2. binds Single-Selected-Future venue-native `InstrumentBindingV1`
   requirements;
3. binds candle authority, separate mark-price authority, PIT /
   no-lookahead, exclusive-tip, and immutable pack identity rules;
4. binds campaign-instance identity fields as **Owner-open** until
   separately filled and ratified;
5. keeps `INPUT_AUTHORITY=false`, `RUNTIME_IMPLEMENTED=false`,
   `CAMPAIGN_START_AUTHORIZED=false`, and
   `RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false`.

It does **not**:

- invent or supply candles, marks, partitions, fold IDs, bootstrap seeds,
  or regime-coverage values;
- authorize campaign start or `--start-evidence-collection`;
- flip input authority or runtime implementation;
- set productive numeric Owner policy values;
- authorize orders, paper exchange, testnet, live trading, credentials,
  or real-capital movement;
- mutate Surface-B collector / producer semantics;
- make Notion or Dashboard an authority source.

```text
OWNER_DECISION_STRUCTURE_RATIFIED=true
INSTANCE_FIELD_VALUES_INVENTED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
CAMPAIGN_START_AUTHORIZED=false
```

## 1. Non-negotiable invariants

```text
INV_AUTHORITY_SURFACE_B_ONLY=true
INV_O4_UNCHANGED=true
INV_DASHBOARD_NOT_SOURCE_AUTHORITY=true
INV_NOTION_NOT_SSOT=true
INV_REPO_IS_SSOT=true
INV_SOLE_TRADING_AUTHORITY_ONLY=true
INV_INPUT_AUTHORITY_REMAINS_FALSE=true
INV_RUNTIME_IMPLEMENTED_REMAINS_FALSE=true
INV_CAMPAIGN_START_UNAUTHORIZED_UNTIL_SEPARATE_GO=true
INV_NO_PRODUCTIVE_NUMERIC_VALUES=true
INV_CANDLE_MARK_TRADE_EQUIVALENCE_FORBIDDEN=true
INV_OPEN_TIP_BARS_FORBIDDEN=true
INV_FIXTURE_DEMO_DASHBOARD_SOURCES_FORBIDDEN=true
INV_MULTI_INSTRUMENT_POOLING_FORBIDDEN=true
INV_PURGE_EMBARGO_FOLD_SIZES_REMAIN_NULL=true
INV_NO_ORDERS_TESTNET_LIVE=true
INV_EXISTING_SURFACE_B_COLLECTOR_SEMANTICS_UNCHANGED=true
```

## 2. Scope

### In scope

- Owner Decision structure for one future immutable Surface-B raw PT1M
  candle+mark input pack
- Campaign-instance binding contract for exactly one Stage-2 Shadow
  Campaign evidence-collection instance
- Machine-readable decision manifest with open Owner fields
- Fail-closed validator/guard for the decision surface
- Documentary cybersecurity / `SECURITY_NOTES.md` mirror of the new
  decision surface

### Out of scope

- Materializing or committing raw market data
- Starting a shadow campaign
- Productive calibration / threshold promotion
- Trading-logic mutation under `src/trading/master_v2/`
- O4 interval / authority expansion
- Dashboard or Notion authority

## 3. Instrument binding (Single-Selected-Future, venue-native)

Required `InstrumentBindingV1` fields (must be Owner-supplied later;
structure only here):

```text
venue
canonical_instrument_id
venue_instrument_id
contract_type
market_type
quote_currency
settlement_currency
```

```text
BINDING_MODE=SINGLE_SELECTED_FUTURE_VENUE_NATIVE
MULTI_INSTRUMENT_POOLING=FORBIDDEN
INSTRUMENT_CHANGE_POLICY=NEW_DATASET_ID_OR_SEGMENT_SPLIT
```

Non-venue-native, multi-instrument, fixture, demo, or dashboard bindings
fail closed.

## 4. Candle authority and finality

```text
OHLCV_SOURCE=VENUE_NATIVE_FINALIZED_CANDLES
CANDLE_ROLE=RAW_OHLCV_INPUT_BEHIND_DEDICATED_PRODUCER_ONLY
PRODUCER=sta_pt1m_finalized_ohlcv_shadow_calibration_producer_v1
TIMEFRAME=PT1M
OPEN_TIP_BARS=FORBIDDEN
VENUE_FINALIZED_REQUIRED=true
EVENT_TIME_MUST_BE_BUCKET_OPEN=true
SILENT_REWRITES=FORBIDDEN
```

A PT1M candle is admissible only when:

1. it is venue-native;
2. the event-time bucket is closed;
3. `venue_finalized=true`;
4. `open_tip=false`;
5. OHLCV fields are present and sane under the existing Surface-B
   producer rules.

Missing candles fail closed. Fixtures, demo packs, dashboard read-models,
and O4 PT1H-as-PT1M substitution fail closed.

## 5. Separate mark-price authority and join semantics

```text
MARK_PRICE=REQUIRED_SEPARATE_FIELD
MARK_SOURCE=VENUE_NATIVE_MARK_OBSERVATION_SEPARATE_FROM_CANDLE
CANDLE_MARK_TRADE_EQUIVALENCE=FORBIDDEN
JOIN_KEY=PT1M_BUCKET_OPEN_EVENT_TIME
MISSING_MARK_FOR_BUCKET=FAIL_CLOSED
```

Candle close / last / trade must never be used as an implicit mark.
Coincident numeric equality is not substitution authority. Mark and candle
must join on the same PT1M bucket-open event time.

## 6. PIT / no-lookahead and exclusive tip

```text
POINT_IN_TIME_ONLY=true
NO_LOOKAHEAD=true
AS_OF_EQUALS_PACK_EXCLUSIVE_TIP=true
EVENT_TIME_EPOCH_S_SEMANTICS=PACK_EXCLUSIVE_TIP
OPEN_BUCKET_AT_AS_OF=FORBIDDEN
BAR_AFTER_AS_OF=FORBIDDEN
PRODUCTIVE_MAX_AGE_MUST_REMAIN_UNSET=true
```

`event_time_epoch_s` for campaign binding must equal the observation-pack
exclusive tip (`last_finalized_bar_open + 60`). Coverage that ends before
or beyond as-of fails closed.

## 7. Immutable dataset / pack identity

Required provenance fields (structure; values Owner-open until filled):

```text
dataset_id
source_id=sta_pt1m_finalized_ohlcv_shadow_calibration_producer_v1
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
observation_pack_digest
```

```text
SNAPSHOTS=IMMUTABLE
REBUILD_POLICY=NEW_DATASET_ID_AND_DIGEST
EVIDENCE_PACK_FUTURE_MUTATION=FORBIDDEN
```

## 8. Campaign-instance binding

Exactly one Stage-2 Shadow Campaign instance may be bound to one ratified
raw input pack. Required instance fields are Owner-open in this decision:

```text
campaign_id=null
dataset_id=null
scenario_id=null
instrument_binding=null
candle_authority_ref=null
mark_price_authority_ref=null
observation_pack_digest=null
raw_source_digest=null
seed=null
event_time_epoch_s=null
partition_boundaries_event_time_epoch_s=null
fold_ids=null
bootstrap_seeds=null
regime_coverage=null
```

Structural numeric policy magnitudes remain null:

```text
purge=null
embargo=null
fold_sizes=null
```

```text
CAMPAIGN_START_AUTHORIZED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
```

A start attempt, collector invocation with
`--start-evidence-collection`, or pack materialization without separate
Owner GO fail closed.

## 9. Fail-closed behaviour

The validator must reject at least:

- missing candles
- missing separate marks
- candle=mark alias / substitution policy
- open-tip or unfinalized candle use
- fixture / demo / dashboard / Notion sources
- non-venue-native instrument binding
- inconsistent dataset / campaign identity
- missing or non-deterministic seed structure when instance fields are
  claimed complete
- any non-null purge / embargo / fold_sizes
- campaign start while `CAMPAIGN_START_AUTHORIZED=false`
- pack materialization while
  `RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false`
- any claim that flips `INPUT_AUTHORITY` or `RUNTIME_IMPLEMENTED`

## 10. Forbidden sources and derivations

```text
fixture
demo
scenario_scalar
dashboard_readmodel
webui
notion
cmc_volatility
ResultV1
SurvivalResultV1
SuitabilityResultV1
o4_pt1h_as_pt1m_authority
candle_close_as_mark
trade_as_mark
parallel_arithmetic_kernel
parallel_survival_kernel
```

## 11. Open Owner decision fields (no invented values)

The following remain unset until a later Owner GO fills them with real,
non-fixture, venue-native values:

1. `campaign_id`
2. `dataset_id`
3. `scenario_id`
4. `InstrumentBindingV1` field values
5. candle authority reference / raw candle source identity
6. mark-price authority reference / raw mark source identity
7. pack digests / provenance timestamps / repository binding for the pack
8. deterministic campaign `seed`
9. `event_time_epoch_s` (exclusive tip)
10. partition boundary event times
11. fold IDs
12. bootstrap seeds
13. regime coverage counts

This document does not invent any of those values.

## 12. Explicit non-effects

```text
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
CAMPAIGN_START_AUTHORIZED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
PRODUCTIVE_CALIBRATION_AUTHORIZED=false
PURGE_VALUE=null
EMBARGO_VALUE=null
FOLD_SIZES_VALUE=null
O4_MUTATED=false
DASHBOARD_AUTHORITY_EFFECT=NONE
NOTION_SSOT=false
ORDERS_AUTHORIZED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
CORE_LOGIC_CHANGE=false
SURFACE_B_COLLECTOR_SEMANTICS_CHANGED=false
```

## 13. Canonical pointers

- Parent Surface-B ratification:
  `docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md`
- Parent decisions:
  `docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_DECISIONS_V1.json`
- Machine manifest:
  `docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_DECISIONS_V1.json`
- Schema:
  `docs/ops/schemas/productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_decisions_v1.schema.json`
- Validator package:
  `src/ops/productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_owner_decision_v1/`
- Existing Surface-B producer/collector (unchanged semantics):
  `src/ops/productive_pure_stack_stage2_shadow_campaign_input_authority_v1/`
- Shadow campaign runner:
  `src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/`
- Evidence output root (future only; not written by this decision):
  `evidence&#47;ops&#47;productive_pure_stack_numeric_policy_shadow_campaign_v1&#47;<campaign_id>&#47;`
