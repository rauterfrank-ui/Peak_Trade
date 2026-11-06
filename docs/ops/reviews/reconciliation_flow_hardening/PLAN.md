# RECONCILIATION FLOW HARDENING PLAN

## Purpose
Define a docs-first hardening slice for reconciliation flow after treasury / balance separation clarification.

## Scope
- mismatch handling
- source-of-truth clarification
- operator-visible failure states
- fail-safe / conservative handling under ambiguity

## Constraints
- no runtime mutation in this slice
- no live-expansion work
- no disturbance to paper/shadow/testnet stability

## Hardening Goals
1. define reconciliation source-of-truth hierarchy
2. define mismatch categories
3. define operator-visible failure states
4. define safe behavior under ambiguity
5. define escalation / follow-up path

## Candidate Reconciliation Questions
- which balance fields are decision-grade vs informational only?
- what counts as a mismatch?
- when is a mismatch only informational vs operationally blocking?
- when should reconciliation ambiguity reduce tradable capacity?
- what should operators see when reconciliation is uncertain?

## Recommended Direction
- fail toward safety under mismatch or ambiguity
- do not increase usable capacity from uncertain data
- preserve separation between treasury, free, reserved, and reconciled balances
- make operator-visible states explicit

## Proposed Deliverables
- reconciliation flow hardening review/spec note
- mismatch taxonomy
- operator-visible state definitions
- handoff for the next slice

## Recommended Next Slice After This
- treasury_balance_incident_runbook
