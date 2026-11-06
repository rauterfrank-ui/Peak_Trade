---
docs_token: DOCS_TOKEN_SECTION_11_14_RECEIPT_MISSING_V1
status: active
scope: §11.14 RECEIPT_MISSING; attachable FlattenPreSendGateReceiptV1 mint and one-shot attach; first deny after attach is UNSIGNED_PRODUCTIVE_HEADERS; no HMAC generation; no GET; no POST
capability: SECTION_11_14_RECEIPT_MISSING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Receipt Missing V1

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
RECEIPT_MISSING=PROVEN
RECEIPT_TYPE=FlattenPreSendGateReceiptV1
RECEIPT_PRODUCER=evaluate_flatten_pre_send_gate_v1
RECEIPT_CONSUMER=AuthenticatedGatedProductiveFlattenTransportV1.send
RECEIPT_MINT_SOURCE=mint_flatten_pre_send_attachable_receipt_v1
RECEIPT_ATTACH_SEAM=attach_flatten_pre_send_receipt_once_v1
RUNTIME_RECEIPT_MINT_EXECUTED=true
RECEIPT_MINT_IS_OFFLINE_ATTEST=true
RECEIPT_MINT_IS_NOT_WIRE_SEND_VERIFY=true
RECEIPT_MINT_IS_NOT_WIRE_SEND_CONSUME=true
HMAC_GENERATION_WIRED=false
RUNTIME_HMAC_EXECUTED=false
HMAC_HEADER_GENERATED=false
LEASE_CONSUMED=false
GET_PERFORMED=false
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
FIRST_DENY_AFTER_ATTACHED_RECEIPT=UNSIGNED_PRODUCTIVE_HEADERS
CURRENT_CANONICAL_BOUNDARY=UNSIGNED_PRODUCTIVE_HEADERS
EARLIEST_UNRESOLVED_RUNTIME_GATE=HMAC_GENERATION
NEXT_OWNER_AUTHORITY_REQUIRED=HMAC_GENERATION
OPEN_GATE_ORDER_BLOCKER=HMAC_GENERATION
OPEN_GATE_ORDER_POINTS=
FINAL_STATUS=RECEIPT_MISSING_PROVEN_UNSIGNED_HEADERS_NO_POST
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice consumes `RECEIPT_MISSING`. It mints an attachable
`allowed=true` `FlattenPreSendGateReceiptV1` as an offline attest and
attaches it once. It does **not** generate HMAC or OK-ACCESS headers.
It does **not** HTTP POST. It does **not** GET. It does **not** issue,
verify-for-send, or consume `OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1`.
It does **not** authorize a network session. It does **not** close
`HMAC_GENERATION`.

## A. Mint (`CANONICAL`)

`mint_flatten_pre_send_attachable_receipt_v1` reuses
`evaluate_flatten_pre_send_gate_v1`. An attachable mint requires a typed
`FlattenPreSendGateInputV1`, matching `expected_origin_main_sha` when
supplied, `allowed=true`, nonempty `approved_request_identity`, nonempty
`request_body` / `approved_body_text`, and an unconsumed send lease.

No mint when the gate input is missing or wrong type, the SHA is stale
or missing, the producer returns `allowed=false`, identity/body is
missing, or the lease is already consumed.

Q1 remains: attachable receipt mint may precede wire-send authority.
This mint is not wire-send verify and not wire-send consume.

## B. Attach (`CANONICAL`)

`attach_flatten_pre_send_receipt_once_v1` reuses
`AuthenticatedGatedProductiveFlattenTransportV1.attach_pre_send_receipt`.
Duplicate attach is `RECEIPT_ALREADY_ATTACHED_NO_REWRITE`. A consumed
lease cannot attach (`RECEIPT_LEASE_ALREADY_CONSUMED`). A denied or
untyped receipt cannot attach.

## C. Remaining boundary (`CANONICAL`)

After a minted receipt is attached, unsigned `send()` first-denies
`UNSIGNED_PRODUCTIVE_HEADERS` before lease consume and urllib.
`HMAC_GENERATION_WIRED=false`. HMAC generation still requires successful
verify / accept of `OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1`.

Historical subordinate `OPEN_GATE_ORDER_POINTS` tuples, including
`productive_wire_send_orchestrator_v1.OPEN_GATE_ORDER_POINTS`, are not
SSOT and were not rewritten. The orchestrator receipt-missing path
without this mint remains fail-closed at `RECEIPT_MISSING`.

## Non-execution

```text
HARD_STOP=true
THIS_GO_IS_NOT_A_HMAC_GO=true
THIS_GO_IS_NOT_A_POST_GO=true
THIS_GO_IS_NOT_A_WIRE_SEND_GO=true
THIS_GO_IS_NOT_A_GET_GO=true
THIS_GO_IS_NOT_A_LIVE_CONSUME_GO=true
NEXT_SLICE_AUTHORIZED=false
REAL_POST_COUNT=0
```
