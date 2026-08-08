---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_CONSUMER_V1
status: active
scope: Phase 11 §11.12.8 productive campaign RUN CONSUMER — implementation only; no productive execution; no network/orders/credential load; no §11.13
capability: CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_CONSUMER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.8 Productive Campaign Run Consumer V1

## Goal

Implement the **missing executable productive campaign RUN CONSUMER** for
Master Runbook **§11.12.8 Long-running autonomous Testnet campaign**, after the
merged terminal consumer
`CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_TERMINAL_V1`.

This OWNER_GO authorizes **IMPLEMENTATION ONLY**:

```text
IMPLEMENTATION_ONLY_FOR_MISSING_PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_CONSUMER=true
NO_PRODUCTIVE_RUN_EXECUTION=true
NO_NETWORK_EFFECT=true
NO_CREDENTIAL_LOAD=true
NO_ORDER_EFFECT=true
NO_LIVE_EFFECT=true
NO_SECTION_11_13=true
NO_NEW_WRAPPER_LAYER=true
TERMINAL_CONSUMER_ROLE_UNCHANGED=true
```

This package does **not** reinterpret the terminal as a productive runner. The
terminal hard-refuse role remains unchanged.

```text
RUN_CONSUMER_CANONICAL_ROLE=PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_CONSUMER
PRODUCTIVE_RUN_CONSUMER_PRESENT=true
PRODUCTIVE_RUN_EXECUTION_AUTHORIZED=false
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
CREDENTIAL_PLAINTEXT_LOADED=false
NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
LIVE_ORDER_EFFECT=NONE
SECTION_11_13_STARTED=false
CORE_LOGIC_CHANGE=false
```

## Reuse (mandatory)

| Concern | Owner |
| --- | --- |
| Terminal predecessor | `ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1` |
| Terminal authorization gate | same package `campaign_authorization_gate_v1` (Phase-9.2 confirm + RiskGate + KillSwitch + credential-scope) |
| Fixture residual | preserved via terminal predecessor |
| Historical PATH&#47;EXECUTION&#47;RUN&#47;RUN_ACTIVATION wrappers | non-extendable residuals — do not extend |

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.section_11_12_8_productive_campaign_run_consumer_v1` |
| Operator entrypoint | `scripts&#47;ops&#47;run_section_11_12_8_productive_campaign_run_consumer_operator_entrypoint_v1.py` |

## Activation

```text
PRODUCTIVE_RUN_EXECUTION_AUTHORIZED=false
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
NETWORK_SESSION_STARTED=false
ORDERS_AUTHORIZED=false
CONFIRM_TOKEN_ISSUANCE_ALLOWED=false
CONFIRM_TOKEN_CONSUMPTION_ALLOWED=false
```

## Next consumer

```text
NEXT_CONSUMER_CAPABILITY_ID=SEPARATE_OWNER_GO_REQUIRED_FOR_PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_ACTIVATION
```

A later separate Owner-GO is required before any productive campaign run
activation&#47;execution.
