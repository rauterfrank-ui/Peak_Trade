---
docs_token: DOCS_TOKEN_SECTION_11_14_DURABLE_CONSUME_SUCCESS_OBJECT_V1
status: active
scope: §11.14 durable-consume success object; typed venue-success mint; COMPLETED consume gated; no receipt mint; no HMAC generation; no POST
capability: SECTION_11_14_DURABLE_CONSUME_SUCCESS_OBJECT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Durable Consume Success Object V1

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
DURABLE_CONSUME_SUCCESS_OBJECT=PROVEN
SUCCESS_OBJECT_TYPE=FlattenProductiveSendSuccessObjectV1
SUCCESS_OBJECT_IMPLEMENTED=true
DURABLE_CONSUME_GATED_ON_SUCCESS_OBJECT=true
RUNTIME_RECEIPT_MINT_EXECUTED=false
RUNTIME_HMAC_EXECUTED=false
HMAC_GENERATION_WIRED=false
LEASE_CONSUMED=false
POST_PERFORMED=false
HTTP_POST_EXECUTED=false
PRODUCTIVE_URLLIB_POST_EXECUTED=false
WIRE_SEND_EXECUTED=false
INNER_SEND_PRODUCTIVE_EXECUTED=false
FLATTEN_EXECUTED=false
DURABLE_CONSUMED=false
POSITION_MUTATION=false
ENVELOPE_REBIND_EXECUTED=false
REAL_POST_COUNT=0
CURRENT_CANONICAL_BOUNDARY=RECEIPT_MISSING
EARLIEST_UNRESOLVED_RUNTIME_GATE=RECEIPT_MISSING
NEXT_OWNER_AUTHORITY_REQUIRED=RECEIPT_MISSING
OPEN_GATE_ORDER_BLOCKER=RECEIPT_MISSING
OPEN_GATE_ORDER_POINTS=
FINAL_STATUS=DURABLE_CONSUME_SUCCESS_OBJECT_PROVEN_NO_POST
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice consumes `DURABLE_CONSUME_SUCCESS_OBJECT`. It does **not**
mint a receipt at runtime. It does **not** generate HMAC or OK-ACCESS
headers. It does **not** HTTP POST. It does **not** consume durable
state against a live send. It does **not** close `RECEIPT_MISSING`.

## A. Success object (`CANONICAL`)

Productive `inner.send` returns `LiveCanaryHttpResponseV1`. That transport
result is not itself a success object. Durable COMPLETED consume on the
productive path may run only after
`mint_flatten_productive_send_success_object_v1` returns
`FlattenProductiveSendSuccessObjectV1`.

Required mint evidence:

```text
typed_allowed_receipt
nonempty_approved_request_identity
typed_http_response
HTTP_STATUS_200
NO_REDIRECT
flatten_venue_acceptance_code_0_scode_0_one_row
nonempty_ordId
clOrdId_match_when_sent
envelope_id_bound
origin_main_sha_bound
request_identity_bound
```

No mint, and therefore no COMPLETED consume, when receipt is missing,
HTTP/transport fails, venue rejects, payload is malformed/ambiguous,
order/request correlation is missing, or the object is stale/foreign
relative to the expected envelope/SHA/authority/request identity.

HTTP 2xx, `code==0`, or `exception is None` alone cannot mint the object.

## B. Durable consume (`CANONICAL`)

`consume_flatten_durable_on_success_object_v1` is the productive COMPLETED
consume entry. It reuses `persist_flatten_durable_consume_v1`. Duplicate
consume remains `DURABLE_CONSUME_ALREADY_PRESENT_NO_REWRITE`. Replay
resubmit remains false.

The fake execution-harness INCOMPLETE ledger for ambiguous fake-transport
exceptions is unchanged and is not this productive success path.

## C. Remaining boundary (`CANONICAL`)

```text
OPEN_GATE_ORDER_POINTS=
CURRENT_CANONICAL_BOUNDARY=RECEIPT_MISSING
EARLIEST_UNRESOLVED_RUNTIME_GATE=RECEIPT_MISSING
NEXT_OWNER_AUTHORITY_REQUIRED=RECEIPT_MISSING
```

Historical subordinate `OPEN_GATE_ORDER_POINTS` tuples, including
`productive_wire_send_orchestrator_v1.OPEN_GATE_ORDER_POINTS`, are not
SSOT and were not rewritten.

## Non-execution

```text
HARD_STOP=true
THIS_GO_IS_NOT_A_RECEIPT_MINT_GO=true
THIS_GO_IS_NOT_A_HMAC_GO=true
THIS_GO_IS_NOT_A_POST_GO=true
THIS_GO_IS_NOT_A_WIRE_SEND_GO=true
THIS_GO_IS_NOT_A_LIVE_CONSUME_GO=true
NEXT_SLICE_AUTHORIZED=false
REAL_POST_COUNT=0
```
