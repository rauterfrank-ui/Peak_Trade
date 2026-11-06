# BALANCE SEMANTICS GUARDRAIL RUNTIME PLAN

## Purpose
Define a docs-first runtime plan for a future balance-semantics guardrail without implementing it in this slice.

## Scope
- future runtime design sequence only
- no runtime mutation now
- no paper/shadow/testnet disturbance

## Runtime Plan Goal
Future runtime logic should prevent ambiguous balance semantics from being treated as decision-grade usable capacity.

## Proposed Runtime Sequence
1. gather raw balance inputs
2. classify semantics as:
   - `balance_semantics_clear`
   - `balance_semantics_warning`
   - `balance_semantics_blocked`
3. expose operator-visible state before decision-adjacent use
4. ensure warning/blocked states restrict interpretation conservatively
5. avoid implicit `cash -> free&#47;usable` upgrade

## Candidate Integration Point
Preferred direction:
- one narrow classification point near the balance interpretation boundary

Possible shapes:
- helper/classifier near `portfolio_monitor`
- upstream normalization layer later, if multiple consumers justify it

## Candidate Runtime Rules
### Clear
- explicit free-like semantics present
- no ambiguity overlap with decision use

### Warning
- fallback semantics used
- conservative interpretation only
- operator-visible warning required

### Blocked
- ambiguity overlaps with decision-grade use
- no new exposure increase should rely on this state

## Required Preconditions Before Any Runtime Work
- terminology remains aligned with Treasury/Balance Spec V2
- reconciliation warning/block semantics remain aligned
- incident/runbook semantics remain aligned
- no disturbance to paper/shadow/testnet stability

## Non-Goals
- no implementation in this slice
- no live-expansion work
- no weakening of existing guardrails

## Recommended Next Slice
- balance_semantics_guardrail_runtime_stub_review
