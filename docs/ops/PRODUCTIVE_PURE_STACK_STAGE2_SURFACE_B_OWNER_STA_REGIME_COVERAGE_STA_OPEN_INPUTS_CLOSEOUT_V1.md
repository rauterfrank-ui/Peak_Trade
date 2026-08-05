# Stage-2 Surface B — Owner/STA Regime Coverage STA Open Inputs Closeout v1

```text
DOCUMENT_TYPE=OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT
STATUS=OWNER_STA_STA_OPEN_INPUTS_CLOSEOUT_RATIFIED
DECISION_ID=DEC_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT
DECISION_STATUS=RATIFIED
OWNER_GO=OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1
OWNER_GO_BASE_SHA=75ea4dc594a7f27b1fb490477e824a8c0a66d779
PARENT_REGIME_COVERAGE_DECISION=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1.md
PARENT_TRIAD=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md
PARENT_RAW_INPUT_PACK=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_DECISIONS_V1.json
SCHEMA=docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_sta_open_inputs_closeout_decisions_v1.schema.json
VALIDATOR=src/ops/productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_sta_open_inputs_closeout_v1/
CYBERSECURITY_MIRROR=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_CYBERSECURITY_MIRROR_V1.md

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
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
PRODUCTIVE_THRESHOLDS_LOOKBACKS=false
TRADING_LOGIC_CHANGE=false
ORDERS_AUTHORIZED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 0. Binding effect

This Owner/STA decision surface closes exactly two previously open STA
external inputs under `DEC_REGIME_COVERAGE_PRODUCER`:

1. `non_invented_coverage_counts`
2. `provable_eth_usdt_swap_compatibility`

It ratifies derivation and compatibility contracts only. It does **not**
reimplement the dedicated producer, wire consumers, adapt PT1M packs,
materialize packs, start campaigns, flip input authority or runtime, set
productive thresholds/lookbacks, change trading logic, or authorize orders /
testnet / live.

```text
CLOSED_INPUTS=non_invented_coverage_counts,provable_eth_usdt_swap_compatibility
STA_OPEN_EXTERNAL_INPUTS_REMAINING=none
PRODUCER_REIMPLEMENTATION=false
CONSUMER_WIRING=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
```

## 1. Closed input A — `non_invented_coverage_counts`

### Authority / provenance / digest / PIT / partition refs

```text
AUTHORITY_REF=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1.md
PRODUCER_AUTHORITY_REF=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/
PROVENANCE_REF=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/label_semantics_v1.py
DIGEST_REF=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/digest_contract_v1.py
PIT_REF=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/pit_rules_v1.py
PARTITION_REF=partition_id_must_bound_observation_window_and_digest
THRESHOLD_AUTHORITY_REF=OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1
LOOKBACK_AUTHORITY_REF=OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1
```

### Binding semantics

- Counts may be derived **only** from label observations emitted by the
  authorized dedicated Surface-B regime-coverage producer
  (`versioned_producer_id=productive_pure_stack_stage2_surface_b_regime_coverage_producer/v1`).
- While `OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1` and
  `OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1` remain in force, only actually
  observed `missing` and `unknown` labels may be counted.
- `low | mid | high` must not be produced, reconstructed, inferred, or counted
  without separately ratified threshold/lookback authority.
- Derived counts must be deterministic, partition-bounded, PIT/no-lookahead
  conformant, and digest-bound to the producer observation set.
- Caller-supplied or invented counts that are not observation-derived fail
  closed.
- Campaign/instance fields `regime_coverage_counts` and
  `regime_coverage_instance` remain `null` on this closeout surface;
  productive emission and pack binding remain unauthorized.

## 2. Closed input B — `provable_eth_usdt_swap_compatibility`

### Authority / compatibility refs

```text
INSTRUMENT_BINDING_AUTHORITY_REF=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#instrument_binding
TRIAD_MANIFEST_REF=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISIONS_V1.json
CANDLE_JOIN_REF=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#candle_source_authority
MARK_JOIN_REF=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#mark_source_authority
RAW_PT1M_PACK_REF=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md
COMPATIBILITY_MODE=EXACT_OWNER_RATIFIED_INSTRUMENTBINDINGV1_FIELD_MATCH
STRING_NAME_SIMILARITY_INFERENCE=false
```

### Owner-ratified InstrumentBindingV1 (exact match required)

```text
venue=okx
canonical_instrument_id=inst-eth-usdt-perp
venue_instrument_id=ETH-USDT-SWAP
contract_type=perpetual
market_type=futures
quote_currency=USDT
settlement_currency=USDT
```

### Binding semantics

- Compatibility is provable only via exact equality against the Owner-ratified
  Single-Selected-Future `InstrumentBindingV1` fields on the triad authority
  surface, together with the candle/mark/instrument triad join refs and the
  raw PT1M pack decision surface.
- No symbol, venue, contract, quote, settlement, or instrument compatibility
  may be inferred from strings or name similarity.
- Incomplete, contradictory, or non-provable bindings fail closed.

## 3. Non-negotiable invariants

```text
INV_CLOSED_INPUTS_EXACTLY_TWO=true
INV_COUNTS_FROM_AUTHORIZED_PRODUCER_OBSERVATIONS_ONLY=true
INV_UNSET_THRESHOLDS_COUNT_MISSING_UNKNOWN_ONLY=true
INV_NO_LOW_MID_HIGH_WITHOUT_THRESHOLD_LOOKBACK_AUTHORITY=true
INV_COUNTS_DETERMINISTIC_PARTITION_PIT_DIGEST_BOUND=true
INV_CALLER_SUPPLIED_INVENTED_COUNTS_FAIL_CLOSED=true
INV_ETH_USDT_SWAP_COMPAT_EXACT_INSTRUMENTBINDINGV1=true
INV_NO_STRING_NAME_SIMILARITY_INFERENCE=true
INV_PRODUCER_REIMPLEMENTATION_FALSE=true
INV_CONSUMER_WIRING_FALSE=true
INV_INPUT_AUTHORITY_FALSE=true
INV_RUNTIME_IMPLEMENTED_FALSE=true
INV_PRODUCER_AVAILABLE_FALSE=true
INV_NO_ORDERS_TESTNET_LIVE=true
INV_DASHBOARD_AUTHORITY_NONE=true
```

## 4. Explicit non-effects

```text
PRODUCER_REIMPLEMENTATION=false
CONSUMER_WIRING=false
PT1M_ADAPTER=false
PACK_MATERIALIZATION=false
CAMPAIGN_START=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
PRODUCTIVE_THRESHOLDS_LOOKBACKS=false
TRADING_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
ORDERS_AUTHORIZED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 5. Canonical next step

STA open external inputs for `DEC_REGIME_COVERAGE_PRODUCER` are empty after this
closeout. A **separate** explicit Owner GO is still required before consumer
wiring, PT1M adapter binding, pack materialization, campaign start, input
authority / runtime flips, productive threshold/lookback ratification, or any
flip of `REGIME_COVERAGE_PRODUCER_AVAILABLE` away from false.
