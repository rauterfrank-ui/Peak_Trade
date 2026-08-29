# Peak_Trade — Post-Restoration Venue Pretrade Metadata Binding Alignment Adjudication v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Persist the forensic adjudication of venue-pretrade metadata-binding alignment beginning at MAX_SIZE after closed limit-gates persist (#6146). Not a second SSOT. Not restoration reopen. Not core runtime mutation. Not live or execution authority. Not a current numeric freeze. Not productive enforcement. Not a Network GET.
docs_token: DOCS_TOKEN_PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md
PRIOR_LIVE_SAFETY_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1.md
PRIOR_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md
PRIOR_ACCOUNTING_PORTFOLIO_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1.md
PRIOR_QUARANTINE_PARALLEL_OWNER=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1.md
PRIOR_QUARANTINE_REMAINING_P0=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_REMAINING_P0_QUARANTINE_V1.md
HOST_GRAPH_SSOT=docs/ops/specs/MASTER_V2_DOUBLE_PLAY_HOST_GRAPH_SSOT_AND_OWNER_COMPOSED_FULL_CHAIN_PROOF_V1.md
PARALLEL_SSOT_CREATED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_RUNTIME_MUTATION=false
DEFAULT_RUNTIME_MUTATION=false
NEW_SEMANTIC_POLICY=false
NEW_RUNTIME_OWNER=false
NEW_STAGE=false
NEW_VENUE_PRETRADE_COMPONENT_REQUIRED=false
NEW_ABSTRACTION_REQUIRED=false
RESTORATION_REOPEN_REQUIRED=false
MASTER_V2_DOUBLE_PLAY_RESTORATION_COMPLETE=true
COMPATIBILITY_CONTRACT_DOES_NOT_GRANT_EXECUTION_AUTHORITY=true
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
LIVE_ENABLED=false
LIVE_ARMED=false
EXECUTION_ELIGIBLE=false
LIVE_READINESS=EVALUATED_NOT_READY
ORDERS_AUTHORIZED=false
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
CHANGED_RUNTIME_FILES=NONE
RUNTIME_ALIGNMENT_REQUIRED=false
RUNTIME_MUTATION_JUSTIFIED=false
NETWORK_GET_PERFORMED=false
NETWORK_POST_PERFORMED=false
```

This document is subordinate to the Master Runbook and to the post-restoration
preservation contract. It does not replace Master §5.3, Appendix A, C4, Replay
Safety, Cap 7.2, live-safety #6145, simulated-execution #6144, accounting/portfolio
#6143, or venue-pretrade limit-gates #6146. It persists the already-true
MAX_SIZE metadata-binding gap so later hosts cannot freeze a historical
numeric, reuse BTC or Kraken evidence, invent units or freshness, or treat
field existence as a bound pretrade gate.

## 1) Restoration boundary

```text
RESTORATION_COMPLETION_CHECKPOINT_SHA=21452016ff998c1af63f24c36060f2a54020c0df
HISTORICAL_MASTER_V2_DOUBLE_PLAY_BASELINE=IMMUTABLE_NORMATIVE_BASELINE
CURRENT_SYSTEM_MUST_CONFORM_TO_HISTORICAL_CORE=true
NO_CURRENT_FIRST_ARCHITECTURE=true
HISTORICAL_CORE_SEMANTICS_MUST_NOT_BE_REWRITTEN=true
P0_QUARANTINE_REMAINS_CLOSED=true
ACCOUNTING_PORTFOLIO_ALIGNMENT_REMAINS_CLOSED=true
SIMULATED_EXECUTION_PIPELINE_REMAINS_CLOSED=true
LIVE_SAFETY_GATES_REMAIN_CLOSED=true
VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_REMAINS_CLOSED=true
```

## 2) Protected productive owner graph

```text
COMPUTE_OWNER=trading.master_v2.integrated_offline_trading_logic_replay_v1
RISK_OWNER=STEP-29P / src.governance.capital_risk_sizing_v1
SAFETY_OWNER=trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0
INTENT_OWNER=STEP-29Q / src.governance.canonical_order_intent_v1
SIDESTATE_WRITER=trading.master_v2.double_play_state.transition_state
ENTRY_EXIT_OWNER=evaluate_double_play_entry_exit_policy_v0
INTENDED_ACTION_MAPPER_ROLE=DOWNSTREAM_TRANSLATOR_ONLY
CANONICAL_EXECUTION_OWNER=SimulatedExecutionPortV1_DELEGATE_CAP3_1
SECOND_COMPUTE_OWNER_EXISTS=false
SECOND_RISK_OWNER_EXISTS=false
SECOND_SAFETY_OWNER_EXISTS=false
SECOND_INTENT_OWNER_EXISTS=false
SECOND_EXECUTION_OWNER_EXISTS=false
SECOND_ACCOUNTING_OWNER_CONFLICT=false
SECOND_VENUE_PRETRADE_OWNER_EXISTS=false
CLOSED_OWNER_GRAPH_PRESERVED=true
PRODUCTIVE_ORDERING=29P → Replay Safety → 29Q PLAN_ONLY → mapper → simulated execution
STEP_29P_BEFORE_SAFETY=true
SAFETY_BEFORE_STEP_29Q=true
NO_29Q_BEFORE_SAFETY=true
SAFETY_PASS_IS_NOT_EXECUTION_PERMISSION=true
VENUE_PRETRADE_IS_NOT_REPLAY_SAFETY=true
VENUE_PRETRADE_IS_NOT_CORE_RISK_AUTHORITY=true
VENUE_PRETRADE_IS_NOT_EXECUTION_AUTHORITY=true
VENUE_PRETRADE_IS_DOWNSTREAM_OF_LIVE_SAFETY=true
VENUE_PRETRADE_IS_UPSTREAM_OF_POST=true
```

Canonical productive order remains STEP-29P → Replay Safety → STEP-29Q
PLAN_ONLY. Venue pretrade remains a downstream OKX-EEA-Canary validator
after Live Safety admission and before POST. Tests are guards, not a
second semantic SSOT. A later metadata consumer, if separately authorized,
must attach to the existing canary order-plan owner. This persist does not
create that consumer.

## 3) Adjudication result

```text
ADJUDICATION_RESULT=PARTIAL
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND
ALL_REQUIRED_METADATA_EDGES_BOUND=false
EARLIEST_INCOMPLETE_VENUE_PRETRADE_EDGE=MAX_SIZE
EARLIEST_REMAINING_UNBOUND_EDGE=MAX_SIZE
EARLIEST_REMAINING_CONFLICT=NONE
REQUIRED_METADATA_EDGE_COUNT=8
BOUND_METADATA_EDGE_COUNT=0
PARTIAL_METADATA_EDGE_COUNT=2
UNBOUND_METADATA_EDGE_COUNT=6
CONFLICTED_METADATA_EDGE_COUNT=0
CANONICAL_VENUE_PRETRADE_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
VENUE_PRETRADE_OWNER_MODEL=OKX_EEA_CANARY_VENUE_CONSTRAINT_PLAN_OWNER_NOT_A_SECOND_CORE_RISK_OR_SAFETY_OWNER
SECOND_VENUE_PRETRADE_OWNER_EXISTS=false
SECOND_OWNER_REQUIRED=false
BYPASS_PATH_CONFLICT=false
RUNTIME_ALIGNMENT_REQUIRED=false
RUNTIME_MUTATION_JUSTIFIED=false
NEW_VENUE_PRETRADE_COMPONENT_REQUIRED=false
NEW_ABSTRACTION_REQUIRED=false
RESTORATION_REOPEN_REQUIRED=false
PREEXISTING_CALL_GRAPH_DRIFT_CLASS=LABEL_ONLY
PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false
PREEXISTING_CALL_GRAPH_DRIFT_REPAIRED=false
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
INSTRUMENT_BIND_PROVEN=true
KRAKEN_CURRENT_CANONICAL_ROLE=NONE
KRAKEN_EVIDENCE_USED_FOR_CURRENT_OKX_PRETRADE=false
NETWORK_GET_REQUIRED=true
NETWORK_GET_PERFORMED=false
NETWORK_POST_PERFORMED=false
NEXT_DISTINCT_SURFACE=EXACT_VENUE_METADATA_GET
NEXT_DISTINCT_SURFACE_AUTHORIZED=false
```

Not `COMPLETE`: MAX_SIZE is only partially bound. Current reusable numeric,
unit, freshness policy, semantic equivalence proof, and runtime consumer
remain unbound.

Not `BLOCKED_BY_MISSING_SOURCE`: a historical exact-`instId` public
instruments observation for the current SUI instrument exists in Master
§11.13.5.Z2AR GET 1. Source identity is not absent.

Not `BLOCKED_BY_CONFLICT`: inventoried sources do not contradict each other
once BTC, family-tier `maxSz`, Kraken, and internal `max_notional` are kept
in separate planes.

Not `VENUE_PRETRADE_RUNTIME_ALIGNMENT_REQUIRED`: this persist does not
authorize or necessitate runtime mutation. The existing canary order-plan
owner remains the only future consumer location. Consumer binding remains
unbound and requires a later separate Owner-GO after a current source.

This slice persists the already-true partial binding. Completeness of the
gates remains `false`. A Network GET is identified as the earliest next
proof step for a current reusable `maxLmtSz` observation and is **not**
authorized here.

## 4) Owner separation

```text
CANONICAL_VENUE_PRETRADE_ROLE=OKX_EEA_CANARY_VENUE_CONSTRAINT_PLAN_VALIDATOR_NOT_CORE_AUTHORITY
FUTURE_MAX_SIZE_CONSUMER_LOCATION=extract_instrument_constraints_v1@submit_transport_v1_instruments_payload
FUTURE_MAX_SIZE_CONSUMER_CURRENTLY_BOUND=false
LIVE_ADMISSION_ROLE=DOWNSTREAM_HOST_FAMILY_ADMISSION_NOT_VENUE_PRETRADE
OKX_CANARY_VENUE_PLAN_ROLE=extract_instrument_constraints_v1 + build_canary_exposure_binding_v1 + quantize_limit_price_v1
OKX_CANARY_VENUE_PLAN_CONSUMER=run_canary_submit_transport_v1
PIPELINE_KRAKEN_ROLE=LEGACY_OR_ALTERNATE_HOST_FAMILY_LIVE_ADMISSION_FAIL_CLOSED_NO_CURRENT_OKX_VENUE_METADATA_AUTHORITY
NETWORKED_ONRAMP_ROLE=FAIL_CLOSED_NETWORKLESS
NO_ORDER_HOST_BARRIER_ROLE=validate_no_order_mode_v1
FLATTEN_ROLE=SEPARATE_EMERGENCY_AUTHORITY_NOT_ENTRY_VENUE_PRETRADE_OWNER
INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_ROLE=NON_AUTHORIZING_QUARANTINED
CAP11_LIVE_TESTNET_FIXTURE_PORTS_ROLE=DECLARED_UNREACHABLE_CONTRACTS_ONLY
RISK_ENVELOPE_ROLE=NOT_VENUE_PRETRADE_OWNER
COVER_USDC_PUBLIC_TIER_MMR_ROLE=OBSERVATIONAL_FAMILY_TIER_PARSER_NOT_ENTRY_MAX_SIZE_CONSUMER
FUTURES_INSTRUMENT_METADATA_CONTRACT_V0_ROLE=DOCS_ONLY_GENERIC_FUTURES_METADATA_FLOOR_NOT_OKX_EEA_SUI_MAX_SIZE_SOURCE
```

## 5) Current venue and instrument

```text
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
VENUE=OKX
ENTITY=OKX Europe Limited
REST_HOST=eea.okx.com
INST_TYPE=FUTURES
RULE_TYPE=xperp
INSTRUMENT_FAMILY=SUI-USD_UM_XPERP
SETTLEMENT_ACCOUNT_TRUTH=USDC
PUBLIC_SETTLE_NOTE=USD_PUBLIC_VS_USDC_ACCOUNT_TRUTH
INSTRUMENT_BIND_PROVEN=true
HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID=BTC-USD_UM_XPERP-310404
HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID=BTC-USDT-SWAP
DEMO_XPERP_INSTRUMENT_ID=BTC-USD_UM_XPERP-310328
BTC_MUST_NOT_BE_CURRENT_INSTRUMENT_RESURRECTED=true
NO_BTC_TO_SUI_EVIDENCE_SUBSTITUTION=true
NO_USD_EQUALS_USDC_NORMALIZATION=true
NO_ABSENCE_EQUALS_ZERO_NORMALIZATION=true
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
KRAKEN_METADATA_MUST_NOT_SOURCE_CURRENT_OKX_PRETRADE=true
KRAKEN_CURRENT_CANONICAL_ROLE=NONE
KRAKEN_EVIDENCE_USED_FOR_CURRENT_OKX_PRETRADE=false
```

Scope is the current selected SUI identity on OKX EEA. Historical BTC values,
Demo 310328, and superseded BTC-310404 remain isolated.

## 6) Reuse-before-new inventory

Classification uses only proven repo artefacts. Name similarity is not
reuse. `REUSABLE_FOR_CURRENT_SUI_PRETRADE` is true only when venue,
instrument, and semantic plane match the current SUI OKX-EEA pretrade
question.

| Artefact | AUTHORITY_ROLE | SOURCE_ROLE | CURRENT_OR_HISTORICAL | VENUE_SCOPE | INSTRUMENT_SCOPE | PRODUCT_SCOPE | CONSUMER | MUTABILITY | REUSABLE_FOR_CURRENT_SUI_PRETRADE |
|---|---|---|---|---|---|---|---|---|---|
| Master §11.13.5.Z2AR GET 1 | CANONICAL_SSOT_PERSIST | RAW_PUBLIC_INSTRUMENTS_GET | HISTORICAL_WINDOW_2026_08_22 | OKX_EEA eea.okx.com | SUI-USD_UM_XPERP-310404 exact instId | FUTURES xperp | none for maxLmtSz | immutable persist | PARTIAL_FIELD_IDENTITY_ONLY_NOT_CURRENT_NUMERIC |
| Master §11.13.5.Z2BD / Z2BF instruments GETs | CANONICAL_SSOT_PERSIST | RAW_PUBLIC_INSTRUMENTS_GET | HISTORICAL_WINDOW_2026_08_24 | OKX_EEA | SUI-USD_UM_XPERP-310404 | FUTURES xperp | named-class ctVal/tick/minSz/lotSz only | immutable persist | FALSE_FOR_MAX_SIZE_EXPLICIT_NON_REUSE |
| `extract_instrument_constraints_v1` | CANONICAL_RUNTIME_OWNER | instruments payload parser | CURRENT | OKX_EEA canary | DEFAULT_INSTRUMENT_ID SUI | FUTURES xperp | submit_transport | mutable code not changed here | TRUE_AS_FUTURE_CONSUMER_LOCATION_NOT_CURRENT_MAX_SIZE_BIND |
| `build_canary_exposure_binding_v1` | CANONICAL_RUNTIME_OWNER | minSz/lotSz/ctVal policy | CURRENT | OKX | current instrument id | LIMIT min-exposure | order_plan | mutable code not changed here | TRUE_FOR_MIN_LOT_NOT_MAX_SIZE |
| `public_instruments_query_path_v1` | CANONICAL_QUERY_GRAMMAR | GET path builder | CURRENT | OKX_EEA | exact instId | FUTURES | submit_transport and historical public GETs | mutable code not changed here | TRUE_QUERY_GRAMMAR |
| `xperp_310404_economic_baseline_contract_v1` | PREPARATION_ONLY_NON_ACTIVATING | static baseline dict | MIXED_SUI_FIELDS_PLUS_ISOLATED_BTC_SNAPSHOT | OKX_EEA | current SUI id with isolated BTC snapshot | FUTURES xperp | none productive | mutable code not changed here | FALSE_AS_MAX_SIZE_SOURCE_NO_MAXLMTSZ_FIELD |
| `cover_usdc_current_public_tier_mmr_productive_evidence_v1` | OBSERVATIONAL_TIER_PARSER | position-tiers `maxSz` | HISTORICAL_AND_SUI_FAMILY | OKX public | family-scoped empty instId | FUTURES | Cover USDC MMR only | mutable code not changed here | FALSE_TIER_MAXSZ_IS_NOT_ORDER_MAX_SIZE |
| Master SUI qty-1 tier row `maxSz=290000` | CANONICAL_SSOT_PERSIST | family-scoped position-tiers | HISTORICAL | OKX_EEA | family SUI-USD_UM_XPERP empty instId | FUTURES xperp | MMR_tier_mapping only | immutable persist | FALSE_NOT_INSTRUMENT_MAXLMTSZ |
| Z2K / Z2Q / funding GET `maxSz` rows | HISTORICAL_EVIDENCE | BTC family position-tiers | HISTORICAL | OKX_EEA | BTC-USD_UM_XPERP | FUTURES xperp | Cover USDC MMR | immutable evidence | FALSE_BTC_MUST_NOT_TRANSFER |
| Z2R public instruments GET pack | HISTORICAL_EVIDENCE | BTC instruments GET | HISTORICAL | OKX_EEA | BTC-USD_UM_XPERP-310404 | FUTURES xperp | ctMult | immutable evidence | FALSE_BTC |
| `FUTURES_INSTRUMENT_METADATA_CONTRACT_V0` | DOCS_ONLY_GENERIC_FLOOR | required-field list including min_qty lot_size | GENERIC | unspecified | unspecified | futures/perps | none | docs | FALSE_NOT_OKX_EEA_SUI_MAX_SIZE |
| Cap 2.1 / 5.1 / 5.2 instrument fixtures | FIXTURE | synthetic minSz/lotSz/tickSz | HISTORICAL_FIXTURE | mixed | ETH/SOL/ADA not SUI-310404 | linear | universe/runtime fixtures | fixture | FALSE |
| Kraken `src&#47;exchange&#47;kraken_live.py` | LEGACY_HOST | none for OKX size fields | CURRENT_CODE | KRAKEN | n/a | n/a | pipeline live admission | mutable code not changed here | FALSE |
| exposure `max_notional` | INTERNAL_POLICY | min-executable notional clone | CURRENT | OKX canary | current instrument | LIMIT qty=minSz | order_plan | mutable code not changed here | FALSE_NOT_VENUE_MAX_SIZE |
| `FUTURES_INSTRUMENT_METADATA` snapshot fixture | FIXTURE | dashboard producer packet | FIXTURE | unspecified | unspecified | futures | dashboard tests | fixture | FALSE |

No new parser, registry, model, or owner is required. Existing query
grammar and the existing order-plan extractor are the reuse surface.

## 7) Edge inventory beginning at MAX_SIZE

Required remaining metadata-bound venue-constraint-plan edges. Bound
lot/min/tick/instrument gates from #6146 remain bound and are not re-opened.

Status vocabulary is exactly:

```text
PROVEN
PARTIALLY_BOUND
UNBOUND
CONFLICTED
NOT_REQUIRED
```

### 7.1 MAX_SIZE

```text
EDGE_ID=MAX_SIZE
EDGE_NAME=VENUE_NATIVE_LIMIT_ORDER_MAX_SIZE
EDGE_ROLE=ENTRY_LIMIT_QTY_UPPER_BOUND_BEFORE_POST
CURRENT_STATUS=PARTIALLY_BOUND
CANONICAL_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
SOURCE_REQUIRED=true
SOURCE_ALREADY_PRESENT=HISTORICAL_Z2AR_GET_1_ONLY
FIELD_NAME=maxLmtSz
FIELD_SEMANTICS=UNBOUND
UNIT=UNBOUND
TYPE=OBSERVED_DECIMAL_STRING_IN_Z2AR
NULLABILITY=UNBOUND
INSTRUMENT_SCOPE=SUI-USD_UM_XPERP-310404
VENUE_SCOPE=OKX_EEA
PRODUCT_SCOPE=FUTURES_xperp
FRESHNESS_REQUIRED=UNKNOWN
NORMALIZATION_REQUIRED=UNBOUND
CONSUMER=UNBOUND
ENFORCEMENT_LOCATION=UNBOUND
CONFLICT_STATUS=NONE
EVIDENCE_POINTERS=Master §11.13.5.Z2AR GET_1_MAX_LMT_SZ; extract_instrument_constraints_v1 required=(minSz,lotSz,tickSz,ctVal); #6146 MAX_LMT_SZ_CONSUMER_BOUND=false
```

### 7.2 MAX_MKT_SZ

```text
EDGE_ID=MAX_MKT_SZ
EDGE_NAME=VENUE_NATIVE_MARKET_ORDER_MAX_SIZE
EDGE_ROLE=PEER_FIELD_ON_SAME_INSTRUMENTS_ROW
CURRENT_STATUS=NOT_REQUIRED
CANONICAL_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
SOURCE_REQUIRED=false_FOR_CURRENT_LIMIT_ONLY_ENTRY
SOURCE_ALREADY_PRESENT=HISTORICAL_Z2AR_GET_1_MAX_MKT_SZ
FIELD_NAME=maxMktSz
FIELD_SEMANTICS=UNBOUND
UNIT=UNBOUND
INSTRUMENT_SCOPE=SUI-USD_UM_XPERP-310404
VENUE_SCOPE=OKX_EEA
PRODUCT_SCOPE=FUTURES_xperp
CONSUMER=UNBOUND
ENFORCEMENT_LOCATION=UNBOUND
CONFLICT_STATUS=NONE
EVIDENCE_POINTERS=LIMIT_ONLY_ENTRY=true; ONLY_LIMIT_ORDER_TYPE_ALLOWED; GET_1_MAX_MKT_SZ=100000 historical
```

Current canary entry is LIMIT-only. MARKET is forbidden. `maxMktSz` is
therefore not required for the current entry plan. It remains a peer field
and must not be substituted for `maxLmtSz`.

### 7.3 MAX_AVAILABLE

```text
EDGE_ID=MAX_AVAILABLE
EDGE_NAME=VENUE_NATIVE_MAX_AVAIL_SIZE
EDGE_ROLE=ACCOUNT_AND_INSTRUMENT_AVAILABLE_SIZE_BEFORE_POST
CURRENT_STATUS=UNBOUND
CANONICAL_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
SOURCE_REQUIRED=true
SOURCE_ALREADY_PRESENT=false_FOR_CURRENT_SUI
FIELD_NAME=maxAvailSize
FIELD_SEMANTICS=UNBOUND
UNIT=UNBOUND
INSTRUMENT_SCOPE=SUI-USD_UM_XPERP-310404
VENUE_SCOPE=OKX_EEA
PRODUCT_SCOPE=FUTURES_xperp
FRESHNESS_REQUIRED=UNKNOWN
CONSUMER=UNBOUND
ENFORCEMENT_LOCATION=UNBOUND
CONFLICT_STATUS=NONE
EVIDENCE_POINTERS=#6146 MAX_AVAILABLE=false; maxAvailSize absent from order_plan/exposure/submit_transport
```

### 7.4 PRICE_BAND

```text
EDGE_ID=PRICE_BAND
EDGE_NAME=VENUE_NATIVE_PRICE_BAND
EDGE_ROLE=LIMIT_PRICE_WITHIN_VENUE_BAND
CURRENT_STATUS=UNBOUND
CANONICAL_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
SOURCE_REQUIRED=true
SOURCE_ALREADY_PRESENT=false_FOR_CURRENT_SUI_PRETRADE
FIELD_NAME=UNBOUND
FIELD_SEMANTICS=UNBOUND
TICK_ALIGNMENT_IS_NOT_PRICE_BAND=true
CURRENT_STATUS_NOTE=tick quantization is bound; venue price-band is not
EVIDENCE_POINTERS=#6146 PRICE_BAND=false PRICE_BAND_PROOF_COMPLETE=false
```

### 7.5 LEVERAGE

```text
EDGE_ID=LEVERAGE
EDGE_NAME=ACCOUNT_OR_INSTRUMENT_LEVERAGE
EDGE_ROLE=PRETRADE_LEVERAGE_COMPATIBILITY
CURRENT_STATUS=UNBOUND
CANONICAL_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
SOURCE_REQUIRED=true
SOURCE_ALREADY_PRESENT=false_FOR_CURRENT_SUI_LEVERAGE
FIELD_NAME=UNBOUND
HISTORICAL_BTC_SET_LEVERAGE_3_IS_NOT_SUI_LEVERAGE=true
SUI_FAMILY_MMR_TIER_IS_NOT_LEVERAGE_GATE=true
EVIDENCE_POINTERS=#6146 LEVERAGE=false SUI_LEVERAGE_PROOF_COMPLETE=false
```

### 7.6 POS_MODE

```text
EDGE_ID=POS_MODE
EDGE_NAME=ACCOUNT_POS_MODE
EDGE_ROLE=NET_OR_LONG_SHORT_MODE_COMPATIBILITY
CURRENT_STATUS=UNBOUND
SOURCE_ALREADY_PRESENT=HISTORICAL_BTC_ACCOUNT_GET_NOT_CURRENT_SUI_REOBSERVATION
EVIDENCE_POINTERS=#6146 POS_MODE=false HISTORICAL_ACCOUNT_GET_IS_NOT_CURRENT_SUI_REOBSERVATION=true
```

### 7.7 MARGIN_MODE

```text
EDGE_ID=MARGIN_MODE
EDGE_NAME=ACCOUNT_OR_ORDER_TDMODE_MARGIN_MODE
EDGE_ROLE=CROSS_OR_ISOLATED_COMPATIBILITY
CURRENT_STATUS=UNBOUND
DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF=true
EVIDENCE_POINTERS=#6146 MARGIN_MODE=false ACCOUNT_MODE_CURRENT_SUI_PROOF_COMPLETE=false tdMode default cross
```

### 7.8 AVAILABLE_MARGIN

```text
EDGE_ID=AVAILABLE_MARGIN
EDGE_NAME=ACCOUNT_AVAILABLE_MARGIN
EDGE_ROLE=MARGIN_SUFFICIENCY_BEFORE_POST
CURRENT_STATUS=UNBOUND
EVIDENCE_POINTERS=#6146 AVAILABLE_MARGIN=false
```

### 7.9 INSTRUMENT_STATE

```text
EDGE_ID=INSTRUMENT_STATE
EDGE_NAME=VENUE_INSTRUMENT_STATE
EDGE_ROLE=LIVE_OR_SUSPEND_OR_EXPIRED_BEFORE_POST
CURRENT_STATUS=PARTIALLY_BOUND
SOURCE_ALREADY_PRESENT=HISTORICAL_Z2AR_GET_1_STATE_live
FIELD_NAME=state
FIELD_SEMANTICS=UNBOUND_BEYOND_RAW_STRING_live
CONSUMER=UNBOUND
FRESHNESS_REQUIRED=UNKNOWN
EVIDENCE_POINTERS=Master §11.13.5.Z2AR GET_1_STATE=live; #6146 INSTRUMENT_STATE=false INSTRUMENT_STATE_RUNTIME_PROOF_COMPLETE=false
```

### 7.10 Count contract

```text
REQUIRED_METADATA_EDGE_COUNT=8
REQUIRED_EDGE_IDS=MAX_SIZE,MAX_AVAILABLE,PRICE_BAND,LEVERAGE,POS_MODE,MARGIN_MODE,AVAILABLE_MARGIN,INSTRUMENT_STATE
BOUND_METADATA_EDGE_COUNT=0
PARTIAL_METADATA_EDGE_COUNT=2
PARTIAL_EDGE_IDS=MAX_SIZE,INSTRUMENT_STATE
UNBOUND_METADATA_EDGE_COUNT=6
UNBOUND_EDGE_IDS=MAX_AVAILABLE,PRICE_BAND,LEVERAGE,POS_MODE,MARGIN_MODE,AVAILABLE_MARGIN
CONFLICTED_METADATA_EDGE_COUNT=0
NOT_REQUIRED_PEER_EDGE_IDS=MAX_MKT_SZ
ALL_REQUIRED_METADATA_EDGES_BOUND=false
EARLIEST_REMAINING_UNBOUND_EDGE=MAX_SIZE
```

`MAX_SIZE` remains earliest because PARTIALLY_BOUND is not PROVEN.
`MAX_MKT_SZ` is a peer, not a required current-entry edge.

## 8) MAX_SIZE forensic adjudication

### 8.1 Does a load-bearing OKX-EEA metadata source exist for current SUI?

Yes as **historical raw observation**. No as **current reusable numeric**.

Master §11.13.5.Z2AR GET 1 is canonical SSOT persist of one public GET:

```text
GET_1_METHOD=GET
GET_1_HOST=eea.okx.com
GET_1_ENDPOINT=&#47;api&#47;v5&#47;public&#47;instruments
GET_1_QUERY=instType=FUTURES&instId=SUI-USD_UM_XPERP-310404
GET_1_HTTP=200
GET_1_EXCHANGE_CODE=0
GET_1_DATE=Sat, 22 Aug 2026 21:03:59 GMT
GET_1_TARGET_INST_ID=SUI-USD_UM_XPERP-310404
GET_1_MAX_LMT_SZ=100000000
GET_1_MAX_MKT_SZ=100000
GET_1_NO_UNIT_CONVERSION_APPLIED=true
GET_1_CLASSIFICATION=CURRENT_RAW_EXCHANGE_EVIDENCE_FOR_THAT_WINDOW
```

Exact instrument match: true for that window. Exact venue match: OKX EEA
`eea.okx.com`. Current-or-historical: historical window 2026-08-22.

Later exact-`instId` public instruments GETs in §11.13.5.Z2BD and
§11.13.5.Z2BF used the same endpoint and observed the same
`BODY_SHA256=038f2bf82f18f2d42ed26dca281cc7733e4ef7d07206fd0b19637189ec3e4cd2`
on 2026-08-24. Those persists bound named-class fields other than
`maxLmtSz` / `maxMktSz` and explicitly forbade reuse:

```text
Z2BD_THIS_OBSERVATION_MUST_NOT_BE_REUSED_AS_FUTURE_INSTRUMENT_METADATA_PROOF=true
Z2BF_THIS_OBSERVATION_MUST_NOT_BE_REUSED_AS_FUTURE_VENUE_CONSTRAINT_FRESHNESS_PROOF=true
```

Therefore the Aug-24 bodies are **not** a current MAX_SIZE source, even
though they are the same SHA as each other.

### 8.2 Is `maxSz` or an equivalent field present?

Two different raw fields exist in repo planes. They are not equivalent.

```text
RAW_VENUE_MAX_SIZE_CANDIDATE_FIELD=maxLmtSz
RAW_VENUE_MAX_SIZE_CANDIDATE_HISTORICAL_VALUE=100000000
RAW_VENUE_MARKET_MAX_SIZE_PEER_FIELD=maxMktSz
RAW_VENUE_MARKET_MAX_SIZE_PEER_HISTORICAL_VALUE=100000
POSITION_TIER_MAXSZ_FIELD=maxSz
POSITION_TIER_MAXSZ_SUI_QTY1_ROW_VALUE=290000
POSITION_TIER_MAXSZ_SCOPE=FAMILY_SCOPED_EMPTY_INSTID
POSITION_TIER_MAXSZ_IS_NOT_ORDER_MAX_SIZE=true
INSTRUMENT_ROW_MAXSZ_AS_ORDER_MAX_NOT_OBSERVED_IN_Z2AR_GET_1=true
```

Z2AR GET 1 recorded `maxLmtSz` and `maxMktSz`. It did **not** record an
instrument-row field named `maxSz`. Family-scoped position-tier `maxSz`
is a different plane.

`MAX_SIZE_EQUALS_MAXLMTSZ_SEMANTIC_PROOF=UNBOUND`. The candidate field
identity is `maxLmtSz` because that is the only exact-`instId` instruments
upper-size field persisted for the current SUI LIMIT path. OKX-EEA
prose semantics of that field are **not** separately proven in-repo.

### 8.3 Term separation (must not collapse)

```text
RAW_VENUE_MAX_SIZE=HISTORICAL_Z2AR_GET_1_MAX_LMT_SZ_100000000_NOT_CURRENT
INTERNAL_NORMALIZED_MAX_SIZE=UNBOUND_NO_TRANSFORMATION_PROVEN
CURRENT_ORDER_PLAN_MAX_ALLOWED_QTY=MIN_SZ_POLICY_QUANTITY_NOT_VENUE_MAX
RISK_MAX_SIZE=NOT_VENUE_PRETRADE
POSITION_LIMIT=NOT_PROVEN_AS_MAX_SIZE
EXPOSURE_LIMIT=EXPOSURE_V1_MAX_NOTIONAL_EQUALS_MIN_EXECUTABLE_NOT_VENUE_MAX
```

`build_canary_exposure_binding_v1` sets quantity to `minSz` and requires
`max_notional == min_executable_notional`. That is minimum-exposure
policy. It is not venue `maxLmtSz`.

No transformation (contracts, base units, quote units, notional, lot
multiples) is proven for `maxLmtSz`. `GET_1_NO_UNIT_CONVERSION_APPLIED=true`
records that none was applied. It does not prove the unit.

```text
MAX_SIZE_SOURCE=HISTORICAL_MASTER_Z2AR_GET_1_PUBLIC_INSTRUMENTS
MAX_SIZE_RAW_FIELD=maxLmtSz
MAX_SIZE_RAW_VALUE=100000000
MAX_SIZE_UNIT=UNBOUND
MAX_SIZE_SCOPE=EXACT_INSTID_SUI-USD_UM_XPERP-310404_OKX_EEA_HISTORICAL_WINDOW
MAX_SIZE_FRESHNESS_STATUS=UNBOUND
MAX_SIZE_NORMALIZATION_STATUS=UNBOUND_NONE_APPLIED_NONE_PROVEN
MAX_SIZE_CURRENT_REUSABLE_NUMERIC=UNBOUND
```

MAX_SIZE remains PARTIALLY_BOUND. No forced closure.

## 9) Current SUI / historical BTC firewall

```text
BTC_METADATA_REUSED=false
SUI_OTHER_INSTRUMENT_METADATA_REUSED=false
FAMILY_SCOPED_METADATA_REUSED=false
VENUE_GLOBAL_METADATA_REUSED=false
KRAKEN_METADATA_REUSED=false
KRAKEN_CURRENT_CANONICAL_ROLE=NONE
```

Reasons:

- BTC instruments, tier, fee, and leverage evidence remain BTC-bound.
  `NO_BTC_TO_SUI_EVIDENCE_SUBSTITUTION=true` is already canonical.
- No other SUI instrument id is used as a source for this MAX_SIZE bind.
- Family-scoped position-tier `maxSz=290000` is **not** reused as order
  MAX_SIZE. Family scope is proven for MMR_tier_mapping only.
- No venue-global max-size field is proven.
- Kraken is not current canonical venue and does not source OKX pretrade.

## 10) Freshness / refresh / fail-closed

```text
FRESHNESS_POLICY=UNBOUND
STATIC_ENOUGH_FOR_CONFIG=UNKNOWN
SESSION_BOUND=UNKNOWN
INSTRUMENT_LIFECYCLE_BOUND=UNKNOWN
REQUIRES_STARTUP_REFRESH=UNKNOWN
REQUIRES_PRE_SUBMIT_REFRESH=UNKNOWN
REQUIRES_PERIODIC_REFRESH=UNKNOWN
UNKNOWN=true
```

No Peak_Trade freshness TTL for `maxLmtSz` is proven. Canonical
§11.13.5.R already forbids inventing a TTL. Z2BD/Z2BF explicitly forbid
reusing those instruments windows as future metadata or venue-constraint
freshness proof. This persist does **not** invent fetch-on-every-order.

Fail-closed that is already true of the existing owner, and is not a new
Safety owner:

```text
MISSING_REQUIRED_OPERAND_MUST_NOT_YIELD_PERMISSIVE_VENUE_CONSTRAINT_PLAN=true
EXISTING_EXTRACTOR_FAILS_CLOSED_ON_MISSING_MINSZ_LOTSZ_TICKSZ_CTVAL=true
EXISTING_EXTRACTOR_DOES_NOT_READ_MAXLMTSZ=true
NO_NEW_SAFETY_OWNER=true
```

If a required MAX_SIZE operand is missing, stale, or semantically unbound,
no permissive venue-constraint plan may be derived from that absence. That
rule attaches to the existing order-plan owner only. This persist does not
implement the check.

Submit-transport already issues a GET of
`public_instruments_query_path_v1` before building the order plan when
submit is separately authorized. That execute-time GET is **not** a
current observation and is **not** this slice's Network GET.

## 11) Source-gap / Network GET boundary

```text
NETWORK_GET_REQUIRED=true
NETWORK_GET_PURPOSE=CURRENT_PUBLIC_INSTRUMENTS_MAXLMTSZ_MAXMKTSZ_REOBSERVATION_FOR_CURRENT_SUI_NOT_CONSUMER_IMPLEMENTATION
TARGET_VENUE=OKX_EEA
TARGET_INSTRUMENT=SUI-USD_UM_XPERP-310404
TARGET_ENDPOINT=&#47;api&#47;v5&#47;public&#47;instruments
QUERY_GRAMMAR=instType=FUTURES&instId=SUI-USD_UM_XPERP-310404
AUTH_REQUIRED=false
EXPECTED_RESPONSE_FIELDS=instId,maxLmtSz,maxMktSz,minSz,lotSz,tickSz,ctVal,ctValCcy,instType,ruleType,state,instFamily
EXPECTED_EVIDENCE_FORM=SANITIZED_GET_SNAPSHOT_PLUS_CANONICAL_SSOT_FIELD_PERSIST
EXPECTED_CONSUMER=LATER_SEPARATE_OWNER_GO_NOT_THIS_SLICE
MUTATION_EXPECTED=false
NETWORK_GET_PERFORMED=false
NETWORK_POST_PERFORMED=false
```

A fresh public GET is the earliest next proof step for a **current
reusable** `maxLmtSz` observation because:

1. Z2AR GET 1 is a dated window, not a standing current numeric.
2. Z2BD/Z2BF later same-endpoint observations may not be reused as future
   instrument-metadata or venue-constraint freshness proof.
3. No freshness policy exists that would otherwise keep the historical
   numeric current.

A GET is **not** sufficient to complete MAX_SIZE. Unit, semantic
equivalence, consumer, and enforcement remain unbound after a GET.
This Owner-GO does **not** authorize the GET.

## 12) Negative / non-equivalence contracts

```text
LIVE_ADMISSION_IS_NOT_VENUE_PRETRADE_VALIDITY=true
VENUE_METADATA_EXISTENCE_IS_NOT_GATE_BINDING=true
STATIC_FIELD_EXISTENCE_IS_NOT_RUNTIME_VALIDATION=true
HISTORICAL_RAW_OBSERVATION_IS_NOT_CURRENT_REUSABLE_NUMERIC=true
MAXLMTSZ_IS_NOT_PROVEN_SEMANTIC_EQUIVALENT_OF_MAX_SIZE=true
MAXLMTSZ_IS_NOT_MAXMKTSZ=true
MAXLMTSZ_IS_NOT_POSITION_TIER_MAXSZ=true
MIN_SIZE_IS_NOT_MAX_SIZE=true
LOT_SIZE_IS_NOT_MAX_AVAILABLE=true
TICK_ALIGNMENT_IS_NOT_PRICE_BAND_VALIDITY=true
EXPOSURE_MAX_NOTIONAL_IS_NOT_VENUE_MAX_SIZE=true
ORDER_PLAN_QTY_MINSZ_IS_NOT_VENUE_MAX_SIZE=true
DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF=true
HISTORICAL_BTC_LEVERAGE_IS_NOT_SUI_LEVERAGE=true
HISTORICAL_ACCOUNT_GET_IS_NOT_CURRENT_SUI_REOBSERVATION=true
FAMILY_SCOPED_TIER_MAXSZ_IS_NOT_INSTRUMENT_MAXLMTSZ=true
Z2BD_Z2BF_SAME_BODY_SHA_IS_NOT_CURRENT_MAX_SIZE_BIND=true
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
KRAKEN_METADATA_MUST_NOT_SOURCE_CURRENT_OKX_PRETRADE=true
VENUE_PRETRADE_COMPLETE_IS_NOT_IMPLIED_BY_BOUND_LOT_MIN_TICK=true
METADATA_BINDING_PARTIAL_IS_NOT_RUNTIME_MUTATION_AUTHORIZATION=true
METADATA_BINDING_PARTIAL_IS_NOT_RUNTIME_MUTATION_NECESSITY=true
NETWORK_GET_REQUIRED_IS_NOT_NETWORK_GET_AUTHORIZATION=true
POSITION_ABSENCE_IS_NOT_ZERO=true
EMPTY_DATA_IS_NOT_ZERO=true
ABSENT_TARGET_ROW_IS_NOT_ZERO=true
FLATTEN_IS_NOT_ENTRY_VENUE_PRETRADE_OWNER=true
NO_UNIT_CONVERSION_APPLIED_IS_NOT_UNIT_PROOF=true
```

## 13) Guards (not SSOT)

Exact proof file:

`tests/ops/test_peak_trade_post_restoration_venue_pretrade_metadata_binding_alignment_adjudication_v1.py`

Guards must keep:

- Master §5.3 names this spec and `VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL`
- MAX_SIZE binding status `PARTIALLY_BOUND`; all required metadata edges bound false
- earliest remaining unbound edge `MAX_SIZE`; earliest remaining conflict `NONE`
- Network GET required true; Network GET performed false; POST performed false
- runtime alignment required false; second owner false; restoration reopen false
- current selected instrument remains `SUI-USD_UM_XPERP-310404`; current venue remains OKX EEA
- Kraken is not current canonical venue and does not source current OKX pretrade
- BTC must not be resurrected as current instrument
- `maxLmtSz` historical raw value `100000000` is not promoted to current reusable numeric
- `maxLmtSz` is not `maxMktSz`; `maxLmtSz` is not position-tier `maxSz`
- exposure `max_notional` is not venue MAX_SIZE
- extract_instrument_constraints required tuple remains `minSz, lotSz, tickSz, ctVal`
- `maxLmtSz` / `maxMktSz` / `maxAvailSize` remain absent from order_plan, exposure, and submit_transport
- #6143, #6144, #6145, and #6146 remain closed
- freshness policy remains UNBOUND
- preexisting CALL_GRAPH equality test is not repaired in this slice

## 14) Out of scope this slice

```text
PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false
CALL_GRAPH_V1_HARMONIZATION=NOT_THIS_SLICE
REQUIRED_CALL_GRAPH_HARMONIZATION=NOT_THIS_SLICE
TEST_CONSTANTS_AND_CALL_GRAPH_BOUND_REPAIR=NOT_THIS_SLICE
MAX_SIZE_IMPLEMENTATION=NOT_THIS_SLICE
MAX_AVAILABLE_IMPLEMENTATION=NOT_THIS_SLICE
PRICE_BAND_IMPLEMENTATION=NOT_THIS_SLICE
LEVERAGE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
ACCOUNT_MODE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
INSTRUMENT_STATE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
AUTHENTICATED_GET=NOT_THIS_SLICE
PUBLIC_VENUE_GET=NOT_THIS_SLICE
NETWORK_GET=NOT_THIS_SLICE
POST=NOT_THIS_SLICE
CANARY_EXECUTE=NOT_THIS_SLICE
FLATTEN=NOT_THIS_SLICE
MULTI_FUTURE=NOT_THIS_SLICE
CAP_11_2_TO_11_12_ACTIVATION=NOT_THIS_SLICE
PR_6129=NOT_THIS_SLICE
RECOVERY_TRACK=NOT_THIS_SLICE
ORDER_PLAN_RUNTIME_MUTATION=NOT_THIS_SLICE
EXPOSURE_RUNTIME_MUTATION=NOT_THIS_SLICE
SUBMIT_TRANSPORT_RUNTIME_MUTATION=NOT_THIS_SLICE
SAFETYGUARD_RUNTIME_MUTATION=NOT_THIS_SLICE
KRAKEN_RUNTIME_MUTATION=NOT_THIS_SLICE
CURRENT_NUMERIC_FREEZE=NOT_THIS_SLICE
UNIT_INVENTION=NOT_THIS_SLICE
FRESHNESS_POLICY_INVENTION=NOT_THIS_SLICE
CORE_RUNTIME_MUTATION=false
SEE_ALSO_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE=docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md
SEE_ALSO_POST_6148_MAX_SIZE_UNIT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md
```

Historical `VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT=NOT_THIS_SLICE` in
#6146 remains historically true for that slice. Later metadata-binding
adjudication is recorded here. This persist does not close venue-pretrade
completeness and does not implement venue limit gates. The later authorized
exact venue metadata GET is recorded in
`SEE_ALSO_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE`. This
#6147 persist did not perform that GET.

## 15) Existing guards reused (not duplicated)

| Invariant | Current guard |
|---|---|
| 29P → Safety → 29Q productive Replay order | `tests/trading/master_v2/test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1.py` |
| Appendix-A core parity | `tests/trading/master_v2/test_master_v2_integrated_replay_appendix_a_core_logic_parity_post_6135_contract_v1.py` |
| Hardening-v2 historical safety seam | `tests/ops/test_hardening_v2_historical_safety_seam_contracts_v1.py` |
| Owner-composed full-chain host consumption | `tests/trading/master_v2/test_master_v2_owner_composed_full_chain_host_consumption_proof_v1.py` |
| §5.3 host-graph SSOT | `tests/ops/test_master_v2_section_5_3_host_graph_ssot_adjudication_v1.py` |
| C4 named Master pointer | `tests/ops/test_master_v2_c4_named_master_ssot_pointer_v1.py` |
| Historically attested restoration authorization | `tests/governance/test_historically_attested_current_system_semantic_restoration_authorization_v1.py` |
| Parallel-owner / skip-safety quarantine | `tests/ops/test_peak_trade_post_restoration_parallel_owner_and_skip_safety_path_quarantine_v1.py` |
| Remaining P0 quarantine | `tests/ops/test_peak_trade_post_restoration_remaining_p0_quarantine_v1.py` |
| Preservation / compatibility contract | `tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py` |
| Accounting / portfolio alignment | `tests/ops/test_peak_trade_post_restoration_accounting_portfolio_alignment_adjudication_v1.py` |
| Simulated execution pipeline adjudication | `tests/ops/test_peak_trade_post_restoration_simulated_execution_pipeline_adjudication_v1.py` |
| Live safety gates adjudication | `tests/ops/test_peak_trade_post_restoration_live_safety_gates_adjudication_v1.py` |
| Venue pretrade limit gates adjudication | `tests/ops/test_peak_trade_post_restoration_venue_pretrade_limit_gates_adjudication_v1.py` |
| Empty/absent is not zero | `tests/ops/test_section_11_13_5_z2cm_position_state_predicate_contract_v1.py` |
| Cap 11.9 fixture unreachable | `tests/ops/test_capability_11_9_live_canary_order_execution_v1.py` |
| Canary submit transport / order plan | `tests/ops/test_section_11_13_5_canary_submit_transport_v1.py` |

## 16) Negative contract

```text
RUNTIME_CORE_MUTATION=false
TRADING_LOGIC_MUTATION=false
COMPUTE_OWNER_MUTATION=false
RISK_OWNER_MUTATION=false
SAFETY_OWNER_MUTATION=false
INTENT_OWNER_MUTATION=false
SIDESTATE_WRITER_MUTATION=false
ENTRY_EXIT_OWNER_MUTATION=false
ORDER_PLAN_MUTATED=false
EXPOSURE_MUTATED=false
QUANTIZE_LIMIT_PRICE_MUTATED=false
SUBMIT_TRANSPORT_MUTATED=false
HTTP_CLIENT_MUTATED=false
SAFETYGUARD_MUTATED=false
KRAKEN_RUNTIME_MUTATED=false
FLATTEN_LOGIC_MUTATED=false
MAX_SIZE_IMPLEMENTED=false
MAX_AVAILABLE_IMPLEMENTED=false
PRICE_BAND_IMPLEMENTED=false
LEVERAGE_GATE_IMPLEMENTED=false
ACCOUNT_MODE_GATE_IMPLEMENTED=false
INSTRUMENT_STATE_GATE_IMPLEMENTED=false
VENUE_PRETRADE_IMPLEMENTED=false
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
CHANGED_RUNTIME_FILES_EXPECTED=NONE
RUNTIME_DECOUPLING_REQUIRED=false
NEW_VENUE_PRETRADE_COMPONENT_REQUIRED=false
RECOVERY_TRACK_TOUCHED=false
PR_6129_TOUCHED=false
LIVE_READINESS_MUTATION=false
ORDER_SUBMIT_PERFORMED=false
FLATTEN_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORITY_CHANGED=false
NETWORK_GET_PERFORMED=false
NETWORK_POST_PERFORMED=false
FORENSIC_REFERENCE_AUTHORITY=NONE
MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY
SECOND_CORE_OWNER_CREATED=false
SECOND_VENUE_PRETRADE_OWNER_CREATED=false
PREEXISTING_CALL_GRAPH_DRIFT_REPAIRED=false
BTC_METADATA_REUSED=false
SUI_OTHER_INSTRUMENT_METADATA_REUSED=false
FAMILY_SCOPED_METADATA_REUSED=false
VENUE_GLOBAL_METADATA_REUSED=false
KRAKEN_METADATA_REUSED=false
```
