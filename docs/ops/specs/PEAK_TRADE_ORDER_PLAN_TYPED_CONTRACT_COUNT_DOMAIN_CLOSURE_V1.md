# Peak_Trade — Order Plan Typed Contract Count Domain Closure v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Define the canonical Peak_Trade order-plan quantity domain as venue contract count and align the canary producer to the already-bound SUI_OPERATIVE_ORDER_SZ object so MAX_SIZE normalization can close. Not a second SSOT. Not restoration reopen. Not core Master V2 mutation. Not live or execution authority. Not a freshness-policy bind. Not a max-size consumer bind. Not venue-pretrade completeness. Not a minSz-to-qty upgrade.
docs_token: DOCS_TOKEN_PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_MAX_SIZE_NORMALIZATION_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1.md
PRIOR_MAX_SIZE_UNIT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md
PRIOR_EXACT_VENUE_METADATA_GET=docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md
PRIOR_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
PRIOR_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md
PARALLEL_SSOT_CREATED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_RUNTIME_MUTATION=false
DEFAULT_RUNTIME_MUTATION=false
CANARY_VENUE_CONSTRAINT_PLAN_RUNTIME_MUTATION=true
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
CHANGED_RUNTIME_FILES=venue_contract_count_v1.py,exposure_v1.py,order_plan_v1.py,submit_transport_v1.py
RUNTIME_ALIGNMENT_REQUIRED=true
RUNTIME_MUTATION_JUSTIFIED=true
RUNTIME_MUTATION_PERFORMED=true
NETWORK_GET_AUTHORIZED=false
NETWORK_GET_PERFORMED=false
NETWORK_VENUE_GET_PERFORMED=false
NETWORK_POST_AUTHORIZED=false
NETWORK_POST_PERFORMED=false
NETWORK_DOCUMENTATION_READ_PERFORMED=false
AUTH_REQUIRED=false
AUTH_HEADER_SENT=false
```

This document is subordinate to the Master Runbook and to the post-restoration
preservation contract. It does not replace Master §5.3, Appendix A, C4, Replay
Safety, Cap 7.2, live-safety #6145, simulated-execution #6144,
accounting/portfolio #6143, venue-pretrade limit-gates #6146,
metadata-binding alignment #6147, exact venue metadata GET #6148,
MAX_SIZE unit adjudication #6149, or MAX_SIZE normalization
adjudication #6150. #6150 remains the closed historical persist that
quantity-domain identity from the untyped minSz copy was UNPROVEN. This
slice does **not** reverse that historical finding. It defines a new
typed system contract and aligns the producer to an already-bound
contract-count object.

## 1) Restoration and predecessor boundary

```text
RESTORATION_COMPLETION_CHECKPOINT_SHA=21452016ff998c1af63f24c36060f2a54020c0df
HISTORICAL_MASTER_V2_DOUBLE_PLAY_BASELINE=IMMUTABLE_NORMATIVE_BASELINE
CURRENT_SYSTEM_MUST_CONFORM_TO_HISTORICAL_CORE=true
NO_CURRENT_FIRST_ARCHITECTURE=true
P0_QUARANTINE_REMAINS_CLOSED=true
ACCOUNTING_PORTFOLIO_ALIGNMENT_REMAINS_CLOSED=true
SIMULATED_EXECUTION_PIPELINE_REMAINS_CLOSED=true
LIVE_SAFETY_GATES_REMAIN_CLOSED=true
VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_REMAINS_CLOSED=true
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_REMAINS_CLOSED=true
EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1_REMAINS_CLOSED=true
POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1_REMAINS_CLOSED=true
POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1_REMAINS_CLOSED=true
HISTORICAL_6150_MAX_SIZE_NORMALIZATION_STATUS=UNBOUND
HISTORICAL_6150_ORDER_PLAN_QTY_UNIT_STATUS=UNBOUND
HISTORICAL_6150_ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING_STATUS=UNBOUND
HISTORICAL_6150_MAX_SIZE_COMPARISON_DOMAIN_STATUS=UNBOUND
HISTORICAL_6150_NETWORK_VENUE_GET_PERFORMED=false
```

#6150 remains the closed investigation that identity from the untyped
`minSz` copy was unproven. This slice consumes the separate Owner-GO
for typed contract-count domain closure. It does not rewrite the #6150
historical UNBOUND persist.

## 2) Protected productive owner graph

```text
CANONICAL_VENUE_PRETRADE_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
VENUE_PRETRADE_OWNER_MODEL=OKX_EEA_CANARY_VENUE_CONSTRAINT_PLAN_OWNER_NOT_A_SECOND_CORE_RISK_OR_SAFETY_OWNER
SECOND_VENUE_PRETRADE_OWNER_EXISTS=false
SECOND_OWNER_REQUIRED=false
SECOND_COMPUTE_OWNER_EXISTS=false
SECOND_RISK_OWNER_EXISTS=false
SECOND_SAFETY_OWNER_EXISTS=false
SECOND_INTENT_OWNER_EXISTS=false
SECOND_EXECUTION_OWNER_EXISTS=false
CLOSED_OWNER_GRAPH_PRESERVED=true
FUTURE_MAX_SIZE_CONSUMER_LOCATION=extract_instrument_constraints_v1@submit_transport_v1_instruments_payload
FUTURE_MAX_SIZE_CONSUMER_CURRENTLY_BOUND=false
VENUE_PRETRADE_IS_NOT_REPLAY_SAFETY=true
VENUE_PRETRADE_IS_NOT_CORE_RISK_AUTHORITY=true
VENUE_PRETRADE_IS_NOT_EXECUTION_AUTHORITY=true
KRAKEN_CURRENT_CANONICAL_ROLE=NONE
KRAKEN_METADATA_REUSED=false
KRAKEN_EVIDENCE_USED_FOR_CURRENT_OKX_PRETRADE=false
KRAKEN_EXCLUSION_CLOSED=true
```

## 3) Epistemic class separation

```text
CURRENT_RAW_EVIDENCE=PR_6148_PUBLIC_INSTRUMENTS_GET_WINDOW_20260829T182239Z
OFFICIAL_DEFINITIONAL_AUTHORITY=REUSED_FROM_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_NO_NEW_DOC_FETCH
CANONICAL_AUTHORITY=MASTER_RUNBOOK_PLUS_THIS_SUBORDINATE_PERSIST
HISTORICAL_RAW_EVIDENCE=Z2BE_SUI_OPERATIVE_ORDER_SZ_AND_Z2BF_ADMISSIBILITY
ADJUDICATED_CONCLUSION=THIS_DOCUMENT
NAVIGATION_ONLY=MAP_OF_TRUTH
INTERPRETATION=INTEGER_CONTRACT_REQUIRED_ON_MINSZ_LOTSZ_REMAINS_PEAK_TRADE_CANARY_CONSTRAINT
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=MAX_SIZE_FRESHNESS_POLICY_AND_CONSUMER
CONFLICTED=NONE
```

Authority for the typed domain is this Owner-ratified system contract.
Authority for the canary numeric count is Z2BE/Z2BF
`SUI_OPERATIVE_ORDER_SZ`. Authority for maxLmtSz/maxMktSz unit remains
#6149. Official Place Order request-parameter unit remains historically
underspecified and is **not** rewritten.

## 4) Current instrument and reused evidence

```text
OWNER_GO_THIS_SLICE=PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1
BOUND_ORIGIN_MAIN_SHA=1d84bd4f0835b0ec719ce4d707f61252fb774a66
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
CURRENT_REST_HOST=eea.okx.com
CURRENT_INST_TYPE=FUTURES
CURRENT_RULE_TYPE=xperp
CURRENT_MAXLMTSZ_FIELD=maxLmtSz
CURRENT_MAXLMTSZ_RAW_VALUE=100000000
CURRENT_MAXMKTSZ_FIELD=maxMktSz
CURRENT_MAXMKTSZ_RAW_VALUE=100000
CURRENT_CTVAL_RAW_VALUE=1
CURRENT_CTVALCCY_RAW_VALUE=SUI
CURRENT_CTMULT_RAW_VALUE=1
CURRENT_CTTYPE_RAW_VALUE=linear
CURRENT_MINSZ_RAW_VALUE=1
CURRENT_LOTSZ_RAW_VALUE=1
CURRENT_STATE_RAW_VALUE=live
MAX_SIZE_UNIT_STATUS=BOUND
MAX_SIZE_UNIT=contracts
NETWORK_VENUE_GET_PERFORMED=false
NETWORK_DOCUMENTATION_READ_PERFORMED=false
```

## 5) Typed quantity contract

Docs alias `qty` and runtime field `quantity` remain the same Python
field. The field is now explicitly typed.

```text
ORDER_PLAN_QTY_SEMANTIC_STATUS=BOUND
ORDER_PLAN_QTY_SEMANTIC=executable venue order quantity expressed as venue contract count
ORDER_PLAN_V1_PYTHON_FIELD_NAME=quantity
ORDER_PLAN_V1_HAS_FIELD_NAMED_QTY=false
ORDER_PLAN_V1_QTY_IS_DOCS_ALIAS=true
ORDER_PLAN_QTY_TYPE=str
ORDER_PLAN_QTY_UNIT_STATUS=BOUND
ORDER_PLAN_QTY_UNIT=contracts
ORDER_PLAN_QTY_DOMAIN_STATUS=BOUND
ORDER_PLAN_QTY_DOMAIN=VENUE_CONTRACT_COUNT
ORDER_PLAN_QTY_PRODUCER=exposure_v1.build_canary_exposure_binding_v1
ORDER_PLAN_QTY_CONSUMER=build_venue_native_order_body_v1@submit_transport_v1
```

This bind is a Peak_Trade system contract. It is **not** derived from
`minSz == 1`, `qty == "1"`, `sz == "1"`, or `ctVal == 1`.

## 6) Producer and sizing formula

Existing `exposure_v1` did **not** produce a proven contract count. It
copied `instrument_min_sz`. That historical producer remains the #6150
finding and is retired as quantity **source**.

Canary sizing does not invert notional. Desired canary exposure is the
already-bound Owner policy object:

```text
CONTRACT_SIZING_PRODUCER=venue_contract_count_v1.canary_venue_contract_count_v1@exposure_v1.build_canary_exposure_binding_v1
CONTRACT_SIZING_FORMULA_STATUS=BOUND
CONTRACT_SIZING_FORMULA=venue_contract_count = SUI_OPERATIVE_ORDER_SZ
SUI_OPERATIVE_ORDER_SZ=1
SUI_OPERATIVE_ORDER_SZ_UNIT=CONTRACTS_SZ
SUI_OPERATIVE_QTY_DERIVED_FROM_MINSZ=false
SUI_OPERATIVE_QTY_DERIVED_FROM_LOTSZ=false
SUI_OPERATIVE_QTY_DERIVED_FROM_CTVAL=false
GENERAL_NOTIONAL_TO_CONTRACT_COUNT_FORMULA_STATUS=UNBOUND
NORMALIZATION_REQUIRES_CTVAL=false
NORMALIZATION_REQUIRES_CTMULT=false
NORMALIZATION_REQUIRES_CTTYPE=false
CTVAL_IS_NOT_QTY_TO_SZ_FORMULA=true
ONE_CONTRACT_EQUALS_ONE_SUI=false
NO_NORMALIZATION_CTVAL_1_TO_ONE_CONTRACT_EQUALS_ONE_SUI=true
```

Pipeline:

```text
strategy/exposure intent
  -> contract sizing (SUI_OPERATIVE_ORDER_SZ)
  -> venue_contract_count
  -> lotSz admissibility / minSz floor
  -> typed order_plan quantity
  -> identity serialize to Place Order sz
```

`ctVal` remains the notional operand `qty * ctVal * price` after the
typed count exists. It is not a qty→sz factor.

## 7) minSz and lotSz

```text
MIN_SIZE_ROLE_STATUS=BOUND
MIN_SIZE_ROLE=venue_contract_count_lower_admissibility_floor_not_quantity_source
FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true
LOT_SIZE_ROLE_STATUS=BOUND
LOT_SIZE_ROLE=venue_contract_count_increment_admissibility_official_derivatives_number_of_contracts_runtime_modulo_validation_not_qty_to_sz_transform
LOTSZ_USED_AS_QTY_TO_SZ_TRANSFORM=false
LOTSZ_USED_AS_RUNTIME_MODULO_VALIDATION=true
ORDER_PLAN_QTY_QUANTIZED_BEFORE_TRANSPORT=false
LOT_SIZE_QUANTIZATION_STATUS=NOT_REQUIRED
LOT_SIZE_QUANTIZATION_POLICY=NOT_REQUIRED_FAIL_CLOSED_IF_NOT_MULTIPLE_NO_FLOOR_CEIL_ROUND_REWRITE
INTEGER_CONTRACT_REQUIRED_ON_MINSZ_LOTSZ_REMAINS_PEAK_TRADE_CANARY_CONSTRAINT=true
INTEGER_CONTRACT_REQUIRED_IS_NOT_OFFICIAL_UNIT_PROOF=true
FRACTIONAL_CONTRACTS_POSSIBLE_IF_LOTSZ_LT_1=UNPROVEN_GLOBALLY_PEAK_TRADE_CANARY_FAIL_CLOSED_ON_NON_INTEGRAL_MINSZ_LOTSZ
CURRENT_SUI_LOTSZ_RAW_VALUE=1
CURRENT_SUI_LOTSZ_1_IS_NOT_CONTRACT_DOMAIN_PROOF=true
```

`minSz` is only a floor. `lotSz` is only an increment check. No
quantization rewrite is implemented because existing authority supplies
fail-closed admissibility and does not ratify floor, ceil, or round.

## 8) Mapping and max-size comparison

After typed contract sizing, Place Order `sz` is identity serialization
of the typed count. Official Place Order request-parameter text remains
"Quantity to buy or sell" and is **not** rewritten.

```text
ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING_STATUS=BOUND
ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING=IDENTITY_AFTER_CONTRACT_SIZING
VENUE_ORDER_SZ_SEMANTIC_STATUS=BOUND
VENUE_ORDER_SZ_SEMANTIC=official_place_order_request_parameter_quantity_to_buy_or_sell
VENUE_ORDER_SZ_UNIT_STATUS=UNBOUND
PLACE_ORDER_SZ_REQUEST_PARAM_STATES_CONTRACTS=false
MAX_SIZE_COMPARISON_DOMAIN_STATUS=BOUND
MAX_SIZE_COMPARISON_DOMAIN=venue_contract_count
MAX_SIZE_NORMALIZATION_STATUS=BOUND
LIMIT_ORDER_MAX_SIZE_FIELD=maxLmtSz
MARKET_ORDER_MAX_SIZE_FIELD=maxMktSz
CANARY_ENTRY_ORDER_TYPE=LIMIT
```

Comparison helper `compare_venue_contract_count_to_max_size_v1` proves
the domain. It is **not** a live instruments consumer. Freshness and
consumer remain independently unbound.

```text
MAX_SIZE_CONSUMER_BOUND=false
MAX_SIZE_FRESHNESS_STATUS=WINDOW_OBSERVED_NOT_POLICY_BOUND
MAX_SIZE_FRESHNESS_POLICY=UNBOUND
CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false
UPCCHG_IS_NOT_FRESHNESS_POLICY=true
EXISTING_EXTRACTOR_REQUIRED_TUPLE=minSz,lotSz,tickSz,ctVal
EXISTING_EXTRACTOR_DOES_NOT_READ_MAXLMTSZ=true
```

## 9) Required edge reassessment

Status vocabulary is exactly `PROVEN`, `PARTIALLY_BOUND`, `UNBOUND`,
`CONFLICTED`, `NOT_REQUIRED`.

| EDGE_ID | CURRENT_STATUS | Reason after this typed-domain closure |
|---|---|---|
| MAX_SIZE | PARTIALLY_BOUND | Current raw `maxLmtSz=100000000` observed; unit `contracts`; quantity domain now `VENUE_CONTRACT_COUNT`; comparison domain bound; freshness policy and consumer remain unbound |
| MAX_MKT_SZ | NOT_REQUIRED | LIMIT-only entry; peer unit `contracts`; comparison helper selects `maxMktSz` for MARKET; still not a substitute for `maxLmtSz` |
| MAX_AVAILABLE | UNBOUND | `maxAvailSize` MISSING on instruments row; official max-avail surface is authenticated account GET |
| PRICE_BAND | UNBOUND | Raw price-limit percent fields observed; field-to-gate semantic proof and consumer unbound |
| LEVERAGE | UNBOUND | Raw instrument `lever=20` observed; not an account leverage gate |
| POS_MODE | UNBOUND | Not supplied by the public instruments GET |
| MARGIN_MODE | UNBOUND | Not supplied by the public instruments GET |
| AVAILABLE_MARGIN | UNBOUND | Not supplied by the public instruments GET |
| INSTRUMENT_STATE | PARTIALLY_BOUND | Current raw `state=live` observed; consumer and freshness policy unbound |

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
EARLIEST_REMAINING_CONFLICT=NONE
EARLIEST_REMAINING_MAX_SIZE_GAP=MAX_SIZE_FRESHNESS_POLICY
REMAINING_MAX_SIZE_SUBDEPENDENCIES=MAX_SIZE_FRESHNESS_POLICY,MAX_SIZE_CONSUMER
BEGINNING_AT=MAX_SIZE
EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_FRESHNESS_POLICY
```

`MAX_SIZE` remains earliest because `PARTIALLY_BOUND` is not `PROVEN`.
Normalization is closed. The next MAX_SIZE subdependency is freshness
policy. Consumer remains independently unbound. This slice does **not**
jump to MAX_AVAILABLE or any later required edge.

## 10) Adjudication result

```text
ADJUDICATION_RESULT=PARTIAL
SOURCE_ADJUDICATION_RESULT=MAX_SIZE_NORMALIZATION_BOUND_TYPED_VENUE_CONTRACT_COUNT_IDENTITY_AFTER_CONTRACT_SIZING_FRESHNESS_AND_CONSUMER_UNBOUND
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
NEXT_DISTINCT_SURFACE=MAX_SIZE_FRESHNESS_POLICY
NEXT_DISTINCT_SURFACE_AUTHORIZED=false
```

Not `COMPLETE`. Not `BLOCKED_BY_MISSING_SOURCE`. Not
`BLOCKED_BY_CONFLICT`. Typed producer plus identity mapping close
normalization. Freshness policy is the remaining earliest MAX_SIZE gap.

## 11) Negative / non-equivalence contracts

```text
TYPED_DOMAIN_IS_NOT_MINSZ_UPGRADE=true
TYPED_DOMAIN_IS_NOT_OFFICIAL_PLACE_ORDER_REQUEST_PARAM_REWRITE=true
TYPED_DOMAIN_IS_NOT_FRESHNESS_POLICY=true
TYPED_DOMAIN_IS_NOT_CONSUMER_BIND=true
FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true
MINSZ_UNIT_IS_NOT_ORDER_PLAN_QTY_SOURCE=true
LOTSZ_UNIT_IS_NOT_QTY_TO_SZ_TRANSFORM=true
LOTSZ_1_IS_NOT_CONTRACT_DOMAIN_PROOF=true
PLACE_ORDER_SZ_UNDERSPECIFIED_REQUEST_PARAM_IS_NOT_ORDER_PLAN_QTY_DOMAIN_PROOF=true
INTEGER_CONTRACT_REQUIRED_IS_NOT_OFFICIAL_UNIT_PROOF=true
Z2S_API_SZ_FUTURES_UNIT_IS_NOT_SUI_ORDER_PLAN_QTY_BIND=true
ONE_CONTRACT_EQUALS_ONE_SUI=false
CTVAL_IS_NOT_QTY_TO_SZ_FORMULA=true
BTC_CTVAL_ALGEBRA_IS_NOT_SUI_QTY_DOMAIN=true
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
MAXLMTSZ_IS_NOT_MAXMKTSZ=true
MAXLMTSZ_IS_NOT_POSITION_TIER_MAXSZ=true
MAXLMTSZ_IS_NOT_MAXAVAILSIZE=true
EXPOSURE_MAX_NOTIONAL_IS_NOT_VENUE_MAX_SIZE=true
UPCCHG_IS_NOT_FRESHNESS_POLICY=true
HISTORICAL_6150_MAX_SIZE_NORMALIZATION_UNBOUND_IS_NOT_THIS_SLICE=true
THIS_SLICE_DOES_NOT_REWRITE_6150_HISTORICAL_UNBOUND=true
STRATEGY_LOGIC_CHANGED=false
SIGNAL_LOGIC_CHANGED=false
POSITION_LOGIC_CHANGED=false
RISK_APPETITE_CHANGED=false
MAX_POSITIONS_CHANGED=false
```

## 12) Guards (not SSOT)

Exact proof files:

`tests/ops/test_peak_trade_order_plan_typed_contract_count_domain_closure_v1.py`

Guards must keep:

- this spec and Master §5.3 name the typed-domain persist and
  `MAX_SIZE_NORMALIZATION_STATUS=BOUND`
- #6150 spec remains historically `MAX_SIZE_NORMALIZATION_STATUS=UNBOUND`
  and historically `ORDER_PLAN_QTY_UNIT_STATUS=UNBOUND` for that slice
- runtime field is `quantity`; docs alias `qty`; no Python field `qty`
- `ORDER_PLAN_QTY_UNIT=contracts`
- `ORDER_PLAN_QTY_DOMAIN=VENUE_CONTRACT_COUNT`
- `CONTRACT_SIZING_FORMULA=venue_contract_count = SUI_OPERATIVE_ORDER_SZ`
- `ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING=IDENTITY_AFTER_CONTRACT_SIZING`
- `FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true`
- `ONE_CONTRACT_EQUALS_ONE_SUI=false`
- `NORMALIZATION_REQUIRES_CTVAL=false`; `NORMALIZATION_REQUIRES_CTMULT=false`;
  `NORMALIZATION_REQUIRES_CTTYPE=false`
- `LOT_SIZE_QUANTIZATION_STATUS=NOT_REQUIRED`
- `MAX_SIZE_COMPARISON_DOMAIN=venue_contract_count`
- freshness policy UNBOUND; consumer unbound
- required metadata edges remain 8; bound 0; partial 2; unbound 6; conflicted 0
- earliest remaining unbound edge `MAX_SIZE`; earliest remaining MAX_SIZE gap
  `MAX_SIZE_FRESHNESS_POLICY`
- Kraken exclusion closed; BTC not resurrected
- extract_instrument_constraints required tuple remains `minSz, lotSz, tickSz, ctVal`
- `maxLmtSz` / `maxMktSz` / `maxAvailSize` remain absent from order_plan, exposure, and submit_transport source
- no venue GET/POST this slice; no new official-doc fetch
- #6143–#6150 remain closed as historical persists
- standing Live / Testnet / Canary authorization remain false

## 13) Out of scope this slice

```text
MAX_SIZE_CONSUMER_IMPLEMENTATION=NOT_THIS_SLICE
MAX_SIZE_FRESHNESS_POLICY=NOT_THIS_SLICE
MAX_AVAILABLE_IMPLEMENTATION=NOT_THIS_SLICE
PRICE_BAND_IMPLEMENTATION=NOT_THIS_SLICE
LEVERAGE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
ACCOUNT_MODE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
INSTRUMENT_STATE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
AUTHENTICATED_GET=NOT_THIS_SLICE
NETWORK_VENUE_GET=NOT_THIS_SLICE
NETWORK_POST=NOT_THIS_SLICE
NETWORK_DOCUMENTATION_FETCH=NOT_THIS_SLICE
CANARY_EXECUTE=NOT_THIS_SLICE
FLATTEN=NOT_THIS_SLICE
KRAKEN_RUNTIME_MUTATION=NOT_THIS_SLICE
CURRENT_NUMERIC_FREEZE=NOT_THIS_SLICE
FRESHNESS_POLICY_INVENTION=NOT_THIS_SLICE
GENERAL_NOTIONAL_TO_CONTRACT_COUNT_FORMULA=NOT_THIS_SLICE
RESTORATION_REOPEN=NOT_THIS_SLICE
MERGE=NOT_THIS_SLICE
CORE_RUNTIME_MUTATION=false
```

## 14) Existing guards reused (not duplicated)

| Invariant | Current guard |
|---|---|
| #6150 post-6149 MAX_SIZE normalization | `tests/ops/test_peak_trade_post_6149_max_size_normalization_adjudication_v1.py` |
| #6149 post-6148 MAX_SIZE unit | `tests/ops/test_peak_trade_post_6148_max_size_unit_adjudication_v1.py` |
| #6148 exact venue metadata GET | `tests/ops/test_peak_trade_exact_venue_metadata_get_current_sui_pretrade_max_size_v1.py` |
| #6147 metadata-binding PARTIAL persist | `tests/ops/test_peak_trade_post_restoration_venue_pretrade_metadata_binding_alignment_adjudication_v1.py` |
| #6146 venue-pretrade limit gates | `tests/ops/test_peak_trade_post_restoration_venue_pretrade_limit_gates_adjudication_v1.py` |
| Preservation / compatibility contract | `tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py` |
| Live safety gates | `tests/ops/test_peak_trade_post_restoration_live_safety_gates_adjudication_v1.py` |
| Simulated execution pipeline | `tests/ops/test_peak_trade_post_restoration_simulated_execution_pipeline_adjudication_v1.py` |
| Accounting / portfolio alignment | `tests/ops/test_peak_trade_post_restoration_accounting_portfolio_alignment_adjudication_v1.py` |
| Canary submit transport / order plan | `tests/ops/test_section_11_13_5_canary_submit_transport_v1.py` |
| Cap 11.9 fixture unreachable | `tests/ops/test_capability_11_9_live_canary_order_execution_v1.py` |

## 15) Negative contract

```text
RUNTIME_CORE_MUTATION=false
TRADING_LOGIC_MUTATION=false
HTTP_CLIENT_MUTATED=false
KRAKEN_RUNTIME_MUTATED=false
MAX_SIZE_IMPLEMENTED=false
MAX_AVAILABLE_IMPLEMENTED=false
PRICE_BAND_IMPLEMENTED=false
LEVERAGE_GATE_IMPLEMENTED=false
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
LIVE_READINESS_MUTATION=false
ORDER_SUBMIT_PERFORMED=false
FLATTEN_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORITY_CHANGED=false
NETWORK_VENUE_GET_PERFORMED=false
NETWORK_POST_PERFORMED=false
NETWORK_DOCUMENTATION_READ_PERFORMED=false
FORENSIC_REFERENCE_AUTHORITY=NONE
MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY
SECOND_VENUE_PRETRADE_OWNER_CREATED=false
BTC_METADATA_REUSED=false
SUI_OTHER_INSTRUMENT_METADATA_REUSED=false
FAMILY_SCOPED_METADATA_REUSED=false
VENUE_GLOBAL_METADATA_REUSED=false
KRAKEN_METADATA_REUSED=false
RECOVERY_MUTATION=false
MERGE_PERFORMED=false
SEE_ALSO_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION=docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1.md
SEE_ALSO_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING=docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1.md
```
