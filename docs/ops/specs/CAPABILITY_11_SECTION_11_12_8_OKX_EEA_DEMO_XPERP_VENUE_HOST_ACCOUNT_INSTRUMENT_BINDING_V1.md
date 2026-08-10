---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1
status: active
scope: Phase 11 §11.12.8 rebind active Demo derivatives path to OKX EEA Demo XPerp; NO_ORDER; no credential load; no Live; no §11.13
capability: CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-10
---

# Capability — §11.12.8 OKX EEA Demo XPerp Venue/Host/Account/Instrument Binding V1

## Goal

Rebind the **active** canonical §11.12.8 Demo derivatives path to the
productively proven OKX EEA Demo XPerp instrument after private READ-only
capability proof. This is **not** order authority and does **not** activate
venue execution.

```text
OWNER_GO=OWNER_GO_CANONICAL_EEA_XPERP_REBINDING_AND_SECTION_11_12_8_CONTINUATION_PREP_NO_ORDER
VENUE=OKX_EEA_DEMO
ENVIRONMENT=DEMO
REST_HOST=https://eea.okx.com
DEMO_MARKER_HEADER=x-simulated-trading:1
INSTRUMENT_SCOPE_EXACT=BTC-USD_UM_XPERP-310328
INSTRUMENT_TYPE=FUTURES
RULE_TYPE=xperp
CREDENTIAL_CLASS=OKX_EEA_DEMO_TRADING_API_KEY_ONLY
FORBIDDEN_SILENT_FALLBACK=true
FORBIDDEN_GENERIC_SYMBOL_SUBSTITUTION=true
LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_REMOVED=true
OKX_GLOBAL_DEMO_ACTIVE_BINDING=false
ORDER_POST_AUTHORIZED=false
VENUE_ACTIVATED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
SECTION_11_13_STARTED=false
PRE_LIVE_CYBERSECURITY_GATE=NOT_PASSED
CORE_LOGIC_CHANGE=false
```

## Bound scope (exact)

| Field | Value |
| --- | --- |
| Venue | `OKX_EEA_DEMO` |
| Environment | `DEMO` |
| REST host | `eea.okx.com` |
| Demo marker | `x-simulated-trading: 1` (mandatory) |
| Instrument | `BTC-USD_UM_XPERP-310328` (exact; no substitution) |
| Instrument type | `FUTURES` |
| Rule type | `xperp` |
| Credential class | `OKX_EEA_DEMO_TRADING_API_KEY_ONLY` via SecretRef only |
| SecretRef | `secretref:&#47;&#47;vault&#47;peak-trade&#47;testnet-demo` |

## Historical non-active paths

OKX Global Demo and `BTC-USDT-SWAP` packages&#47;evidence remain **historical**
forensics only. Their existence must not be rewritten and must not become the
active §11.12.8 binding again without a new scoped Owner-GO.

Bound private READ-only proof pointer (immutable; not rewritten by this package):

`evidence&#47;ops&#47;section_11_12_8_retry_okx_eea_private_ro_xperp_verify_no_order_v1&#47;20260810T165847Z&#47;`

## Explicit non-effects

```text
BINDING_PACKAGE != VENUE_ACTIVATION
BINDING_PACKAGE != TESTNET_AUTHORIZED
BINDING_PACKAGE != PRODUCTIVE_PREFLIGHT
BINDING_PACKAGE != ORDER_AUTHORIZATION
BINDING_PACKAGE != PRE_LIVE_CYBERSECURITY_GATE_PASS
BINDING_PACKAGE != SECTION_11_13_START
```

## Productive owners

| Surface | Owner |
| --- | --- |
| Binding package | `ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1` |
| Contract tests | `tests&#47;ops&#47;test_section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.py` |

## Next step after merge

```text
CANONICAL_NEXT_STEP_AFTER_MERGE=OWNER_GO_EXECUTE_BOUNDED_SECTION_11_12_8_CONTINUATION_ON_OKX_EEA_DEMO_XPERP_NO_ORDER
```

This package does not load credentials and must not place orders.
