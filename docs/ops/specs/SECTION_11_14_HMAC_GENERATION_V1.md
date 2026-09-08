---
docs_token: DOCS_TOKEN_SECTION_11_14_HMAC_GENERATION_V1
status: active
scope: §11.14 HMAC_GENERATION; typed request-identity-bound HMAC/header artifact from an attached FlattenPreSendGateReceiptV1; first deny after HMAC-signed send is PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED; no GET; no POST; no lease consume; no wire-send consume
capability: SECTION_11_14_HMAC_GENERATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 HMAC Generation V1

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
HMAC_GENERATION=PROVEN
HMAC_GENERATION_WIRED=true
HMAC_GENERATION_ON_SEND_PATH=false
HMAC_SOURCE=generate_flatten_authenticated_headers_v1
HMAC_OUTPUT_TYPE=AuthenticatedProductiveFlattenHeadersV1
PRODUCTIVE_SIGNING_COMPONENT=build_okx_live_canary_auth_headers_v1
HMAC_GENERATION_REQUIRES_WIRE_SEND_AUTHORITY_VERIFY_ACCEPT=true
RUNTIME_HMAC_EXECUTED=true
HMAC_HEADER_GENERATED=true
RECEIPT_MINT_IS_OFFLINE_ATTEST=true
LEASE_CONSUMED=false
WIRE_SEND_CONSUMED=false
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
REAL_GET_COUNT=0
REAL_POST_COUNT=0
FIRST_DENY_AFTER_HMAC_SIGNED_SEND=PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED
CURRENT_CANONICAL_BOUNDARY=PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED
EARLIEST_UNRESOLVED_RUNTIME_GATE=PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED
NEXT_OWNER_AUTHORITY_REQUIRED=PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED
OPEN_GATE_ORDER_BLOCKER=PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED
OPEN_GATE_ORDER_POINTS=
FINAL_STATUS=HMAC_GENERATION_PROVEN_NO_POST
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice consumes `HMAC_GENERATION`. It generates a typed
request-identity-bound HMAC/header artifact from an attached
`FlattenPreSendGateReceiptV1`. It does **not** HTTP POST. It does
**not** GET. It does **not** consume `OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1`.
It does **not** consume the send lease. It does **not** authorize a
network session. It does **not** close
`PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED`.

## A. Generation (`CANONICAL`)

`generate_flatten_authenticated_headers_v1` reuses
`attach_authenticated_headers_via_existing_signer_v1` /
`build_okx_live_canary_auth_headers_v1`. Generation requires an attached
typed `allowed=true` receipt, a request whose method/path/query/body
match `approved_request_identity`, an unconsumed send lease, a
credential handle, and successful verify/accept of
`OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1`.

No artifact when the receipt is missing, untyped, unattached, or
`allowed=false`; when request identity, method, path, or body mismatch;
when the lease is already consumed; when wire-send verify is not
ACCEPT; when origin/main, envelope, or instrument bindings mismatch the
existing wire-send contract; or when signing input is malformed.

Q2 remains: HMAC generation may occur only after successful
verify/accept. Verify is not consume. `allowed=true` alone cannot mint
headers.

## B. Artifact (`CANONICAL`)

Output type is `AuthenticatedProductiveFlattenHeadersV1`. It binds
request identity, method, URL, request path, body text, OKX ISO-8601
millisecond timestamp, and signing-input digest. Audit/repr omit API
key, passphrase, and secret. Timestamp freshness is the existing OKX
ISO-8601-ms format check. No new age window.

HMAC generation does not consume the send lease. Duplicate generation
without consume is not send-replay. Duplicate send remains
`DUPLICATE_POST_FORBIDDEN` at transport. Body is not mutated after
signing; the artifact body equals `approved_body_text`.

## C. Remaining boundary (`CANONICAL`)

HMAC-signed `send()` first-denies
`PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED` before lease consume and
urllib. `HMAC_GENERATION_ON_SEND_PATH=false`. Send still does not
generate HMAC. Historical subordinate `OPEN_GATE_ORDER_POINTS` tuples
are not SSOT and were not rewritten.

## Non-execution

```text
HARD_STOP=true
THIS_GO_IS_NOT_A_POST_GO=true
THIS_GO_IS_NOT_A_WIRE_SEND_GO=true
THIS_GO_IS_NOT_A_GET_GO=true
THIS_GO_IS_NOT_A_LIVE_CONSUME_GO=true
THIS_GO_IS_NOT_A_NETWORK_SESSION_GO=true
NEXT_SLICE_AUTHORIZED=false
REAL_GET_COUNT=0
REAL_POST_COUNT=0
```
