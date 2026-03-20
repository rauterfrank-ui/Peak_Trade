# CODE-LEVEL BALANCE MODEL BOUNDARY AUDIT FINDINGS

## Purpose
Record concrete docs-first findings from the code-level balance boundary audit without changing runtime behavior.

## Audit Basis
- `docs&#47;ops&#47;reviews&#47;code_level_balance_model_boundary_audit&#47;REVIEW.md`
- `docs&#47;ops&#47;specs&#47;TREASURY_BALANCE_SEPARATION_SPEC_V2.md`
- `docs&#47;ops&#47;reviews&#47;reconciliation_flow_hardening_review&#47;REVIEW.md`

## Findings Summary
The current code/docs surface shows several balance-boundary gaps that matter for future safety hardening.

## Finding 1 — Free vs Reserved Not Explicitly Modeled
Category:
- `B. Mixed Semantic Surface`

Observation:
- balance handling appears to rely mainly on generic cash/balance notions
- an explicit free-vs-reserved boundary is not consistently modeled

Why It Matters:
- reserved funds may later be confused with usable capacity
- this conflicts with the spec requirement that reserved funds are never treated as free balance

Recommended Follow-Up:
- future guardrail or model-refactor candidate
- clarify code-facing terminology before runtime decisions rely on it

## Finding 2 — Treasury vs Trading Balance Boundary Is Policy-Heavy, Model-Light
Category:
- `D. Docs / Code Drift Surface`

Observation:
- treasury vs tradable balance is clearly defined in docs/specs
- the code surface does not yet show an equally explicit separate model boundary

Why It Matters:
- operator-safe policy exists, but model clarity may lag
- future runtime work could accidentally compress treasury and tradable concepts

Recommended Follow-Up:
- future docs/code alignment candidate
- keep implementation work blocked behind explicit boundary clarification

## Finding 3 — Reported vs Reconciled Balance Is Not Yet a Clear Decision-Grade Model Surface
Category:
- `C. Decision-Adjacent Surface`

Observation:
- reconciliation exists as a concept, but a distinct decision-grade reconciled balance field is not clearly surfaced
- exchange-reported data may still appear close to decision use without a strong explicit hierarchy

Why It Matters:
- this is directly adjacent to exposure sizing and usable-capacity interpretation
- ambiguity here should fail toward safety

Recommended Follow-Up:
- future guardrail candidate
- reconcile/source-of-truth hierarchy should become more explicit before runtime changes

## Finding 4 — Reconciliation Failure Severity Appears Too Soft Relative to Spec Direction
Category:
- `D. Docs / Code Drift Surface`

Observation:
- there is evidence that reconciliation failure is not always treated as a critical blocker
- this is weaker than the newer spec/review direction, which prefers caution/block under ambiguity

Why It Matters:
- docs-first hardening now expects warning/block semantics
- softer runtime or operator assumptions would drift from the current safety position

Recommended Follow-Up:
- future docs/code alignment candidate
- incident/runbook semantics should stay stricter than legacy assumptions

## Finding 5 — portfolio_monitor Free-Semantics Hotspot
Category:
- `C. Decision-Adjacent Surface`

Observation:
- `portfolio_monitor` uses a pattern equivalent to `balance.get("free", balance.get("cash"))`
- this is the clearest currently known hotspot where free-like semantics may fall back to generic cash semantics

Why It Matters:
- this is precisely the kind of boundary blur the spec is trying to prevent
- decision-adjacent fallback semantics deserve extra scrutiny

Recommended Follow-Up:
- highest-priority audit hotspot for later targeted guardrail/refactor review
- do not mutate runtime in this slice; record it as a concrete follow-up anchor

## Overall Risk Posture
Current posture:
- docs/specs now express safer boundaries more clearly than the known code surface
- immediate next work should remain clarification/audit-first, not runtime expansion-first

## Recommended Next Slice
- `portfolio_monitor_balance_semantics_review`
