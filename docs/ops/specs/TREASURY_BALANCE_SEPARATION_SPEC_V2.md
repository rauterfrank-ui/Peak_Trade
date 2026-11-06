# TREASURY BALANCE SEPARATION SPEC V2

## Purpose
Consolidate treasury / balance separation rules into one clearer source of truth before any runtime changes.

## Scope
- boundary definitions only
- operator-visible invariants
- reconciliation source-of-truth expectations
- no live-expansion work
- no paper/shadow/testnet mutation

## Core Boundaries
### 1. Treasury vs Trading Balance
- treasury funds are not implicitly equivalent to available trading balance
- available trading balance must be explicitly derived, not assumed

### 2. Free vs Reserved Balance
- free balance: currently usable under bounded constraints
- reserved balance: committed, held, or otherwise unavailable for new exposure
- operator flows must not collapse these into one number

### 3. Reported vs Reconciled Balance
- exchange-reported balance is not automatically the final operational source of truth
- reconciliation logic must define which fields become decision-grade balance inputs

### 4. Balance vs Risk Capacity
- visible balance does not by itself authorize exposure
- risk caps, Entry Contract, Go/No-Go, and operator gates remain primary controls

## Required Invariants
- treasury and tradable balance remain conceptually separated
- reserved funds are never treated as free balance
- operator-facing docs must state the source of truth used for decisions
- bounded pilot decisions must remain conservative under ambiguity

## Reconciliation Expectations
- define the canonical source-of-truth fields
- define mismatch handling
- define operator-visible failure states
- ambiguity should fail toward safety, not toward more tradable capacity

## Non-Goals
- no runtime implementation changes in this slice
- no broker/live expansion
- no weakening of existing guardrails

## Recommended Next Slice
- reconciliation flow hardening
