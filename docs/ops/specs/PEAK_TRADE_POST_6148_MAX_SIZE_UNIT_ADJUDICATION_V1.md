# Peak_Trade — Post-6148 MAX_SIZE Unit Adjudication v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Persist the forensic unit adjudication of OKX EEA public-instruments maxLmtSz and maxMktSz for current SUI-USD_UM_XPERP-310404 after closed #6148 current-window GET persist. Not a second SSOT. Not restoration reopen. Not core runtime mutation. Not live or execution authority. Not a freshness-policy bind. Not a normalization bind. Not a consumer bind. Not venue-pretrade completeness.
docs_token: DOCS_TOKEN_PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
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
RUNTIME_ALIGNMENT_REQUIRED=false
RUNTIME_MUTATION_JUSTIFIED=false
NETWORK_GET_AUTHORIZED=false
NETWORK_GET_PERFORMED=false
NETWORK_VENUE_GET_PERFORMED=false
NETWORK_POST_AUTHORIZED=false
NETWORK_POST_PERFORMED=false
NETWORK_DOCUMENTATION_READ_PERFORMED=true
AUTH_REQUIRED=false
AUTH_HEADER_SENT=false
```

This document is subordinate to the Master Runbook and to the post-restoration
preservation contract. It does not replace Master §5.3, Appendix A, C4, Replay
Safety, Cap 7.2, live-safety #6145, simulated-execution #6144,
accounting/portfolio #6143, venue-pretrade limit-gates #6146,
metadata-binding alignment #6147, or exact venue metadata GET #6148.
It binds MAX_SIZE unit from official OKX EEA API documentation. It does not
re-observe the raw numeric, invent a freshness policy, bind normalization to
`order_plan_v1.qty`, or implement a runtime consumer.

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
HISTORICAL_6148_MAX_SIZE_UNIT=UNBOUND
HISTORICAL_6148_NETWORK_GET_PERFORMED=true
```

#6148 remains the closed current-window raw GET persist. That slice left
`MAX_SIZE_UNIT=UNBOUND` because the instruments response does not itself
state a unit. This slice consumes the separate Owner-GO for unit
adjudication only. It does not rewrite the #6148 GET observation.

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
OFFICIAL_DEFINITIONAL_AUTHORITY=MY_OKX_DOCS_V5_EN_EEA_PRODUCTION_API_GUIDE
CANONICAL_AUTHORITY=MASTER_RUNBOOK_PLUS_THIS_SUBORDINATE_PERSIST
HISTORICAL_RAW_EVIDENCE=Z2AR_GET_1_AND_Z2BD_Z2BF_BODY_PARITY
ADJUDICATED_CONCLUSION=THIS_DOCUMENT
HISTORICAL_INTERMEDIATE=NOT_USED_AS_UNIT_AUTHORITY
NAVIGATION_ONLY=MAP_OF_TRUTH
INTERPRETATION=PEAK_TRADE_RUNTIME_INTEGER_CONTRACT_REQUIRED_AND_DOCSTRINGS
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=MAX_SIZE_NORMALIZATION_AND_FRESHNESS_POLICY_AND_CONSUMER
CONFLICTED=NONE
```

Raw numbers remain #6148 current-window evidence. Official documentation
binds unit semantics. Runtime names, Python types, field neighbourhood,
minSz/lotSz alone, Kraken, BTC, and plausibility are not unit authority.

## 4) Current raw evidence reused (not re-observed)

```text
OWNER_GO_THIS_SLICE=PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1
BOUND_ORIGIN_MAIN_SHA=edcf0ff63446c5a456aa769c2e05dd53d9ccc9b4
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
CURRENT_STATE_RAW_VALUE=live
MAXAVAILSIZE_ON_INSTRUMENTS_ROW=MISSING
NETWORK_VENUE_GET_PERFORMED=false
Z2AR_WINDOW_REUSED_AS_CURRENT=false
Z2BD_WINDOW_REUSED=false
Z2BF_WINDOW_REUSED=false
```

Source: `CURRENT_RAW_EVIDENCE` pack
`evidence&#47;ops&#47;exact_venue_metadata_get_current_sui_pretrade_max_size_v1&#47;20260829T182239Z`.
Unauthenticated public GET to `eea.okx.com` using
`public_instruments_query_path_v1`. HTTP 200, OKX code 0, exactly one
target row. Official documentation does **not** replace this window.

## 5) Official definitional authority

Preferred surface is the official OKX API guide that names the EEA
production REST URL.

```text
OFFICIAL_DOC_SURFACE=https:&#47;&#47;my.okx.com&#47;docs-v5&#47;en&#47;
OFFICIAL_DOC_ACCESS_DATE=2026-08-29
OFFICIAL_DOC_CLASS=OFFICIAL_DEFINITIONAL_AUTHORITY
THIRD_PARTY_BLOGS_USED_AS_AUTHORITY=false
STACKOVERFLOW_USED_AS_AUTHORITY=false
REDDIT_USED_AS_AUTHORITY=false
LLM_SUMMARY_USED_AS_AUTHORITY=false
WWW_OKX_AC_USED_AS_AUTHORITY=false
WWW_OKX_COM_DOCS_V5_FETCH_STATUS=HTTP_500_NOT_USED
```

### 5.1 EEA production REST bind on the same surface

Same document, section `Production Trading Services`:

```text
OFFICIAL_PRODUCTION_TRADING_REST_URL=https:&#47;&#47;eea.okx.com
OFFICIAL_PRODUCTION_TRADING_PUBLIC_WS=wss:&#47;&#47;wseea.okx.com:8443&#47;ws&#47;v5&#47;public
OFFICIAL_DEMO_TRADING_REST_URL=https:&#47;&#47;eea.okx.com
GLOBAL_OPENAPI_OKX_COM_NAMED_AS_THIS_SURFACE_PRODUCTION_REST=false
GLOBAL_DOC_SEMANTICS_APPLICABLE_TO_OKX_EEA=true
EEA_DOC_SURFACE_NAMES_EEA_PRODUCTION_REST_AND_FIELD_DEFS=true
```

This is not an inference that global docs "probably apply" to EEA. The
consulted official surface itself lists `https:&#47;&#47;eea.okx.com` as
**the** Production Trading REST URL and, on the same guide, defines
`maxLmtSz` / `maxMktSz`. Peak_Trade current venue host is `eea.okx.com`.

A distinct global guide snapshot (`www.okx.ac&#47;docs-v5&#47;en&#47;`) names
`https:&#47;&#47;openapi.okx.com` as Production REST. That global host
difference is recorded. It is **not** used as unit authority. The
`maxLmtSz` / `maxMktSz` English sentences observed on that global snapshot
were text-identical to the EEA surface; that identity is corroboration
only and does not carry the conclusion.

### 5.2 Public Get instruments field table

Same official surface, `Public Data` → `REST API` → `Get instruments`.
HTTP `GET &#47;api&#47;v5&#47;public&#47;instruments`. Unauthenticated.
This is the same endpoint class as the #6148 GET.

Exact official English text:

```text
MAXLMTSZ_OFFICIAL_TYPE=String
MAXLMTSZ_OFFICIAL_DEFINITION=The maximum order quantity of a single limit order.If it is a derivatives contract, the value is the number of contracts.If it is SPOT/MARGIN, the value is the quantity in base currency.
MAXMKTSZ_OFFICIAL_TYPE=String
MAXMKTSZ_OFFICIAL_DEFINITION=The maximum order quantity of a single market order.If it is a derivatives contract, the value is the number of contracts.If it is SPOT/MARGIN, the value is the quantity in USDT.
MINSZ_OFFICIAL_DEFINITION=Minimum order size.If it is a derivatives contract, the value is the number of contracts.If it is SPOT/MARGIN, the value is the quantity in base currency.
LOTSZ_OFFICIAL_DEFINITION=Lot size.If it is a derivatives contract, the value is the number of contracts.If it is SPOT/MARGIN, the value is the quantity in base currency.
```

minSz/lotSz official unit is recorded for separation only. It is **not**
the proof of maxLmtSz/maxMktSz. Each field has its own official sentence.

The authenticated `GET &#47;api&#47;v5&#47;account&#47;instruments` table on
the same guide repeats the same `maxLmtSz` / `maxMktSz` sentences. That
account endpoint was **not** called. The repeated text is same-guide
corroboration, not a second GET.

### 5.3 X-Perp / FUTURES bridge

Official `ruleType` on the same Get-instruments table:

```text
RULETYPE_XPERP_OFFICIAL_DEFINITION=xperp: perpetual-style futures, only applicable to certain FUTURES contracts. A pre-market X-Perp changes from pre_market to xperp after it converts to a normal X-Perp
INSTTYPE_FUTURES_REQUEST_ENUM_LABEL=Expiry Futures
```

Independent `CURRENT_RAW_EVIDENCE` for the target row:

```text
RAW_INSTTYPE=FUTURES
RAW_RULETYPE=xperp
```

Adjudicated bridge, not a product-class transfer from SWAP or SPOT:

```text
TARGET_IS_FUTURES=true
XPERP_IS_OFFICIALLY_A_FUTURES_RULETYPE=true
TARGET_IS_XPERP_FUTURES=true
TARGET_IS_SPOT=false
TARGET_IS_MARGIN=false
TARGET_IS_SWAP_INSTTYPE=false
DERIVATIVES_BRANCH_OF_MAXLMTSZ_DEFINITION_APPLIES=true
```

The official maxLmtSz/maxMktSz sentences split `derivatives contract`
versus `SPOT`/`MARGIN`. The target is `FUTURES` with `ruleType=xperp`.
`FUTURES` is not `SPOT`/`MARGIN`. Official `ctVal` is "Only applicable to
`FUTURES`/`SWAP`/`OPTION`". This slice does **not** transfer SWAP-only
semantics. It treats the target as a FUTURES derivatives contract under
the official xperp rule type.

### 5.4 Place-order `sz` (normalization neighbour, not unit proof)

Official Place Order request parameter on the same guide:

```text
PLACE_ORDER_SZ_OFFICIAL_DEFINITION=Quantity to buy or sell
PLACE_ORDER_SZ_REQUEST_PARAM_STATES_CONTRACTS=false
```

Separate official sentences on the same guide do state contract units for
other `sz` surfaces:

- order-channel `fillSz` / `accFillSz`: unit is contract for
  `FUTURES`/`SWAP`/`OPTION`
- public trades `sz`: for `FUTURES`/`SWAP`/`OPTION`, the unit is contract
- some algo `sz` rows: `FUTURES`/`SWAP`/`OPTION`: in the unit of contract

Those neighbour sentences do **not** rewrite the Place Order request
parameter, and they do **not** by themselves bind Peak_Trade
`order_plan_v1.qty`.

### 5.5 ctVal / ctMult / ctType

Public Get-instruments `ctVal` on the same guide includes the longer
sentence: face value of one contract; denomination depends on `ctType`;
linear notional `sz × ctVal × markPx`. Account Get-instruments uses the
shorter label "Contract value". Both are official. They answer exposure /
notional conversion, not the unit of maxLmtSz.

```text
UNIT_REQUIRES_CTVAL=false
UNIT_REQUIRES_CTMULT=false
UNIT_REQUIRES_CTTYPE=false
CTVAL_IS_FACE_VALUE_OF_ONE_CONTRACT=true
CTVAL_REQUIRED_TO_IDENTIFY_MAXLMTSZ_UNIT=false
CTVAL_MAY_BE_REQUIRED_TO_CONVERT_CONTRACT_COUNT_TO_NOTIONAL_OR_BASE=true
NOTIONAL_CONVERSION_IS_NOT_THIS_SLICE=true
```

### 5.6 upcChg / mutability without freshness policy

Official `upcChg` on the same Get-instruments table:

```text
UPCCHG_OFFICIAL_DEFINITION=Upcoming changes. It is [] when there is no upcoming change.
UPCCHG_PARAM_OFFICIAL=The parameter name to be updated. tickSz. minSz: For FUTURES/SWAP, lotSz will be modified synchronously. maxMktSz
UPCCHG_NEWVALUE_OFFICIAL=The parameter value that will replace the current one.
UPCCHG_EFFTIME_OFFICIAL=Effective time. Unix timestamp format in milliseconds
UPCCHG_NAMED_PARAMS_INCLUDE_MAXMKTSZ=true
UPCCHG_NAMED_PARAMS_INCLUDE_MAXLMTSZ=UNPROVEN
METADATA_CAN_CHANGE=true
EFFECTIVE_TIME_MECHANISM_EXISTS_FOR_NAMED_UPCCHG_PARAMS=true
MAX_SIZE_FRESHNESS_STATUS=WINDOW_OBSERVED_NOT_POLICY_BOUND
MAX_SIZE_FRESHNESS_POLICY=UNBOUND
```

`upcChg` proves that named instrument parameters, including `maxMktSz`,
can be scheduled to a future `newValue` at `effTime`. It does **not**
prove that `maxLmtSz` is in that named param list. It does **not** create
a Peak_Trade TTL, startup-only, per-session, or per-order refresh rule.

### 5.7 maxAvailSize separation

```text
MAXAVAILSIZE_NOT_LISTED_ON_OFFICIAL_PUBLIC_INSTRUMENTS_RESPONSE_TABLE=true
MAXAVAILSIZE_MISSING_ON_CURRENT_INSTRUMENTS_ROW=true
OFFICIAL_MAX_AVAIL_SURFACE=GET &#47;api&#47;v5&#47;account&#47;max-avail-size
OFFICIAL_MAX_AVAIL_RESPONSE_FIELDS=availBuy,availSell
OFFICIAL_MAX_AVAIL_REQUIRES_AUTHENTICATION=true
MAXLMTSZ_IS_NOT_MAXAVAILSIZE=true
MAXMKTSZ_IS_NOT_MAXAVAILSIZE=true
ACCOUNT_MAX_AVAIL_GET_PERFORMED=false
```

Absence of `maxAvailSize` on the public instruments row is not repaired
by interpretation. No account GET is authorized.

## 6) Unit adjudication

### 6.1 maxLmtSz

```text
MAXLMTSZ_UNIT_STATUS=BOUND
MAXLMTSZ_UNIT=contracts
MAXLMTSZ_UNIT_OFFICIAL_PHRASE=number_of_contracts
MAXLMTSZ_ROLE=MAXIMUM_ORDER_QUANTITY_OF_A_SINGLE_LIMIT_ORDER
MAXLMTSZ_PRODUCT_CLASS_DEPENDENT=true
MAXLMTSZ_ORDER_TYPE_DEPENDENT=true
MAXLMTSZ_INSTRUMENT_TYPE_DEPENDENT=true
MAXLMTSZ_SPOT_MARGIN_UNIT=base_currency
MAXLMTSZ_DERIVATIVES_UNIT=contracts
MAXLMTSZ_NOT_CURRENCY=true
MAXLMTSZ_NOT_BASE_ASSET=true
MAXLMTSZ_NOT_QUOTE_ASSET=true
MAXLMTSZ_NOT_NOTIONAL=true
MAXLMTSZ_NOT_NUMBER_OF_ORDERS=true
MAXLMTSZ_NOT_PROVEN_USD=true
MAXLMTSZ_NOT_PROVEN_USDC=true
MAXLMTSZ_IS_RAW_VENUE_FIELD=true
MAXLMTSZ_IS_NOT_ALREADY_NORMALIZED_PEAK_TRADE_QTY=true
```

For the current FUTURES xperp instrument the official derivatives branch
applies. The unit is the number of contracts. That is not a freeze of
the raw value `100000000`.

### 6.2 maxMktSz

```text
MAXMKTSZ_UNIT_STATUS=BOUND
MAXMKTSZ_UNIT=contracts
MAXMKTSZ_UNIT_OFFICIAL_PHRASE=number_of_contracts
MAXMKTSZ_ROLE=MAXIMUM_ORDER_QUANTITY_OF_A_SINGLE_MARKET_ORDER
MAXMKTSZ_PRODUCT_CLASS_DEPENDENT=true
MAXMKTSZ_ORDER_TYPE_DEPENDENT=true
MAXMKTSZ_INSTRUMENT_TYPE_DEPENDENT=true
MAXMKTSZ_SPOT_MARGIN_UNIT=USDT
MAXMKTSZ_DERIVATIVES_UNIT=contracts
MAXMKTSZ_IS_NOT_MAXLMTSZ=true
MAX_MKT_SZ_EDGE_STATUS=NOT_REQUIRED
```

Current canary entry remains LIMIT-only. `maxMktSz` is a peer field on
the same row. Its unit is bound. It is still not a substitute for
`maxLmtSz`. For SPOT/MARGIN the official maxMktSz unit is USDT, which
differs from maxLmtSz base currency. That SPOT divergence is recorded
and is not applied to this FUTURES instrument.

### 6.3 Combined MAX_SIZE unit

```text
MAX_SIZE_UNIT_STATUS=BOUND
MAX_SIZE_UNIT=contracts
MAX_SIZE_EQUALS_MAXLMTSZ_SEMANTIC_PROOF=LIMIT_ORDER_MAX_QUANTITY_IN_CONTRACTS_FOR_DERIVATIVES
MAXLMTSZ_IS_NOT_POSITION_TIER_MAXSZ=true
EXPOSURE_MAX_NOTIONAL_IS_NOT_VENUE_MAX_SIZE=true
```

Both observed fields are contract counts for this FUTURES instrument.
MAX_SIZE as the required entry edge remains the LIMIT field `maxLmtSz`.

### 6.4 Authority source inventory

```text
UNIT_AUTHORITY_SOURCE_COUNT=3
```

1. `OFFICIAL_DEFINITIONAL_AUTHORITY` —
   `https:&#47;&#47;my.okx.com&#47;docs-v5&#47;en&#47;` section
   `Production Trading Services` naming REST `https:&#47;&#47;eea.okx.com`.
   Conclusion carried: EEA production REST bind;
   `GLOBAL_DOC_SEMANTICS_APPLICABLE_TO_OKX_EEA=true`.
2. Same surface, `Public Data` / `Get instruments` /
   `GET &#47;api&#47;v5&#47;public&#47;instruments` response table,
   fields `maxLmtSz` and `maxMktSz`. Conclusion carried:
   derivatives unit = number of contracts.
3. Same Get-instruments table, field `ruleType` `xperp`, plus
   `CURRENT_RAW_EVIDENCE` `instType=FUTURES` `ruleType=xperp`.
   Conclusion carried: target is a FUTURES xperp derivatives contract
   on the official derivatives branch.

Repo/forensic GET bodies, Z2AR raw values, Python extractors, and
`INTEGER_CONTRACT_REQUIRED` are **not** unit-authority sources.

## 7) Normalization remains unbound

Peak_Trade canary `build_venue_native_order_body_v1` copies
`quantity` into venue request field `sz`. Official Place Order `sz` is
only "Quantity to buy or sell". Canary `quantity` is policy-set to
`minSz`. Official minSz for derivatives is number of contracts. That
chain is recorded as `INTERPRETATION` / incomplete mapping, not as a
canonical quantity-domain proof.

```text
MAX_SIZE_NORMALIZATION_STATUS=UNBOUND
PEAK_TRADE_QTY_WIRE_FIELD=sz
PEAK_TRADE_QTY_EQUALS_MINSZ_BY_MINIMUM_EXPOSURE_POLICY=true
OFFICIAL_PLACE_ORDER_SZ_UNIT_FOR_FUTURES=UNPROVEN_ON_REQUEST_PARAM
PEAK_TRADE_ORDER_PLAN_QTY_DOMAIN_EQUALS_CONTRACTS=UNPROVEN
TRANSFORMATION_REQUIRED_BEFORE_COMPARE_WITH_ORDER_PLAN_QTY=UNPROVEN
INTEGER_CONTRACT_REQUIRED_IS_NOT_OFFICIAL_UNIT_PROOF=true
EXPOSURE_DOCSTRING_IS_NOT_OFFICIAL_UNIT_PROOF=true
Z2S_API_SZ_FUTURES_UNIT_IS_NOT_SUI_ORDER_PLAN_QTY_BIND=true
```

Expected intermediate state:

```text
MAX_SIZE_UNIT=BOUND
MAX_SIZE_NORMALIZATION_STATUS=UNBOUND
```

## 8) Consumer / freshness / runtime firewall

```text
MAX_SIZE_CONSUMER_BOUND=false
EXISTING_EXTRACTOR_REQUIRED_TUPLE=minSz,lotSz,tickSz,ctVal
EXISTING_EXTRACTOR_DOES_NOT_READ_MAXLMTSZ=true
RUNTIME_ALIGNMENT_REQUIRED=false
RUNTIME_MUTATION_JUSTIFIED=false
RUNTIME_MUTATION_PERFORMED=false
CHANGED_RUNTIME_FILES=NONE
MAX_SIZE_FRESHNESS_STATUS=WINDOW_OBSERVED_NOT_POLICY_BOUND
MAX_SIZE_FRESHNESS_POLICY=UNBOUND
CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false
```

Unit bind does not imply a consumer. Freshness remains the #6148 window
observation without a policy. `CURRENT_REUSABLE_MAXLMTSZ_PROVEN` remains
false because freshness policy, normalization, and consumer remain
unbound.

## 9) Required edge reassessment

Status vocabulary is exactly `PROVEN`, `PARTIALLY_BOUND`, `UNBOUND`,
`CONFLICTED`, `NOT_REQUIRED`.

| EDGE_ID | CURRENT_STATUS | Reason after this unit adjudication |
|---|---|---|
| MAX_SIZE | PARTIALLY_BOUND | Current raw `maxLmtSz=100000000` observed; unit now `contracts`; freshness policy, normalization, and consumer remain unbound |
| MAX_MKT_SZ | NOT_REQUIRED | LIMIT-only entry; peer unit now `contracts`; still not a substitute for `maxLmtSz` |
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

`MAX_SIZE` remains earliest because `PARTIALLY_BOUND` is not `PROVEN`.
Unit is closed. The next semantic gap inside MAX_SIZE is the mapping
from venue contract-count to `order_plan_v1` / `exposure_v1` quantity
domain. Freshness policy and consumer remain independently unbound and
are not authorized here. This slice does **not** jump to MAX_AVAILABLE
or any later required edge.

## 10) Adjudication result

```text
ADJUDICATION_RESULT=PARTIAL
SOURCE_ADJUDICATION_RESULT=MAX_SIZE_UNIT_BOUND_CONTRACTS_NORMALIZATION_UNBOUND
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
NEXT_DISTINCT_SURFACE=MAX_SIZE_NORMALIZATION
NEXT_DISTINCT_SURFACE_AUTHORIZED=false
```

Not `COMPLETE`. Not `BLOCKED_BY_MISSING_SOURCE`. Not `BLOCKED_BY_CONFLICT`.

## 11) Negative / non-equivalence contracts

```text
UNIT_BIND_IS_NOT_NORMALIZATION_BIND=true
UNIT_BIND_IS_NOT_FRESHNESS_POLICY=true
UNIT_BIND_IS_NOT_CONSUMER_BIND=true
UNIT_BIND_IS_NOT_CURRENT_NUMERIC_FREEZE=true
CURRENT_RAW_OBSERVATION_IS_NOT_UNIT_PROOF=true
OFFICIAL_DEFINITION_IS_NOT_RAW_NUMERIC=true
MINSZ_UNIT_IS_NOT_MAXLMTSZ_UNIT_PROOF=true
LOTSZ_UNIT_IS_NOT_MAXLMTSZ_UNIT_PROOF=true
PLACE_ORDER_SZ_UNDERSPECIFIED_REQUEST_PARAM_IS_NOT_ORDER_PLAN_QTY_DOMAIN_PROOF=true
INTEGER_CONTRACT_REQUIRED_IS_NOT_OFFICIAL_UNIT_PROOF=true
BTC_CTVAL_ALGEBRA_IS_NOT_SUI_MAX_SIZE_UNIT=true
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
MAXLMTSZ_IS_NOT_MAXMKTSZ=true
MAXLMTSZ_IS_NOT_POSITION_TIER_MAXSZ=true
MAXLMTSZ_IS_NOT_MAXAVAILSIZE=true
EXPOSURE_MAX_NOTIONAL_IS_NOT_VENUE_MAX_SIZE=true
UPCCHG_IS_NOT_FRESHNESS_POLICY=true
GLOBAL_OPENAPI_HOST_IS_NOT_EEA_PRODUCTION_REST=true
RUNTIME_ALIGNMENT_REQUIRED_IS_NOT_IMPLIED_BY_UNIT_BIND=true
HISTORICAL_6148_MAX_SIZE_UNIT_UNBOUND_IS_NOT_THIS_SLICE=true
```

## 12) Guards (not SSOT)

Exact proof file:

`tests/ops/test_peak_trade_post_6148_max_size_unit_adjudication_v1.py`

Guards must keep:

- this spec and Master §5.3 name the unit persist and `MAX_SIZE_UNIT=contracts`
- #6148 spec remains historically `MAX_SIZE_UNIT=UNBOUND` for that GET slice
- current raw `maxLmtSz=100000000` and `maxMktSz=100000` unchanged
- `GLOBAL_DOC_SEMANTICS_APPLICABLE_TO_OKX_EEA=true` from EEA doc surface
- `UNIT_REQUIRES_CTVAL=false`; `UNIT_REQUIRES_CTMULT=false`; `UNIT_REQUIRES_CTTYPE=false`
- `MAX_SIZE_NORMALIZATION_STATUS=UNBOUND`; freshness policy UNBOUND; consumer unbound
- required metadata edges remain 8; bound 0; partial 2; unbound 6; conflicted 0
- earliest remaining unbound edge `MAX_SIZE`; earliest remaining MAX_SIZE gap `MAX_SIZE_NORMALIZATION`
- Kraken exclusion closed; BTC not resurrected
- extract_instrument_constraints required tuple remains `minSz, lotSz, tickSz, ctVal`
- `maxLmtSz` / `maxMktSz` / `maxAvailSize` remain absent from order_plan, exposure, and submit_transport
- no venue GET/POST this slice; documentation read only
- #6143–#6148 remain closed as historical persists
- runtime files unchanged

## 13) Out of scope this slice

```text
MAX_SIZE_NORMALIZATION=NOT_THIS_SLICE
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
CANARY_EXECUTE=NOT_THIS_SLICE
FLATTEN=NOT_THIS_SLICE
ORDER_PLAN_RUNTIME_MUTATION=NOT_THIS_SLICE
EXPOSURE_RUNTIME_MUTATION=NOT_THIS_SLICE
SUBMIT_TRANSPORT_RUNTIME_MUTATION=NOT_THIS_SLICE
KRAKEN_RUNTIME_MUTATION=NOT_THIS_SLICE
CURRENT_NUMERIC_FREEZE=NOT_THIS_SLICE
FRESHNESS_POLICY_INVENTION=NOT_THIS_SLICE
RESTORATION_REOPEN=NOT_THIS_SLICE
MERGE=NOT_THIS_SLICE
CORE_RUNTIME_MUTATION=false
```

## 14) Existing guards reused (not duplicated)

| Invariant | Current guard |
|---|---|
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
SEE_ALSO_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1.md
SEE_ALSO_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE=docs/ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md
SEE_ALSO_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION=docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1.md
SEE_ALSO_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING=docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1.md
```
