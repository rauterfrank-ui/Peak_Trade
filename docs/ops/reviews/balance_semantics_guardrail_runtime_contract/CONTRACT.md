# BALANCE SEMANTICS GUARDRAIL RUNTIME CONTRACT

## Purpose
Define the docs-first runtime contract for a future balance-semantics guardrail without implementing runtime behavior in this slice.

## Scope
- input/output contract only
- no runtime mutation
- no paper/shadow/testnet disturbance

## Contract Intent
A future guardrail should explicitly classify balance semantics before any decision-adjacent interpretation.

## Candidate Inputs
A runtime guardrail contract may accept:
- raw balance-like payload
- source/context metadata
- optional reconciliation context
- optional mode/context flags

## Required Outputs
At minimum, the contract should return:
- `semantic_state`
  - `balance_semantics_clear`
  - `balance_semantics_warning`
  - `balance_semantics_blocked`
- `reason_code`
- `decision_use_allowed`
- `operator_visible_state`

## Semantic Rules
### Clear
- explicit semantics present
- no ambiguity overlap with decision use
- decision use may proceed under existing higher-level controls

### Warning
- fallback or ambiguity present
- interpretation must remain conservative
- operator-visible warning required

### Blocked
- ambiguity overlaps with decision-grade use
- no new exposure increase should depend on this state
- operator-visible blocked state required

## Contract Constraints
- do not silently upgrade `cash` fallback into free&#47;usable capacity
- do not collapse treasury, tradable, free, reserved, and reconciled semantics
- fail toward caution or blocked under ambiguity
- preserve alignment with Treasury/Balance Spec V2 and reconciliation docs

## Non-Goals
- no implementation in this slice
- no live-expansion work
- no weakening of existing guardrails

## Recommended Next Slice
- balance_semantics_guardrail_contract_usage_review
