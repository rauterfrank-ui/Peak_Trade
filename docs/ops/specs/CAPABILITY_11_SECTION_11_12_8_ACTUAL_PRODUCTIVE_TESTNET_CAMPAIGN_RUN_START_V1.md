---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START_V1
status: active
scope: Phase 11 §11.12.8 ACTUAL productive Testnet campaign RUN START — coherent package closing B01–B24; stubbed acceptance only in this OWNER_GO; no real network/orders/credentials; no §11.13
capability: CAPABILITY_11_SECTION_11_12_8_ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.8 ACTUAL Productive Testnet Campaign Run Start V1

## Goal

Implement **one coherent package** that closes audit blockers B01–B24 so that
after merge, a separate future OWNER_GO for
`EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW` can traverse the productive start
path without further architectural / governance / token HARD_STOPs.

This OWNER_GO authorizes **IMPLEMENTATION + STUBBED ACCEPTANCE ONLY**:

```text
OWNER_GO=CAPABILITY_11_SECTION_11_12_8_ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START_V1
AUTHORIZATION=IMPLEMENT_ONE_COHERENT_PACKAGE_CLOSE_ALL_B01_B24
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
LIVE_ORDER_EFFECT=NONE
SECTION_11_13_STARTED=false
CORE_LOGIC_CHANGE=false
ALL_B01_B24_CLOSED=true
PRE_MERGE_ACCEPTANCE_GATE=PASS
```

## Exact future productive OWNER_GO contract

```text
TOKEN=CAPABILITY_11_SECTION_11_12_8_ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START_V1
SCOPE=EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
AUTHORIZATION=EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
one_time_consume=true
productive_campaign_authorized=true
LIVE_AUTHORIZED=false
```

## Non-goals / preserved surfaces

- Do **not** extend deprecated PATH / EXECUTION / RUN / RUN_ACTIVATION wrappers.
- Do **not** turn the dry Activation-and-Executable-Handoff package into a
  productive executor; it remains dry-only.
- Terminal / run-consumer hard-refuse roles remain intact.
- No real credentials, real network, real orders, or §11.13 in this GO.

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1` |
| Operator entrypoint | `scripts&#47;ops&#47;run_section_11_12_8_actual_productive_testnet_campaign_run_start_operator_entrypoint_v1.py` |

## Next step after merge

```text
NEXT_CONSUMER_CAPABILITY_ID=SEPARATE_OWNER_GO_REQUIRED_FOR_EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
```

A separate Owner-GO is required before any **real** productive Testnet campaign
run (non-stubbed network side effects).
