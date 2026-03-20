# PORTFOLIO MONITOR BALANCE SEMANTICS REVIEW

## Purpose
Document the balance-semantics hotspot in `src/live/portfolio_monitor.py` without changing runtime behavior.

## Scope
- docs-first review only
- focus on `free` vs `cash` fallback semantics
- no runtime mutation
- no paper/shadow/testnet disturbance

## Hotspot
Observed hotspot:
- `balance.get("free", balance.get("cash"))`

File:
- `src&#47;live&#47;portfolio_monitor.py`

## Why This Matters
This pattern can blur:
- free balance semantics
- generic cash semantics
- decision-adjacent interpretation of usable capacity

That is directly relevant to:
- treasury vs trading balance separation
- free vs reserved distinction
- reported vs reconciled balance expectations

## Risk Interpretation
Category:
- `C. Decision-Adjacent Surface`

Risk:
- if `free` is absent, fallback to `cash` may silently widen semantic meaning
- operator or future runtime logic may read this as usable balance when the boundary is not explicit

## Docs-First Position
Current docs/spec direction implies:
- ambiguity should fail toward safety
- generic balance/cash values should not be assumed decision-grade
- free/reserved/tradable distinctions should not be collapsed implicitly

## Review Conclusion
`portfolio_monitor` should be treated as a high-priority semantic hotspot for future guardrail/refactor review.

This review does **not** change behavior now.
It records why this surface deserves special handling later.

## Recommended Follow-Up
- future targeted guardrail note or refactor candidate for `portfolio_monitor`
- keep runtime unchanged in this slice
- do not treat fallback semantics as resolved by docs alone
