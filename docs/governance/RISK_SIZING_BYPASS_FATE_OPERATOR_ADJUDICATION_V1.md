# Risk Sizing Bypass Fate Operator Adjudication V1

**Status:** BINDING per-BYPASS `operator_fate_adjudication` pins (docs + static contract only)  
**Date:** 2026-09-23  
**Obligation:** `OBL_B05_BYPASS_FATE_OPERATOR_ADJUDICATION_V1`  
**Workpackage:** `WP_B05_BYPASS_FATE_OPERATOR_ADJUDICATION_V1`  
**Machine contract:** [`config/governance/risk_sizing_bypass_fate_operator_adjudication_v1.json`](../../config/governance/risk_sizing_bypass_fate_operator_adjudication_v1.json)  
**Fate vocabulary (unchanged):** [`RISK_SIZING_BYPASS_FATE_VOCABULARY_AND_DECISION_AUTHORITY_FREEZE_V1.md`](RISK_SIZING_BYPASS_FATE_VOCABULARY_AND_DECISION_AUTHORITY_FREEZE_V1.md)  
**Fate implementation semantics:** [`RISK_SIZING_BYPASS_FATE_IMPLEMENTATION_CONTRACT_V1.md`](RISK_SIZING_BYPASS_FATE_IMPLEMENTATION_CONTRACT_V1.md)

```
RISK_SIZING_BYPASS_FATE_OPERATOR_ADJUDICATION_V1=true
SCOPED_OPERATOR_GO=true
INVENTORY_ONLY=true
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
OPERATOR_FATE_ADJUDICATION_EXECUTED=true
FATE_IMPLEMENTATION_EXECUTED=false
RUNTIME_REWIRE_EXECUTED=false
BYPASS_SET_CHANGED=false
CONSOLIDATION_STATUS=NOT_STARTED
CONVERSION_READY=false
C2_INPUT_AUTHORITIES=UNRESOLVED
NO_RUNTIME_REWIRE=true
NO_SIZING_MATH_CHANGE=true
PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
```

## Purpose

Assign exactly one allowed `operator_fate_adjudication` token per inventored BYPASS ID under `SCOPED_OPERATOR_GO`, using token-specific required evidence from the vocabulary freeze. No runtime rewire, conversion, C2 closure, or consolidation implementation.

## Adjudicated fates (summary)

| BYPASS ID | Fate |
|---|---|
| `BYPASS_CLASSIC_BACKTEST_DEFAULT` | `GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE` |
| `BYPASS_CORE_POSITION_SIZER` | `KEEP_PARALLEL_NON_CANONICAL` |
| `BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS` | `KEEP_PARALLEL_NON_CANONICAL` |
| `BYPASS_LIVE_SHADOW_POSITION_FRACTION` | `GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE` |
| `BYPASS_OFFLINE_EVAL_SIZING_CONTRACT` | `RESEARCH_OR_OFFLINE_SCOPE_ONLY` |

Per-ID epistemic evidence records live in the JSON contract (`evidence_record` with `CANONICAL_AUTHORITY`, `OBSERVED_CURRENT_EVIDENCE`, `ALREADY_ADJUDICATED`, `INTERPRETATION`, `UNKNOWN_CONFLICTING`).

## Explicit non-claims

- no runtime rewire / delete / disable / rebind implementation
- no sizing-math change
- no C2 input authority closure
- no `CONVERSION_READY` flip
- no repo-wide CRS owner promotion
- no BYPASS-set change
- Map `AUTHORITY` remains `NONE`
