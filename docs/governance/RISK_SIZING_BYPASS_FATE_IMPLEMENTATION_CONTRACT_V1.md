# Risk Sizing Bypass Fate Implementation Contract V1

**Status:** BINDING fate-implementation **semantics and completion rules** (docs + static contract only)  
**Date:** 2026-09-23  
**Obligation:** `OBL_B05_BYPASS_FATE_IMPLEMENTATION_CONTRACT_V1`  
**Workpackage:** `WP_B05_BYPASS_FATE_IMPLEMENTATION_CONTRACT_V1`  
**Machine contract:** [`config/governance/risk_sizing_bypass_fate_implementation_contract_v1.json`](../../config/governance/risk_sizing_bypass_fate_implementation_contract_v1.json)  
**Adjudicated fates (authority):** [`RISK_SIZING_BYPASS_FATE_OPERATOR_ADJUDICATION_V1.md`](RISK_SIZING_BYPASS_FATE_OPERATOR_ADJUDICATION_V1.md)

```
RISK_SIZING_BYPASS_FATE_IMPLEMENTATION_CONTRACT_V1=true
SCOPED_OPERATOR_GO=true
INVENTORY_ONLY=true
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
FATE_IMPLEMENTATION_SEMANTICS_DEFINED=true
FATE_IMPLEMENTATION_EXECUTED=false
PER_BYPASS_FATE_IMPLEMENTATION_EXECUTED_COUNT=0
RUNTIME_MUTATION_EXECUTED=false
CONVERSION_READY=false
C2_INPUT_AUTHORITIES=UNRESOLVED
CANONICAL_RISK_SIZING_OWNER=UNRESOLVED
CONSOLIDATION_STATUS=NOT_STARTED
NO_RUNTIME_REWIRE=true
NO_SIZING_MATH_CHANGE=true
PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED=false
```

## Purpose

Define **what counts as implemented** for each of the five PR #6755 adjudicated bypass fates: minimum requirements, runtime-mutation boundaries, provenance/evidence effects, forbidden implicit effects, and machine-checkable completion evidence. This slice does **not** mark any bypass implemented and does **not** mutate runtime.

## Bound bypass set (adjudicated fates)

| BYPASS ID | Adjudicated fate |
|---|---|
| `BYPASS_CLASSIC_BACKTEST_DEFAULT` | `GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE` |
| `BYPASS_CORE_POSITION_SIZER` | `KEEP_PARALLEL_NON_CANONICAL` |
| `BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS` | `KEEP_PARALLEL_NON_CANONICAL` |
| `BYPASS_LIVE_SHADOW_POSITION_FRACTION` | `GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE` |
| `BYPASS_OFFLINE_EVAL_SIZING_CONTRACT` | `RESEARCH_OR_OFFLINE_SCOPE_ONLY` |

Per-ID and per-token fields live in the JSON contract (`bypass_fate_implementations`, `fate_token_implementation_semantics`, `global_completion_rule`).

## Global completion

`FATE_IMPLEMENTATION_EXECUTED=true` is allowed only when **all five** per-bypass entries satisfy their completion evidence and the global conjunction in `global_completion_rule` — not in this semantics-only slice.

## Explicit non-claims

- no per-bypass implementation execution in S0  
- no runtime rewire / disable / delete / deauthorize  
- no sizing-math or CRS scope change  
- no C2 closure or `CONVERSION_READY` flip  
- no repo-wide canonical sizing owner  
- Map `AUTHORITY` remains `NONE`
