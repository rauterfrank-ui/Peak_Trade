# Stage-2 Surface B — Owner/STA Regime Coverage Producer Decision v1

```text
DOCUMENT_TYPE=OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION
STATUS=OWNER_STA_OWNER_VALUE_RECORDED_AUTHORIZE_DETAIL_FIELDS_STILL_OPEN
DECISION_ID=DEC_REGIME_COVERAGE_PRODUCER
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER
OWNER_GO_BASE_SHA=9f4974824bb647b6f9dec5509ace990c2678188a
BASELINE_ORIGIN_MAIN_SHA=42e8527c929264c702d8f7d59a80fc38f850baff
PARENT_TRIAD=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md
PARENT_RAW_INPUT_PACK=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md
PARENT_SURFACE_B=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISIONS_V1.json
SCHEMA=docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decisions_v1.schema.json
VALIDATOR=src/ops/productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decision_v1/
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

LIVE_ORDERS=false
TESTNET_ORDERS=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
CORE_LOGIC_CHANGE=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 0. Binding effect

This document is the Owner/STA **decision surface** for exactly one decision:

`DEC_REGIME_COVERAGE_PRODUCER`

The Owner has recorded:

```text
OWNER_VALUE=AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER
DECISION_STATUS=RATIFIED
OWNER_GO_BASE_SHA=9f4974824bb647b6f9dec5509ace990c2678188a
```

The only allowed alternatives remain:

1. `AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER`
2. `EXPLICITLY_REJECT_REGIME_COVERAGE_PRODUCER`

It:

1. records the Owner authorize choice while keeping authorize-detail fields null;
2. binds the sole taxonomy sink
   `low | mid | high | unknown | missing` without inventing thresholds or
   label magnitudes;
3. documents STA open external inputs that remain unratified;
4. keeps `INPUT_AUTHORITY=false`, `RUNTIME_IMPLEMENTED=false`,
   `RAW_INPUT_PACK_CREATED=false`, and `CAMPAIGN_STARTED=false`.

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
- change trading logic or existing runtime producers;
- make Dashboard an authority (`DASHBOARD_AUTHORITY_EFFECT=NONE`);
- fill authorize-detail fields (separate Owner/STA ratification required).

```text
OWNER_STA_OWNER_VALUE_RECORDED=true
DECISION_STATUS=RATIFIED
OWNER_VALUE=AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER
AUTHORIZE_DETAIL_FIELDS_NULL=true
EXISTING_PRODUCERS_ELEVATED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
```

## 1. Non-negotiable invariants

```text
INV_AUTHORITY_SURFACE_B_ONLY=true
INV_ONLY_TWO_OWNER_ALTERNATIVES=true
INV_OWNER_VALUE_RECORDED=true
INV_AUTHORIZE_DETAIL_FIELDS_STILL_NULL=true
INV_TAXONOMY_SINK_EXCLUSIVE=low|mid|high|unknown|missing
INV_NO_FOREIGN_TAXONOMY_DERIVATION=true
INV_NO_INVENTED_THRESHOLDS_LOOKBACKS_COUNTS=true
INV_NO_EXISTING_PRODUCER_ELEVATION=true
INV_DASHBOARD_CONSUMER_ONLY=true
INV_INPUT_AUTHORITY_REMAINS_FALSE=true
INV_RUNTIME_IMPLEMENTED_REMAINS_FALSE=true
INV_RAW_PACK_AND_CAMPAIGN_UNAUTHORIZED=true
INV_NO_ORDERS_TESTNET_LIVE=true
```

## 2. Decision identity

| Field | Recorded value |
|-------|----------------|
| `decision_id` | `DEC_REGIME_COVERAGE_PRODUCER` |
| `status` / `decision_status` | `RATIFIED` |
| `owner_value` | `AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER` |
| Allowed owner values | exactly the two alternatives below |

### Allowed owner values

```text
AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER
EXPLICITLY_REJECT_REGIME_COVERAGE_PRODUCER
```

No other owner value is accepted by the fail-closed validator.

## 3. Authorize detail fields (still null)

Owner chose `AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER`. The
following fields must exist as separate Owner fields and remain `null` until a
further explicit Owner/STA ratification fills them:

```text
canonical_producer_name=null
canonical_producer_version=null
versioned_producer_id=null
taxonomy_binding=null
threshold_authority_ref=null
lookback_window_authority_ref=null
time_basis=null
PIT_no_lookahead_rules_ref=null
candle_join_acceptance_ref=null
mark_join_acceptance_ref=null
instrument_binding_acceptance_ref=null
determinism_contract_ref=null
reproducibility_contract_ref=null
producer_digest_contract_ref=null
missing_label_semantics_ref=null
unknown_label_semantics_ref=null
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
- no invented coverage counts.

## 5. STA open external inputs

The following remain open external STA inputs (not satisfied by this surface):

```text
dedicated_surface_b_regime_recorder_under_sta
ratified_taxonomy_mapping
non_invented_coverage_counts
producer_version_and_digest_contract
provable_eth_usdt_swap_compatibility
ratified_pt1m_candle_authority_join
ratified_pt1m_mark_authority_join
pit_no_lookahead_proof
deterministic_reproducible_computation
```

## 6. REJECT semantics

If Owner had chosen `EXPLICITLY_REJECT_REGIME_COVERAGE_PRODUCER`:

```text
regime_coverage remains not materializable
Surface-B campaign remains not startable while regime_coverage is a required field
no observability/research/bridge/dashboard component may become substitute authority
instance fields and coverage counts remain null or absent
```

## 7. AUTHORIZE semantics (current Owner choice)

Owner chose `AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER`:

```text
INPUT_AUTHORITY=false until all Owner fields and STA proofs are fully ratified
RUNTIME_IMPLEMENTED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
separate explicit implementation order required later
authorize_detail_fields remain null until separate Owner/STA ratification
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
- non-null authorize-detail fields until a separate Owner/STA order fills them.

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
EXISTING_PRODUCERS_ELEVATED=false
TRADING_LOGIC_CHANGED=false
DASHBOARD_AUTHORITY_EFFECT=NONE
ORDERS_TESTNET_LIVE_PAPER_EFFECTS=false
EXCHANGE_CREDENTIAL_EFFECTS=false
NOTION_CHANGED=false
```

## 11. Canonical next step

Owner value is recorded as
`AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER`. A **separate**
explicit Owner/STA order is required to fill authorize-detail fields. A further
separate explicit order is required before any implementation, raw-pack
materialization, or campaign start.
