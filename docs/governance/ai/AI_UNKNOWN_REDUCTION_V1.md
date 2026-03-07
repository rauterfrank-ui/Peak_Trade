# AI Unknown Reduction v1

## Purpose
This document reduces architectural ambiguity around AI-layer semantics without changing runtime behavior.

It clarifies placeholders, authority ceilings, and unresolved slots.

## Status Vocabulary
- `IMPLEMENTED`
- `PARTIAL`
- `DOC-ONLY`
- `UNKNOWN`
- `NOT ALLOWED`

## Layer Semantics (Current Canonical Placeholder View)

| Layer | Intended Scope | Intended Authority Ceiling | What Is Known Today | What Remains Unknown | Status |
|---|---|---|---|---|---|
| L0 | base system / infra / deterministic substrate | non-decisioning | layer token exists in repo-near references | exact runtime mapping | UNKNOWN |
| L1 | early analysis / support | advisory only | layer token exists in repo-near references | exact inputs / outputs / runtime owner | UNKNOWN |
| L2 | structured analysis / support | advisory only | layer token exists in repo-near references | exact semantics and runtime path | UNKNOWN |
| L3 | higher-order analysis / orchestration support | advisory only | layer token exists in repo-near references | exact semantics and runtime path | UNKNOWN |
| L4 | supervisory / orchestration-adjacent layer | supervisory only | intended pre-execution positioning is compatible with current truth model | exact implementation path | UNKNOWN |
| L5 | highest referenced layer token currently visible | may not exceed documented guarded boundary | referenced in repo-near signals | exact semantics, exact authority, exact bindings | UNKNOWN |

## Runtime Slot Clarification

### proposer
- role intent: proposal / generation slot
- authority ceiling: advisory only
- current evidence class: `UNKNOWN`
- known today:
  - proposer terminology is referenced
- unresolved fields:
  - runtime module
  - exact inputs
  - exact outputs
  - exact model/provider binding

### critic
- role intent: pre-execution critique / policy influence slot
- authority ceiling: supervisory only
- current evidence class: `PARTIAL`
- known today:
  - pre-execution critique intent is evidenced
  - policy / gate influence is consistent with current truth model
- unresolved fields:
  - exact runtime ownership
  - exact provider/model binding
  - exact data contract

### provider
- role intent: binding slot for future or existing model/provider references
- authority ceiling: none by itself
- current evidence class: `UNKNOWN`
- known today:
  - provider references exist
- unresolved fields:
  - exact provider assignment
  - exact model assignment
  - exact layer/component ownership

## Authority Boundary (Canonical)
The current closest-to-trade path remains a deterministic gated path.

This means:
- `NO_TRADE` baseline remains controlling
- deny-by-default remains controlling
- treasury separation remains controlling
- strategy environment gating remains controlling
- policy / critic influence may exist before execution
- no explicit model-final trade authority is currently evidenced

## What This Document Does Not Claim
- it does not claim L0-L5 are fully implemented runtime layers
- it does not claim proposer is bound in runtime
- it does not claim provider/model assignments are resolved
- it does not claim any AI component currently has final trade authority
- it does not claim self-improving live autonomy

## Canonical Unknown-Reduction Backlog
1. define L0-L5 semantics with exact repo-near ownership
2. identify proposer runtime slot or mark as doc-only
3. identify provider/model binding locations
4. define exact critic data contract
5. define execution-adjacent AI boundary in one canonical source

## Not Allowed
- promoting UNKNOWN fields to IMPLEMENTED without code/config evidence
- implying model-final trade authority
- implying autonomous self-improving live execution
- weakening deterministic gated execution wording
