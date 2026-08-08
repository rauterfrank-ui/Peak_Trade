---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_REAL_PRODUCTIVE_TESTNET_EXECUTE_PATH_UNLOCK_V1
status: active
scope: Phase 11 §11.12.8 unlock real productive Testnet execute path end-to-end; pre-merge no network/orders; no §11.13; after merge EXECUTE is canonical next step
capability: CAPABILITY_11_SECTION_11_12_8_REAL_PRODUCTIVE_TESTNET_EXECUTE_PATH_UNLOCK_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.8 Real Productive Testnet Execute Path Unlock V1

## Goal

Make the already-authorized §11.12.8 productive Testnet campaign runtime path
**actually executable end-to-end** by removing implementation-only refusals,
binding a real SecretRef vault resolver, binding a real Testnet HTTP client,
adding a real operator EXECUTE entrypoint, and updating the Master Runbook so
that after merge `EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW` is the explicit
canonical next Owner-authorized Testnet runtime action.

```text
OWNER_GO=CAPABILITY_11_SECTION_11_12_8_REAL_PRODUCTIVE_TESTNET_EXECUTE_PATH_UNLOCK_V1
AUTHORIZATION=IMPLEMENT_ONE_COHERENT_PACKAGE_UNLOCK_REAL_EXECUTE_PATH
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
PRE_MERGE_REAL_NETWORK_EFFECT=false
PRE_MERGE_ORDER_EFFECT=false
LIVE_ORDER_EFFECT=NONE
SECTION_11_13_STARTED=false
CORE_LOGIC_CHANGE=false
AUTHORIZED_RUNTIME_PATH_IMPLEMENTATION_ONLY=false
NO_ADDITIONAL_IMPLEMENTATION_GO_REQUIRED_BEFORE_EXECUTE=true
```

## Governance after merge (binding)

```text
CANONICAL_NEXT_STEP_AFTER_MERGE=SEPARATE_OWNER_GO_EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
REQUEST_MATCHES_CANONICAL_NEXT_STEP=true
AUTHORIZATION_REQUIRED=PRESENT_OWNER_GO_EXECUTE
MODE_PRODUCTIVE_REAL_PERMITTED_FOR_TESTNET_ONLY=true
SECRETREF_AND_HIDDEN_CONFIRM_ARE_RUNTIME_PRECONDITIONS_ONLY=true
LIVE_HARD_BLOCK_PRESERVED=true
SECTION_11_13_STARTED=false
```

No additional implementation GO, governance unlock PR, or capability PR is
required before a scoped Owner `EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW`.

## Required final runtime chain

```text
OWNER_GO_EXECUTE
→ ACTIVATION_ENABLED_ARMED
→ TESTNET_AUTHORIZED
→ PRODUCTIVE_SECRETREF_RESOLVER
→ EPHEMERAL_SECRET_LOAD
→ RISK_GATE
→ KILL_SWITCH
→ EMERGENCY_CONTROL
→ HIDDEN_CONFIRM_SINGLE_USE
→ PRODUCTIVE_REAL_CONSUMER
→ PRODUCTIVE_REAL_EXECUTOR
→ TESTNET_ACCOUNT_BINDING
→ ENDPOINT_ALLOWLIST
→ BOUND_REAL_TESTNET_HTTP_CLIENT
→ NETWORK_SESSION_ENTRY
→ FIRST_PERMITTED_TESTNET_SIDE_EFFECT
→ CAMPAIGN_RUNNING
→ EXECUTION_EVIDENCE
→ EVIDENCE_SEAL
→ COMPLETED_OR_ABORTED
```

## Productive owners

| Surface | Owner |
| --- | --- |
| Unlock package | `ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1` |
| Real execute entrypoint | `scripts&#47;ops&#47;run_section_11_12_8_real_productive_testnet_execute_operator_entrypoint_v1.py` |
| Predecessor start package | `ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1` |

## Pre-merge boundary

Pre-merge acceptance proves the real path is constructible and reaches the
network send boundary with `wire_send_enabled=false`. It must not open sockets,
submit orders, start a productive campaign, or start §11.13.

## Next step after merge

```text
NEXT_CONSUMER_CAPABILITY_ID=SEPARATE_OWNER_GO_EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
```

SecretRef material and single-use hidden confirm remain **runtime
preconditions** for that Owner EXECUTE, not future governance dependencies.
