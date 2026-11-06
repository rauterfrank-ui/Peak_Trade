---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_7_KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_V1
status: active
scope: Phase 11 §11.12.7 kill-switch/emergency residual — Cap 11.5 command fixture reuse + §11.12.6 bind; no order submit/network writes/§11.12.8/Cap 11.13; TESTNET_KILL_SWITCH_PROVEN remains false
capability: CAPABILITY_11_SECTION_11_12_7_KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.7 Kill-Switch And Emergency Control Proof V1

## Goal

Implement Master Runbook **§11.12.7 Kill-switch and emergency control proof**
(plus §11.9 properties) as the next productive Testnet-progression residual after
closed `CAPABILITY_11_SECTION_11_12_6_RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION_V1`.

This capability **reuses** the Cap 11.5 fixture-only kill-switch / emergency-control
contracts for all six §11.9 emergency commands, and **binds** the §11.12.6
productive restart predecessor. It produces a deterministic emergency-command
closure record with `NETWORK_EFFECT=NONE`, fail-closed runtime-clear / side-effect-
bypass / risk-increase refusal, and Alpha-independent cancel/exit-or-reduce
paths. It does **not** submit orders, does not authorize network writes, does not
activate Cap 11.5 Testnet adapters, does not activate the kill-switch contract,
does **not** claim `TESTNET_KILL_SWITCH_PROVEN`, does not start §11.12.8, and does
not start Cap 11.13.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
REFERENCE_ONLY=false
KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_ALLOWED=true
CAP_11_5_KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_REUSE_ALLOWED=true
SECTION_11_12_6_PREDECESSOR_BINDING_REQUIRED=true
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
KILL_SWITCH_CONTRACT_ACTIVATED=false
SECTION_11_12_8_STARTED=false
CAPABILITY_11_13_STARTED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
TESTNET_ORDER_LIFECYCLE_PROVEN=false
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=false
TESTNET_RESTART_PROVEN=false
TESTNET_KILL_SWITCH_PROVEN=false
PATH_CLASS=KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF
LIFECYCLE_SOURCE=FIXTURE_ONLY
ALLOWED_COMMANDS=BLOCK_NEW_ENTRY,EXIT_ONLY,REDUCE_ONLY,CANCEL_ALL,HALT_AFTER_CANCEL,PERSISTENT_KILL
```

## In scope

- Binding closed §11.12.6 productive restart-with-open-order/position predecessor
- Reuse of Cap 11.5 `build_kill_switch_fixture_record_v1` for all six §11.9 commands
- Fail-closed §11.9 semantics: persisted, restart-surviving, runtime-clear forbidden,
  Alpha-independent cancel/exit-or-reduce, no silent risk increase
- Productive emergency-control execution record with command histories + binding digest
- Fail-closed refusals for network submit/writes, Cap 11.5 adapter activation,
  kill-switch contract activation, §11.12.8 paths, Cap 11.13, LIVE mode,
  non-fixture sources, unknown/out-of-scope commands
- Evidence / verifier / contract tests

## Out of scope

- §11.12.8 Long-running autonomous Testnet campaign
- Cap 11.5+ Testnet order submit / adapter activation / network kill-switch session
- Cap 11.13 Live activation
- Network writes (POST/PUT/PATCH/DELETE) or exchange order submit
- Trading / risk / safety core mutation
- Claiming `TESTNET_KILL_SWITCH_PROVEN` or later §11.12 closure flags

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1` |
| Predecessor §11.12.6 | retained, unchanged |
| Cap 11.5 kill-switch/emergency contracts | reused, unchanged |

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
KILL_SWITCH_CONTRACT_ACTIVATED=false
SECTION_11_12_8_STARTED=false
CAPABILITY_11_13_STARTED=false
TESTNET_ORDER_LIFECYCLE_PROVEN=false
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=false
TESTNET_RESTART_PROVEN=false
TESTNET_KILL_SWITCH_PROVEN=false
```

## Evidence

- Package: `docs/evidence/capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1/`
- Generator: `scripts/ops/generate_capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1.py`
- Verifier: `scripts/ops/verify_capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1.py`
- Tests: `tests/ops/test_capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1.py`

## Activation

This capability is **not** runtime Testnet/Live kill-switch activation. Emergency
control closure remains fixture-only with `NETWORK_EFFECT=NONE` and
`TESTNET_KILL_SWITCH_PROVEN=false`. Separate Owner-GO is required before §11.12.8
or any later Testnet order-lifecycle residual.
