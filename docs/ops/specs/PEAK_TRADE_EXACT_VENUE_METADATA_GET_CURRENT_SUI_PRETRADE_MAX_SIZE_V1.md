# Peak_Trade — Exact Venue Metadata GET Current SUI Pretrade MAX_SIZE v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Persist the authorized read-only public OKX_EEA instruments GET observation for current SUI-USD_UM_XPERP-310404 beginning at MAX_SIZE. Not a second SSOT. Not restoration reopen. Not core runtime mutation. Not live or execution authority. Not a unit bind. Not a freshness-policy bind. Not a consumer bind. Not venue-pretrade completeness.
docs_token: DOCS_TOKEN_PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
PRIOR_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md
PRIOR_LIVE_SAFETY_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1.md
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
NETWORK_GET_AUTHORIZED=true
NETWORK_GET_PERFORMED=true
NETWORK_POST_AUTHORIZED=false
NETWORK_POST_PERFORMED=false
AUTH_REQUIRED=false
AUTH_HEADER_SENT=false
```

This document is subordinate to the Master Runbook and to the post-restoration
preservation contract. It does not replace Master §5.3, Appendix A, C4, Replay
Safety, Cap 7.2, live-safety #6145, simulated-execution #6144,
accounting/portfolio #6143, venue-pretrade limit-gates #6146, or
metadata-binding alignment #6147. It persists one authorized current-window
public instruments GET. It does not freeze a standing numeric, invent a unit,
invent a freshness policy, or implement a runtime consumer.

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
HISTORICAL_6147_NETWORK_GET_PERFORMED=false
```

#6147 remains the closed PARTIAL metadata-binding persist. That slice
identified `EXACT_VENUE_METADATA_GET` and did not authorize or perform it.
This slice consumes the separate Owner-GO for that GET only.

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

## 3) Query-contract revalidation before GET

Canonical grammar reused, not invented:

```text
QUERY_OWNER=public_instruments_query_path_v1
TARGET_VENUE=OKX_EEA
TARGET_HOST=eea.okx.com
TARGET_INSTRUMENT=SUI-USD_UM_XPERP-310404
TARGET_INST_TYPE=FUTURES
TARGET_METHOD=GET
TARGET_PATH=&#47;api&#47;v5&#47;public&#47;instruments
TARGET_QUERY=instType=FUTURES&instId=SUI-USD_UM_XPERP-310404
CANONICAL_QUERY_PATH=&#47;api&#47;v5&#47;public&#47;instruments?instType=FUTURES&instId=SUI-USD_UM_XPERP-310404
QUERY_CONTRACT_REVALIDATION=PASS
ALTERNATE_VENUE_USED=false
KRAKEN_USED=false
BTC_INSTRUMENT_USED=false
SWAP_INST_TYPE_USED=false
OTHER_SUI_INSTRUMENT_USED=false
FUZZY_SYMBOL_NORMALIZATION=false
```

`public_instruments_query_path_v1()` with default instrument and instType
returns exactly that path. `REUSED_BINDING_REST_HOST=eea.okx.com`.
Endpoint, host, and query match the already-adjudicated #6147 source-gap
grammar and the historical Z2AR GET 1 grammar. No improvisation.

Public unauthenticated venue semantics for this endpoint remain bound by
historical Z2AR / Z2R / Z2BD public-instruments GETs. Canary
`submit_transport_v1` signed GETs are a different execute-path surface and
were not used.

```text
AUTH_REQUIRED=false
AUTH_HEADER_SENT=false
COOKIE_HEADER_SENT=false
SIGNED_CANARY_CLIENT_USED=false
CREDENTIAL_SCOPE_ADDED=false
```

## 4) Network GET observation

```text
OWNER_GO=PEAK_TRADE_EXACT_VENUE_METADATA_GET_FOR_CURRENT_SUI_PRETRADE_MAX_SIZE_V1
OWNER_GO_STATUS=CONSUMED
BOUND_ORIGIN_MAIN_SHA=0b9f15a0086d58ec100fe7fb173d9fa12acdf5ea
NETWORK_GET_AUTHORIZED=true
NETWORK_GET_PERFORMED=true
NETWORK_POST_PERFORMED=false
GET_REQUEST_COUNT=1
POST_COUNT=0
REQUEST_EVENT_TIME=2026-08-29T18:22:39.339529000Z
RESPONSE_EVENT_TIME=2026-08-29T18:22:39.549656000Z
VENUE_DATE_HEADER=Sat, 29 Aug 2026 18:22:39 GMT
HTTP_STATUS=200
OKX_CODE=0
OKX_MSG=
OKX_MSG_PRESENCE=PRESENT_EMPTY_STRING
RESPONSE_BODY_SHA256=038f2bf82f18f2d42ed26dca281cc7733e4ef7d07206fd0b19637189ec3e4cd2
BODY_BYTE_LEN=1134
DATA_ROW_COUNT=1
EXACT_INSTID_MATCH_COUNT=1
SOURCE_RESULT=EXACT_ONE_TARGET_ROW
CURRENT_RAW_METADATA_OBSERVED=true
CURRENT_RAW_METADATA_OBSERVATION_TIME=2026-08-29T18:22:39.549656000Z
```

Exactly one data row. Exact `instId=SUI-USD_UM_XPERP-310404`. No heuristic
row selection. HTTP 200 without Authorization. Unexpected auth was not
required.

Evidence pack (derived, non-SSOT):
`evidence/ops/exact_venue_metadata_get_current_sui_pretrade_max_size_v1/20260829T182239Z`

Safe persisted headers only: `Content-Type`, `Date`, `Server`.
`Set-Cookie` / `__cf_bm` were observed on the wire and were **not**
persisted.

## 5) Raw field extraction (exact target row)

Presence vocabulary is exact. Empty string is not null and is not missing.

| Field | Presence | JSON type | Raw value |
|---|---|---|---|
| instId | PRESENT_STRING | str | SUI-USD_UM_XPERP-310404 |
| instType | PRESENT_STRING | str | FUTURES |
| instFamily | PRESENT_STRING | str | SUI-USD_UM_XPERP |
| uly | PRESENT_STRING | str | SUI-USD |
| category | PRESENT_STRING | str | 1 |
| state | PRESENT_STRING | str | live |
| minSz | PRESENT_STRING | str | 1 |
| lotSz | PRESENT_STRING | str | 1 |
| tickSz | PRESENT_STRING | str | 0.0001 |
| maxLmtSz | PRESENT_STRING | str | 100000000 |
| maxMktSz | PRESENT_STRING | str | 100000 |
| ctVal | PRESENT_STRING | str | 1 |
| ctValCcy | PRESENT_STRING | str | SUI |
| ctType | PRESENT_STRING | str | linear |
| settleCcy | PRESENT_STRING | str | USD |
| baseCcy | PRESENT_EMPTY_STRING | str | (empty string) |
| quoteCcy | PRESENT_EMPTY_STRING | str | (empty string) |
| ruleType | PRESENT_STRING | str | xperp |
| lever | PRESENT_STRING | str | 20 |
| maxLmtAmt | PRESENT_STRING | str | 20000000 |
| maxMktAmt | PRESENT_EMPTY_STRING | str | (empty string) |
| maxPxLmtPct | PRESENT_STRING | str | 0.01 |
| floatPxLmtPct | PRESENT_STRING | str | 0.005 |
| initPxLmtPct | PRESENT_STRING | str | 0.02 |
| posLmtAmt | PRESENT_STRING | str | 250000 |
| posLmtPct | PRESENT_STRING | str | 30 |
| maxAvailSize | MISSING | missing | (field absent from row) |

`instIdCode` is a JSON number `255649`. `futureSettlement` is JSON boolean
`false`. Those types are preserved. They are not MAX_SIZE operands.

```text
CURRENT_MAXLMTSZ_FIELD=maxLmtSz
CURRENT_MAXLMTSZ_RAW_VALUE=100000000
CURRENT_MAXMKTSZ_FIELD=maxMktSz
CURRENT_MAXMKTSZ_RAW_VALUE=100000
CURRENT_RAW_MAXLMTSZ_OBSERVED=true
CURRENT_STATE_RAW_VALUE=live
NO_FIELD_INVENTED=true
NO_EMPTY_STRING_NORMALIZED_TO_NULL=true
NO_MISSING_NORMALIZED_TO_ZERO=true
```

## 6) Currentness adjudication

All of the following are true for this window:

- successful GET
- exact host `eea.okx.com`
- exact endpoint `&#47;api&#47;v5&#47;public&#47;instruments`
- exact `instType=FUTURES`
- exact `instId=SUI-USD_UM_XPERP-310404`
- exactly one target row
- `maxLmtSz` present as a non-empty string

Therefore:

```text
CURRENT_RAW_MAXLMTSZ_OBSERVED=true
MAX_SIZE_CURRENT_OBSERVATION_PROVEN=true
CURRENT_WINDOW_RAW_MAXLMTSZ_OBSERVED=true
```

This proves only a current raw observation of the field in the
request/response window. It does **not** prove:

```text
MAX_SIZE_UNIT_BOUND=false
MAX_SIZE_NORMALIZATION_BOUND=false
MAX_SIZE_CONSUMER_BOUND=false
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND
CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false
MAX_SIZE_CURRENT_REUSABLE_NUMERIC=WINDOW_BOUND_FRESHNESS_POLICY_UNBOUND
```

`CURRENT_REUSABLE_MAXLMTSZ_PROVEN` remains false because no freshness
policy, unit, or consumer is bound. The observation is reusable only as a
dated-window raw persist, not as a standing numeric freeze.

## 7) Historical parity / drift

```text
HISTORICAL_MAXLMTSZ_RAW_VALUE=100000000
HISTORICAL_MAXMKTSZ_RAW_VALUE=100000
CURRENT_MAXLMTSZ_RAW_VALUE=100000000
CURRENT_MAXMKTSZ_RAW_VALUE=100000
MAXLMTSZ_RAW_VALUE_PARITY_WITH_Z2AR=true
MAXMKTSZ_RAW_VALUE_PARITY_WITH_Z2AR=true
MAXLMTSZ_RAW_VALUE_DRIFT=false
MAXMKTSZ_RAW_VALUE_DRIFT=false
BODY_SHA256_PARITY_WITH_Z2BD_Z2BF=true
Z2BD_WINDOW_REUSED=false
Z2BF_WINDOW_REUSED=false
Z2AR_WINDOW_REUSED_AS_CURRENT=false
```

Raw string values match Z2AR GET 1. Wire body SHA-256 matches the
2026-08-24 Z2BD / Z2BF instruments bodies
(`038f2bf82f18f2d42ed26dca281cc7733e4ef7d07206fd0b19637189ec3e4cd2`).
That SHA coincidence is parity, not reuse. Z2BD / Z2BF remain forbidden as
future instrument-metadata or venue-constraint freshness proof. This GET is
a new observation window. Identical values do not create an unbounded
freshness guarantee.

## 8) Unit / semantics / freshness firewall

The response does not specify the unit of `maxLmtSz`. No canonical or
forensic in-repo proof binds that unit.

```text
MAX_SIZE_UNIT=UNBOUND
MAX_SIZE_NORMALIZATION_STATUS=UNBOUND_NONE_APPLIED_NONE_PROVEN
NO_UNIT_CONVERSION_APPLIED=true
NO_UNIT_CONVERSION_APPLIED_IS_NOT_UNIT_PROOF=true
MAXLMTSZ_NOT_PROVEN_CONTRACTS=true
MAXLMTSZ_NOT_PROVEN_BASE_SUI=true
MAXLMTSZ_NOT_PROVEN_QUOTE=true
MAXLMTSZ_NOT_PROVEN_USD=true
MAXLMTSZ_NOT_PROVEN_USDC=true
MAXLMTSZ_NOT_PROVEN_NOTIONAL=true
MAX_SIZE_EQUALS_MAXLMTSZ_SEMANTIC_PROOF=UNBOUND
MAXLMTSZ_IS_NOT_MAXMKTSZ=true
MAXLMTSZ_IS_NOT_POSITION_TIER_MAXSZ=true
EXPOSURE_MAX_NOTIONAL_IS_NOT_VENUE_MAX_SIZE=true
```

```text
MAX_SIZE_FRESHNESS_STATUS=WINDOW_OBSERVED_NOT_POLICY_BOUND
MAX_SIZE_FRESHNESS_POLICY=UNBOUND
REQUIRES_PRE_SUBMIT_REFRESH=UNBOUND
PER_ORDER_FRESHNESS_BOUND=false
PER_SESSION_FRESHNESS_BOUND=false
STATIC_FOREVER=false
```

Observed `lever=20`, `maxPxLmtPct=0.01`, and related raw fields are not
leverage-gate or price-band binds.

## 9) Consumer

Read-only recheck of `extract_instrument_constraints_v1`:

```text
EXISTING_EXTRACTOR_REQUIRED_TUPLE=minSz,lotSz,tickSz,ctVal
EXISTING_EXTRACTOR_DOES_NOT_READ_MAXLMTSZ=true
MAX_SIZE_CONSUMER_BOUND=false
RUNTIME_ALIGNMENT_REQUIRED=false
RUNTIME_MUTATION_JUSTIFIED=false
RUNTIME_MUTATION_PERFORMED=false
CHANGED_RUNTIME_FILES=NONE
```

`CURRENT_RAW_MAXLMTSZ_OBSERVED=true` does not itself require runtime
alignment. Consumer binding remains a later distinct Owner-GO after unit
and freshness are resolved or separately authorized.

## 10) Required edge reassessment

Status vocabulary is exactly `PROVEN`, `PARTIALLY_BOUND`, `UNBOUND`,
`CONFLICTED`, `NOT_REQUIRED`.

| EDGE_ID | CURRENT_STATUS | Reason after this GET |
|---|---|---|
| MAX_SIZE | PARTIALLY_BOUND | Current raw `maxLmtSz=100000000` observed; unit, freshness policy, semantic proof, and consumer remain unbound |
| MAX_MKT_SZ | NOT_REQUIRED | LIMIT-only entry; peer field currently observed `100000`; not a substitute for `maxLmtSz` |
| MAX_AVAILABLE | UNBOUND | `maxAvailSize` MISSING on this instruments row |
| PRICE_BAND | UNBOUND | Raw `maxPxLmtPct` / `floatPxLmtPct` / `initPxLmtPct` observed; field-to-gate semantic proof and consumer unbound |
| LEVERAGE | UNBOUND | Raw instrument `lever=20` observed; not an account leverage gate |
| POS_MODE | UNBOUND | Not supplied by this public instruments GET |
| MARGIN_MODE | UNBOUND | Not supplied by this public instruments GET |
| AVAILABLE_MARGIN | UNBOUND | Not supplied by this public instruments GET |
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
EARLIEST_REMAINING_MAX_SIZE_GAP=MAX_SIZE_UNIT
BEGINNING_AT=MAX_SIZE
EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_UNIT
```

`MAX_SIZE` remains earliest because `PARTIALLY_BOUND` is not `PROVEN`.
The GET closed the identified `EXACT_VENUE_METADATA_GET` source-gap. The
earliest remaining MAX_SIZE gap is unit semantics.

## 11) Adjudication result

```text
ADJUDICATION_RESULT=PARTIAL
SOURCE_ADJUDICATION_RESULT=CURRENT_RAW_MAXLMTSZ_OBSERVED_PARTIAL_MAX_SIZE_REMAINS
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
NEXT_DISTINCT_SURFACE=MAX_SIZE_UNIT
NEXT_DISTINCT_SURFACE_AUTHORIZED=false
```

Not `COMPLETE`. Not `BLOCKED_BY_MISSING_SOURCE`. Not `BLOCKED_BY_CONFLICT`.

## 12) Negative / non-equivalence contracts

```text
CURRENT_RAW_OBSERVATION_IS_NOT_UNIT_PROOF=true
CURRENT_RAW_OBSERVATION_IS_NOT_FRESHNESS_POLICY=true
CURRENT_RAW_OBSERVATION_IS_NOT_CONSUMER_BIND=true
IDENTICAL_SHA_TO_Z2BD_IS_NOT_Z2BD_REUSE=true
IDENTICAL_VALUE_TO_Z2AR_IS_NOT_UNBOUNDED_FRESHNESS=true
HISTORICAL_6147_NETWORK_GET_PERFORMED_IS_NOT_THIS_SLICE=true
VENUE_METADATA_EXISTENCE_IS_NOT_GATE_BINDING=true
STATIC_FIELD_EXISTENCE_IS_NOT_RUNTIME_VALIDATION=true
MAXLMTSZ_IS_NOT_MAXMKTSZ=true
MAXLMTSZ_IS_NOT_POSITION_TIER_MAXSZ=true
MIN_SIZE_IS_NOT_MAX_SIZE=true
TICK_ALIGNMENT_IS_NOT_PRICE_BAND_VALIDITY=true
EXPOSURE_MAX_NOTIONAL_IS_NOT_VENUE_MAX_SIZE=true
DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF=true
INSTRUMENT_LEVER_IS_NOT_ACCOUNT_LEVERAGE_GATE=true
MAXPXLMTPCT_IS_NOT_PRICE_BAND_GATE=true
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
KRAKEN_METADATA_MUST_NOT_SOURCE_CURRENT_OKX_PRETRADE=true
EMPTY_STRING_IS_NOT_NULL=true
EMPTY_STRING_IS_NOT_MISSING=true
MISSING_IS_NOT_ZERO=true
NO_UNIT_CONVERSION_APPLIED_IS_NOT_UNIT_PROOF=true
RUNTIME_ALIGNMENT_REQUIRED_IS_NOT_IMPLIED_BY_CURRENT_RAW_MAXLMTSZ_OBSERVED=true
```

## 13) Guards (not SSOT)

Exact proof file:

`tests/ops/test_peak_trade_exact_venue_metadata_get_current_sui_pretrade_max_size_v1.py`

Guards must keep:

- this spec and Master §5.3 name the GET persist and `NETWORK_GET_PERFORMED=true` for this slice
- #6147 spec remains `NETWORK_GET_PERFORMED=false` for that historical slice
- current raw `maxLmtSz=100000000` and `maxMktSz=100000` with Z2AR parity
- `MAX_SIZE_UNIT=UNBOUND`; freshness policy UNBOUND; consumer unbound
- `CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false`
- required metadata edges remain 8; bound 0; partial 2; unbound 6; conflicted 0
- earliest remaining unbound edge `MAX_SIZE`; earliest remaining MAX_SIZE gap `MAX_SIZE_UNIT`
- Kraken exclusion closed; BTC not resurrected
- extract_instrument_constraints required tuple remains `minSz, lotSz, tickSz, ctVal`
- `maxLmtSz` / `maxMktSz` / `maxAvailSize` remain absent from order_plan, exposure, and submit_transport
- evidence body SHA-256 matches the persisted wire body
- no Set-Cookie persisted
- #6143–#6147 remain closed as historical persists
- runtime files unchanged

## 14) Out of scope this slice

```text
MAX_SIZE_UNIT_BIND=NOT_THIS_SLICE
MAX_SIZE_NORMALIZATION=NOT_THIS_SLICE
MAX_SIZE_CONSUMER_IMPLEMENTATION=NOT_THIS_SLICE
MAX_SIZE_FRESHNESS_POLICY=NOT_THIS_SLICE
MAX_AVAILABLE_IMPLEMENTATION=NOT_THIS_SLICE
PRICE_BAND_IMPLEMENTATION=NOT_THIS_SLICE
LEVERAGE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
ACCOUNT_MODE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
INSTRUMENT_STATE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
AUTHENTICATED_GET=NOT_THIS_SLICE
NETWORK_POST=NOT_THIS_SLICE
CANARY_EXECUTE=NOT_THIS_SLICE
FLATTEN=NOT_THIS_SLICE
ORDER_PLAN_RUNTIME_MUTATION=NOT_THIS_SLICE
EXPOSURE_RUNTIME_MUTATION=NOT_THIS_SLICE
SUBMIT_TRANSPORT_RUNTIME_MUTATION=NOT_THIS_SLICE
KRAKEN_RUNTIME_MUTATION=NOT_THIS_SLICE
CURRENT_NUMERIC_FREEZE=NOT_THIS_SLICE
UNIT_INVENTION=NOT_THIS_SLICE
FRESHNESS_POLICY_INVENTION=NOT_THIS_SLICE
RESTORATION_REOPEN=NOT_THIS_SLICE
MERGE=NOT_THIS_SLICE
CORE_RUNTIME_MUTATION=false
SEE_ALSO_POST_6148_MAX_SIZE_UNIT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md
SEE_ALSO_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1.md
SEE_ALSO_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE=docs/ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md
```

## 15) Existing guards reused (not duplicated)

| Invariant | Current guard |
|---|---|
| #6147 metadata-binding PARTIAL persist | `tests/ops/test_peak_trade_post_restoration_venue_pretrade_metadata_binding_alignment_adjudication_v1.py` |
| #6146 venue-pretrade limit gates | `tests/ops/test_peak_trade_post_restoration_venue_pretrade_limit_gates_adjudication_v1.py` |
| Preservation / compatibility contract | `tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py` |
| Live safety gates | `tests/ops/test_peak_trade_post_restoration_live_safety_gates_adjudication_v1.py` |
| Simulated execution pipeline | `tests/ops/test_peak_trade_post_restoration_simulated_execution_pipeline_adjudication_v1.py` |
| Accounting / portfolio alignment | `tests/ops/test_peak_trade_post_restoration_accounting_portfolio_alignment_adjudication_v1.py` |
| Canary submit transport / order plan | `tests/ops/test_section_11_13_5_canary_submit_transport_v1.py` |
| Cap 11.9 fixture unreachable | `tests/ops/test_capability_11_9_live_canary_order_execution_v1.py` |

## 16) Negative contract

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
```
