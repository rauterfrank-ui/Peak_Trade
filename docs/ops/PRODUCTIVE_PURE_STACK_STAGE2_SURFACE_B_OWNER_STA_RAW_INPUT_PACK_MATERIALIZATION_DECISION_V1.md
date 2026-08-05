# Stage-2 Surface B — Owner/STA Raw Input Pack Materialization Decision v1

```text
DOCUMENT_TYPE=OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISION
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISION
STATUS=OWNER_STA_PROVABLE_INSTANCE_FIELDS_CLOSED_NON_PROVABLE_INSTANCE_FIELDS_STILL_OPEN
DECISION_ID=DEC_RAW_INPUT_PACK_MATERIALIZATION
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
OWNER_GO_BASE_SHA=ac8b1e67baf361156c6f666a2c4cddbe49362400
BASELINE_ORIGIN_MAIN_SHA=56721ad0666fac5627d2dedbf33a22b59cd5996e
SCOPE=DOCS_MANIFEST_SCHEMA_VALIDATOR_ONLY
PARENT_RAW_INPUT_PACK=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md
PARENT_TRIAD=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md
PARENT_REGIME_COVERAGE=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1.md
PARENT_STA_OPEN_INPUTS_CLOSEOUT=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1.md
PARENT_SURFACE_B=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISIONS_V1.json
SCHEMA=docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decisions_v1.schema.json
VALIDATOR=src/ops/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1/
CYBERSECURITY_MIRROR=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_CYBERSECURITY_MIRROR_V1.md

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
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true
SILENT_DEFAULTS=false
```

## 0. Binding effect

This document is the Owner/STA **decision surface** for exactly one decision:

`DEC_RAW_INPUT_PACK_MATERIALIZATION`

The Owner has recorded:

```text
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
DECISION_STATUS=RATIFIED
OWNER_GO_BASE_SHA=ac8b1e67baf361156c6f666a2c4cddbe49362400
STATUS=OWNER_STA_PROVABLE_INSTANCE_FIELDS_CLOSED_NON_PROVABLE_INSTANCE_FIELDS_STILL_OPEN
AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED=true
AUTHORIZE_DETAIL_FIELDS_COMPLETE=false
PROVABLE_INSTANCE_FIELDS_CLOSED=true
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true
SILENT_DEFAULTS=false
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
5. keeps all non-provable instance/pack identity fields null and requires
   explicit Owner values for them (`SILENT_DEFAULTS=false`);
6. keeps `RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false`,
   `PACK_MATERIALIZATION=false`, `RAW_INPUT_PACK_CREATED=false`,
   `CAMPAIGN_START_AUTHORIZED=false`, `INPUT_AUTHORITY=false`, and
   `RUNTIME_IMPLEMENTED=false`.

It does **not**:

- invent campaign/instance identity, digests, seeds, partitions, folds, or
  bootstrap seeds;
- silently default any non-provable field;
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
OWNER_STA_PROVABLE_INSTANCE_FIELDS_CLOSED_NON_PROVABLE_INSTANCE_FIELDS_STILL_OPEN=true
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED=true
AUTHORIZE_DETAIL_FIELDS_COMPLETE=false
PROVABLE_INSTANCE_FIELDS_CLOSED=true
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true
SILENT_DEFAULTS=false
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
INV_NON_PROVABLE_INSTANCE_FIELDS_REQUIRE_EXPLICIT_OWNER_VALUES=true
INV_SILENT_DEFAULTS_FORBIDDEN=true
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
| `status` | `OWNER_STA_PROVABLE_INSTANCE_FIELDS_CLOSED_NON_PROVABLE_INSTANCE_FIELDS_STILL_OPEN` |
| `decision_status` | `RATIFIED` |
| `owner_value` | `AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION` |
| Allowed owner values | exactly the two alternatives below |

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
dataset_id=null
scenario_id=null
observation_pack_digest=null
raw_source_digest=null
seed=null
event_time_epoch_s=null
partition_boundaries_event_time_epoch_s=null
fold_ids=null
bootstrap_seeds=null
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

## 5. Non-provable instance fields (explicit Owner values required)

These fields remain `null`. They must not be invented or silently defaulted.
A separate explicit Owner GO with explicit values is required before they may
be set:

```text
campaign_id=null
dataset_id=null
scenario_id=null
seed=null
event_time_epoch_s=null
partition_boundaries=null
fold_ids=null
bootstrap_seeds=null
purge=null
embargo=null
fold_sizes=null
regime_coverage_counts=null
regime_coverage_instance=null
observation_pack_digest=null
raw_source_digest=null
```

```text
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true
SILENT_DEFAULTS=false
```

## 6. STA external inputs

Closed by this closeout (proven by authorize-detail venue-native refs):

```text
venue_native_candle_source_identity
venue_native_mark_source_identity
```

Remaining open external STA inputs (not satisfied by this surface):

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
closes provable refs, and closes the provable instance binding:

```text
AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED=true
PROVABLE_INSTANCE_FIELDS_CLOSED=true
AUTHORIZE_DETAIL_FIELDS_COMPLETE=false
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true
SILENT_DEFAULTS=false
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
- silent defaults for non-provable fields;
- fixture / demo / dashboard / Notion / candle-close-as-mark sources;
- Dashboard authority other than `NONE`;
- pack materialization, campaign start, input-authority or runtime flips from
  this surface alone.

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
```

## 11. Canonical next step

Provable instance field `instrument_binding` is closed under
`OWNER_STA_PROVABLE_INSTANCE_FIELDS_CLOSED_NON_PROVABLE_INSTANCE_FIELDS_STILL_OPEN`.
Non-provable instance fields remain null and require explicit Owner values.
A **separate** explicit Owner GO remains required before remaining instance
fields, pack materialization execution (`PACK_MATERIALIZATION` /
`RAW_INPUT_PACK_CREATED`), campaign start, input-authority/runtime flips,
consumer wiring, PT1M adapter binding, or productive threshold/lookback
ratification.
