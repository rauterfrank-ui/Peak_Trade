---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN_PRIVATE_WRITE_GATE_V1
status: active
scope: Phase 11 §11.12.8 ephemeral OKX EEA Demo XPerp campaign private-write gate; package ORDER_POST remains false; no auto campaign execute; no Live; no §11.13
capability: CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN_PRIVATE_WRITE_GATE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-10
---

# Capability — §11.12.8 OKX EEA Demo XPerp Campaign Private-Write Gate V1

## Goal

Provide a default-deny ephemeral private-write gate for the bound OKX EEA
Demo XPerp productive campaign path. Package &#47; binding
`ORDER_POST_AUTHORIZED=false` remains permanent. Mutation is allowed only
when `ephemeral_campaign_write_gate_pass=true` under the full runtime
precondition chain.

```text
VENUE=OKX_EEA_DEMO
ENVIRONMENT=DEMO
REST_HOST=https://eea.okx.com
INSTRUMENT_SCOPE_EXACT=BTC-USD_UM_XPERP-310328
CANONICAL_ORDER_SZ=0.0001
PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED=false
CANONICAL_OWNER_GO_SCOPE=EXECUTE_BOUNDED_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN
LEGACY_OWNER_GO_ALIASES=EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW|EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
OWNER_GO_ALONE_INSUFFICIENT=true
LIVE_AUTHORIZED=false
SECTION_11_13_STARTED=false
PRE_LIVE_CYBERSECURITY_GATE=NOT_PASSED
SECTION_11_12_8_STATUS=OPEN_OKX_EEA_DEMO_XPERP_CAMPAIGN_WRITE_PATH_READY_AWAITING_OWNER_EXECUTE
```

## Bound scope (exact)

| Field | Value |
| --- | --- |
| Venue | `OKX_EEA_DEMO` |
| Environment | `DEMO` |
| REST host | `eea.okx.com` |
| Demo marker | `x-simulated-trading: 1` (mandatory) |
| Instrument | `BTC-USD_UM_XPERP-310328` |
| Canonical sz | `0.0001` (bound minSz&#47;lotSz; no dynamic sizing policy) |
| Mutation endpoints | `&#47;api&#47;v5&#47;trade&#47;order`, `&#47;api&#47;v5&#47;trade&#47;cancel-order` |

## Required runtime chain (Owner-GO alone insufficient)

```text
enabled_and_armed
MODE_PRODUCTIVE_REAL_or_Testnet_binding
ephemeral_SecretRef
Hidden_Confirm_latch
Risk_Gate
Kill_Switch
Emergency_Gate
Account_Binding
Endpoint_Allowlist
bound_client
Live_hard_block
exact_XPerp_ephemeral_write_scope
```

## Explicit non-effects

```text
GATE_PACKAGE != CAMPAIGN_EXECUTE
GATE_PACKAGE != PERMANENT_ORDER_POST_AUTHORIZED
GATE_PACKAGE != LIVE_AUTHORIZED
GATE_PACKAGE != SECTION_11_13_START
LEGACY_GO_ALIAS != VENUE_OR_INSTRUMENT_EXPANSION
FURTHER_OKX_EEA_DEMO_ORDER_POSTS_AUTHORIZED_SWAP_CLOSEOUT != XPERP_PATH_BAN
BTC_USDT_SWAP_PATH_STATUS=CLOSED_DEPRECATED_HISTORICAL_EVIDENCE_ONLY
ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH=OKX_EEA_DEMO_XPERP
SWAP_RUNTIME_FALLBACK=false
SWAP_WRITE_AUTHORIZATION=false
XPERP_ONLY_ACTIVE_WRITE_SCOPE=true
```

## Productive owners

| Surface | Owner |
| --- | --- |
| Write gate | `ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1` |
| Contract tests | `tests&#47;ops&#47;test_section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.py` |

## Next step after merge

```text
CANONICAL_NEXT_STEP_AFTER_MERGE=OWNER_GO_EXECUTE_BOUNDED_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN_WITH_HIDDEN_CONFIRM_AND_SECRETREF_VAULT_RUNTIME
```

This package does not execute the campaign and must not place orders by itself.
