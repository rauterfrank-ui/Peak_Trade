---
docs_token: DOCS_TOKEN_AUTHENTICATED_PRODUCTIVE_TRANSPORT_V1
status: active
scope: Offline AUTHENTICATED_PRODUCTIVE_TRANSPORT contract; no GET; no POST; no credential use
capability: AUTHENTICATED_PRODUCTIVE_TRANSPORT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# AUTHENTICATED_PRODUCTIVE_TRANSPORT Offline Contract V1

## Goal

Close the named residual `AUTHENTICATED_PRODUCTIVE_TRANSPORT` as an offline
CASE_B contract. Wire the existing HMAC signer onto the productive flatten
path. Construct signing inputs without secrets. Deny unsigned User-Agent-only
headers as authenticated transport. Do not claim runtime authentication. Do
not GET. Do not POST. Do not flatten. Do not unlock Live or Canary. Do not
issue a runtime permit. Do not authorize a network session. Do not use live
credentials. Do not treat this persist as flatten-execute or venue HMAC proof.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
GET_PERFORMED_THIS_PERSIST=false
PRIVATE_AUTH_USED=false
RUNTIME_GET_REQUIRED=false
RUNTIME_GET_PERFORMED=false
ORDER_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
STP_CLOSED=true
CASE=CASE_B_OFFLINE_CLOSABLE_CONTRACT
AUTHENTICATED_PRODUCTIVE_TRANSPORT=PASS_OFFLINE_CONTRACT
AUTHENTICATED_PRODUCTIVE_TRANSPORT_OFFLINE_CONTRACT=PASS_OFFLINE_CONTRACT
AUTHENTICATED_PRODUCTIVE_TRANSPORT_RUNTIME_PROVEN=false
AUTHENTICATION_PROVEN=false
NETWORK_PROVEN=false
CREDENTIAL_USE_PROVEN=false
PRIVATE_GET_PROVEN=false
POST_PROVEN=false
APT_FLATTEN_EXECUTE_AUTHORIZED=false
APT_NETWORK_SESSION_AUTHORIZED=false
APT_DOES_NOT_ISSUE_RUNTIME_PERMIT=true
APT_DOES_NOT_SET_LIVE_AUTHORIZED=true
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_AUTHENTICATED_PRODUCTIVE_TRANSPORT
EARLIEST_UNRESOLVED_DEPENDENCY=SEND_TIME_POSITION_REOBSERVATION
APT_DOES_NOT_GRANT_EXECUTION_READINESS=true
EXECUTION_READY=false
BOUNDED_RUNTIME_PERMIT_ISSUANCE=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE=true
```

## Canonical semantics

`AUTHENTICATED_PRODUCTIVE_TRANSPORT` is the send-time HMAC wiring residual
named after Z2CL unsigned urllib and after SEND_TIME_PASS_18_19_21_24. It is
not a wall-clock, not a venue `uTime`, not an authorized send, and not a
productive POST.

Z2CL already bound gated productive urllib with User-Agent-only headers and
`network_session_authorized=false`. The existing signer
`build_okx_live_canary_auth_headers_v1` remains the only signing component.
This persist proves the **offline contract**:

- unsigned headers are not authenticated productive transport
- signing-input prehash is timestamp + method + path + body with no secret
- the existing signer is reused; no new signing ontology
- HMAC handle is not reordered before Prerequisite 08
- dedicated authenticated transport class exists and never sets the network
  session flag true
- runtime authentication, network, credential use, private GET, and POST
  remain unproven

The name is not self-authorizing runtime or execution authority. A later send
still needs send-time position reobservation, bounded runtime permit issuance,
flatten-execute Owner-GO, network-session authorization, and actual HMAC with
an authorized credential handle. This persist does not issue that permit and
does not authorize flatten execute.

## Proof vs later runtime value

This persist proves the authenticated-transport **evaluation gates** exist and
deny on missing/unproven SEND_TIME_PASS, missing dedicated authenticated
transport, signer mismatch, invented signing ontology, HMAC reordered before
08, unsigned headers counted as authenticated, runtime-authentication claims,
network/credential/GET/POST proven claims, live-authorized substitution,
runtime-permit/flatten/network/GET/POST claims, this implementation GO used as
flatten-execute, remaining-set mismatch, and predecessor lineage mismatch.

Fixture HMAC in tests is not credential use and is not venue authentication.

## Out of scope

- Private GET / POST / flatten / position mutation
- Live / Testnet / Canary execute
- `LIVE_AUTHORIZED=true` / `LIVE_ENABLED` / `LIVE_ARMED` activation
- Network session authorization
- Runtime permit issuance
- Credential borrow / SecretRef resolve / API-key use
- Send-time position reobservation
- Claiming `AUTHENTICATION_PROVEN=true` or `AUTHENTICATED_PRODUCTIVE_TRANSPORT_RUNTIME_PROVEN=true`
- Merge
- Master V2 / Double Play Core mutation
