---
docs_token: DOCS_TOKEN_SECTION_11_14_ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND_V1
status: active
scope: §11.14 Envelope reprice or freshness-at-send; seven producer GETs executed; frozen LIMIT stale; Flatten SELL envelope rebuilt; no POST; no HMAC POST; no receipt mint/bind/attach
capability: SECTION_11_14_ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Envelope Reprice Or Freshness At Send V1

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
REPRICE_CONTRACT_STATUS=DEFINED
REPRICE_ALGORITHM_SOURCE=evaluate_canary_flatten_limit_price_contract_v1+build_flatten_sell_envelope_v1
ROUNDING_RULE=SELL_ROUND_DOWN_TO_TICK
PRICE_BAND_RULE=LIMIT_PX_MUST_BE_GTE_FRESH_SELL_LMT
FRESH_GET_REQUIRED=true
FRESH_GET_EXECUTED=true
GET_CALL_COUNT=7
GET_SUCCESS_COUNT=7
ENVELOPE_FRESHNESS_STATUS=REPRICE_REQUIRED
REPRICE_REQUIRED=true
REPRICE_EXECUTED=true
ENVELOPE_REBUILD_EXECUTED=true
OLD_ENVELOPE_ID=76f0ad245070206d7fe8807fca8d130dbdedbdc3969e7ba42f23ca88901c164a
OLD_LIMIT_PRICE=0.8343
FRESH_REFERENCE_FIELD=bidPx
FRESH_REFERENCE_PRICE=0.8185
NEW_LIMIT_PRICE=0.8185
NEW_ENVELOPE_ID=0a0133a3b82e4a15bf6986605a9a8e6b47b22665b485ff0f570200803f21cdbe
ENVELOPE_FRESHNESS_STATUS_AFTER=VALID_WITH_FRESH_GET
RECEIPT_MINTED=false
RECEIPT_BOUND=false
RECEIPT_ATTACHED=false
HMAC_EXECUTED=false
HMAC_HEADER_GENERATED=false
LEASE_CONSUMED=false
POST_PERFORMED=false
HTTP_POST_EXECUTED=false
PRODUCTIVE_URLLIB_POST_EXECUTED=false
WIRE_SEND_EXECUTED=false
DURABLE_CONSUMED=false
POSITION_MUTATION=false
CURRENT_CANONICAL_BOUNDARY=RECEIPT_MISSING
EARLIEST_UNRESOLVED_RUNTIME_GATE=RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER
NEXT_OWNER_AUTHORITY_REQUIRED=RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER
OPEN_GATE_ORDER_BLOCKER=RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER
FINAL_STATUS=ENVELOPE_REPRICED_FRESH_AT_SEND
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice consumes `ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND` for freshness
adjudication and, when required, a full Flatten SELL envelope rebuild.
It does **not** mint, bind, or attach a receipt. It does **not**
HMAC-sign a POST. It does **not** consume a lease. It does **not** HTTP
POST. It does **not** decide `RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER`.

## A. Canonical reprice contract (`ADJUDICATED`)

Producer remains `build_flatten_sell_envelope_v1`. Identity is SHA-256
of frozen identity fields; there is no in-place mutation API. Price
permit remains quote-locked LIMIT from
`evaluate_canary_flatten_limit_price_contract_v1`: SELL selects BID,
round down to `tickSz`, freshness 5000 ms, no extra-deviation collar.
Price-band is fresh `sellLmt` from `GET &#47;api&#47;v5&#47;public&#47;price-limit`
(`px >= sellLmt`). Alternative freshness-at-send predicate:
`VALID_WITH_FRESH_GET` when computed LIMIT equals frozen LIMIT.

Required contemporaneous GETs are the producer inputs:

```text
GET /api/v5/public/instruments?instType=FUTURES&instId=SUI-USD_UM_XPERP-310404
GET /api/v5/market/ticker?instId=SUI-USD_UM_XPERP-310404
GET /api/v5/public/price-limit?instId=SUI-USD_UM_XPERP-310404
GET /api/v5/account/positions
GET /api/v5/account/trade-fee?instType=FUTURES&instFamily=SUI-USD_UM_XPERP
GET /api/v5/account/max-size?instId=SUI-USD_UM_XPERP-310404&tdMode=cross&px=<computed_limit>
GET /api/v5/trade/orders-pending
```

`max-size` is conditional on a computed LIMIT. Historical frozen values
are not reused as fresh.

## B. Fresh observation (`ADJUDICATED`)

Evidence:
`evidence&#47;ops&#47;section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1&#47;20260908T084936Z_envelope_reprice_or_freshness_at_send_v1`

```text
GET_CALL_COUNT=7
GET_SUCCESS_COUNT=7
POSITION_VALUE=1
QUOTE_BID=0.8185
QUOTE_ASK=0.8189
QUOTE_TS_MS=1788857375964
QUOTE_TICK_SZ=0.0001
COMPUTED_LIMIT_PX=0.8185
FRESH_SELL_LMT=0.8145
FRESH_MAX_SELL=9
FROZEN_LIMIT_PX=0.8343
ENVELOPE_FRESHNESS_STATUS=REPRICE_REQUIRED
```

## C. Rebuild (`ADJUDICATED`)

Frozen envelope `76f0ad245070206d7fe8807fca8d130dbdedbdc3969e7ba42f23ca88901c164a`
`px=0.8343` remains historical evidence. New envelope
`0a0133a3b82e4a15bf6986605a9a8e6b47b22665b485ff0f570200803f21cdbe`
binds `ORIGIN_MAIN_SHA=8b1fa60b9256ad28656946ac08d271b35d9fe602` and
fresh ticker `ts=1788857375964`. New LIMIT `0.8185` equals quantized
fresh BID. `ENVELOPE_FRESHNESS_STATUS_AFTER=VALID_WITH_FRESH_GET`.

```text
REPRICE_EXECUTED=true
ENVELOPE_REBUILD_EXECUTED=true
RECEIPT_MINTED=false
```

## D. Current runtime boundary

Send() first deny remains `RECEIPT_MISSING` because no receipt is
attached. The next named open gate-order point is
`RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER`. This slice does not decide
that point and does not mint a receipt.

```text
CURRENT_CANONICAL_BOUNDARY=RECEIPT_MISSING
EARLIEST_UNRESOLVED_RUNTIME_GATE=RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER
NEXT_OWNER_AUTHORITY_REQUIRED=RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER
OPEN_GATE_ORDER_POINTS=RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER;DURABLE_CONSUME_SUCCESS_OBJECT
```

## Non-execution

```text
HARD_STOP=true
THIS_GO_IS_NOT_A_RECEIPT_MINT_GO=true
THIS_GO_IS_NOT_A_HMAC_GO=true
THIS_GO_IS_NOT_A_POST_GO=true
THIS_GO_IS_NOT_A_WIRE_SEND_GO=true
THIS_GO_IS_NOT_A_CONSUME_GO=true
NEXT_SLICE_AUTHORIZED=false
REAL_POST_COUNT=0
```
