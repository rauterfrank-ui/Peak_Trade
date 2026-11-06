# KILL SWITCH ADAPTER MIGRATION PLAN

## Purpose
Define one docs-first migration plan for kill-switch adapter alignment before any runtime mutation.

## Scope
- migration plan only
- no runtime mutation
- no paper/shadow/testnet mutation
- exactly one PR

## Current Position
- kill-switch behavior is distributed across operator tooling, runtime gates, and visibility surfaces
- `risk_hook_impl` still treats kill-switch policy as future work
- operator visibility is stronger than full runtime unification

## Migration Goal
Clarify how kill-switch signaling should move from today's partially split state toward a more explicit adapter-aligned path.

## Candidate Migration Questions
1. what is the canonical kill-switch source for runtime consumers?
2. where should adapter logic sit relative to risk hook, risk gate, and operator tooling?
3. what must remain unchanged during migration planning?
4. what proof points are required before runtime adoption?

## Recommended Plan Structure
### Phase 1
- define adapter boundary and source-of-truth expectations

### Phase 2
- document consumer mapping:
  - risk gate
  - risk hook
  - operator tooling
  - visibility surfaces

### Phase 3
- define rollout guardrails and test expectations before any runtime change

## Constraints
- do not implement migration in this slice
- do not weaken existing safety posture
- do not imply full unification already exists

## Recommended Next Step
- turn this plan into one concrete migration review in the same topic area
