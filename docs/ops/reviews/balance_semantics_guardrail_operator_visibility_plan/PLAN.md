# BALANCE SEMANTICS GUARDRAIL OPERATOR VISIBILITY PLAN

## Purpose
Define the implementation order for operator-visible balance semantics without changing runtime behavior in this slice.

## Scope
- choose the first operator-facing surfaces
- define visible fields
- define safest rollout order
- no runtime mutation

## Minimum Visible Fields
The first operator-visible surface should expose:
- `balance_semantic_state`
- `balance_reason_code`
- `balance_operator_visible_state`

## Recommended First Surface
Preferred first surface:
- preview / portfolio-oriented visibility surface

Why first:
- closest to the portfolio snapshot
- easiest place to show semantic state without changing execution behavior
- lower risk than deeper ops/web UI expansion

## Candidate Rollout Order
### Phase 1
- preview / portfolio display surface
- expose state + reason code + visible state

### Phase 2
- live risk alert / risk-adjacent operator summaries
- ensure warning/blocked semantics are legible in alert context

### Phase 3
- ops / cockpit or broader operator summary surface
- unify visibility across higher-level operator views

## Visibility Rules
### Clear
- show healthy / clear state
- no special caution text required

### Warning
- show caution / degraded state
- show reason code
- make it explicit that interpretation is conservative

### Blocked
- show blocked / not decision-grade state
- show reason code
- make it explicit that new exposure increase should not rely on this balance view

## Safety Constraints
- no silent semantic blocking
- no hidden `cash -> free&#47;usable` upgrade
- no disturbance to paper/shadow/testnet stability
- operator-visible semantics must remain aligned with runtime contract docs

## Recommended Next Slice
- balance_semantics_guardrail_preview_visibility
