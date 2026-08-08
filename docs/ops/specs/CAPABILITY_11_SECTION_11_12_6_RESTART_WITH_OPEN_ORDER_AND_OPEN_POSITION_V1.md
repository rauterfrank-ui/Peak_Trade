---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_6_RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION_V1
status: active
scope: Phase 11 §11.12.6 restart-with-open-order/position residual — Cap 11.5 two-path fixture reuse + §11.12.5 bind; no order submit/network writes/§11.12.7/Cap 11.13
capability: CAPABILITY_11_SECTION_11_12_6_RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.6 Restart With Open Order And Open Position V1

## Goal

Implement Master Runbook **§11.12.6 Restart with open order and open position**
as the next productive Testnet-progression residual after closed
`CAPABILITY_11_SECTION_11_12_5_UNKNOWN_SUBMIT_AND_RECONNECT_RECOVERY_V1`.

This capability **reuses** the Cap 11.5 fixture-only paths
`restart_with_open_order` and `restart_with_open_position`, and **binds** the
§11.12.5 productive unknown-submit/reconnect predecessor. It produces a
deterministic two-path restart-recovery closure record with
`NETWORK_EFFECT=NONE`, fail-closed silent-reinitialization refusal, and
required reconciliation before Alpha. It does **not** submit orders, does not
authorize network writes or restart-session activation, does not activate Cap
11.5 Testnet adapters, does not start §11.12.7 kill-switch/emergency proof, and
does not start Cap 11.13.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
REFERENCE_ONLY=false
RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION_ALLOWED=true
CAP_11_5_RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_REUSE_ALLOWED=true
SECTION_11_12_5_PREDECESSOR_BINDING_REQUIRED=true
ORDER_SEND_DISABLED=true
ORDERS_AUTHORIZED=false
ORDER_PATH_STARTED=false
ORDER_SUBMIT_PERFORMED=false
MUTATING_EXCHANGE_CALLS=false
NETWORK_WRITES_AUTHORIZED=false
NETWORK_WRITE_PERFORMED=false
LIFECYCLE_NETWORK_EFFECT=NONE
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
TESTNET_ORDER_SUBMIT_PERFORMED=false
CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED=false
CAPABILITY_11_5_STARTED=false
SECTION_11_12_7_STARTED=false
CAPABILITY_11_13_STARTED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
TESTNET_ORDER_LIFECYCLE_PROVEN=false
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=false
TESTNET_RESTART_PROVEN=false
PATH_CLASS=RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION
LIFECYCLE_SOURCE=FIXTURE_ONLY
ALLOWED_PATHS=restart_with_open_order,restart_with_open_position
```

## In scope

- Binding closed §11.12.5 productive unknown-submit/reconnect predecessor
- Reuse of Cap 11.5 `run_restart_recovery_fixture_path_v1` for the two §11.12.6 paths
- Fail-closed restart semantics: reconstruct OPEN without re-submit; reconcile before Alpha
- Productive recovery execution record with path histories + binding digest
- Fail-closed refusals for network submit/writes, Cap 11.5 adapter activation,
  §11.12.7 paths, Cap 11.13, LIVE mode, non-fixture sources, out-of-scope paths
- Evidence / verifier / contract tests

## Out of scope

- §11.12.7 Kill-switch and emergency control proof
- Cap 11.5+ Testnet order submit / adapter activation / network restart session
- Cap 11.13 Live activation
- Network writes (POST/PUT/PATCH/DELETE) or exchange order submit
- Trading / risk / safety core mutation
- Claiming `TESTNET_RESTART_PROVEN` or later §11.12 closure flags

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1` |
| Predecessor §11.12.5 | retained, unchanged |
| Cap 11.5 restart-with-open-order/position contracts | reused, unchanged |

## Safety claims

```text
ORDER_SEND_DISABLED=true
ORDERS_AUTHORIZED=false
NETWORK_WRITES_AUTHORIZED=false
NETWORK_WRITE_PERFORMED=false
LIFECYCLE_NETWORK_EFFECT=NONE
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
TESTNET_ORDER_SUBMIT_PERFORMED=false
CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED=false
SECTION_11_12_7_STARTED=false
CAPABILITY_11_13_STARTED=false
TESTNET_ORDER_LIFECYCLE_PROVEN=false
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=false
TESTNET_RESTART_PROVEN=false
```

## Evidence

- Package: `docs/evidence/capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1/`
- Generator: `scripts/ops/generate_capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1.py`
- Verifier: `scripts/ops/verify_capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1.py`
- Tests: `tests/ops/test_capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1.py`

## Activation

This capability is **not** runtime Testnet/Live order activation. Restart
closure remains fixture-only with `NETWORK_EFFECT=NONE`. Separate Owner-GO is
required before §11.12.7 or any later Testnet order-lifecycle residual.
