---
docs_token: DOCS_TOKEN_SECTION_11_14_FLATTEN_PRE_SEND_RECEIPT_AUTHORITY_AND_BINDING_V1
status: active
scope: §11.14 flatten pre-send receipt authority adjudication; schema defined; mint blocked by open gate order; no GET; no POST; no HMAC; no receipt mint
capability: SECTION_11_14_FLATTEN_PRE_SEND_RECEIPT_AUTHORITY_AND_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Flatten Pre-Send Receipt Authority And Binding V1

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
RECEIPT_AUTHORITY_SCHEMA_STATUS=DEFINED
RECEIPT_PRODUCER=evaluate_flatten_pre_send_gate_v1
RECEIPT_CONSUMER=AuthenticatedGatedProductiveFlattenTransportV1.send
RECEIPT_PRODUCER_ADJUDICATED=true
RECEIPT_CONSUMER_ADJUDICATED=true
PRODUCER_CONSUMER_SCHEMA_MATCH=true
RECEIPT_OWNER_ISSUANCE_SCHEMA_INVENTED=false
RECEIPT_MINTED=false
RECEIPT_BOUND=false
RECEIPT_ATTACHED=false
RECEIPT_WORK_BLOCKED_BY_OPEN_GATE_ORDER=true
OPEN_GATE_ORDER_BLOCKER=FRESH_PRE_SUBMIT_GET
OPEN_GATE_ORDER_BLOCKER_SECONDARY=ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND
CURRENT_CANONICAL_BOUNDARY=RECEIPT_MISSING
EARLIEST_UNRESOLVED_RUNTIME_GATE=FLATTEN_PRE_SEND_GATE_RECEIPT
NEXT_OWNER_AUTHORITY_REQUIRED=FRESH_PRE_SUBMIT_GET
FIRST_DENY=RECEIPT_MISSING
FIRST_DENY_AFTER_RECEIPT=NOT_REACHED
PRODUCTIVE_INNER_SEND_INVOKED=true
REAL_INNER_SEND_EXECUTED=false
HMAC_EXECUTED=false
LEASE_CONSUMED=false
GET_PERFORMED=false
REPRICE_EXECUTED=false
POST_PERFORMED=false
WIRE_SEND_EXECUTED=false
DURABLE_CONSUMED=false
POSITION_MUTATION_EXECUTED=false
REAL_POST_COUNT=0
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice consumes `OWNER_FLATTEN_PRE_SEND_RECEIPT_GO` for receipt-authority
and schema adjudication. It does **not** mint an attachable receipt. It does
**not** GET. It does **not** HTTP POST. It does **not** HMAC. It does **not**
reprice. It does **not** invent an Owner receipt-issuance schema. It does
**not** close open gate-order points.

## A. Schema census (`ADJUDICATED`)

```text
RECEIPT_TYPE=FlattenPreSendGateReceiptV1
RECEIPT_PRODUCER=evaluate_flatten_pre_send_gate_v1
RECEIPT_CONSUMER=AuthenticatedGatedProductiveFlattenTransportV1.send
RECEIPT_ATTACH_SEAM=AuthenticatedGatedProductiveFlattenTransportV1.attach_pre_send_receipt
RECEIPT_SINGLE_USE=true
RECEIPT_LEASE_TYPE=FlattenReceiptSendLeaseV1
RECEIPT_FRESHNESS_SEMANTICS=EVALUATED_AT_GATE_NOT_STORED_AS_RECEIPT_EXPIRY
RECEIPT_AUTHORITY_OR_GO_NAME=OWNER_FLATTEN_PRE_SEND_RECEIPT_GO
```

The type, producer, consumer, bind fields, single-use lease, and fail-closed
`RECEIPT_MISSING` / `RECEIPT_NOT_ALLOWED` checks are already named in the
predecessor persist and implemented in `flatten_pre_send_gate_v1` /
`AuthenticatedGatedProductiveFlattenTransportV1`. This slice does not add
receipt fields.

## B. Why mint/attach is blocked (`ADJUDICATED`)

`attach_pre_send_receipt` and `send` require `allowed=True` plus
`approved_request_identity` and a non-empty `request_body`. The producer sets
those only when every gate predicate passes, including quote freshness and
position-observation freshness.

Canonical §11.14 constant:

```text
PRE_SUBMIT_FRESH_GET_REQUIRED=true
```

This Owner-GO forbids Fresh Venue GET and envelope reprice. Using frozen
envelope quotes or historical GET as if fresh would silently decide
`FRESH_PRE_SUBMIT_GET` and `ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND`.

Producer census with no GET/reprice snapshots returns a typed object with
`allowed=false`. Attach of that object is `RECEIPT_NOT_ALLOWED`. That census
is not an attachable mint.

## C. Current runtime boundary

```text
CURRENT_CANONICAL_BOUNDARY=RECEIPT_MISSING
EARLIEST_UNRESOLVED_RUNTIME_GATE=FLATTEN_PRE_SEND_GATE_RECEIPT
NEXT_OWNER_AUTHORITY_REQUIRED=FRESH_PRE_SUBMIT_GET
OPEN_GATE_ORDER_POINTS=FRESH_PRE_SUBMIT_GET;ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND;RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER;DURABLE_CONSUME_SUCCESS_OBJECT
PRODUCTIVE_INNER_SEND_INVOKED=true
REAL_INNER_SEND_EXECUTED=false
RECEIPT_PRESENT=false
```

The bound §11.14 path still invokes productive `send` with a missing
receipt. `FIRST_DENY` remains `RECEIPT_MISSING`.

## Non-execution

```text
HARD_STOP=true
THIS_GO_IS_NOT_A_GET_GO=true
THIS_GO_IS_NOT_A_REPRICE_GO=true
THIS_GO_IS_NOT_A_HMAC_GO=true
THIS_GO_IS_NOT_A_POST_GO=true
THIS_GO_IS_NOT_A_WIRE_SEND_GO=true
THIS_GO_IS_NOT_A_CONSUME_GO=true
THIS_GO_IS_NOT_AN_ATTACHABLE_RECEIPT_MINT_GO=true
NEXT_SLICE_AUTHORIZED=false
```
