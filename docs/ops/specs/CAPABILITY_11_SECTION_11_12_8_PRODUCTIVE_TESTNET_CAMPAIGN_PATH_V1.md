---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_TESTNET_CAMPAIGN_PATH_V1
status: active
scope: Phase 11 §11.12.8 productive Testnet campaign PATH — gates only; no campaign start; no network/orders; no §11.13
capability: CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_TESTNET_CAMPAIGN_PATH_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.8 Productive Testnet Campaign Path V1

## Goal

Add a **strictly separate** productive Testnet campaign **PATH** after the closed
fixture-only residual
`CAPABILITY_11_SECTION_11_12_8_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_V1`.

This OWNER_GO authorizes **implementation and local verification only**. It does
**not** authorize productive Testnet campaign execution, network sessions, order
submit, credential plaintext load, or Cap 11.13 Live activation.

```text
FIXTURE_PROOF = predecessor Cap 11 §11.12.8 fixture evidence (preserved)
PRODUCTIVE_TESTNET_CAPABILITY = this path package (gates present)
PRODUCTIVE_TESTNET_EXECUTION = later separate Owner-GO (out of scope)

PRODUCTIVE_TESTNET_CAPABILITY_IMPLEMENTED=true
PRODUCTIVE_TESTNET_CAMPAIGN_PATH_PRESENT=true
PRODUCTIVE_TESTNET_EXECUTION_AUTHORIZED=false
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
SECTION_11_13_STARTED=false
CORE_LOGIC_CHANGE=false
```

## In scope

- Productive §11.12.8 preflight / start-gate evaluation
- Testnet-only + credential-scope gates
- Owner-authorization binding
- Hidden-confirm digest binding (no plaintext / argv / env leak)
- Kill-switch + emergency-control operational preconditions (reuse §11.12.7 / Cap 11.5)
- Risk / instrument / order-type scope gates from canonical authority
- Fail-closed refusals for Live, §11.13, execution, network, orders
- Evidence / verifier / contract tests

## Out of scope

- Productive Testnet campaign start / completion
- Network writes or exchange order submit
- Cap 11.13 Live activation
- Weakening or removing fixture §11.12.8 proof
- Trading / risk / safety core mutation
- Parameter / instrument / order-type expansion

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1` |
| Fixture predecessor | `ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1` (unchanged) |
| Kill-switch / emergency | Cap 11.5 / §11.12.7 contracts reused |

## Canonical authority bounds (no expansion)

```text
runtime_mode=TESTNET
venue=OKX
instrument_scope=BTC-USDT-SWAP
allowed_order_types=LIMIT
position_count_limit=1
```

## Activation

```text
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
PRODUCTIVE_TESTNET_EXECUTION_AUTHORIZED=false
NETWORK_SESSION_STARTED=false
ORDERS_AUTHORIZED=false
```

A later separate Owner-GO is required before any productive campaign execution.
