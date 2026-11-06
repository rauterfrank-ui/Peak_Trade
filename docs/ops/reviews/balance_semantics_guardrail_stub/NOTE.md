# BALANCE SEMANTICS GUARDRAIL STUB

## Purpose
Define a docs-first stub for a future balance-semantics guardrail without changing runtime behavior.

## Scope
- semantic classification only
- operator-visible states only
- no runtime mutation
- no paper/shadow/testnet disturbance

## Problem
A hotspot currently uses fallback semantics equivalent to:
- `free -> cash`

This can blur:
- free balance
- generic cash balance
- decision-grade usable capacity

## Guardrail Stub
Future guardrail should classify balance semantics into:

### 1. `balance_semantics_clear`
Use only when:
- free-like semantics are explicit
- no semantic fallback ambiguity is present
- decision use is understandable

### 2. `balance_semantics_warning`
Use when:
- fallback semantics are used
- balance meaning is conservative but not fully explicit
- operator visibility is required

### 3. `balance_semantics_blocked`
Use when:
- ambiguity overlaps with decision-grade use
- semantics are not safe enough for new exposure increase
- operator should treat state as blocked pending clarification

## Design Constraints
- do not silently upgrade cash fallback into free/usable capacity
- prefer explicit classification over scattered implicit checks
- preserve docs/spec alignment with treasury / balance separation
- fail toward caution or block under ambiguity

## Candidate Future Integration Points
- local classification near `portfolio_monitor`
- or upstream balance normalization boundary
- operator-visible warning/block state emission before any decision-adjacent interpretation

## Non-Goals
- no implementation in this slice
- no broker/live expansion
- no disturbance to paper/shadow/testnet stability

## Recommended Next Slice
- balance_semantics_guardrail_runtime_plan
