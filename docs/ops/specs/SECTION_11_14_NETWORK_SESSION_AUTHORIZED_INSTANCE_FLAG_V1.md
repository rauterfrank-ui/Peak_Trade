---
docs_token: DOCS_TOKEN_SECTION_11_14_NETWORK_SESSION_AUTHORIZED_INSTANCE_FLAG_V1
status: active
scope: §11.14 network_session_authorized instance-flag seam on the send-capable bound inner; no session arming; no GET; no POST; no inner.send
capability: SECTION_11_14_NETWORK_SESSION_AUTHORIZED_INSTANCE_FLAG_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Network Session Authorized Instance Flag V1

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
NETWORK_SESSION_INSTANCE_AUTHORIZATION_IMPLEMENTED=true
NETWORK_SESSION_AUTHORIZED=true
SESSION_ARMING_EXECUTED=false
SESSION_ARMED=false
SEND_PERMISSION_CHANGED=false
GET_PERFORMED=false
POST_PERFORMED=false
INNER_SEND_EXECUTED=false
WIRE_SEND_EXECUTED=false
DURABLE_CONSUMED=false
POSITION_MUTATION_EXECUTED=false
REAL_POST_COUNT=0
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice implements the explicit instance-authorization seam
`authorize_network_session_instance_v1`. It does **not** issue Owner
authority. It does **not** arm a session. It does **not** set
`send_permitted=true`. It does **not** GET. It does **not** POST. It does
**not** invoke `inner.send`. It does **not** consume durable state.

```text
OWNER_NETWORK_SESSION_AUTHORITY_V1 issued/accepted
≠ network_session_authorized instance state
≠ session_armed
≠ send_permitted
≠ inner.send
≠ wire send
```

Census (`FORENSIC_RAW`): no named Owner schema previously set
`AuthenticatedGatedProductiveFlattenTransportV1.network_session_authorized=true`.
Issuer/verifier `network_session_authority_v1.py` never sets that flag.

## A. Implemented symbol

```text
INSTANCE_AUTHORIZATION_SYMBOL=authorize_network_session_instance_v1
BOUND_INNER=send-capable ProductiveFlattenSubmitSendAdapterV1.inner
BIND_LEVEL_NETWORK_SESSION_AUTHORIZED_REMAINS_FALSE=true
```

The bind-level field `ProductiveTransportBindSendCapableV1.network_session_authorized`
remains false. The instance flag lives on `bind.adapter.inner`.

## B. Binding (existing fields only)

Fail-closed to:

1. predecessor `OWNER_NETWORK_SESSION_AUTHORITY_V1` issued and accepted
2. `origin_main_sha`
3. `instrument_id`
4. `exact_envelope_id`
5. send-capable bind identity (`PRODUCTIVE_TRANSPORT_BIND_SEND_CAPABLE`)

Mismatch or missing predecessor => deny. Flag remains false.

## C. Current runtime boundary

Standing `session_armed=false` is unchanged. After a successful instance
authorization the send-capable orchestrator leaves
`PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED` and stops at the existing
deny `SESSION_NOT_ARMED` before `inner.send`.

```text
CURRENT_CANONICAL_BOUNDARY=SESSION_NOT_ARMED
EARLIEST_UNRESOLVED_RUNTIME_GATE=SESSION_ARMED
NEXT_OWNER_AUTHORITY_REQUIRED=OWNER_SESSION_ARMING_GO
OPEN_GATE_ORDER_POINTS=FRESH_PRE_SUBMIT_GET;ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND;RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER;DURABLE_CONSUME_SUCCESS_OBJECT
```

`OWNER_SESSION_ARMING` remains `NONE_NAMED`. This slice does not invent that
schema. Session arming is not authorized here.

## Non-execution

```text
HARD_STOP=true
THIS_GO_IS_NOT_A_SEND_GO=true
THIS_GO_IS_NOT_A_SESSION_ARMING_GO=true
NEXT_SLICE_AUTHORIZED=false
```
