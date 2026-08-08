---
docs_token: DOCS_TOKEN_CAPABILITY_11_3_PRODUCTIVE_PRIVATE_READONLY_PATH_BINDING_V1
status: active
scope: Phase 11 Cap 11.3 productive private read-only path binding only; no network fetch; no Cap 11.4 orders
capability: CAPABILITY_11_3_PRODUCTIVE_PRIVATE_READONLY_PATH_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability 11.3 — Productive Private Read-Only Path Binding V1

## Goal

Bind the **productive private read-only path** as a fail-closed prerequisite for
later Master Runbook §11.12.1 private read-only Testnet progression. This
capability reuses Cap 11.2 productive credential-load path binding (secret
reference only) and Cap 11.3 private read-only venue contracts (GET allowlist).
It does **not** perform private API fetches, does not start a network session,
does not load plaintext secrets, does not construct Testnet order adapters, and
does not start Cap 11.13.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
PRIVATE_READONLY_PATH_ALLOWED_DEFAULT=false
PRIVATE_READONLY_FETCH_PERFORMED=false
PRIVATE_READONLY_NETWORK_REACHABLE=false
PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED=false
PRIVATE_READONLY_GET_ONLY=true
NETWORK_SESSION_STARTED=false
CAPABILITY_11_4_STARTED=false
CAPABILITY_11_13_STARTED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
PLAINTEXT_SECRET_FORBIDDEN=true
WITHDRAWAL_PERMISSION=false
LEAST_PRIVILEGE=true
```

## In scope

- Productive private read-only path binding record (secret reference only)
- Fail-closed precondition evaluation for `private_readonly_path_allowed`
- Mandatory GET&#47;read-only allowlist: `accounts`, `open_positions`, `open_orders`
- Mandatory refusal of mutation actions (submit&#47;cancel&#47;amend&#47;withdraw&#47;transfer)
- Cap 11.2 productive credential-load path predecessor binding
- Cap 11.3 private read-only port declaration retention
- Negative refusals for fetch, network session, Cap 11.4, Cap 11.13, provider access
- Evidence &#47; verifier &#47; contract tests

## Out of scope

- Real private API network fetch
- Real credential materialization or provider access
- Cap 11.4+ Testnet order submit
- Cap 11.13 Live activation
- Trading &#47; risk &#47; safety core mutation
- Runtime activation

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_3_productive_private_readonly_path_binding_v1` |
| Predecessor Cap 11.2 productive credential-load path | retained, unchanged |
| Cap 11.3 private read-only contracts | retained, unchanged |

## Safety claims

```text
PRIVATE_READONLY_PATH_ALLOWED_DEFAULT=false
PRIVATE_READONLY_FETCH_PERFORMED=false
PRIVATE_READONLY_NETWORK_REACHABLE=false
PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED=false
PRIVATE_READONLY_GET_ONLY=true
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
NETWORK_SESSION_STARTED=false
CAPABILITY_11_4_STARTED=false
CAPABILITY_11_13_STARTED=false
TESTNET_EXECUTION_REACHABLE=false
LIVE_EXECUTION_REACHABLE=false
WITHDRAWAL_PERMISSION=false
PLAINTEXT_SECRET_NEVER_PERSISTED=true
CREDENTIAL_LOAD_PERFORMED=false
```

## Evidence

- Package: `docs&#47;evidence&#47;capability_11_3_productive_private_readonly_path_binding_v1&#47;`
- Generator: `scripts&#47;ops&#47;generate_capability_11_3_productive_private_readonly_path_binding_v1.py`
- Verifier: `scripts&#47;ops&#47;verify_capability_11_3_productive_private_readonly_path_binding_v1.py`
- Tests: `tests&#47;ops&#47;test_capability_11_3_productive_private_readonly_path_binding_v1.py`

## Activation

This capability is **not** an activation and does not authorize Cap 11.4 network
order paths or Cap 11.13 Live activation.
