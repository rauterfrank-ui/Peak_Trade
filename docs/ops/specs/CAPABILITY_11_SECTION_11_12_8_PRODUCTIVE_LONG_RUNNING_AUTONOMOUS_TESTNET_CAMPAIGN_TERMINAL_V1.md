---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_TERMINAL_V1
status: active
scope: Phase 11 §11.12.8 TERMINAL productive consumer — implementation only; no productive run; no network/orders/credential load; no §11.13; NO new wrapper layer
capability: CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_TERMINAL_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.8 Terminal Productive Long-Running Autonomous Testnet Campaign V1

## Goal

Implement the **single terminal productive consumer** for Master Runbook
**§11.12.8 Long-running autonomous Testnet campaign**.

This OWNER_GO authorizes **ARCHITECTURE IMPLEMENTATION ONLY**:

```text
NO_PRODUCTIVE_RUN=true
NO_NETWORK_EFFECT=true
NO_CREDENTIAL_LOAD=true
NO_ORDER_EFFECT=true
NO_LIVE_EFFECT=true
NO_SECTION_11_13=true
NO_NEW_WRAPPER_LAYER=true
```

This package terminates the PATH / EXECUTION / RUN / RUN_ACTIVATION wrapper
loop. It does **not** start a productive campaign.

```text
TERMINAL_CONSUMER_CANONICAL_ROLE=TERMINAL_PRODUCTIVE_CONSUMER_SECTION_11_12_8
NEW_WRAPPER_LAYER_CREATED=false
TESTNET_EXECUTION_PORT_CONSTRUCTIBLE=true
TESTNET_EXECUTION_PORT_REACHABLE_UNDER_AUTHORIZED_TERMINAL=true
CREDENTIAL_LOAD_IMPLEMENTED=true
CREDENTIAL_PLAINTEXT_LOADED=false
PRODUCTIVE_RUN_STARTED=false
NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
LIVE_ORDER_EFFECT=NONE
SECTION_11_13_STARTED=false
CORE_LOGIC_CHANGE=false
```

## Reuse (mandatory)

| Concern | Owner |
| --- | --- |
| Hidden Confirm / Real-TTY / Delegated | `ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1` (+ Step-6 hidden PTY) |
| Risk gate | `src.ops.gates.risk_gate` |
| Kill switch | `src.risk_layer.kill_switch.core.KillSwitch` |
| Port declaration | Cap 11.1 `execution_ports_v1` (construction remains forbidden in Cap 11.1) |
| Adapter anti-corruption | Cap 11.4 venue adapter contracts (construction remains forbidden in Cap 11.4) |
| Fixture predecessor | `ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1` |

## Productive owners

| Surface | Owner |
| --- | --- |
| Terminal package | `ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1` |
| Operator entrypoint | `scripts/ops/run_section_11_12_8_productive_long_running_autonomous_testnet_campaign_operator_entrypoint_v1.py` |

## Non-extendable wrapper residuals

The following remain historical and **must not** be extended with further
wrapper layers:

- `capability_11_section_11_12_8_productive_testnet_campaign_path_v1`
- `capability_11_section_11_12_8_productive_testnet_campaign_execution_v1`
- `capability_11_section_11_12_8_productive_testnet_campaign_run_v1`
- `capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1`

## Next consumer

```text
NEXT_CONSUMER_CAPABILITY_ID=SEPARATE_OWNER_GO_REQUIRED_FOR_PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN
```

A later separate Owner-GO is required before any productive campaign run.
