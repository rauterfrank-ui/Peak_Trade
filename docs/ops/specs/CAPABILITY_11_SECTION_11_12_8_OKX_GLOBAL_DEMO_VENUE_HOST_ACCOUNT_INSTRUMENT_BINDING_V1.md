---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1
status: superseded_not_activated
scope: HISTORICAL §11.12.8 OKX Global Demo binding package (NO_ORDER; never activated). Active continuation authority moved to OKX EEA Demo XPerp §11.12.8.5.
capability: CAPABILITY_11_SECTION_11_12_8_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-10
---

# Capability — §11.12.8 OKX Global Demo Venue/Host/Account/Instrument Binding V1

## Goal

Prepare the canonical fail-closed binding package for continuing §11.12.8 on
**OKX Global Demo** after the OKX EEA Demo productive order path was closed as
`EXTERNAL_CAPABILITY_UNAVAILABLE`.

```text
OWNER_GO=OWNER_GO_AUTHORIZE_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_PACKAGE_NO_ORDER
VENUE=okx_global
ENVIRONMENT=DEMO
REST_HOST=https://openapi.okx.com
DEMO_MARKER_HEADER=x-simulated-trading:1
INSTRUMENT_SCOPE_EXACT=BTC-USDT-SWAP
INSTRUMENT_TYPE=SWAP
CREDENTIAL_CLASS=OKX_DEMO_TRADING_API_KEY_ONLY
FORBIDDEN_SILENT_FALLBACK=true
FORBIDDEN_GENERIC_SYMBOL_SUBSTITUTION=true
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
| Venue | `okx_global` |
| Environment | `DEMO` |
| REST host | `openapi.okx.com` |
| Demo marker | `x-simulated-trading: 1` (mandatory) |
| Instrument | `BTC-USDT-SWAP` (exact; no substitution) |
| Credential class | `OKX_DEMO_TRADING_API_KEY_ONLY` via SecretRef only |
| SecretRef | `secretref:&#47;&#47;vault&#47;peak-trade&#47;okx-global-demo-trading` |

## Shared-host compensating controls

`openapi.okx.com` is shared with Live. This package therefore requires **all** of:

1. mandatory Demo marker header;
2. Demo credential class only (Live and EEA classes hard-blocked);
3. exact instrument scope;
4. SecretRef-only credential path;
5. order-mutation endpoints hard-blocked;
6. no silent host / venue / instrument fallback.

Ambiguity fails closed (Cybersecurity V2.1 §4.3 / §19 / §20; Master §4.8.1).

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
| Binding package | `ops.section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1` |
| Contract tests | `tests/ops/test_section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1.py` |

## Next step after merge

```text
CANONICAL_NEXT_STEP_AFTER_MERGE_ROLE=HISTORICAL_POINTER_SUPERSEDED_BY_SECTION_11_12_8_5
HISTORICAL_NEXT_STEP_POINTER=OWNER_GO_EXECUTE_BOUNDED_NO_ORDER_PREFLIGHT_ON_OKX_GLOBAL_DEMO_BTC_USDT_SWAP
ACTIVE_CANONICAL_NEXT_STEP=OWNER_GO_EXECUTE_BOUNDED_SECTION_11_12_8_CONTINUATION_ON_OKX_EEA_DEMO_XPERP_NO_ORDER
```

This Global Demo package was prepared but **not activated**. Active §11.12.8
derivatives continuation is bound to OKX EEA Demo XPerp (§11.12.8.5). Do not
treat this package as the current active binding.
