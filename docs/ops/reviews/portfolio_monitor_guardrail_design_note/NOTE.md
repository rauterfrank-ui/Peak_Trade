# PORTFOLIO MONITOR GUARDRAIL DESIGN NOTE

## Purpose
Define a docs-first guardrail design note for the `portfolio_monitor` balance semantics hotspot before any runtime mutation.

## Context
Known hotspot:
- `balance.get("free", balance.get("cash"))`

This is decision-adjacent because it can blur:
- free balance
- generic cash balance
- usable decision-grade capacity

## Guardrail Intent
Future logic should avoid silently widening balance semantics when `free` is absent.

## Proposed Design Direction
1. distinguish explicitly between:
   - reported free-like value
   - generic cash-like fallback
   - decision-grade reconciled balance
2. prevent implicit upgrade of fallback cash into free/usable capacity
3. fail toward caution when balance semantics are ambiguous
4. surface operator-visible warning/block semantics when the boundary is unclear

## Candidate Guardrail States
- `balance_semantics_clear`
- `balance_semantics_warning`
- `balance_semantics_blocked`

## Candidate Behavior
### Clear
- explicit free/reconciled semantics present
- monitoring may continue normally

### Warning
- fallback path used
- capacity interpretation should remain conservative
- operator-visible warning recommended

### Blocked
- semantic ambiguity overlaps with decision use
- no new exposure increase should rely on this balance view

## Non-Goals
- no runtime changes in this slice
- no paper/shadow/testnet mutation
- no live-expansion work

## Recommended Next Slice
- portfolio_monitor_guardrail_implementation_review
