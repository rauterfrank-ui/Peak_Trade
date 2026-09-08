---
docs_token: DOCS_TOKEN_SECTION_11_14_FRESH_PRE_SUBMIT_GET_AND_FRESHNESS_ADJUDICATION_V1
status: active
scope: §11.14 Fresh Pre-Submit GET and freshness adjudication; four required GETs executed; quote-locked frozen envelope stale; reprice not executed; no POST; no HMAC POST; no receipt attach
capability: SECTION_11_14_FRESH_PRE_SUBMIT_GET_AND_FRESHNESS_ADJUDICATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Fresh Pre-Submit GET And Freshness Adjudication V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
AUTHORITY=NONE
MAP_OF_TRUTH_AUTHORITY=NONE
ATLAS_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
SECTION_11_14_AUTHORIZED=false
SECTION_11_14_COMPLETE=false
SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED=false
LIVE_ENABLED=false
LIVE_ARMED=false
CANARY_AUTHORIZED=false
POST_ALLOWED=false
OWNER_EXECUTION_AUTHORIZED=false
FRESH_PRE_SUBMIT_GET=true
GET_CONTRACT_STATUS=DEFINED
GET_TARGETS_ADJUDICATED=true
GET_PERFORMED=true
GET_CALL_COUNT=4
GET_SUCCESS_COUNT=4
ENVELOPE_FRESHNESS_STATUS=REPRICE_REQUIRED
REPRICE_EXECUTED=false
ENVELOPE_REBUILT=false
RECEIPT_MINTED=false
RECEIPT_BOUND=false
RECEIPT_ATTACHED=false
HMAC_EXECUTED=false
HMAC_HEADER_GENERATED=false
LEASE_CONSUMED=false
POST_PERFORMED=false
WIRE_SEND_EXECUTED=false
DURABLE_CONSUMED=false
POSITION_MUTATION_EXECUTED=false
CURRENT_CANONICAL_BOUNDARY=RECEIPT_MISSING
EARLIEST_UNRESOLVED_RUNTIME_GATE=ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND
NEXT_OWNER_AUTHORITY_REQUIRED=ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND
FIRST_DENY_BEFORE=RECEIPT_MISSING
FIRST_DENY_AFTER_FRESH_GET=ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND
OPEN_GATE_ORDER_BLOCKER=ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND
FINAL_STATUS=FRESH_GET_COMPLETE_REPRICE_AUTHORITY_REQUIRED
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice consumes `FRESH_PRE_SUBMIT_GET` for Fresh-Pre-Submit-GET and
freshness adjudication only. It does **not** reprice. It does **not**
rebuild a Flatten SELL envelope. It does **not** HMAC-sign a POST. It
does **not** attach a receipt. It does **not** consume a lease. It does
**not** HTTP POST. It does **not** close
`ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND` as an architecture decision.

## A. Required Fresh GET census (`ADJUDICATED`)

Receipt producer `evaluate_flatten_pre_send_gate_v1` never GETs. It
consumes caller-supplied snapshots. The required contemporaneous GETs
are:

```text
GET /api/v5/account/positions
GET /api/v5/market/ticker?instId=SUI-USD_UM_XPERP-310404
GET /api/v5/trade/orders-pending
GET /api/v5/public/instruments?instType=FUTURES&instId=SUI-USD_UM_XPERP-310404
```

Not required by the current receipt producer:

```text
public/price-limit
account/config
account/balance
account/leverage-info
account/max-size
account/trade-fee
public/mark-price
market/books
```

Position: unfiltered `GET &#47;api&#47;v5&#47;account&#47;positions`.
`data=[]` is `TARGET_POSITION_NOT_OBSERVED`, not zero. Explicit `pos=0`
is `TARGET_POSITION_ZERO_PROVEN`. Freshness is local monotonic
response-received, max-age 5000 ms.

Quote: `GET &#47;api&#47;v5&#47;market&#47;ticker` `bidPx`/`askPx`/`ts`. SELL selects
BID. Threshold 5000 ms wall-clock. `tickSz` from instruments (no TTL).

Pending: `GET &#47;api&#47;v5&#47;trade&#47;orders-pending`. `data=[]` with `code=0`
means zero pending rows. That is not position empty-data-is-zero.

## B. Fresh GET observation (`ADJUDICATED`)

Evidence:
`evidence&#47;ops&#47;section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1&#47;20260908T062634Z_fresh_pre_submit_get_v1`

```text
POSITION_OBSERVED=true
POSITION_VALUE=1
POSITION_STATE=TARGET_POSITION_NONZERO_PROVEN
POS_SIDE=net
MGN_MODE=cross
POSITION_FRESHNESS_VALID=true
QUOTE_OBSERVED=true
QUOTE_BID=0.8121
QUOTE_ASK=0.8127
QUOTE_TS_MS=1788848794462
QUOTE_TICK_SZ=0.0001
QUOTE_FRESHNESS_VALID=true
COMPUTED_LIMIT_PX=0.8121
FROZEN_LIMIT_PX=0.8343
PENDING_ORDER_COUNT=0
```

## C. Envelope freshness / reprice separation (`ADJUDICATED`)

The producer price contract is quote-locked LIMIT from current BID.
Frozen envelope `px=0.8343` bound at SHA
`565cee16783ba0a3f1aea606626bf6418bad21e8` is not send-fresh.
Fresh quantized BID `0.8121` != frozen `0.8343`.

```text
ENVELOPE_FRESHNESS_STATUS=REPRICE_REQUIRED
REPRICE_EXECUTED=false
ENVELOPE_REBUILT=false
RECEIPT_MINTED=false
```

SHA difference alone is not the reprice proof. The proof is the
quote-locked LIMIT contract plus the fresh ticker observation.

## D. Receipt producer re-evaluation (`ADJUDICATED`)

Producer was evaluated with fresh snapshots. Freshness gates
`QUOTE_FRESHNESS_5000MS` and `POSITION_OBSERVATION_FRESHNESS` PASS.
`allowed=false` because this GO does not authorize live/flatten claims.
Denied producer output is not an attachable mint.

```text
RECEIPT_PRODUCER_EVALUATED=true
RECEIPT_ALLOWED=false
RECEIPT_ATTACHED=false
```

## E. Current runtime boundary

```text
CURRENT_CANONICAL_BOUNDARY=RECEIPT_MISSING
EARLIEST_UNRESOLVED_RUNTIME_GATE=ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND
NEXT_OWNER_AUTHORITY_REQUIRED=ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND
OPEN_GATE_ORDER_POINTS=FRESH_PRE_SUBMIT_GET;ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND;RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER;DURABLE_CONSUME_SUCCESS_OBJECT
FIRST_DENY_AFTER_FRESH_GET=ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND
```

Send() first deny remains `RECEIPT_MISSING` because no receipt is
attached. The next Owner authority required to advance past this
Fresh-GET close is the already-named open gate-order point
`ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND`. This slice does not decide
that point.

## Non-execution

```text
HARD_STOP=true
THIS_GO_IS_NOT_A_REPRICE_GO=true
THIS_GO_IS_NOT_A_HMAC_GO=true
THIS_GO_IS_NOT_A_POST_GO=true
THIS_GO_IS_NOT_A_WIRE_SEND_GO=true
THIS_GO_IS_NOT_A_CONSUME_GO=true
THIS_GO_IS_NOT_AN_ATTACHABLE_RECEIPT_MINT_GO=true
NEXT_SLICE_AUTHORIZED=false
```
