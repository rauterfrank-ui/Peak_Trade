---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_V1
status: active
scope: Phase 11 §11.12.8 long-running campaign residual — Cap 11.6 campaign fixture reuse + §11.12.7 bind; no productive campaign/network/orders/§11.13; TESTNET_*_PROVEN remain false
capability: CAPABILITY_11_SECTION_11_12_8_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.8 Long-Running Autonomous Testnet Campaign V1

## Goal

Implement Master Runbook **§11.12.8 Long-running autonomous Testnet campaign**
as the next productive Testnet-progression residual after closed
`CAPABILITY_11_SECTION_11_12_7_KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_V1`.

This OWNER_GO authorizes **implementation / evidence binding only**. It
**reuses** Cap 11.6 fixture-only long-running campaign evidence contracts and
**binds** the closed §11.12.7 kill-switch/emergency predecessor. It produces a
deterministic campaign-evidence closure record with `NETWORK_EFFECT=NONE`,
`ORDER_EFFECT=NONE`, fail-closed runtime-gate / kill-switch / scope-escalation
refusals, and Cap 11.13 refusal. It does **not** start a productive Testnet
campaign, does not authorize network sessions or writes, does not submit
orders, does not activate Cap 11.6 adapters, does not activate the kill-switch
contract, does **not** claim any `TESTNET_*_PROVEN` / `TESTNET_EVIDENCE_VERIFIED`
flags, and does not start Cap 11.13.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
REFERENCE_ONLY=false
LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE_ALLOWED=true
CAP_11_6_LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_REUSE_ALLOWED=true
SECTION_11_12_7_PREDECESSOR_BINDING_REQUIRED=true
KILL_SWITCH_BINDING_REQUIRED=true
KILL_SWITCH_BINDING_STATUS=BOUND
ORDER_SEND_DISABLED=true
ORDERS_AUTHORIZED=false
ORDER_PATH_STARTED=false
ORDER_SUBMIT_PERFORMED=false
MUTATING_EXCHANGE_CALLS=false
NETWORK_WRITES_AUTHORIZED=false
NETWORK_WRITE_PERFORMED=false
LIFECYCLE_NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
TESTNET_ORDER_SUBMIT_PERFORMED=false
TESTNET_CAMPAIGN_STARTED=false
TESTNET_CAMPAIGN_COMPLETED=false
LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED=false
NETWORK_SESSION_STARTED=false
CAPABILITY_11_6_STARTED=false
KILL_SWITCH_CONTRACT_ACTIVATED=false
CAPABILITY_11_13_STARTED=false
SECTION_11_13_STARTED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
TESTNET_ORDER_LIFECYCLE_PROVEN=false
TESTNET_RECONCILIATION_PROVEN=false
TESTNET_RESTART_PROVEN=false
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=false
TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN=false
TESTNET_KILL_SWITCH_PROVEN=false
TESTNET_AUTONOMOUS_RECOVERY_PROVEN=false
TESTNET_EVIDENCE_VERIFIED=false
PATH_CLASS=LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE
LIFECYCLE_SOURCE=FIXTURE_ONLY
```

## In scope

- Binding closed §11.12.7 kill-switch/emergency-control predecessor
- Kill-switch binding retained (`KILL_SWITCH_BINDING_STATUS=BOUND`) without activation
- Reuse of Cap 11.6 long-running campaign evidence fixture paths
- Fail-closed campaign/runtime/kill-switch/scope-escalation refusals
- Explicit refusal of productive Testnet campaign start, network session, Cap 11.13
- Explicit refusal of `TESTNET_*_PROVEN` overclaims
- Evidence / verifier / contract tests

## Out of scope

- Productive long-running Testnet campaign execution
- Cap 11.6+ Testnet adapter activation / network trading session
- Cap 11.13 Live activation
- Network writes (POST/PUT/PATCH/DELETE) or exchange order submit
- Trading / risk / safety core mutation
- Claiming any §11.12 Testnet closure proven flags

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1` |
| Predecessor §11.12.7 | retained, unchanged |
| Cap 11.6 campaign evidence contracts | reused, unchanged |

## Safety claims

```text
ORDER_SEND_DISABLED=true
ORDERS_AUTHORIZED=false
NETWORK_WRITES_AUTHORIZED=false
NETWORK_WRITE_PERFORMED=false
LIFECYCLE_NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
TESTNET_ORDER_SUBMIT_PERFORMED=false
TESTNET_CAMPAIGN_STARTED=false
TESTNET_CAMPAIGN_COMPLETED=false
LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED=false
NETWORK_SESSION_STARTED=false
CAPABILITY_11_6_STARTED=false
KILL_SWITCH_CONTRACT_ACTIVATED=false
KILL_SWITCH_BINDING_STATUS=BOUND
CAPABILITY_11_13_STARTED=false
SECTION_11_13_STARTED=false
TESTNET_ORDER_LIFECYCLE_PROVEN=false
TESTNET_RECONCILIATION_PROVEN=false
TESTNET_RESTART_PROVEN=false
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=false
TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN=false
TESTNET_KILL_SWITCH_PROVEN=false
TESTNET_AUTONOMOUS_RECOVERY_PROVEN=false
TESTNET_EVIDENCE_VERIFIED=false
```

## Evidence

- Package: `docs/evidence/capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1/`
- Generator: `scripts/ops/generate_capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.py`
- Verifier: `scripts/ops/verify_capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.py`
- Tests: `tests/ops/test_capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.py`

## Activation

This capability is **not** productive Testnet campaign execution. Campaign
evidence closure remains fixture-only with `NETWORK_EFFECT=NONE`,
`ORDER_EFFECT=NONE`, `TESTNET_CAMPAIGN_STARTED=false`, and all
`TESTNET_*_PROVEN=false`. Separate Owner-GO is required before any productive
Testnet campaign execution or Cap 11.13 Live activation.
