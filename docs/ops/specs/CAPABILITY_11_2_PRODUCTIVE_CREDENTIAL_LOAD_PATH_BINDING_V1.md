---
docs_token: DOCS_TOKEN_CAPABILITY_11_2_PRODUCTIVE_CREDENTIAL_LOAD_PATH_BINDING_V1
status: active
scope: Phase 11 Cap 11.2 productive credential-load path binding only; no credential load; no Cap 11.3 network
capability: CAPABILITY_11_2_PRODUCTIVE_CREDENTIAL_LOAD_PATH_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability 11.2 — Productive Credential Load Path Binding V1

## Goal

Bind the **productive credential-load path** as a fail-closed prerequisite for
later Cap 11.3 / Master Runbook §11.12.1 private read-only Testnet progression.
This capability reuses Cap 11.2 credential-reference, authorization-binding and
credential-load-gate contracts. It does **not** load secrets, does not query
ENV/keychain/credential providers, does not start Cap 11.3 network sessions,
and does not construct Testnet/Live adapters.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
CREDENTIAL_LOAD_ALLOWED_DEFAULT=false
CREDENTIAL_LOAD_PERFORMED=false
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE=false
NETWORK_SESSION_STARTED=false
CAPABILITY_11_3_STARTED=false
CAPABILITY_11_13_STARTED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
PLAINTEXT_SECRET_FORBIDDEN=true
WITHDRAWAL_PERMISSION=false
LEAST_PRIVILEGE=true
```

## In scope

- Productive credential-load path binding record (secret reference only)
- Fail-closed precondition evaluation for `credential_load_allowed`
- Mandatory bindings: testnet-only scope; venue/account/instrument; least
  privilege; withdrawal_permission=false; plaintext forbidden; explicit
  credential-use authorization; expected SHA/config/account/venue match
- Negative refusals for real load, Cap 11.3 construction, network, orders
- Evidence / verifier / contract tests

## Out of scope

- Real credential materialization or provider access
- Cap 11.3 private-readonly network fetch / port construction
- Cap 11.4+ Testnet order submit
- Cap 11.13 Live activation
- Trading / risk / safety core mutation
- Runtime activation

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_2_productive_credential_load_path_binding_v1` |
| Predecessor Cap 11.2 boundary | retained, unchanged |

## Safety claims

```text
CREDENTIAL_LOAD_ALLOWED_DEFAULT=false
CREDENTIAL_LOAD_PERFORMED=false
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE=false
NETWORK_SESSION_STARTED=false
CAPABILITY_11_3_PRIVATE_READONLY_STARTED=false
CAPABILITY_11_13_STARTED=false
TESTNET_EXECUTION_REACHABLE=false
LIVE_EXECUTION_REACHABLE=false
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
WITHDRAWAL_PERMISSION=false
PLAINTEXT_SECRET_NEVER_PERSISTED=true
```

## Evidence

- Package: `docs&#47;evidence&#47;capability_11_2_productive_credential_load_path_binding_v1&#47;`
- Generator: `scripts&#47;ops&#47;generate_capability_11_2_productive_credential_load_path_binding_v1.py`
- Verifier: `scripts&#47;ops&#47;verify_capability_11_2_productive_credential_load_path_binding_v1.py`
- Tests: `tests&#47;ops&#47;test_capability_11_2_productive_credential_load_path_binding_v1.py`

## Activation

This capability is **not** an activation and does not authorize Cap 11.3 or Cap 11.13.
