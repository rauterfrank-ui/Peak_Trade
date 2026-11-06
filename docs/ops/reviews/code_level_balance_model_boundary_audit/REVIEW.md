# CODE-LEVEL BALANCE MODEL BOUNDARY AUDIT

## Purpose
Audit the code surface for treasury / trading / free / reserved / available balance boundary clarity without changing runtime behavior.

## Scope
- code terminology
- model / schema surfaces
- execution / exchange / portfolio adjacency
- risk-capacity adjacency
- docs/code term alignment

## Audit Questions
1. Where are balance-like concepts represented in code?
2. Where might treasury, tradable, free, reserved, or available concepts blur?
3. Where could operator-facing ambiguity later become runtime ambiguity?
4. Which surfaces are likely candidates for future guardrails or refactors?

## Expected Findings Categories
### A. Clear Boundary Surface
- term usage appears explicit
- role is narrow and understandable
- low immediate ambiguity risk

### B. Mixed Semantic Surface
- terms like balance / funds / available / free appear without a clear boundary contract
- likely candidate for stronger naming or boundary notes later

### C. Decision-Adjacent Surface
- balance-like values appear near exposure sizing, risk, or execution decisions
- highest priority for future guardrail review

### D. Docs / Code Drift Surface
- docs define distinctions that code terminology may not yet reflect clearly
- likely candidate for later alignment work

## Review Outcome Format
The audit should identify:
- file or module surface
- observed balance terms
- likely boundary risk level
- reason the surface matters
- recommendation:
  - leave as-is
  - clarify in docs
  - future refactor candidate
  - future guardrail candidate

## Constraints
- docs-first only
- no runtime mutation in this slice
- no paper/shadow/testnet disturbance
- no live-expansion work

## Recommended Next Slice
- produce one concrete audit findings review from the inventory
