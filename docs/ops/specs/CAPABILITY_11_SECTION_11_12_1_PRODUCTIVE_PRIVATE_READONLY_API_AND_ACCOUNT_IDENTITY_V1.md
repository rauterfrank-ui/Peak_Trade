---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_1_PRODUCTIVE_PRIVATE_READONLY_API_AND_ACCOUNT_IDENTITY_V1
status: active
scope: Phase 11 §11.12.1 productive private-readonly API and account-identity residual — auth/credential consume + GET accounts only; no orders/writes/Cap 11.4/Cap 11.13/§11.12.2
capability: CAPABILITY_11_SECTION_11_12_1_PRODUCTIVE_PRIVATE_READONLY_API_AND_ACCOUNT_IDENTITY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.1 Productive Private Read-Only API and Account Identity V1

## Goal

Implement Master Runbook **§11.12.1 Read-only private API and account identity** as the
first productive private-readonly residual after
`CAPABILITY_11_PRODUCTIVE_PRIVATE_READONLY_FETCH_REFERENCE_ONLY_V1`.

This capability **consumes** Owner authorization and credential material (digest-only
persistence), starts a private-readonly GET-only network session, and performs a single
allowlisted **GET `accounts`** account-identity fetch. It does **not** enable order send,
does not authorize network writes, does not start Cap 11.4 Testnet execution adapters,
does not start Cap 11.13, and does not begin §11.12.2 order-serialization dry-run.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
REFERENCE_ONLY=false
AUTHORIZATION_CONSUMPTION_ALLOWED=true
PRODUCTIVE_CREDENTIAL_CONSUMPTION_ALLOWED=true
PRIVATE_READONLY_NETWORK_SESSION_ALLOWED=true
ACCOUNT_IDENTITY_FETCH_ALLOWED=true
ORDER_SEND_DISABLED=true
ORDERS_AUTHORIZED=false
ORDER_PATH_STARTED=false
MUTATING_EXCHANGE_CALLS=false
NETWORK_WRITES_AUTHORIZED=false
NETWORK_WRITE_PERFORMED=false
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
CAPABILITY_11_4_STARTED=false
CAPABILITY_11_13_STARTED=false
LIVE_AUTHORIZED=false
PLAINTEXT_SECRET_FORBIDDEN=true
WITHDRAWAL_PERMISSION=false
LEAST_PRIVILEGE=true
HTTP_METHOD=GET
ENDPOINT=accounts
PATH_CLASS=PRIVATE_READONLY_ACCOUNT_IDENTITY
```

## In scope

- Owner Auth Artifact consumption (one-shot; replay fail-closed)
- Productive credential consumption with material digest only (no plaintext in evidence)
- Private-readonly GET-only network session start
- Account-identity fetch via GET `accounts` only
- Fail-closed allowlist for HTTP method/endpoint
- Negative refusals for POST/writes, mutation endpoints, Cap 11.4, Cap 11.13, order send
- Evidence / verifier / contract tests (governed fixture transport for sealed evidence)

## Out of scope

- §11.12.2 Order serialization dry-run
- Cap 11.4+ Testnet order submit / adapter activation
- Cap 11.13 Live activation
- Network writes (POST/PUT/PATCH/DELETE)
- GET `open_positions` / `open_orders` (deferred beyond this residual)
- Trading / risk / safety core mutation
- Logging of credential plaintext, secrets, signatures, tokens, or sensitive headers

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1` |
| Predecessor fetch reference-only | retained, unchanged |
| Cap 11.3 GET allowlist | reused; section subset = `accounts` only |
| Transport for sealed evidence | `GOVERNED_FIXTURE_PRIVATE_READONLY_GET_V1` |

## Safety claims

```text
ORDER_SEND_DISABLED=true
ORDERS_AUTHORIZED=false
NETWORK_WRITES_AUTHORIZED=false
NETWORK_WRITE_PERFORMED=false
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
CAPABILITY_11_4_STARTED=false
CAPABILITY_11_13_STARTED=false
PLAINTEXT_SECRET_NEVER_PERSISTED=true
VENUE_LIVE_CONTACT=false_for_sealed_evidence_fixture_transport
```

## Evidence

- Package: `docs&#47;evidence&#47;capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1&#47;`
- Generator: `scripts&#47;ops&#47;generate_capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.py`
- Verifier: `scripts&#47;ops&#47;verify_capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.py`
- Tests: `tests&#47;ops&#47;test_capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.py`

## Activation

This capability is **not** runtime Live/Testnet order activation. Sealed evidence uses a
governed fixture transport (`VENUE_LIVE_CONTACT=false`). Separate Owner-GO is required
before §11.12.2 or any later Testnet order-path residual.
