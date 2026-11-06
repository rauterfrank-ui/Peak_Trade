# Peak_Trade — LEVERAGE Forensic Binding Implementation and Closure v1

status: ACTIVE
last_updated: 2026-08-30
owner: Peak_Trade
purpose: Bind Peak_Trade LEVERAGE to the First-Party authenticated account leverage-info GET, wire the productive consumer, and persist one current-SUI forensic observation. Not a second SSOT. Not restoration reopen. Not live or trading authority. Not POS_MODE, MARGIN_MODE, AVAILABLE_MARGIN, or INSTRUMENT_STATE closure. Not set-leverage. Not a TTL. Not an operative cache. Not historical BTC lever=3. Not maximum leverage. Not IMR/MMR reconstruction. Not account-mode proof.
docs_token: DOCS_TOKEN_PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_PRICE_BAND_FORENSIC_BINDING=docs/ops/specs/PEAK_TRADE_PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md
PRIOR_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
EVIDENCE_PACK=evidence/ops/leverage_forensic_binding_implementation_and_closure_v1/20260829T230336Z
PARALLEL_SSOT_CREATED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_RUNTIME_MUTATION=false
CANARY_VENUE_CONSTRAINT_PLAN_RUNTIME_MUTATION=true
NEW_SEMANTIC_POLICY=true
NEW_RUNTIME_OWNER=false
NEW_STAGE=false
NEW_VENUE_PRETRADE_COMPONENT_REQUIRED=false
RESTORATION_REOPEN_REQUIRED=false
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
CHANGED_RUNTIME_FILES=leverage_observation_v1.py,leverage_consumer_v1.py,order_plan_v1.py,submit_transport_v1.py,constants_v1.py,config_v1.py
RUNTIME_ALIGNMENT_REQUIRED=true
RUNTIME_MUTATION_JUSTIFIED=true
RUNTIME_MUTATION_PERFORMED=true
NETWORK_GET_AUTHORIZED=true
NETWORK_GET_PERFORMED=true
NETWORK_VENUE_GET_PERFORMED=true
NETWORK_AUTHENTICATED_GET_PERFORMED=true
NETWORK_POST_AUTHORIZED=false
NETWORK_POST_PERFORMED=false
TRADING_PERFORMED=false
SET_LEVERAGE_EXECUTED=false
AUTH_REQUIRED=true
AUTH_HEADER_SENT=true
```

This document is subordinate to the Master Runbook. Historical
`BTC-USD_UM_XPERP-310404` `lever=3` remains true as a BTC-family
observation and remains non-transferable to SUI. GATE_22 historical
`UNPROVEN_BTC_SET_ACCOUNT_LEVERAGE_3_NOT_TRANSFERRED_TO_SUI` is not
reopened as a BTC reuse path. This persist binds a fresh SUI FUTURES
family GET. Numeric coincidence with historical BTC `3` is not transfer.

## 1) Epistemic class separation

```text
CANONICAL_AUTHORITY=MASTER_RUNBOOK_PLUS_THIS_SUBORDINATE_PERSIST
RAW_OBSERVATION=EVIDENCE_PACK_THIS_SLICE
VALIDATED_FACTS=THIS_DOCUMENT_SECTION_4
ADJUDICATED_CONSUMER_CONTRACT=THIS_DOCUMENT_SECTION_5
HISTORICAL_INTERMEDIATE=GATE_22_BTC_LEVER_3_NOT_TRANSFERRED
NAVIGATION_ONLY=MAP_OF_TRUTH
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=POS_MODE_AND_LATER_REQUIRED_METADATA_EDGES
CONFLICTED=NONE
```

## 2) Owner-GO and current instrument

```text
OWNER_GO_THIS_SLICE=PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1
BOUND_ORIGIN_MAIN_SHA=e968777cf717f6a63f065b50a49eeb777328bc61
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
CURRENT_REST_HOST=eea.okx.com
CURRENT_INST_TYPE=FUTURES
CURRENT_INST_FAMILY=SUI-USD_UM_XPERP
CURRENT_RULE_TYPE=xperp
CANARY_ENTRY_ORDER_TYPE=LIMIT
CANARY_ENTRY_SIDE=BUY
INST_FAMILY_PARSED_FROM_INSTID=false
```

## 3) Current operative binding

```text
LEVERAGE_CANONICAL_DEFINITION=SET_ACCOUNT_LEVERAGE
LEVERAGE_EDGE_ROLE=CURRENT_CONFIGURED_SET_ACCOUNT_LEVERAGE
LEVERAGE_ENDPOINT=/api/v5/account/leverage-info
LEVERAGE_REQUEST_GRAMMAR=instId,mgnMode
LEVERAGE_RESPONSE_FIELDS=instId,ccy,mgnMode,posSide,lever
LEVERAGE_OUTPUT_DOMAIN=SET_ACCOUNT_LEVERAGE
LEVERAGE_DOMAIN=SET_ACCOUNT_LEVERAGE
LEVERAGE_SCOPE=PER_INSTRUMENT_FAMILY
REQUEST_INSTID_ROLE=FAMILY_SELECTOR
LEVERAGE_EXPECTED_MGN_MODE=cross
LEVERAGE_EXPECTED_POS_SIDE=net
LEVERAGE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION
LEVERAGE_TS_AGE_BOUND=UNBOUND
LEVERAGE_NO_TS_FIELD=true
LEVERAGE_AUTH_CLASS=AUTHENTICATED_PRIVATE_GET
LEVERAGE_FIRST_PARTY_SEMANTICS_CONFIRMED=true
MGNMODE_IS_NOT_TDMODE=true
MGNMODE_IS_NOT_ACCOUNT_MODE=true
TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF=true
CROSS_TDMODE_USED_AS_ACCOUNT_MODE_PROOF=false
ACCOUNT_MODE=UNPROVEN
ACCOUNT_MODE_PROOF_STATUS=UNPROVEN
HISTORICAL_BTC_LEVERAGE_REUSED=false
DEFAULT_LEVERAGE_USED=false
MAX_LEVERAGE_SUBSTITUTION_USED=false
IMR_MMR_RECONSTRUCTION_USED=false
POSITION_LEVER_FALLBACK_USED=false
PUBLIC_INSTRUMENTS_LEVER_USED=false
ZERO_NORMALIZATION_PERFORMED=false
FUTURES_SWAP_SEPARATION_PRESERVED=true
PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false
SET_LEVERAGE_EXECUTED=false
```

Owner answers:

- Q1_SOURCE=`AUTHENTICATED_ACCOUNT_LEVERAGE_INFO`
- Q2_DOMAIN=`SET_ACCOUNT_LEVERAGE` current configured value, not maximum leverage
- Q3_SCOPE=`PER_INSTRUMENT_FAMILY`; request `instId` is a family selector
- Q4_FRESHNESS=`FRESH_GET_PER_PRETRADE_DECISION`; no invented `ts` TTL
- Q5_REQUEST_GRAMMAR=`instId` plus required `mgnMode=cross`; no `tdMode`; no `ccy`; no `posSide` query; no POST

First-Party: GET `&#47;api&#47;v5&#47;account&#47;leverage-info` is the documented
Read-permission current-configured leverage surface. POST
`&#47;api&#47;v5&#47;account&#47;set-leverage` is not authorized in this slice.
`mgnMode` is required (`cross` or `isolated`). Order trade mode remains
`tdMode`. They are not the same field.

There is no global leverage setting. For FUTURES + Cross, First-Party
scopes leverage per instrument family. The request `instId` selects a
representative of that family. It does not prove a per-instId leverage
scope. FUTURES and SWAP remain distinct even if family names look
similar. Family identity is the bound constant `DEFAULT_INST_FAMILY`,
not string-parsed from `instId`.

`lever` is the current configured leverage of that family/mode/posSide
row. It is not maximum allowed leverage, not risk-tier max, not
effective leverage, not IMR, not MMR, and not available margin. Margin
formulas may use leverage as an operand; they are not a source for the
current value.

First-Party documents no numeric `ts` on this response. No PRICE_BAND
age-bound is transferred. Freshness is a fresh GET per pretrade
decision. A persisted pack is not an operative cache.

Position-mode policy is not invented here. Peak_Trade still binds
`posMode=net` as a later POS_MODE edge. This consumer therefore
requires a unique response row with `posSide=net`. Long/short or
multirow responses fail closed. This slice does not close POS_MODE.

Successful GET does not prove account mode. `mgnMode=cross` does not
prove account mode. `tdMode=cross` does not prove account mode.

## 4) Raw observation (this slice GET)

Filled after the authorized authenticated READ-ONLY GET. The pack is
forensic evidence for this Owner-GO. Later pretrade decisions must
perform their own GET. The pack is not an operative cache.

```text
LEVERAGE_OBSERVATION_PERFORMED=true
LEVERAGE_GET_PERFORMED=true
LEVERAGE_GET_TIMESTAMP_UTC=2026-08-29T23:03:36.913601Z
LEVERAGE_GET_REQUEST_TIMESTAMP_UTC=2026-08-29T23:03:36.676196Z
LEVERAGE_GET_HTTP_STATUS=200
LEVERAGE_GET_VENUE_CODE=0
LEVERAGE_GET_VENUE_MSG=
LEVERAGE_GET_AUTH_CLASS=AUTHENTICATED_PRIVATE_GET
LEVERAGE_ENDPOINT_OBSERVED=/api/v5/account/leverage-info?instId=SUI-USD_UM_XPERP-310404&mgnMode=cross
LEVERAGE_RAW_ROW_COUNT=1
LEVERAGE_RAW_INST_ID=SUI-USD_UM_XPERP-310404
LEVERAGE_RAW_CCY=
LEVERAGE_RAW_MGN_MODE=cross
LEVERAGE_RAW_POS_SIDE=net
LEVERAGE_RAW_LEVER=3
LEVERAGE_BOUND_INST_FAMILY=SUI-USD_UM_XPERP
LEVERAGE_OBSERVATION_CLASS=SUCCESS_NUMERIC
LEVERAGE_VALIDATED_LEVER=3
LEVERAGE_VALIDATED_MGN_MODE=cross
LEVERAGE_VALIDATED_POS_SIDE=net
LEVERAGE_VALIDATED_DOMAIN=SET_ACCOUNT_LEVERAGE
LEVERAGE_CARDINALITY=UNIQUE_NET
RESPONSE_BODY_SHA256=fbfc9480218e15b0a15a5aac5b662b222108336d71501da82436b8df60b42ef7
PRETRADE_DECISION_ID=leverage-forensic-binding-sui-20260830T0052Z
AUTH_REQUIRED=true
AUTH_HEADER_SENT=true
GET_REQUEST_COUNT_PUBLIC=0
GET_REQUEST_COUNT_AUTHENTICATED=1
POST_COUNT=0
SET_LEVERAGE_EXECUTED=false
ZERO_NORMALIZATION_PERFORMED=false
DEFAULT_LEVERAGE_USED=false
HISTORICAL_BTC_LEVERAGE_REUSED=false
MAX_LEVERAGE_SUBSTITUTION_USED=false
IMR_MMR_RECONSTRUCTION_USED=false
PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false
HISTORICAL_REUSE_PATH_EXISTS=false
NUMERIC_COINCIDENCE_WITH_HISTORICAL_BTC_LEVER_3=true
NUMERIC_COINCIDENCE_IS_NOT_BTC_TRANSFER=true
ACCOUNT_MODE=UNPROVEN
```

The observed SUI `lever=3` is an independent current configured value
for family `SUI-USD_UM_XPERP` under `mgnMode=cross` and `posSide=net`.
It is not reuse of historical BTC leverage-info. Tests must not treat
`3` as a hardcoded default or BTC fallback. Empty `ccy` is the raw
venue field for this FUTURES instrument query and is not currency-level
leverage.

Peak_Trade observation class remains `SUCCESS_NUMERIC`. Unique
`posSide=net` is a validation constraint of this consumer, not a newly
invented taxonomy. Empty data, missing/malformed/non-positive `lever`,
`mgnMode` mismatch, unexpected instId, long/short, or multirow
responses fail closed and do not normalize to historical `3`.

## 5) Consumer contract

```text
LEVERAGE_CONSUMER_IDENTIFIED=apply_fresh_leverage_pretrade_gate_v1@order_plan_v1.build_minimum_valid_canary_order_plan_v1@submit_transport_v1
LEVERAGE_CONSUMER_BOUND=true
LEVERAGE_FAIL_CLOSED_BOUND=true
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION=true
LEVERAGE_BINDING_STATUS=PROVEN
PRICE_BAND_BINDING_STATUS=PROVEN
MAX_SIZE_BINDING_STATUS=PROVEN
MAX_AVAILABLE_BINDING_STATUS=PROVEN
ORDER_PLAN_TYPED_DOMAIN_PRESERVED=true
CANONICAL_VENUE_PRETRADE_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
SECOND_VENUE_PRETRADE_OWNER_EXISTS=false
```

`submit_transport_v1` performs one authenticated GET of
`&#47;api&#47;v5&#47;account&#47;leverage-info` with `instId` equal to the bound
SUI instrument and `mgnMode=cross` before order-plan construction. The
order body does not carry leverage. Failure of this GET or of the
typed domain gate prevents downstream POST. Missing GET defaults
fail-closed. Persisted evidence is not reread as an operative cache.

## 6) Required edge reassessment

| EDGE_ID | CURRENT_STATUS | Reason |
|---|---|---|
| MAX_SIZE | PROVEN | unchanged |
| MAX_MKT_SZ | NOT_REQUIRED | LIMIT-only canary entry; MARKET max-size gate still bound |
| MAX_AVAILABLE | PROVEN | unchanged |
| PRICE_BAND | PROVEN | unchanged |
| LEVERAGE | PROVEN | Owner-adjudicated authenticated `leverage-info` consumer bound; BTC `3` not reused; family-scoped current configured value |
| POS_MODE | UNBOUND | unique `posSide=net` on this GET is not POS_MODE proof |
| MARGIN_MODE | UNBOUND | `mgnMode=cross` on this GET is not account-mode or margin-mode proof |
| AVAILABLE_MARGIN | UNBOUND | unchanged |
| INSTRUMENT_STATE | PARTIALLY_BOUND | unchanged |

```text
REQUIRED_METADATA_EDGE_COUNT=8
BOUND_METADATA_EDGE_COUNT=4
PARTIAL_METADATA_EDGE_COUNT=1
PARTIAL_EDGE_IDS=INSTRUMENT_STATE
UNBOUND_METADATA_EDGE_COUNT=3
UNBOUND_EDGE_IDS=POS_MODE,MARGIN_MODE,AVAILABLE_MARGIN
ALL_REQUIRED_METADATA_EDGES_BOUND=false
EARLIEST_REMAINING_UNBOUND_EDGE=POS_MODE
EARLIEST_UNRESOLVED_DEPENDENCY=POS_MODE
LEVERAGE_BINDING_STATUS=PROVEN
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
ADJUDICATION_RESULT=PARTIAL
NEXT_DISTINCT_SURFACE=POS_MODE
NEXT_DISTINCT_SURFACE_AUTHORIZED=false
```

## 7) Negative contract

```text
HISTORICAL_BTC_LEVERAGE_IS_NOT_CURRENT_SUI=true
HISTORICAL_BTC_LEVERAGE_REUSED=false
DEFAULT_LEVERAGE_USED=false
PUBLIC_INSTRUMENTS_LEVER_IS_NOT_SET_ACCOUNT_LEVERAGE=true
POSITION_TIERS_MAXLEVER_IS_NOT_SET_ACCOUNT_LEVERAGE=true
POSITIONS_LEVER_IS_NOT_SET_ACCOUNT_LEVERAGE=true
IMR_IS_NOT_SET_ACCOUNT_LEVERAGE=true
MMR_IS_NOT_SET_ACCOUNT_LEVERAGE=true
MAX_LEVERAGE_IS_NOT_CURRENT_CONFIGURED_LEVERAGE=true
LEVER_IS_NOT_MAX_LEVERAGE=true
REQUEST_INSTID_IS_NOT_PER_INSTID_SCOPE=true
MGNMODE_IS_NOT_TDMODE=true
MGNMODE_IS_NOT_ACCOUNT_MODE=true
TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF=true
CROSS_TDMODE_USED_AS_ACCOUNT_MODE_PROOF=false
SUCCESSFUL_GET_IS_NOT_ACCOUNT_MODE_PROOF=true
FUTURES_LEVERAGE_IS_NOT_SWAP_LEVERAGE=true
EMPTY_CCY_IS_NOT_CURRENCY_LEVEL_LEVERAGE=true
EMPTY_STRING_IS_NOT_ZERO=true
MISSING_IS_NOT_ZERO=true
VENUE_ERROR_IS_NOT_ZERO=true
AUTH_ERROR_IS_NOT_ZERO=true
MALFORMED_IS_NOT_ZERO=true
LONG_SHORT_ROW_IS_NOT_UNIQUE_NET=true
MULTIROW_IS_NOT_UNIQUE_NET=true
ZERO_NORMALIZATION_PERFORMED=false
POLICY_BIND_IS_NOT_TTL=true
PERSISTED_PACK_IS_NOT_OPERATIVE_CACHE=true
TS_AGE_BOUND_NOT_INVENTED=true
SET_LEVERAGE_EXECUTED=false
NETWORK_POST_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
FLATTEN_IS_NOT_ENTRY_VENUE_PRETRADE_OWNER=true
SEE_ALSO_PRICE_BAND=docs/ops/specs/PEAK_TRADE_PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md
SEE_ALSO_METADATA_BINDING=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
```
