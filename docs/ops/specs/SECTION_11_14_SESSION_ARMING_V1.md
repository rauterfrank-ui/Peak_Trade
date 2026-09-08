---
docs_token: DOCS_TOKEN_SECTION_11_14_SESSION_ARMING_V1
status: active
scope: §11.14 bound session_armed seam on the send-capable adapter; no send_permitted; no GET; no POST; no inner.send
capability: SECTION_11_14_SESSION_ARMING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Session Arming V1

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
SESSION_ARMING_IMPLEMENTED=true
SESSION_ARMED=true
SESSION_ARMING_STANDING=false
SEND_PERMISSION_CHANGED=false
NETWORK_SESSION_AUTHORIZED=true
GET_PERFORMED=false
POST_PERFORMED=false
INNER_SEND_EXECUTED=false
WIRE_SEND_EXECUTED=false
DURABLE_CONSUMED=false
POSITION_MUTATION_EXECUTED=false
REAL_POST_COUNT=0
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice implements the explicit bound arming seam
`arm_productive_session_v1`. It does **not** invent
`OWNER_SESSION_ARMING` as a named Owner schema. It does **not** set
`send_permitted=true`. It does **not** change
`network_session_authorized`. It does **not** GET. It does **not** POST.
It does **not** invoke `inner.send`. It does **not** consume durable state.
The global constant `SESSION_ARMING_STANDING` remains false.

```text
OWNER_NETWORK_SESSION_AUTHORITY_V1 issued/accepted
≠ network_session_authorized instance state
≠ session_armed
≠ send_permitted
≠ inner.send
≠ wire send
```

Census (`FORENSIC_RAW`): no named `OWNER_SESSION_ARMING` schema existed.
`session_armed` was a constructor/orchestrator parameter. This GO covers
only the bound adapter transition.

## A. Implemented symbol

```text
SESSION_ARMING_SYMBOL=arm_productive_session_v1
BOUND_ADAPTER=ProductiveFlattenSubmitSendAdapterV1.session_armed
SESSION_ARMING_STANDING_REMAINS_FALSE=true
```

## B. Binding (existing fields only)

Fail-closed to:

1. predecessor `OWNER_NETWORK_SESSION_AUTHORITY_V1` issued and accepted
2. `network_session_authorized=true` on the exact bound inner
3. `OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1` issued, accepted, unconsumed
4. `origin_main_sha`
5. `instrument_id`
6. `exact_envelope_id`
7. send-capable bind identity (`PRODUCTIVE_TRANSPORT_BIND_SEND_CAPABLE`)

Mismatch or missing prerequisite => deny. `session_armed` remains false.

## C. Current runtime boundary

After successful bound arming the send-capable orchestrator, with standing
caller `session_armed=false`, leaves `SESSION_NOT_ARMED` and stops at the
existing deny `SEND_PERMITTED_FALSE` before `inner.send`.

```text
CURRENT_CANONICAL_BOUNDARY=SEND_PERMITTED_FALSE
EARLIEST_UNRESOLVED_RUNTIME_GATE=SEND_PERMITTED
NEXT_OWNER_AUTHORITY_REQUIRED=OWNER_SEND_PERMITTED_GO
OPEN_GATE_ORDER_POINTS=FRESH_PRE_SUBMIT_GET;ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND;RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER;DURABLE_CONSUME_SUCCESS_OBJECT
```

No named `OWNER_SEND_PERMITTED` schema is invented here.

## Non-execution

```text
HARD_STOP=true
THIS_GO_IS_NOT_A_SEND_GO=true
THIS_GO_IS_NOT_A_SEND_PERMITTED_GO=true
NEXT_SLICE_AUTHORIZED=false
```
