# PORTFOLIO MONITOR GUARDRAIL IMPLEMENTATION REVIEW

## Purpose
Review how a future guardrail could be implemented around the `portfolio_monitor` balance semantics hotspot, without changing runtime behavior in this slice.

## Scope
- implementation-adjacent review only
- no runtime mutation
- no paper/shadow/testnet disturbance

## Known Hotspot
Current hotspot:
- `balance.get("free", balance.get("cash"))`

Known design direction:
- `balance_semantics_clear`
- `balance_semantics_warning`
- `balance_semantics_blocked`

## Implementation Review Questions
1. Where should semantic classification happen?
2. Should classification live inside `portfolio_monitor` or at an upstream balance-normalization boundary?
3. What operator-visible signal should be emitted when fallback semantics are used?
4. What should later runtime logic avoid doing when semantics are warning/blocked?

## Preferred Design Direction
- keep classification logic explicit
- do not silently upgrade `cash` fallback into free/usable capacity
- prefer one narrow classification point rather than many scattered checks
- make warning/blocked states observable before any decision-adjacent use

## Candidate Implementation Shapes
### A. Local Classification in portfolio_monitor
Pros:
- smallest local surface
- hotspot addressed directly

Cons:
- semantics remain embedded near one consumer
- less reusable if other consumers appear later

### B. Upstream Balance Normalization Layer
Pros:
- cleaner separation of raw vs classified balance semantics
- reusable for later consumers

Cons:
- broader future change surface
- should not be attempted in this docs-only slice

## Recommended Review Outcome
If/when runtime work is considered later:
- prefer an explicit classification layer or helper
- preserve warning/blocked semantics
- ensure operator-visible state exists before capacity-like interpretation

## Non-Goals
- no runtime implementation in this slice
- no live-expansion work
- no disturbance to paper/shadow/testnet stability

## Recommended Next Slice
- balance_semantics_guardrail_stub
