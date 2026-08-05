# Stage-2 Surface B — Owner/STA Regime Coverage Producer Decision v1

```text
DOCUMENT_TYPE=OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION
STATUS=OWNER_STA_AUTHORIZE_DETAIL_FIELDS_COMPLETE_PRODUCER_IMPLEMENTED
DECISION_ID=DEC_REGIME_COVERAGE_PRODUCER
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER
OWNER_GO_BASE_SHA=9f4974824bb647b6f9dec5509ace990c2678188a
OWNER_IMPL_GO_BASE_SHA=52af83870a775ee9a4647107273964fa4857322b
BASELINE_ORIGIN_MAIN_SHA=42e8527c929264c702d8f7d59a80fc38f850baff
PARENT_TRIAD=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md
PARENT_RAW_INPUT_PACK=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md
PARENT_SURFACE_B=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISIONS_V1.json
SCHEMA=docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decisions_v1.schema.json
VALIDATOR=src/ops/productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decision_v1/
PRODUCER_PACKAGE=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/
PRODUCER_SPEC=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_REGIME_COVERAGE_PRODUCER_V1.md
CYBERSECURITY_MIRROR=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_CYBERSECURITY_MIRROR_V1.md

AUTHORITY_SURFACE=B
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
O4_UNCHANGED=true
O4_PT1H_AS_PT1M_FORBIDDEN=true
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_ROLE=READ_ONLY_CONSUMER
NOTION_SSOT=false
REPOSITORY_IS_SSOT=true

INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
CAMPAIGN_START_AUTHORIZED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
EXISTING_PRODUCERS_ELEVATED=false
TRADING_LOGIC_CHANGED=false
AUTHORIZE_DETAIL_FIELDS_COMPLETE=true
DEDICATED_PRODUCER_IMPLEMENTED=true

LIVE_ORDERS=false
TESTNET_ORDERS=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
CORE_LOGIC_CHANGE=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 0. Binding effect

This document is the Owner/STA **decision surface** for
`DEC_REGIME_COVERAGE_PRODUCER`.

Owner recorded:

```text
OWNER_VALUE=AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER
DECISION_STATUS=RATIFIED
OWNER_GO_BASE_SHA=9f4974824bb647b6f9dec5509ace990c2678188a
OWNER_IMPL_GO_BASE_SHA=52af83870a775ee9a4647107273964fa4857322b
STATUS=OWNER_STA_AUTHORIZE_DETAIL_FIELDS_COMPLETE_PRODUCER_IMPLEMENTED
AUTHORIZE_DETAIL_FIELDS_COMPLETE=true
DEDICATED_PRODUCER_IMPLEMENTED=true
```

The only allowed alternatives remain:

1. `AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER`
2. `EXPLICITLY_REJECT_REGIME_COVERAGE_PRODUCER`

It:

1. completes authorize-detail fields for the dedicated Surface-B producer;
2. binds the versioned deterministic PIT-safe producer package
   `src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/`;
3. binds the sole taxonomy sink
   `low | mid | high | unknown | missing` without inventing thresholds or
   label magnitudes;
4. keeps `INPUT_AUTHORITY=false`, `RUNTIME_IMPLEMENTED=false`,
   `RAW_INPUT_PACK_CREATED=false`, `CAMPAIGN_STARTED=false`, and
   `REGIME_COVERAGE_PRODUCER_AVAILABLE=false`.

It does **not**:

- select or elevate existing candidates
  (`analytics.regimes`, `regime.detectors`, `feature_regime_pipeline_v2`,
  `ai.switch_layer`, research max-age regime map, bull/bear evidence
  readmodel, reporting regime buckets, Dashboard projections, test fixtures);
- invent productive numeric values, thresholds, lookbacks, or coverage counts;
- materialize a raw input pack;
- start a Surface-B campaign;
- authorize orders, credentials, testnet, live, paper exchange, or capital
  movement;
- change trading logic;
- make Dashboard an authority (`DASHBOARD_AUTHORITY_EFFECT=NONE`);
- flip `REGIME_COVERAGE_PRODUCER_AVAILABLE` or resolve
  `REGIME_COVERAGE_STATUS` for campaign materialization.

```text
OWNER_STA_AUTHORIZE_DETAIL_FIELDS_COMPLETE_PRODUCER_IMPLEMENTED=true
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER
AUTHORIZE_DETAIL_FIELDS_COMPLETE=true
EXISTING_PRODUCERS_ELEVATED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
```

## 1. Non-negotiable invariants

```text
INV_AUTHORITY_SURFACE_B_ONLY=true
INV_ONLY_TWO_OWNER_ALTERNATIVES=true
INV_OWNER_VALUE_RECORDED=true
INV_AUTHORIZE_DETAIL_FIELDS_COMPLETE=true
INV_DEDICATED_PRODUCER_IMPLEMENTED=true
INV_TAXONOMY_SINK_EXCLUSIVE=low|mid|high|unknown|missing
INV_NO_FOREIGN_TAXONOMY_DERIVATION=true
INV_NO_INVENTED_THRESHOLDS_LOOKBACKS_COUNTS=true
INV_NO_EXISTING_PRODUCER_ELEVATION=true
INV_DASHBOARD_CONSUMER_ONLY=true
INV_INPUT_AUTHORITY_REMAINS_FALSE=true
INV_RUNTIME_IMPLEMENTED_REMAINS_FALSE=true
INV_RAW_PACK_AND_CAMPAIGN_UNAUTHORIZED=true
INV_PRODUCER_AVAILABLE_REMAINS_FALSE=true
INV_NO_ORDERS_TESTNET_LIVE=true
```

## 2. Decision identity

| Field | Value |
|-------|-------|
| `decision_id` | `DEC_REGIME_COVERAGE_PRODUCER` |
| `status` | `OWNER_STA_AUTHORIZE_DETAIL_FIELDS_COMPLETE_PRODUCER_IMPLEMENTED` |
| `decision_status` | `RATIFIED` |
| `owner_value` | `AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER` |

### Allowed owner values

```text
AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER
EXPLICITLY_REJECT_REGIME_COVERAGE_PRODUCER
```

## 3. Authorize detail fields (complete)

```text
canonical_producer_name=surface_b_regime_coverage_producer_v1
canonical_producer_version=v1
versioned_producer_id=productive_pure_stack_stage2_surface_b_regime_coverage_producer/v1
taxonomy_binding=TAXONOMY_SINK_EXCLUSIVE:low|mid|high|unknown|missing
threshold_authority_ref=OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1
lookback_window_authority_ref=OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1
time_basis=EVENT_TIME_PT1M_FINALIZED_BAR_CLOSE_UTC
PIT_no_lookahead_rules_ref=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/pit_rules_v1.py
candle_join_acceptance_ref=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#candle_source_authority
mark_join_acceptance_ref=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#mark_source_authority
instrument_binding_acceptance_ref=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#instrument_binding
determinism_contract_ref=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/determinism_contract_v1.py
reproducibility_contract_ref=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/reproducibility_contract_v1.py
producer_digest_contract_ref=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/digest_contract_v1.py
missing_label_semantics_ref=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/label_semantics_v1.py#missing
unknown_label_semantics_ref=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/label_semantics_v1.py#unknown
```

No existing producer token may be written into these fields.

## 4. Taxonomy sink

Target sink remains exclusively:

```text
low | mid | high | unknown | missing
```

Rules:

- no mapping from foreign taxonomies;
- no invented thresholds or label magnitudes;
- no invented coverage counts;
- while Owner numeric threshold/lookback authority remains UNSET, the producer
  emits `missing` (complete inputs) or `unknown` (incomplete inputs) only.

## 5. STA external inputs

Satisfied by this producer implementation:

```text
dedicated_surface_b_regime_recorder_under_sta
ratified_taxonomy_mapping
producer_version_and_digest_contract
ratified_pt1m_candle_authority_join
ratified_pt1m_mark_authority_join
pit_no_lookahead_proof
deterministic_reproducible_computation
```

Still open:

```text
non_invented_coverage_counts
provable_eth_usdt_swap_compatibility
```

## 6. REJECT semantics

If Owner had chosen `EXPLICITLY_REJECT_REGIME_COVERAGE_PRODUCER`:

```text
regime_coverage remains not materializable
Surface-B campaign remains not startable while regime_coverage is a required field
no observability/research/bridge/dashboard component may become substitute authority
instance fields and coverage counts remain null or absent
```

## 7. AUTHORIZE semantics (current Owner choice + implementation)

Owner chose `AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER` and this
order completed authorize-detail fields plus the dedicated producer:

```text
INPUT_AUTHORITY=false until remaining Owner fields and STA proofs are fully ratified
RUNTIME_IMPLEMENTED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
AUTHORIZE_DETAIL_FIELDS_COMPLETE=true
DEDICATED_PRODUCER_IMPLEMENTED=true
separate explicit pack/campaign/input-authority order still required later
```

## 8. Explicitly null instance / coverage fields

```text
campaign_id=null
dataset_id=null
scenario_id=null
seed=null
partition_boundaries=null
fold_ids=null
bootstrap_seeds=null
purge=null
embargo=null
fold_sizes=null
regime_coverage_counts=null
regime_coverage_instance=null
all_productive_numeric_calibration_values=unset
```

## 9. Fail-closed guards

Validator package
`src/ops/productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decision_v1/`
rejects:

- any owner value outside the two allowed alternatives;
- elevation of forbidden existing producers into canonical producer fields;
- invented productive numeric values, thresholds, lookbacks, or coverage counts;
- Dashboard authority other than `NONE`;
- pack materialization, campaign start, input-authority or runtime flips from
  this surface alone;
- authorize-detail drift away from the dedicated producer constants.

## 10. Explicit non-effects

```text
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
RAW_INPUT_PACK_CREATED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
CAMPAIGN_STARTED=false
CAMPAIGN_START_AUTHORIZED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
EXISTING_PRODUCERS_ELEVATED=false
TRADING_LOGIC_CHANGED=false
DASHBOARD_AUTHORITY_EFFECT=NONE
ORDERS_TESTNET_LIVE_PAPER_EFFECTS=false
EXCHANGE_CREDENTIAL_EFFECTS=false
NOTION_CHANGED=false
```

## 11. Canonical next step

Authorize-detail fields are complete and the dedicated producer is implemented.
`REGIME_COVERAGE_PRODUCER_AVAILABLE` remains `false` and
`REGIME_COVERAGE_STATUS` remains `SEMANTICALLY_UNRESOLVED`. A **separate**
explicit Owner GO is still required before raw-input-pack materialization,
campaign start, input-authority flips, or productive threshold/lookback
ratification.
