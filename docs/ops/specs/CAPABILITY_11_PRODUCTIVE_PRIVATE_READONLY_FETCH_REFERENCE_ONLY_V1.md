---
docs_token: DOCS_TOKEN_CAPABILITY_11_PRODUCTIVE_PRIVATE_READONLY_FETCH_REFERENCE_ONLY_V1
status: active
scope: Phase 11 post-credential-load-reference-only order-free residual — productive private-readonly FETCH REFERENCE-ONLY; no network fetch/consume/orders/Cap 11.4/Cap 11.13
capability: CAPABILITY_11_PRODUCTIVE_PRIVATE_READONLY_FETCH_REFERENCE_ONLY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — Productive Private Read-Only Fetch Reference-Only V1

## Goal

Bind a fail-closed **productive private-readonly fetch reference-only** record that
proves which GET allowlist fetch plan would be intended under the closed
credential-load reference-only predecessor (Master Runbook §11.12.1 prep),
without performing any private API network fetch. This capability consumes
`CAPABILITY_11_PRODUCTIVE_CREDENTIAL_LOAD_REFERENCE_ONLY_V1` and retains Cap 11.3
path binding + Owner Auth Artifact predecessors. It does **not** start a network
session, does not load plaintext secrets, does not consume authorization, does
not enable order send, does not construct Cap 11.4 Testnet execution adapters,
and does not start Cap 11.13.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
REFERENCE_ONLY=true
REFERENCE_ONLY_FETCH_ADMISSIBLE_DEFAULT=false
PRIVATE_READONLY_FETCH_PERFORMED=false
PRIVATE_READONLY_NETWORK_REACHABLE=false
PRIVATE_READONLY_GET_ONLY=true
ORDER_SEND_DISABLED=true
ORDERS_AUTHORIZED=false
ORDER_PATH_STARTED=false
MUTATING_EXCHANGE_CALLS=false
AUTHORIZATION_CONSUMPTION_ALLOWED=false
AUTHORIZATION_CONSUMED=false
CREDENTIAL_CONSUMED=false
NETWORK_SESSION_STARTED=false
CREDENTIAL_LOAD_PERFORMED=false
CREDENTIAL_PLAINTEXT_LOADED=false
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE=false
CAPABILITY_11_4_STARTED=false
CAPABILITY_11_13_STARTED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
PLAINTEXT_SECRET_FORBIDDEN=true
WITHDRAWAL_PERMISSION=false
LEAST_PRIVILEGE=true
```

## In scope

- Productive private-readonly fetch reference-only record (GET allowlist plan only)
- Fail-closed precondition evaluation for `reference_only_fetch_admissible`
- Binding of intended fetch endpoints: `accounts`, `open_positions`, `open_orders`
- Mandatory refusal of mutation actions (submit&#47;cancel&#47;amend&#47;withdraw&#47;transfer)
- Predecessor credential-load reference-only + Owner Auth Artifact + Cap 11.3 path
- Negative refusals for fetch, consume, network session, Cap 11.4, Cap 11.13,
  provider access, order send
- Evidence &#47; verifier &#47; contract tests

## Out of scope

- Real private API network fetch (Master Runbook §11.12.1 execution)
- Authorization or credential consumption
- Credential plaintext materialization
- Cap 11.4+ Testnet order submit &#47; adapter activation
- Cap 11.13 Live activation
- Trading &#47; risk &#47; safety core mutation
- Runtime activation

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_productive_private_readonly_fetch_reference_only_v1` |
| Predecessor credential-load reference-only | retained, unchanged |
| Predecessor Owner Auth Artifact | retained, unchanged |
| Cap 11.3 productive private-readonly path | retained, unchanged |
| Cap 11.3 private-readonly GET allowlist | reused |

## Safety claims

```text
REFERENCE_ONLY=true
PRIVATE_READONLY_FETCH_PERFORMED=false
PRIVATE_READONLY_NETWORK_REACHABLE=false
PRIVATE_READONLY_GET_ONLY=true
ORDER_SEND_DISABLED=true
ORDERS_AUTHORIZED=false
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
AUTHORIZATION_CONSUMPTION_ALLOWED=false
CREDENTIAL_LOAD_PERFORMED=false
CREDENTIAL_PLAINTEXT_LOADED=false
NETWORK_SESSION_STARTED=false
CAPABILITY_11_4_STARTED=false
CAPABILITY_11_13_STARTED=false
TESTNET_EXECUTION_REACHABLE=false
LIVE_EXECUTION_REACHABLE=false
WITHDRAWAL_PERMISSION=false
PLAINTEXT_SECRET_NEVER_PERSISTED=true
```

## Evidence

- Package: `docs&#47;evidence&#47;capability_11_productive_private_readonly_fetch_reference_only_v1&#47;`
- Generator: `scripts&#47;ops&#47;generate_capability_11_productive_private_readonly_fetch_reference_only_v1.py`
- Verifier: `scripts&#47;ops&#47;verify_capability_11_productive_private_readonly_fetch_reference_only_v1.py`
- Tests: `tests&#47;ops&#47;test_capability_11_productive_private_readonly_fetch_reference_only_v1.py`

## Activation

This capability is **not** an activation and does not authorize Cap 11.4 network
order paths, Cap 11.13 Live activation, credential materialization, or real
§11.12.1 private read-only network fetch. Separate Owner-GO is required before
any later consuming residual.
