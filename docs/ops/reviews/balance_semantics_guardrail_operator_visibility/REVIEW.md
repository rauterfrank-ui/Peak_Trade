# BALANCE SEMANTICS GUARDRAIL OPERATOR VISIBILITY REVIEW

## Purpose
Define the docs-first operator-visibility expectations for balance semantics guardrails after downstream consumer handling.

## Scope
- operator-visible fields
- warning / blocked visibility
- reason-code visibility
- no runtime mutation in this slice

## Operator-Visible Minimum
Operator-facing surfaces should make these fields visible when present:
- `balance_semantic_state`
- `balance_reason_code`
- `balance_operator_visible_state`

## Required Visibility Semantics
### Clear
- visible as healthy / clear
- no special caution messaging required beyond normal context

### Warning
- visible as caution / degraded
- operator should be able to identify why cash or balance interpretation is conservative
- reason code should be inspectable

### Blocked
- visible as blocked / not decision-grade
- operator should be able to see that new exposure increase should not rely on this state
- reason code should be inspectable

## Candidate Surfaces
- preview / portfolio views
- live risk alert context
- ops / cockpit or adjacent operator summaries
- logs / serialized state where operator review relies on them

## Review Direction
Preferred operator experience:
- no silent semantic blocking
- no hidden fallback from `cash` to implied usable balance
- warning/blocked states should be legible without reading source code

## Non-Goals
- no UI/runtime implementation in this slice
- no paper/shadow/testnet disturbance
- no live-expansion work

## Recommended Next Slice
- balance_semantics_guardrail_operator_visibility_plan
