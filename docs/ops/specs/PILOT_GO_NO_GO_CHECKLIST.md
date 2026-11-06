# Pilot Go / No-Go Checklist

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Canonical go/no-go checklist for tightly capped, operator-supervised pilot readiness
docs_token: DOCS_TOKEN_PILOT_GO_NO_GO_CHECKLIST

## Intent
This document defines a conservative operator-facing checklist for deciding whether Peak_Trade may advance toward a tightly capped, operator-supervised pilot phase.

## Critical Clarification
This checklist is for pilot gating only.
It does not imply:
- production readiness
- autonomy readiness
- scale readiness
- authority softening

## Verdict States
- `NO_GO` — progression remains blocked
- `CONDITIONAL` — major blockers resolved, but additional bounded work remains
- `GO_FOR_NEXT_PHASE_ONLY` — acceptable for the next tightly constrained evaluation phase, not broad live trading

## Hard Blockers
Any single unresolved hard blocker must result in `NO_GO`.

- execution ambiguity without safe-stop behavior
- treasury vs trading balance separation unclear
- stale balance or stale position ambiguity unresolved
- missing critical incident response path
- bounded pilot caps unclear or unverified
- kill-switch / confirm-token / armed-state posture unclear
- insufficient audit/evidence continuity
- operator cannot determine current policy/safety posture
- exchange/broker degradation handling unclear
- replay/idempotency ambiguity unresolved

## Checklist

| Area | Question | Expected Answer for Progression | Failure Outcome |
|---|---|---|---|
| Safety Gates | Are enabled / armed / confirm-token / dry-run semantics explicit and intact? | Yes | `NO_GO` |
| Kill Switch | Is kill-switch posture visible and operationally clear? | Yes | `NO_GO` |
| Policy Posture | Is current policy action visible and non-ambiguous? | Yes | `NO_GO` |
| Operator Visibility | Can operator identify blocked vs allowed posture quickly? | Yes | `NO_GO` |
| Pilot Caps | Are bounded caps defined and documented? | Yes | `NO_GO` |
| Treasury Separation | Is trading vs treasury separation explicit? | Yes | `NO_GO` |
| Fee/Slippage Realism | Are conservative assumptions documented? | Yes | `CONDITIONAL` or `NO_GO` depending on severity |
| Partial Fill Handling | Is partial-fill behavior bounded and understood? | Yes | `NO_GO` |
| Stale State Handling | Are stale balance/order/position cases handled safely? | Yes | `NO_GO` |
| Restart / Replay | Are restart and replay semantics safe enough for bounded pilot progression? | Yes | `NO_GO` |
| Incident Runbooks | Do critical incident paths exist? | Yes | `NO_GO` |
| Evidence Continuity | Is evidence/audit trail sufficient for operator review? | Yes | `NO_GO` |
| Dependency Degradation | Is degraded exchange/telemetry behavior explicit? | Yes | `NO_GO` |
| Human Supervision | Is the pilot explicitly operator-supervised? | Yes | `NO_GO` |
| Ambiguity Rule | Does ambiguity resolve to `NO_TRADE` / safe stop? | Yes | `NO_GO` |

## Minimum Interpretation Rules
- `GO_FOR_NEXT_PHASE_ONLY` is the strongest positive outcome in this document
- any unresolved critical ambiguity forces `NO_GO`
- missing documentation for a critical control is treated as unresolved
- operational convenience never outranks reconciliation and safety
- pilot progression must remain reversible and tightly bounded

## Suggested Use
This checklist should be applied together with:
- `docs/ops/specs/PILOT_READY_EXECUTION_REVIEW_SPEC.md`
- `docs/ops/specs/PILOT_EXECUTION_EDGE_CASE_MATRIX.md`

## Explicit Non-Goals
- no direct activation authority
- no replacement for runbooks
- no replacement for future reconciliation flow specification
- no claim of broad live-readiness
