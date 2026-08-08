---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_V1
status: deprecated_non_extendable_wrapper_residual
scope: Phase 11 §11.12.8 productive Testnet campaign RUN ACTIVATION — historical wrapper residual; superseded by TERMINAL consumer; do not extend
capability: CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.8 Productive Testnet Campaign Run Activation V1

## Goal

Implement the productive Testnet campaign **RUN ACTIVATION** surface after the
closed run package
`CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_V1`
(bound to merge SHA `ca5ffd404ab6afd5af3e79ec583d0a07c0b596b7`).

This OWNER_GO authorizes **IMPLEMENTATION_ONLY**. `RUN_AUTHORIZED=false` and
`ACTIVATION_AUTHORIZED=false`. It does **not** activate a productive campaign,
start a network session, submit orders, mint/consume Hidden Confirm tokens,
or start Cap 11.13.

```text
FIXTURE_PROOF = Cap 11 §11.12.8 fixture residual (preserved)
PRODUCTIVE_TESTNET_PATH = path package (preserved)
PRODUCTIVE_TESTNET_EXECUTION = execution package (preserved)
PRODUCTIVE_TESTNET_RUN = run package (preserved; predecessor)
PRODUCTIVE_TESTNET_RUN_ACTIVATION = this package (activation surface present)
PRODUCTIVE_TESTNET_RUN_ACTIVATION_GO = later separate Owner-GO (out of scope)

PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_IMPLEMENTED=true
PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_PRESENT=true
PRODUCTIVE_ACTIVATION_ENTRYPOINT_PRESENT=true
RUN_AUTHORIZED=false
ACTIVATION_AUTHORIZED=false
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
LIVE_ORDER_EFFECT=NONE
SECTION_11_13_STARTED=false
CORE_LOGIC_CHANGE=false
```

## In scope

- Bind run predecessor without mutation (SHA-bound to `ca5ffd40…`)
- Activation-gate evaluation reusing run / execution / path start-gate /
  confirm / kill-switch / emergency / risk scopes
- Structural `activation_may_start` for a later activation GO
- Explicit productive activation entrypoint that hard-refuses activation
  in this capability
- Hard refusal of campaign start / network / orders / Live / §11.13 /
  future-activation-GO consumption
- Evidence / verifier / contract tests

## Out of scope

- Productive Testnet campaign activation / start / completion
- Network writes or exchange order submit
- Hidden Confirm mint / consume / plaintext exposure
- Cap 11.13 Live activation
- Weakening path / execution / run packages
- Trading / risk / safety core mutation

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1` |
| Run predecessor | `ops.capability_11_section_11_12_8_productive_testnet_campaign_run_v1` (unchanged) |
| Operator entrypoint | `scripts&#47;ops&#47;run_capability_11_section_11_12_8_productive_testnet_campaign_run_activation_operator_entrypoint_v1.py` |

## Activation

```text
RUN_AUTHORIZED=false
ACTIVATION_AUTHORIZED=false
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
NETWORK_SESSION_STARTED=false
ORDERS_AUTHORIZED=false
FUTURE_ACTIVATION_GO_CONSUMED=false
CONFIRM_TOKEN_ISSUANCE_ALLOWED=false
CONFIRM_TOKEN_CONSUMPTION_ALLOWED=false
```

A later separate Owner-GO is required before any productive campaign run activation.
