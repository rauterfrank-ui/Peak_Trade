---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_ACTIVATION_AND_EXECUTABLE_HANDOFF_V1
status: active
scope: Phase 11 §11.12.8 productive campaign RUN ACTIVATION + executable handoff — implementation only with end-to-end dry activation proof; no productive campaign start; no network&#47;orders&#47;credential plaintext; no §11.13
capability: CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_ACTIVATION_AND_EXECUTABLE_HANDOFF_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.8 Productive Campaign Run Activation And Executable Handoff V1

## Goal

Implement **one bounded end-to-end package** that closes the complete known
non-executable&#47;missing blocker set from the §11.12.8 audit and proves the
productive activation chain via
`END_TO_END_DRY_ACTIVATION_PROOF` without productive side effects.

This OWNER_GO authorizes **IMPLEMENTATION ONLY WITH DRY PROOF**:

```text
OWNER_GO=CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_ACTIVATION_AND_EXECUTABLE_HANDOFF_V1
SCOPE=IMPLEMENTATION_ONLY_WITH_END_TO_END_DRY_ACTIVATION_PROOF
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
LIVE_ORDER_EFFECT=NONE
SECTION_11_13_STARTED=false
CORE_LOGIC_CHANGE=false
```

## Complete blocker set closed

1. scoped OWNER_GO consumer
2. non-deprecated activation executor
3. authorization state transition
4. durable campaign enabled state
5. durable campaign armed state
8. SecretRef-only credential path
9. productive testnet account binding
18. PRODUCTIVE_CAMPAIGN_RUN_CONSUMER_V1 authorization handoff
19. network session entry boundary
22. execution evidence production
23. evidence sealing
24. campaign completion&#47;abort handling

## Preserved executable controls

Hidden confirm channel, confirm-token digest binding, config&#47;venue&#47;instrument&#47;
order-type&#47;max-position bindings, productive RiskGate &#47; KillSwitch &#47; emergency
control, testnet-only enforcement, live-path hard block, §11.13 isolation.

## Reuse (mandatory)

| Concern | Owner |
| --- | --- |
| Run consumer predecessor | `ops.section_11_12_8_productive_campaign_run_consumer_v1` |
| Terminal gate &#47; confirm &#47; risk &#47; kill-switch | terminal package `campaign_authorization_gate_v1` |
| Network-session GO boundary | Phase-9.2 Step-5 `network_session_go_v1` |
| Deprecated PATH&#47;EXECUTION&#47;RUN&#47;RUN_ACTIVATION wrappers | non-extendable residuals — do not extend |

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1` |
| Operator entrypoint | `scripts&#47;ops&#47;run_section_11_12_8_productive_campaign_run_activation_and_executable_handoff_operator_entrypoint_v1.py` |

## Activation

```text
enabled=false and armed=false by default
authorization_state=UNAUTHORIZED by default
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
NETWORK_SESSION_STARTED=false
ORDERS_AUTHORIZED=false
CONFIRM_TOKEN_ISSUANCE_ALLOWED=false
CONFIRM_TOKEN_CONSUMPTION_ALLOWED=false
```

A later separate Owner-GO is required for
`ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START`.
