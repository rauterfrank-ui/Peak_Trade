---
docs_token: DOCS_TOKEN_SECTION_11_14_SEND_PERMITTED_V1
status: active
scope: §11.14 bound send_permitted seam on the send-capable adapter; no inner.send; no GET; no POST
capability: SECTION_11_14_SEND_PERMITTED_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Send Permitted V1

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
SEND_PERMISSION_IMPLEMENTED=true
SEND_PERMITTED=true
BIND_LEVEL_SEND_PERMITTED=false
SESSION_ARMING_STANDING=false
SESSION_ARMED=true
NETWORK_SESSION_AUTHORIZED=true
GET_PERFORMED=false
POST_PERFORMED=false
INNER_SEND_EXECUTED=false
FAKE_INNER_SEND_REACHED=false
REAL_INNER_SEND_EXECUTED=false
WIRE_SEND_EXECUTED=false
DURABLE_CONSUMED=false
POSITION_MUTATION_EXECUTED=false
REAL_POST_COUNT=0
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice implements the explicit bound permission seam
`permit_productive_send_v1`. It does **not** invent
`OWNER_SEND_PERMITTED` as a named Owner schema. It does **not** invoke
`inner.send`. It does **not** GET. It does **not** POST. It does **not**
reprice. It does **not** consume durable state. It does **not** change
`network_session_authorized`. It does **not** change `session_armed`.
Bind-level `bind.send_permitted` remains false. The global constant
`SESSION_ARMING_STANDING` remains false.

```text
OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1 issued/accepted
≠ network_session_authorized
≠ session_armed
≠ send_permitted
≠ inner.send
≠ HTTP POST
≠ wire send
≠ durable consume
```

Census (`FORENSIC_RAW`): no named `OWNER_SEND_PERMITTED` schema existed.
`send_permitted` was a bind/adapter field with constructor false and
auto-promote deny. This GO covers only the bound adapter transition.

## A. Implemented symbol

```text
SEND_PERMISSION_SYMBOL=permit_productive_send_v1
BOUND_ADAPTER=ProductiveFlattenSubmitSendAdapterV1.send_permitted
BIND_LEVEL_SEND_PERMITTED_REMAINS_FALSE=true
```

## B. Binding (existing fields only)

Fail-closed to:

1. `OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1` issued, accepted, unconsumed
2. predecessor `OWNER_NETWORK_SESSION_AUTHORITY_V1` issued and accepted
3. `network_session_authorized=true` on the exact bound inner
4. `session_armed=true` on the exact bound adapter
5. `origin_main_sha`
6. `instrument_id`
7. `exact_envelope_id`
8. send-capable bind identity (`PRODUCTIVE_TRANSPORT_BIND_SEND_CAPABLE`)

Mismatch or missing prerequisite => deny. `send_permitted` remains false.

## C. Current runtime boundary

After successful bound permission the send-capable orchestrator, with
standing caller `session_armed=false`, leaves `SEND_PERMITTED_FALSE` and
stops at the existing adapter deny
`INNER_SEND_NOT_INVOKED_IN_THIS_IMPLEMENTATION` before `inner.send`.
The adapter does not call `inner.send`. Fake recording inners remain
unreached.

```text
CURRENT_CANONICAL_BOUNDARY=INNER_SEND_NOT_INVOKED_IN_THIS_IMPLEMENTATION
EARLIEST_UNRESOLVED_RUNTIME_GATE=INNER_SEND
NEXT_OWNER_AUTHORITY_REQUIRED=OWNER_INNER_SEND_GO
OPEN_GATE_ORDER_POINTS=FRESH_PRE_SUBMIT_GET;ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND;RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER;DURABLE_CONSUME_SUCCESS_OBJECT
FAKE_INNER_SEND_REACHED=false
REAL_INNER_SEND_EXECUTED=false
```

No named `OWNER_INNER_SEND` schema is invented here. Open gate-order
points remain unadjudicated.

## Non-execution

```text
HARD_STOP=true
THIS_GO_IS_NOT_A_GET_GO=true
THIS_GO_IS_NOT_A_REPRICE_GO=true
THIS_GO_IS_NOT_A_POST_GO=true
THIS_GO_IS_NOT_AN_INNER_SEND_GO=true
THIS_GO_IS_NOT_A_WIRE_SEND_GO=true
THIS_GO_IS_NOT_A_FLATTEN_EXECUTE_GO=true
THIS_GO_IS_NOT_A_CONSUME_GO=true
NEXT_SLICE_AUTHORIZED=false
```
