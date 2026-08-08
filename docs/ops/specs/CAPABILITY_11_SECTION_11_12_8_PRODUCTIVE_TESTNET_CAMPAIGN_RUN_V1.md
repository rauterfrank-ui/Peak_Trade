---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_V1
status: active
scope: Phase 11 §11.12.8 productive Testnet campaign RUN — implementation only; no campaign start; no network/orders; no §11.13
capability: CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.8 Productive Testnet Campaign Run V1

## Goal

Implement the productive Testnet campaign **RUN** surface after the closed
execution package
`CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_TESTNET_CAMPAIGN_EXECUTION_V1`.

This OWNER_GO authorizes **IMPLEMENTATION_ONLY**. `RUN_AUTHORIZED=false`.
It does **not** start a productive campaign, network session, order submit,
consume a future run GO, or Cap 11.13.

```text
FIXTURE_PROOF = Cap 11 §11.12.8 fixture residual (preserved)
PRODUCTIVE_TESTNET_PATH = path package (preserved)
PRODUCTIVE_TESTNET_EXECUTION = execution package (preserved)
PRODUCTIVE_TESTNET_RUN = this package (run surface present)
PRODUCTIVE_TESTNET_RUN_ACTIVATION = later separate Owner-GO (out of scope)

PRODUCTIVE_TESTNET_CAMPAIGN_RUN_IMPLEMENTED=true
PRODUCTIVE_TESTNET_CAMPAIGN_RUN_SURFACE_PRESENT=true
RUN_AUTHORIZED=false
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
LIVE_ORDER_EFFECT=NONE
SECTION_11_13_STARTED=false
CORE_LOGIC_CHANGE=false
```

## In scope

- Bind execution predecessor without mutation
- Run-gate evaluation reusing execution / path start-gate / confirm / kill-switch / emergency / risk scopes
- Structural `run_may_start` for a later activation GO
- Explicit run entrypoint that hard-refuses campaign start in this capability
- Hard refusal of network / orders / Live / §11.13 / future-run-GO consumption
- Evidence / verifier / contract tests

## Out of scope

- Productive Testnet campaign start / completion
- Network writes or exchange order submit
- Consuming a future Owner run-activation GO
- Cap 11.13 Live activation
- Weakening path or execution packages
- Trading / risk / safety core mutation

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_section_11_12_8_productive_testnet_campaign_run_v1` |
| Execution predecessor | `ops.capability_11_section_11_12_8_productive_testnet_campaign_execution_v1` (unchanged) |

## Activation

```text
RUN_AUTHORIZED=false
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
NETWORK_SESSION_STARTED=false
ORDERS_AUTHORIZED=false
FUTURE_RUN_GO_CONSUMED=false
```

A later separate Owner-GO is required before any productive campaign run activation.
