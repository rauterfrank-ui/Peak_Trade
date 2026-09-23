# Risk Sizing C2 Input Authority Closure v1

**Status:** BINDING C2 census + closure verdict (docs + static contract only)  
**Date:** 2026-09-23  
**Obligation:** `OBL_B05_C2_INPUT_AUTHORITY_CLOSURE_V1`  
**Workpackage:** `BOUNDED_WP_C2_INPUT_AUTHORITY_CLOSURE_V1`  
**Machine contract:** [`config/governance/risk_sizing_c2_input_authority_closure_v1.json`](../../config/governance/risk_sizing_c2_input_authority_closure_v1.json)

```
RISK_SIZING_C2_INPUT_AUTHORITY_CLOSURE_V1=true
INVENTORY_ONLY=true
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
C2_STATUS=UNRESOLVED
C2_INPUT_AUTHORITIES=UNRESOLVED
C2_CLOSURE_RULE_SATISFIED=false
C2_INPUT_SET_COMPLETE_PROVEN=true
C2_REQUIRED_INPUT_COUNT=3
CONVERSION_READY=false
B05_FATE_PHASE_STATUS=CLOSED
FATE_IMPLEMENTATION_EXECUTED=true
```

## C2 definition (CURRENT)

**C2** in B05 markers (`C2_INPUT_AUTHORITIES`) denotes **Companion Shadow/Live Fraction→Units conversion input authorities** — not Runbook Confirmation C1/C2/C3 observation state.

Canonical consumer chain:

- `PATH_SHADOW_COMPANION` / `PATH_LIVE_COMPANION` → `ExecutionPipeline.signal_to_orders` (pass-through; no conversion math on CURRENT main)

Required input set is proven **complete at three families** via `required_for_companion_conversion` in [`RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1.md`](RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1.md). No fourth `required_for_companion_conversion` input exists on CURRENT main.

## Closure verdict

`C2_STATUS=CLOSED` is **not** satisfied on CURRENT evidence: no required Companion-path input is `PROVEN_CURRENT`; authority owners remain `UNRESOLVED`; `CONVERSION_READY=false` unchanged.

Full-Core account-equity source→semantic mapping pins (Runbook) do **not** close Companion C2 while `ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED` and Companion provenance remains `REQUIRED_INPUT_MISSING`.

## Explicit non-claims

- no Fraction→Units conversion math  
- no Companion caller rewire  
- no `CONVERSION_READY=true`  
- no B05 bypass fate reinterpretation  
- no repo-wide canonical sizing owner  
- Map `AUTHORITY=NONE`
