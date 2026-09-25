# Risk Sizing — Full-Core Account Equity Authority Owner Ratification v1

**Status:** BINDING scoped Owner-GO ratification (docs + static contract only)  
**Date:** 2026-09-25  
**Obligation:** `OBL_B05_ACCOUNT_EQUITY_AUTHORITY_OWNER_FULL_CORE_TRACK_RATIFICATION_V1`  
**Machine contract:** [`config/governance/risk_sizing_account_equity_authority_owner_full_core_track_ratification_v1.json`](../../config/governance/risk_sizing_account_equity_authority_owner_full_core_track_ratification_v1.json)  
**Baseline:** `origin/main @ acb6e340a0ecafcba2bc9fee579e17732dd61277`

```
RISK_SIZING_ACCOUNT_EQUITY_AUTHORITY_OWNER_FULL_CORE_TRACK_RATIFICATION_V1=true
OWNER_GO=OWNER_GO_RATIFY_B05_ACCOUNT_EQUITY_AUTHORITY_OWNER_FULL_CORE_TRACK_V1
OWNER_GO_STATUS=CONSUMED
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
FULL_CORE_ACCOUNT_EQUITY_AUTHORITY_OWNER_RATIFIED=true
ACCOUNT_EQUITY_AUTHORITY_OWNER=ops.governed_productive_account_equity_authority_producer_v1
DIMENSION_ID=RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING
UNIT_CLASS=CAPITAL_CURRENCY_SCALAR_USDC_SETTLEMENT
SCOPE_TRACK=FULL_CORE
ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=false
GOVERNED_PRODUCER_CREATED=false
PRODUCER_IMPLEMENTATION_PRESENT=false
OBSERVATION_IS_NOT_AUTHORITY=true
MAPPING_IS_NOT_OWNER_CLOSURE=true
RATIFICATION_IS_NOT_IMPLEMENTATION=true
COMPANION_EQUITY_HANDOFF_AUTHORIZED=false
COMPANION_HANDOFF_STATUS=NO_CONVERSION_HANDOFF_ON_COMPANION_PATH
C2_EQUITY_DOMAIN_VERDICT=PARTIAL
C2_EQUITY_GATE_FULL_CORE_OWNER=RATIFIED
C2_EQUITY_GATE_COMPANION=UNRESOLVED
CONVERSION_READY=false
```

## Owner decision (consumed)

For the **Full-Core track** only, B05 `ACCOUNT_EQUITY_AUTHORITY_OWNER` is ratified to:

`ops.governed_productive_account_equity_authority_producer_v1`

**Scope:** `RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING` in `CAPITAL_CURRENCY_SCALAR_USDC_SETTLEMENT`.

This supersedes the prior B05 pin `ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED` **for this scope only**. Historical Runbook blocks that recorded `UNRESOLVED` under earlier Owner-GOs remain historical; this additive ratification block is authoritative for Full-Core B05 owner assignment.

## Explicit non-claims

- No Companion Shadow/Live equity handoff to `signal_to_orders`
- No Fraction→Units conversion
- No Reference Price or Instrument Metadata owner assignment
- No repo-wide `CANONICAL_RISK_SIZING_OWNER`
- No bypass consolidation
- No Live / external-effect gate relaxation
- Ratification does **not** assert `GOVERNED_PRODUCER_CREATED=true` or `PRODUCER_IMPLEMENTATION_PRESENT=true`

## C2 mechanical reevaluation

Companion C2 census: `ACCOUNT_EQUITY_AVAILABLE_CAPITAL` → **PARTIAL** (Full-Core owner ratified; Companion path still `REQUIRED_INPUT_MISSING`).  
`C2_STATUS` remains **UNRESOLVED**; `CONVERSION_READY` remains **false**.

## Binding surfaces

Listed in the machine contract `binding_surfaces_updated` array (B05 freeze, C2 contracts, Runbook additive block, current-system interaction map).
