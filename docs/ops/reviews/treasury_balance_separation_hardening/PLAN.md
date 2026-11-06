# TREASURY BALANCE SEPARATION HARDENING PLAN

## Purpose
Choose one concrete hardening slice for treasury / balance separation without expanding live scope.

## Constraints
- docs/spec + guardrail hardening preferred first
- no live-expansion work
- no disturbance to paper/shadow/testnet stability

## Candidate Slices
1. treasury / balance separation spec consolidation
2. reconciliation flow hardening
3. operator runbook for treasury / balance incident handling
4. code-level balance model boundary audit

## Selection Criteria
- highest safety value
- lowest runtime risk
- strongest clarification of money / balance boundaries
- preserves current mode isolation

## Recommended First Slice
- treasury / balance separation spec consolidation

## Why This First
- clarifies source of truth before implementation changes
- reduces ambiguity across runbooks / specs / operator behavior
- creates a stable base for reconciliation and incident handling follow-up

## Proposed Deliverables
- consolidated treasury / balance separation review or spec note
- explicit boundary definitions:
  - treasury vs available trading balance
  - reserved vs free balance
  - reconciliation source of truth
  - operator-visible invariants
- handoff for next hardening slice

## Deferred Until After This Slice
- runtime changes
- broker/live expansion
- testnet/paper/shadow mutations
