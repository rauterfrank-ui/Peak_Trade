---
docs_token: DOCS_TOKEN_SECTION_11_14_RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER_V1
status: active
scope: §11.14 receipt/HMAC vs wire-send-authority order; inner lease consume repaired; no receipt mint; no HMAC generation; no POST
capability: SECTION_11_14_RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Receipt HMAC Vs Wire Send Authority Order V1

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
Q1_CANONICAL=YES
Q2_CANONICAL=NO
Q3_CANONICAL=INNER_REPAIR_REQUIRED
ATTACHABLE_RECEIPT_MINT_MAY_PRECEDE_WIRE_SEND_AUTHORITY=true
RECEIPT_MINT_IS_OFFLINE_ATTEST=true
RECEIPT_MINT_IS_NOT_WIRE_SEND_VERIFY=true
RECEIPT_MINT_IS_NOT_WIRE_SEND_CONSUME=true
HMAC_GENERATION_REQUIRES_WIRE_SEND_AUTHORITY_VERIFY_ACCEPT=true
HMAC_GENERATION_WIRED=false
RUNTIME_RECEIPT_MINT_EXECUTED=false
RUNTIME_HMAC_EXECUTED=false
HMAC_HEADER_GENERATED=false
INNER_REPAIR_IMPLEMENTED=true
LEASE_CONSUME_AFTER_LOCAL_PREWIRE_GATES=true
LEASE_CONSUMED=false
POST_PERFORMED=false
HTTP_POST_EXECUTED=false
PRODUCTIVE_URLLIB_POST_EXECUTED=false
WIRE_SEND_EXECUTED=false
DURABLE_CONSUMED=false
POSITION_MUTATION=false
ENVELOPE_REBIND_EXECUTED=false
CURRENT_CANONICAL_BOUNDARY=RECEIPT_MISSING
EARLIEST_UNRESOLVED_RUNTIME_GATE=DURABLE_CONSUME_SUCCESS_OBJECT
NEXT_OWNER_AUTHORITY_REQUIRED=DURABLE_CONSUME_SUCCESS_OBJECT
OPEN_GATE_ORDER_BLOCKER=DURABLE_CONSUME_SUCCESS_OBJECT
OPEN_GATE_ORDER_POINTS=DURABLE_CONSUME_SUCCESS_OBJECT
FINAL_STATUS=RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER_DECIDED_INNER_LEASE_REPAIRED
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice consumes `RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER`. It
does **not** mint a receipt at runtime. It does **not** generate HMAC
or OK-ACCESS headers. It does **not** HTTP POST. It does **not** close
`DURABLE_CONSUME_SUCCESS_OBJECT`.

## A. Owner order (`CANONICAL`)

```text
Q1_ATTACHABLE_RECEIPT_MINT_BEFORE_WIRE_SEND_AUTHORITY=YES
Q2_HMAC_GENERATION_BEFORE_WIRE_SEND_AUTHORITY=NO
Q3_INNER_LEASE_BEFORE_SESSION_POLICY=INNER_REPAIR_REQUIRED
```

Attachable `allowed=true` receipt mint may precede issued/accepted
`OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1`. Receipt mint is an offline
attest, not wire-send verify and not wire-send consume.

HMAC / OK-ACCESS header generation may occur only after successful
verify/accept of `OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1`. HMAC
generation is not wired in this persist.

## B. Inner repair (`ADJUDICATED`)

In `GatedProductiveFlattenTransportV1.send` and
`AuthenticatedGatedProductiveFlattenTransportV1.send`, lease consume and
`_sent=True` occur after `network_session_authorized` and the other local
pre-wire denies, and still before `last_wire_attempted=True` / urllib.

Session deny does not consume the lease and does not irreversibly set
`_sent`. Receipt-missing and HMAC-presence denies remain pre-consume.
A successful gated path consumes the lease exactly once. Duplicate
send remains fail-closed.

## C. Subordinate OPEN_GATE_ORDER_POINTS (`NAVIGATION_ONLY`)

Historical subordinate `OPEN_GATE_ORDER_POINTS` lists, including
`productive_wire_send_orchestrator_v1.OPEN_GATE_ORDER_POINTS`, are not
SSOT and were not rewritten. Remaining open order point in this
Master-Runbook persist:

```text
OPEN_GATE_ORDER_POINTS=DURABLE_CONSUME_SUCCESS_OBJECT
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
