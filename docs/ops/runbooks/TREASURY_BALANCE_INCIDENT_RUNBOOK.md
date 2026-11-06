# TREASURY BALANCE INCIDENT RUNBOOK

## Purpose
Operator runbook for treasury / balance incidents under a docs-first, safety-first posture.

## Scope
Applies to incidents involving:
- reconciliation mismatch
- ambiguity in decision-grade balance
- treasury vs tradable balance confusion
- free vs reserved balance confusion

## Non-Goals
- no live-expansion work
- no paper/shadow/testnet mutation
- no runtime implementation changes in this slice

## Trigger Conditions
Treat as incident when one or more apply:
- source-of-truth is unclear
- blocking mismatch exists
- operator cannot determine decision-grade balance
- reserved funds may be treated as free
- treasury and tradable balances appear conflated

## Immediate Operator Actions
1. stop any new exposure increase
2. treat state as safety-degraded or blocked
3. preserve evidence and visible state
4. do not infer extra usable capacity from ambiguous data

## Minimum Evidence To Capture
- active mode
- relevant session or operator context
- visible balance inputs
- visible mismatch or ambiguity signal
- operator action taken
- follow-up required

## Incident States
- `reconciliation_warning`
- `reconciliation_blocked`

## Decision Rule
- warning: continue only conservatively if decision-grade balance remains clear
- blocked: no new exposure increase until clarified

## Escalation
Escalate when:
- ambiguity persists
- mismatch is unresolved
- operator cannot explain which balance is decision-grade
- treasury/tradable boundary is unclear

## References
- `docs&#47;ops&#47;specs&#47;TREASURY_BALANCE_SEPARATION_SPEC_V2.md`
- `docs&#47;ops&#47;reviews&#47;reconciliation_flow_hardening_review&#47;REVIEW.md`
