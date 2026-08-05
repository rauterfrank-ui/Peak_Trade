# Stage-2 Surface B — Owner/STA Raw Input Pack Materialization Decision v1

```text
DOCUMENT_TYPE=OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISION
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISION
STATUS=OWNER_STA_OWNER_VALUE_RECORDED_AUTHORIZE_DETAIL_FIELDS_STILL_OPEN
DECISION_ID=DEC_RAW_INPUT_PACK_MATERIALIZATION
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
OWNER_GO_BASE_SHA=59bda81aec59b149d52e5cc863691fd7ac16de02
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
```

## 0. Binding effect

This document is the Owner/STA **decision surface** for exactly one decision:

`DEC_RAW_INPUT_PACK_MATERIALIZATION`

The Owner has recorded:

```text
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
DECISION_STATUS=RATIFIED
OWNER_GO_BASE_SHA=59bda81aec59b149d52e5cc863691fd7ac16de02
STATUS=OWNER_STA_OWNER_VALUE_RECORDED_AUTHORIZE_DETAIL_FIELDS_STILL_OPEN
```

The only allowed alternatives remain:

1. `AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION`
2. `EXPLICITLY_REJECT_RAW_INPUT_PACK_MATERIALIZATION`

It:

1. records the Owner authorize choice while keeping authorize-detail fields null;
2. binds STA open external inputs that remain unratified for pack materialization;
3. keeps `RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false`,
   `PACK_MATERIALIZATION=false`, `RAW_INPUT_PACK_CREATED=false`,
   `CAMPAIGN_START_AUTHORIZED=false`, `INPUT_AUTHORITY=false`, and
   `RUNTIME_IMPLEMENTED=false`.

It does **not**:

- invent campaign/instance identity, candles, marks, digests, seeds, partitions,
  folds, bootstrap seeds, or regime-coverage instance values;
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
OWNER_STA_OWNER_VALUE_RECORDED_AUTHORIZE_DETAIL_FIELDS_STILL_OPEN=true
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
AUTHORIZE_DETAIL_FIELDS_NULL=true
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
INV_AUTHORIZE_DETAIL_FIELDS_INITIALLY_NULL=true
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

| Field | Initial value |
|-------|---------------|
| `decision_id` | `DEC_RAW_INPUT_PACK_MATERIALIZATION` |
| `status` | `OWNER_STA_OWNER_VALUE_RECORDED_AUTHORIZE_DETAIL_FIELDS_STILL_OPEN` |
| `decision_status` | `RATIFIED` |
| `owner_value` | `AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION` |
| Allowed owner values | exactly the two alternatives below |

### Allowed owner values

```text
AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION
EXPLICITLY_REJECT_RAW_INPUT_PACK_MATERIALIZATION
```

No other owner value is accepted by the fail-closed validator.

## 3. Authorize detail fields (initially null)

When the Owner later chooses `AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION`, the following fields must exist as
separate Owner fields. On this open surface they remain `null`:

```text
campaign_id=null
dataset_id=null
scenario_id=null
instrument_binding_ref=null
candle_authority_source_ref=null
mark_price_authority_source_ref=null
observation_pack_digest=null
raw_source_digest=null
seed=null
event_time_epoch_s=null
partition_boundaries_event_time_epoch_s=null
fold_ids=null
bootstrap_seeds=null
regime_coverage_binding_ref=null
```

No fixture, demo, dashboard, Notion, O4-as-PT1M, candle-close-as-mark, or
trade-as-mark token may be written into these fields.

## 4. STA open external inputs

The following remain open external STA inputs (not satisfied by this surface):

```text
non_invented_campaign_instance_identity
venue_native_candle_source_identity
venue_native_mark_source_identity
immutable_pack_provenance_digests
deterministic_campaign_seed
exclusive_tip_event_time_epoch_s
partition_fold_bootstrap_structure
regime_coverage_materialization_readiness
```

Parent triad and regime-coverage closeout authorities remain prerequisites by
reference only. They do **not** fill instance values or authorize pack
materialization on this surface.

## 5. REJECT semantics

If Owner chooses `EXPLICITLY_REJECT_RAW_INPUT_PACK_MATERIALIZATION`:

```text
raw input pack remains not materializable
Surface-B campaign remains not startable
no fixture/demo/dashboard/Notion component may become substitute authority
instance fields remain null or absent
```

## 6. AUTHORIZE semantics

Even after Owner chooses `AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION`:

```text
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false until instance fields and STA proofs are fully ratified
PACK_MATERIALIZATION=false until a separate explicit materialization-execution Owner GO
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
separate explicit pack-materialization execution order required later
```

## 7. Explicitly null instance / policy fields

```text
campaign_id=null
dataset_id=null
scenario_id=null
instrument_binding=null
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
all_productive_numeric_calibration_values=unset
```

## 8. Fail-closed guards

Validator package
`src/ops/productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1/`
rejects:

- any owner value outside the two allowed alternatives;
- invented instance/pack values or productive numeric policy values;
- fixture / demo / dashboard / Notion / candle-close-as-mark sources;
- Dashboard authority other than `NONE`;
- pack materialization, campaign start, input-authority or runtime flips from
  this surface alone.

## 9. Explicit non-effects

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
```

## 10. Canonical next step

Owner value is recorded as
`AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION` under
`OWNER_STA_OWNER_VALUE_RECORDED_AUTHORIZE_DETAIL_FIELDS_STILL_OPEN`.
Authorize-detail fields remain null. A **separate** explicit Owner GO is
required to ratify authorize-detail fields. A further separate explicit Owner
GO remains required before pack materialization execution
(`PACK_MATERIALIZATION` / `RAW_INPUT_PACK_CREATED`), campaign start,
input-authority/runtime flips, consumer wiring, PT1M adapter binding, or
productive threshold/lookback ratification.
