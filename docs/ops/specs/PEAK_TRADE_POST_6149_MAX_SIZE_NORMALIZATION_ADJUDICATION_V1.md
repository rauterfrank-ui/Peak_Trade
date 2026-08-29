# Peak_Trade — Post-6149 MAX_SIZE Normalization Adjudication v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Persist the forensic quantity-domain mapping adjudication from section_11_13_5.order_plan_v1.qty to OKX FUTURES Place Order sz after closed #6149 MAX_SIZE unit persist. Not a second SSOT. Not restoration reopen. Not core runtime mutation. Not live or execution authority. Not a freshness-policy bind. Not a consumer bind. Not venue-pretrade completeness. Not a silent identity bind.
docs_token: DOCS_TOKEN_PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_MAX_SIZE_UNIT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md
PRIOR_EXACT_VENUE_METADATA_GET=docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md
PRIOR_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
PRIOR_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md
EVIDENCE_PACK=evidence/ops/exact_venue_metadata_get_current_sui_pretrade_max_size_v1/20260829T182239Z
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
RUNTIME_ALIGNMENT_REQUIRED=unproven
RUNTIME_MUTATION_JUSTIFIED=false
RUNTIME_MUTATION_PERFORMED=false
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
metadata-binding alignment #6147, exact venue metadata GET #6148, or
MAX_SIZE unit adjudication #6149. It adjudicates whether
`order_plan_v1.qty` already represents OKX contract count, or whether an
explicit transformation is proven, before comparison with `maxLmtSz` /
`maxMktSz`. It does not invent a freshness policy, implement a runtime
consumer, or mutate runtime.

A numeric identity copy of `quantity` into Place Order `sz` is
implementation evidence. It is **not** a semantic proof of domain
identity.

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
HISTORICAL_6149_MAX_SIZE_UNIT=contracts
HISTORICAL_6149_MAX_SIZE_NORMALIZATION_STATUS=UNBOUND
HISTORICAL_6149_NETWORK_VENUE_GET_PERFORMED=false
```

#6149 remains the closed MAX_SIZE unit persist. That slice left
`MAX_SIZE_NORMALIZATION_STATUS=UNBOUND` because Place Order `sz` was
only "Quantity to buy or sell" and because a minSz-to-quantity chain
was classified as `INTERPRETATION`, not a quantity-domain proof. This
slice consumes the separate Owner-GO for normalization adjudication
only. It does not rewrite the #6149 unit bind.

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
HISTORICAL_RAW_EVIDENCE=Z2AR_GET_1_AND_Z2BD_Z2BF_BODY_PARITY_AND_Z2BL_CTVAL_OPERAND_AND_Z2BN_PV1
ADJUDICATED_CONCLUSION=THIS_DOCUMENT
HISTORICAL_INTERMEDIATE=Z2S_API_SZ_SEMANTICS_NUMBER_OF_CONTRACTS_FOR_FUTURES_SWAP_NOT_SUI_ORDER_PLAN_QTY_BIND
NAVIGATION_ONLY=MAP_OF_TRUTH
INTERPRETATION=PEAK_TRADE_RUNTIME_INTEGER_CONTRACT_REQUIRED_AND_EXPOSURE_DOCSTRING_AND_MINSZ_TO_QUANTITY_POLICY_COPY
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=MAX_SIZE_FRESHNESS_POLICY_AND_CONSUMER_AND_ORDER_PLAN_QTY_UNIT_AND_PLACE_ORDER_SZ_REQUEST_PARAM_UNIT
CONFLICTED=NONE
```

Raw numbers remain #6148 current-window evidence. Official Place Order
`sz` request-parameter underspecification remains the #6149 persist.
Runtime names, Python types, field neighbourhood, minSz/lotSz numeric
coincidence, Kraken, BTC, and plausibility are not quantity-domain
authority. A later Owner-ratified SUI operative `sz=1` contract is a
**separate object** from the runtime `order_plan_v1.quantity` field.

## 4) Current instrument and reused raw evidence

```text
OWNER_GO_THIS_SLICE=PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1
BOUND_ORIGIN_MAIN_SHA=01d3a8e51e60783370381eadce72bfb50f25fb43
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
Z2AR_WINDOW_REUSED_AS_CURRENT=false
Z2BD_WINDOW_REUSED=false
Z2BF_WINDOW_REUSED=false
```

Source: `CURRENT_RAW_EVIDENCE` pack reused from #6148 / #6149. This
slice does **not** re-observe the instruments row.

## 5) Exact questions and bound answers

### 5.1 What `order_plan_v1.qty` means

The runtime dataclass field is `CanaryOrderPlanV1.quantity`, type
`str`. There is no Python field named `qty`. Docs and Master language
`order_plan_v1.qty` is a documentation alias for that `quantity`
string.

Producer: `build_canary_exposure_binding_v1` sets `quantity` to
`instrument_min_sz` unless an explicit `quantity` argument is supplied,
then fail-closed requires `quantity == min_sz` via
`MINIMUM_EXPOSURE_REQUIRES_MIN_SZ_QUANTITY`. Consumer of the plan
field: `build_venue_native_order_body_v1(..., quantity=exposure.quantity)`
and `submit_transport_v1` POSTs `plan.venue_native_payload`.

```text
ORDER_PLAN_QTY_SEMANTIC_STATUS=BOUND
ORDER_PLAN_QTY_SEMANTIC=runtime_field_quantity_docs_alias_qty_canary_minimum_exposure_order_size_string_copied_from_instrument_min_sz
ORDER_PLAN_V1_PYTHON_FIELD_NAME=quantity
ORDER_PLAN_V1_HAS_FIELD_NAMED_QTY=false
ORDER_PLAN_V1_QTY_IS_DOCS_ALIAS=true
ORDER_PLAN_QTY_TYPE=str
ORDER_PLAN_QTY_PRODUCER=exposure_v1.build_canary_exposure_binding_v1
ORDER_PLAN_QTY_CONSUMER=build_venue_native_order_body_v1@submit_transport_v1
MINIMUM_EXPOSURE_REQUIRES_MIN_SZ_QUANTITY=true
```

This binds the **operational** meaning of the runtime field. It does
**not** bind a venue unit.

### 5.2 Internal unit of `order_plan_v1.qty`

```text
ORDER_PLAN_QTY_UNIT_STATUS=UNBOUND
ORDER_PLAN_QTY_UNIT=UNBOUND
PEAK_TRADE_ORDER_PLAN_QTY_DOMAIN_EQUALS_CONTRACTS=UNPROVEN
INTEGER_CONTRACT_REQUIRED_IS_NOT_OFFICIAL_UNIT_PROOF=true
EXPOSURE_DOCSTRING_IS_NOT_OFFICIAL_UNIT_PROOF=true
MINSZ_OFFICIAL_DERIVATIVES_UNIT_IS_NOT_ORDER_PLAN_QTY_UNIT_PROOF=true
FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true
```

Official minSz for derivatives is number of contracts (#6149). Runtime
copies minSz into `quantity`. That chain remains `INTERPRETATION`.
Canonical §11.13.5.Z2BE / §11.13.5.Z2BF **forbid** promoting `minSz` to
operative qty even when both numerics are `1`. Therefore the official
minSz unit cannot be transferred onto `order_plan_v1.quantity`.

### 5.3 Direct serialization to OKX `sz`

```text
RUNTIME_STRING_COPY_QUANTITY_TO_SZ=true
RUNTIME_STRING_COPY_CLASS=CURRENT_RAW_EVIDENCE_OF_IMPLEMENTATION
RUNTIME_STRING_COPY_IS_NOT_DOMAIN_IDENTITY_PROOF=true
RUNTIME_QTY_TO_SZ_MAPPING_IS_CANONICAL_AUTHORITY=false
SZ_SERIALIZATION_TRANSFORMS_QUANTITY=false
SZ_VALUE_EQUALS_PLAN_QUANTITY_STRING=true
```

`build_venue_native_order_body_v1` assigns `"sz": quantity` with no
Decimal conversion, no `ctVal`/`ctMult`/`ctType` factor, and no
lot-size rewrite. Tests observe `plan.venue_native_payload["sz"] ==
plan.quantity == "1"`. That is historical implementation, not canonical
domain identity.

### 5.4 Quantization / lot size

```text
LOT_SIZE_ROLE_STATUS=BOUND
LOT_SIZE_ROLE=venue_increment_constraint_official_derivatives_number_of_contracts_runtime_modulo_validation_not_qty_to_sz_transform
LOTSZ_OFFICIAL_DERIVATIVES_UNIT=number_of_contracts
LOTSZ_USED_AS_QTY_TO_SZ_TRANSFORM=false
LOTSZ_USED_AS_RUNTIME_MODULO_VALIDATION=true
ORDER_PLAN_QTY_QUANTIZED_BEFORE_TRANSPORT=false
QUANTIZE_LIMIT_PRICE_EXISTS=true
QUANTIZE_LIMIT_PRICE_IS_NOT_QTY_QUANTIZATION=true
INTEGER_CONTRACT_COUNT_MANDATORY_ON_VENUE=UNPROVEN
FRACTIONAL_CONTRACTS_POSSIBLE_IF_LOTSZ_LT_1=UNPROVEN_GLOBALLY
CURRENT_SUI_LOTSZ_RAW_VALUE=1
CURRENT_SUI_LOTSZ_1_IS_NOT_CONTRACT_DOMAIN_PROOF=true
```

`exposure_v1` rejects `qty % lotSz != 0`. That is validation. It does
not rewrite `quantity` before `sz`. `order_plan_v1` also requires
`minSz` and `lotSz` to be integral (`INTEGER_CONTRACT_REQUIRED`). That
Peak_Trade constraint is `INTERPRETATION`, not official proof that
Place Order `sz` must be an integer contract count. Observed
`lotSz=1` is not itself a contract-domain proof.

### 5.5 ctVal / ctMult / ctType

```text
NORMALIZATION_REQUIRES_CTVAL=false
NORMALIZATION_REQUIRES_CTMULT=false
NORMALIZATION_REQUIRES_CTTYPE=false
CTVAL_USED_IN_QTY_TO_SZ=false
CTMULT_READ_BY_EXTRACT_INSTRUMENT_CONSTRAINTS=false
CTTYPE_USED_IN_QTY_TO_SZ=false
CTVAL_ROLE_SEPARATED=true
CTVAL_EXPOSURE_NOTIONAL_FORMULA=qty * ctVal * reference_price
CTVAL_PV1_INTERNAL_FORM=sz * ctVal * markPx
CTVAL_IS_FACE_VALUE_OF_ONE_CONTRACT=true
CTVAL_IS_NOT_QTY_TO_SZ_FORMULA=true
CTVAL_1_AND_CTVALCCY_SUI_IS_NOT_ONE_CONTRACT_EQUALS_ONE_SUI=true
```

`derive_min_executable_notional_v1` computes `qty * ctVal * price`.
Z2BL binds `ctVal=1` `ctValCcy=SUI` as the PV-1 internal notional
operand only. Z2BN instantiates `sz * ctVal * markPx` as Peak_Trade
internal notional, not OKX position value. Those are exposure /
notional roles. They are **not** a qty→sz normalization formula.
`extract_instrument_constraints_v1` required tuple remains
`minSz, lotSz, tickSz, ctVal`. It does not read `ctMult` or `ctType`.

### 5.6 Historical `qty=1` versus one contract

```text
QTY_1_NUMERIC_OBSERVED_IN_CANARY_TESTS=true
QTY_1_OBSERVED_IS_NOT_ONE_CONTRACT_PROOF=true
SUI_OPERATIVE_ORDER_SZ=1
SUI_OPERATIVE_ORDER_SZ_UNIT=CONTRACTS_SZ
SUI_OPERATIVE_QTY_KIND=OWNER_POLICY_PLUS_CURRENT_VENUE_ADMISSIBILITY_ONLY
SUI_OPERATIVE_QTY_PROVEN=true
SUI_OPERATIVE_QTY_IS_EXCHANGE_SELECTED_QTY=false
SUI_OPERATIVE_QTY_DERIVED_FROM_MINSZ=false
SUI_OPERATIVE_ORDER_SZ_IS_NOT_ORDER_PLAN_QUANTITY_OBJECT_PROOF=true
QTY_LIMIT_1_IS_NOT_SUI_OPERATIVE_QTY=true
BTC_CANARY_QTY_IS_NOT_SUI_OPERATIVE_QTY=true
```

Canary tests observe the numeric string `"1"`. That is numeric
observation, not a unit proof. Canonical §11.13.5.Z2BE Owner-ratifies
SUI operative order `sz=1` **contract** as minimum-exposure **policy**.
§11.13.5.Z2BF proves that already-bound policy size satisfies then-current
`minSz` floor and `lotSz` increment. That object is
`SUI_OPERATIVE_ORDER_SZ`, unit `CONTRACTS_SZ`. It is **not** proven
identical to the runtime `order_plan_v1.quantity` field, because the
runtime field is copied from `minSz` and the canonical persist forbids
that upgrade.

### 5.7 SUI-XPERP one canonical qty unit = one OKX contract

```text
ONE_CANONICAL_ORDER_PLAN_QTY_UNIT_EQUALS_ONE_OKX_CONTRACT=UNPROVEN
SUI_OPERATIVE_ORDER_SZ_UNIT_EQUALS_CONTRACTS_SZ=true
SUI_OPERATIVE_ORDER_SZ_OBJECT_EQUALS_ORDER_PLAN_QUANTITY=UNPROVEN
Z2S_API_SZ_FUTURES_UNIT_IS_NOT_SUI_ORDER_PLAN_QTY_BIND=true
PLACE_ORDER_SZ_REQUEST_PARAM_STATES_CONTRACTS=false
NEIGHBOUR_FILLSZ_AND_PUBLIC_TRADES_SZ_CONTRACT_SENTENCES_DO_NOT_REWRITE_PLACE_ORDER_REQUEST_PARAM=true
```

Owner-ratified `SUI_OPERATIVE_ORDER_SZ_UNIT=CONTRACTS_SZ` is true for
that named policy object. Historical Z2S
`API_SZ_SEMANTICS=NUMBER_OF_CONTRACTS_FOR_FUTURES_SWAP` is the
position-value formula layer and remains not a SUI `order_plan_v1.qty`
bind (#6149). Official Place Order request parameter still does not
state contracts.

### 5.8 One contract = one SUI

```text
ONE_CONTRACT_EQUALS_ONE_SUI=false
NO_NORMALIZATION_CTVAL_1_TO_ONE_CONTRACT_EQUALS_ONE_SUI=true
PV1_ASSERTS_ONE_CONTRACT_EQUALS_ONE_SUI=false
FAIL_CLOSED_IF_ONE_CONTRACT_EQUALS_ONE_SUI_ASSERTED=true
```

No new authority reverses this. `ctVal=1` with `ctValCcy=SUI` is face
value of one contract in SUI denomination for the PV-1 internal
operand. It is **not** a proof that one contract equals one SUI token
as an order-quantity identity.

### 5.9 Official Place Order `sz` (reused, not re-fetched)

This slice does **not** fetch official documentation. It reuses the
#6149 persist of the same official EEA guide:

```text
OFFICIAL_PLACE_ORDER_SZ_DEFINITION=Quantity to buy or sell
PLACE_ORDER_SZ_REQUEST_PARAM_STATES_CONTRACTS=false
OFFICIAL_PLACE_ORDER_SZ_UNIT_FOR_FUTURES=UNPROVEN_ON_REQUEST_PARAM
VENUE_ORDER_SZ_SEMANTIC_STATUS=BOUND
VENUE_ORDER_SZ_SEMANTIC=official_place_order_request_parameter_quantity_to_buy_or_sell
VENUE_ORDER_SZ_UNIT_STATUS=UNBOUND
VENUE_ORDER_SZ_UNIT=UNBOUND
NETWORK_DOCUMENTATION_READ_PERFORMED=false
HISTORICAL_6149_NETWORK_DOCUMENTATION_READ_PERFORMED=true
```

Neighbour official sentences (order-channel `fillSz` / `accFillSz`,
public trades `sz`, some algo `sz` rows) state contract units for
`FUTURES`/`SWAP`/`OPTION`. Those sentences do **not** rewrite the Place
Order request parameter and do **not** bind `order_plan_v1.qty`.

## 6) Mapping adjudication

```text
ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING_STATUS=UNBOUND
ORDER_PLAN_QTY_TO_VENUE_SZ_MAPPING=UNBOUND
MAPPING_IDENTITY_REJECTED_AS_UNPROVEN=true
MAPPING_FORMULA_WITH_CTVAL_CTMULT_CTTYPE_PROVEN=false
TRANSFORMATION_REQUIRED_BEFORE_COMPARE_WITH_MAXLMTSZ=UNPROVEN
IDENTITY_MAPPING_REQUIRED_BEFORE_COMPARE_WITH_MAXLMTSZ=UNPROVEN
```

Permitted results A (IDENTITY because qty already represents OKX
contract count) and B (explicit formula) are both **unproven**. Result
D (`CONFLICTED`) is rejected: the runtime minSz-copy and the Owner
`SUI_OPERATIVE_ORDER_SZ` are **distinct objects**, not two authorities
disagreeing on one object. Result C (`UNBOUND`) is the adjudicated
conclusion.

Why IDENTITY is unproven:

1. Official Place Order `sz` request parameter does not state
   contracts.
2. Runtime `quantity := minSz` may not be promoted to operative qty
   (`FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true`).
3. Owner-ratified `SUI_OPERATIVE_ORDER_SZ_UNIT=CONTRACTS_SZ` is a
   different object from `order_plan_v1.quantity`.
4. Numeric coincidence `quantity="1"` and `SUI_OPERATIVE_ORDER_SZ=1`
   is not object identity.
5. Z2S API `sz` contract semantics are not a SUI order-plan qty bind.
6. `INTEGER_CONTRACT_REQUIRED` and the exposure docstring are
   `INTERPRETATION`.

Why a ctVal/ctMult/ctType formula is unproven:

- No runtime qty→sz path multiplies or divides by those fields.
- Those fields serve notional / PV-1 internal notional, not wire size.

```text
MAX_SIZE_COMPARISON_DOMAIN_STATUS=UNBOUND
MAX_SIZE_COMPARISON_DOMAIN=UNBOUND
MAX_SIZE_NORMALIZATION_STATUS=UNBOUND
```

Comparison-domain bind is authorized only after the mapping question
is answered. Mapping is UNBOUND. Therefore comparison domain remains
UNBOUND. `maxLmtSz` / `maxMktSz` remain venue contract counts (#6149).
That unit bind does **not** by itself prove that `order_plan_v1.qty`
is already in that domain.

## 7) Object inventory (must not be conflated)

| Object | Epistemic class | Unit status |
|---|---|---|
| `CanaryOrderPlanV1.quantity` | CURRENT_RAW_EVIDENCE of runtime | UNBOUND |
| docs alias `order_plan_v1.qty` | NAVIGATION_ONLY name | same as quantity |
| `instrument_min_sz` / venue `minSz` | OFFICIAL_DEFINITIONAL_AUTHORITY for minSz itself | number of contracts for derivatives |
| `SUI_OPERATIVE_ORDER_SZ` | CANONICAL_AUTHORITY Z2BE/Z2BF | CONTRACTS_SZ |
| Place Order request `sz` | OFFICIAL_DEFINITIONAL_AUTHORITY | UNPROVEN on request param |
| `maxLmtSz` / `maxMktSz` | CANONICAL_AUTHORITY #6149 | contracts |
| PV-1 envelope `sz` operand | CANONICAL_AUTHORITY Z2BN | reused SUI_OPERATIVE_ORDER_SZ contracts |
| exposure notional `qty * ctVal * px` | INTERPRETATION / internal algebra | notional, not wire size |

## 8) Consumer / freshness / runtime firewall

```text
MAX_SIZE_CONSUMER_BOUND=false
EXISTING_EXTRACTOR_REQUIRED_TUPLE=minSz,lotSz,tickSz,ctVal
EXISTING_EXTRACTOR_DOES_NOT_READ_MAXLMTSZ=true
RUNTIME_ALIGNMENT_REQUIRED=unproven
RUNTIME_MUTATION_JUSTIFIED=false
RUNTIME_MUTATION_PERFORMED=false
CHANGED_RUNTIME_FILES=NONE
MAX_SIZE_FRESHNESS_STATUS=WINDOW_OBSERVED_NOT_POLICY_BOUND
MAX_SIZE_FRESHNESS_POLICY=UNBOUND
CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false
UPCCHG_IS_NOT_FRESHNESS_POLICY=true
```

The recorded split between runtime minSz-copy and Owner
`SUI_OPERATIVE_ORDER_SZ` is **not** a mutation authorization. Freshness
policy remains the #6148 window observation without a TTL. `upcChg` /
`newValue` / `effTime` remain context only.

## 9) Required edge reassessment

Status vocabulary is exactly `PROVEN`, `PARTIALLY_BOUND`, `UNBOUND`,
`CONFLICTED`, `NOT_REQUIRED`.

| EDGE_ID | CURRENT_STATUS | Reason after this normalization adjudication |
|---|---|---|
| MAX_SIZE | PARTIALLY_BOUND | Current raw `maxLmtSz=100000000` observed; unit `contracts`; quantity-domain mapping to `order_plan_v1.qty` remains UNBOUND; freshness policy and consumer remain unbound |
| MAX_MKT_SZ | NOT_REQUIRED | LIMIT-only entry; peer unit `contracts`; still not a substitute for `maxLmtSz` |
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
EARLIEST_REMAINING_MAX_SIZE_GAP=MAX_SIZE_NORMALIZATION
REMAINING_MAX_SIZE_SUBDEPENDENCIES=MAX_SIZE_NORMALIZATION,MAX_SIZE_FRESHNESS_POLICY,MAX_SIZE_CONSUMER
BEGINNING_AT=MAX_SIZE
EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_NORMALIZATION
```

`MAX_SIZE` remains earliest because `PARTIALLY_BOUND` is not
`PROVEN`. Unit remains bound. This slice **closes the currently
authorized investigation of existing repo/forensic/official-reuse
evidence** and persists `UNBOUND` as the mapping result. Freshness
policy and consumer remain independently unbound and are **not**
authorized here. This slice does **not** jump to MAX_AVAILABLE or any
later required edge. A later Owner-GO would need new Place Order
request-parameter unit authority, or a typed bind of
`order_plan_v1.quantity` as contract count that is not the forbidden
minSz upgrade, before IDENTITY or a formula can be BOUND.

## 10) Adjudication result

```text
ADJUDICATION_RESULT=PARTIAL
SOURCE_ADJUDICATION_RESULT=MAX_SIZE_NORMALIZATION_UNBOUND_DOMAIN_IDENTITY_UNPROVEN_IDENTITY_COPY_IS_IMPLEMENTATION_NOT_AUTHORITY
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
NEXT_DISTINCT_SURFACE=MAX_SIZE_NORMALIZATION
NEXT_DISTINCT_SURFACE_AUTHORIZED=false
```

Not `COMPLETE`. Not `BLOCKED_BY_MISSING_SOURCE`. Not
`BLOCKED_BY_CONFLICT`. A cleanly proven UNBOUND is the successful
outcome of this Owner-GO.

## 11) Negative / non-equivalence contracts

```text
NORMALIZATION_ADJUDICATION_IS_NOT_IDENTITY_BIND=true
NORMALIZATION_ADJUDICATION_IS_NOT_FORMULA_BIND=true
NORMALIZATION_ADJUDICATION_IS_NOT_FRESHNESS_POLICY=true
NORMALIZATION_ADJUDICATION_IS_NOT_CONSUMER_BIND=true
RUNTIME_STRING_COPY_IS_NOT_DOMAIN_IDENTITY_PROOF=true
MINSZ_UNIT_IS_NOT_ORDER_PLAN_QTY_UNIT_PROOF=true
LOTSZ_UNIT_IS_NOT_ORDER_PLAN_QTY_UNIT_PROOF=true
LOTSZ_1_IS_NOT_CONTRACT_DOMAIN_PROOF=true
PLACE_ORDER_SZ_UNDERSPECIFIED_REQUEST_PARAM_IS_NOT_ORDER_PLAN_QTY_DOMAIN_PROOF=true
NEIGHBOUR_SZ_CONTRACT_SENTENCES_ARE_NOT_PLACE_ORDER_REQUEST_PARAM_PROOF=true
INTEGER_CONTRACT_REQUIRED_IS_NOT_OFFICIAL_UNIT_PROOF=true
EXPOSURE_DOCSTRING_IS_NOT_OFFICIAL_UNIT_PROOF=true
Z2S_API_SZ_FUTURES_UNIT_IS_NOT_SUI_ORDER_PLAN_QTY_BIND=true
SUI_OPERATIVE_ORDER_SZ_IS_NOT_ORDER_PLAN_QUANTITY_OBJECT_PROOF=true
FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true
ONE_CONTRACT_EQUALS_ONE_SUI=false
CTVAL_IS_NOT_QTY_TO_SZ_FORMULA=true
BTC_CTVAL_ALGEBRA_IS_NOT_SUI_QTY_DOMAIN=true
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
MAXLMTSZ_IS_NOT_MAXMKTSZ=true
MAXLMTSZ_IS_NOT_POSITION_TIER_MAXSZ=true
MAXLMTSZ_IS_NOT_MAXAVAILSIZE=true
EXPOSURE_MAX_NOTIONAL_IS_NOT_VENUE_MAX_SIZE=true
UPCCHG_IS_NOT_FRESHNESS_POLICY=true
RUNTIME_ALIGNMENT_REQUIRED_IS_NOT_MUTATION_AUTHORIZATION=true
HISTORICAL_6149_MAX_SIZE_NORMALIZATION_UNBOUND_IS_NOT_THIS_SLICE=true
THIS_SLICE_DOES_NOT_REWRITE_6149_UNIT_BIND=true
```

## 12) Guards (not SSOT)

Exact proof file:

`tests/ops/test_peak_trade_post_6149_max_size_normalization_adjudication_v1.py`

Guards must keep:

- this spec and Master §5.3 name the normalization persist and
  `MAX_SIZE_NORMALIZATION_STATUS=UNBOUND`
- #6149 spec remains historically `MAX_SIZE_UNIT=contracts` and
  historically `MAX_SIZE_NORMALIZATION_STATUS=UNBOUND` for that unit slice
- runtime field is `quantity`; docs alias `qty`; no Python field `qty`
- `RUNTIME_STRING_COPY_QUANTITY_TO_SZ=true` and
  `RUNTIME_STRING_COPY_IS_NOT_DOMAIN_IDENTITY_PROOF=true`
- `ORDER_PLAN_QTY_UNIT_STATUS=UNBOUND`
- `VENUE_ORDER_SZ_SEMANTIC=official_place_order_request_parameter_quantity_to_buy_or_sell`
- `PLACE_ORDER_SZ_REQUEST_PARAM_STATES_CONTRACTS=false`
- `LOT_SIZE_ROLE_STATUS=BOUND` as modulo validation, not transform
- `NORMALIZATION_REQUIRES_CTVAL=false`; `NORMALIZATION_REQUIRES_CTMULT=false`;
  `NORMALIZATION_REQUIRES_CTTYPE=false`
- `ONE_CONTRACT_EQUALS_ONE_SUI=false`
- `FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1=true`
- `MAX_SIZE_COMPARISON_DOMAIN_STATUS=UNBOUND`
- freshness policy UNBOUND; consumer unbound
- required metadata edges remain 8; bound 0; partial 2; unbound 6; conflicted 0
- earliest remaining unbound edge `MAX_SIZE`; earliest remaining MAX_SIZE gap
  `MAX_SIZE_NORMALIZATION`
- Kraken exclusion closed; BTC not resurrected
- extract_instrument_constraints required tuple remains `minSz, lotSz, tickSz, ctVal`
- `maxLmtSz` / `maxMktSz` / `maxAvailSize` remain absent from order_plan, exposure, and submit_transport
- no venue GET/POST this slice; no new official-doc fetch
- #6143–#6149 remain closed as historical persists
- runtime files unchanged

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
ORDER_PLAN_RUNTIME_MUTATION=NOT_THIS_SLICE
EXPOSURE_RUNTIME_MUTATION=NOT_THIS_SLICE
SUBMIT_TRANSPORT_RUNTIME_MUTATION=NOT_THIS_SLICE
KRAKEN_RUNTIME_MUTATION=NOT_THIS_SLICE
CURRENT_NUMERIC_FREEZE=NOT_THIS_SLICE
FRESHNESS_POLICY_INVENTION=NOT_THIS_SLICE
IDENTITY_BIND_FROM_PLAUSIBILITY=NOT_THIS_SLICE
RESTORATION_REOPEN=NOT_THIS_SLICE
MERGE=NOT_THIS_SLICE
CORE_RUNTIME_MUTATION=false
```

## 14) Existing guards reused (not duplicated)

| Invariant | Current guard |
|---|---|
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
ORDER_PLAN_MUTATED=false
EXPOSURE_MUTATED=false
SUBMIT_TRANSPORT_MUTATED=false
HTTP_CLIENT_MUTATED=false
KRAKEN_RUNTIME_MUTATED=false
MAX_SIZE_IMPLEMENTED=false
MAX_AVAILABLE_IMPLEMENTED=false
PRICE_BAND_IMPLEMENTED=false
LEVERAGE_GATE_IMPLEMENTED=false
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
CHANGED_RUNTIME_FILES_EXPECTED=NONE
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
SEE_ALSO_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE=docs/ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md
SEE_ALSO_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION=docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1.md
```
