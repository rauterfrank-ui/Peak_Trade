# BOUNDED PILOT LIVE ORDER EXECUTION DECISION PACKAGE

## Status
- Project: Peak_Trade
- Topic: bounded_pilot_live_governance_decision_package
- Branch Baseline: `main`
- Mode: `read_only_review`
- Decision State: **pending governance decision**
- Technical State: **no implementation decision made by this document**
- Current Feature State: `live_order_execution = locked`

## Purpose
This document formalizes the decision package for a governance decision on whether a bounded-pilot path for live order execution should exist as a separately governed capability.

This document is a decision input package only. It does **not** authorize live trading, does **not** unlock the current `live_order_execution` path, and does **not** replace existing gates, evidence requirements, or operator controls.

## Decision Question
Should Peak_Trade introduce a separately governed bounded-pilot path for live order execution, with explicit semantics, explicit scope boundaries, and explicit downstream implementation follow-up?

## Baseline / Current State
- `live_order_execution` remains `locked`.
- A separate `GO_NO_GO_2026` decision path is already anticipated.
- Entry-contract prerequisites for bounded-pilot execution have been defined outside this document.
- Governance review identified **B2** as the central prerequisite for any first live step.
- A structured review package exists, but the decision package has not yet been formalized into a canonical governance document.

## Scope of This Document
This document covers:
- the governance decision surface for bounded-pilot live order execution
- the candidate options for expressing that decision in a controlled way
- the evaluation criteria for governance selection
- the downstream dependency map after a governance decision

This document does **not** cover:
- implementation of runner, CLI, config, wrappers, or exchange integration
- operational go-live approval
- production deployment approval
- enabling unrestricted live trading
- changing the current generic `live_order_execution` lock state directly

## Inputs
Primary review artifacts are located under:

`docs/ops/reviews/bounded_pilot_live_governance_decision_package_review/`

Expected inputs include:
- `decision_package_inventory.md`
- `inputs_and_criteria.md`
- `options_and_dependencies.md`
- `findings.md`
- `review_report.md`
- `HANDOFF.txt`

## Decision Options

### Option A — New Feature Key
Introduce a distinct governance key:

`live_order_execution_bounded_pilot`

#### Intent
Create an explicitly separate capability for bounded-pilot live order execution without changing the semantics of the existing generic `live_order_execution` control.

#### Strengths
- highest semantic clarity
- strongest separation between generic live execution and bounded pilot
- lowest operator interpretation risk
- cleanest audit trail for exception-scoped approval
- clean downstream mapping for B1/B3/B4/B6 work
- reversible without redefining the generic live execution meaning

#### Risks / Costs
- requires explicit implementation across governance and technical surfaces
- adds one more named control to maintain

### Option B — New Approval Status
Retain the existing feature surface but introduce a specific approval status, such as:

`approved_bounded_pilot_2026`

#### Intent
Represent bounded-pilot allowance through a specialized status value rather than through a distinct capability key.

#### Strengths
- potentially smaller schema change at some layers
- may align with status-based governance models

#### Risks / Costs
- semantic meaning depends on consistent interpretation of status values
- less explicit than a separate feature key
- higher risk of confusion between capability and approval state
- may complicate auditability if status and scope boundaries are not universally enforced

### Option C — Reuse Generic Live Approval
Use the existing generic path and move `live_order_execution` toward a broader approval state such as:

`approved_2026`

#### Intent
Avoid introducing a bounded-pilot-specific capability and instead reuse the generic live execution semantics.

#### Strengths
- smallest conceptual surface change in the short term

#### Risks / Costs
- weakest separation of meaning
- highest risk of governance/operator misunderstanding
- bounded-pilot scope could be conflated with broader live authorization
- least robust for audit, rollback, and future control hygiene

## Evaluation Criteria
Governance should evaluate options against the following criteria:

1. **Semantic Separation**
   - Does the option clearly distinguish bounded-pilot execution from generic live execution?

2. **Operator Safety**
   - Does the option reduce the chance of misinterpretation, accidental overreach, or unsafe activation?

3. **Governance Clarity**
   - Can decision-makers express approval narrowly and unambiguously?

4. **Auditability**
   - Does the option produce a clean decision trail and support later review of what exactly was approved?

5. **Implementation Alignment**
   - Does the option provide a clean basis for downstream work across B1, B3, B4, and B6?

6. **Reversibility**
   - Can the bounded-pilot authorization be constrained or rolled back without redefining broader live-trading semantics?

7. **Boundary Preservation**
   - Does the option preserve current safety gates and avoid implicitly weakening existing controls?

## Comparative Assessment

### Option A
Assessment: **preferred**

Reasoning:
- maximizes explicitness
- best preserves the current meaning of `live_order_execution`
- best supports narrowly scoped authorization
- best supports strong governance-to-implementation traceability

### Option B
Assessment: **possible but secondary**

Reasoning:
- may be workable if status semantics are rigorously defined
- weaker than Option A on clarity and boundary separation

### Option C
Assessment: **not preferred**

Reasoning:
- introduces avoidable ambiguity
- risks implying broader live authorization than intended
- weakens governance clarity for a bounded pilot

## Recommended Governance Position
Recommended option: **Option A**

Recommended direction:
- create a separate governance capability key for bounded-pilot live order execution
- keep the generic `live_order_execution` path locked unless and until a separate broader governance decision explicitly changes it
- treat bounded-pilot authorization as an exception-scoped, tightly governed path rather than as an early form of generic live approval

## Entry Contract / Preconditions
This document assumes bounded-pilot entry-contract prerequisites are defined outside this package and must be satisfied independently.

This package does not restate those prerequisites in full, but governance should confirm that the following classes of conditions are already defined and evidence-backed before any downstream implementation activation:
- operator prerequisites
- evidence prerequisites
- telemetry and audit prerequisites
- rollback / kill-switch readiness
- bounded scope definition
- control ownership and review accountability

## Non-Decision Clarifications
Approval of this package would **not** mean:
- unrestricted live trading is approved
- Kraken live execution is approved by default
- current production/live gates are lifted
- technical implementation may bypass staged delivery
- paper/shadow/testnet controls are superseded

Any future technical or operational activation remains separately gated.

## Downstream Dependencies After Governance Approval
After a governance decision, downstream work is expected in the following sequence:

- **B2 Governance** → formal decision and chosen semantic model
- **B1 Runner**
- **B3 CLI**
- **B4 Config**
- **B6 Wrapper**

Parallel-capable track:
- **B5 Kraken Live** may proceed in parallel where appropriate, but remains independently gated

No downstream implementation work is authorized by this document alone.

## Proposed Governance Decision Record Template
To be completed by decision-makers:

- Decision Date:
- Decision Makers:
- Decision:
- Selected Option:
- Scope Boundaries:
- Preconditions Required Before Implementation:
- Additional Constraints / Conditions:
- Follow-Up Owners:
- Review / Reassessment Date:
- Outcome:
- Notes:

## Suggested Governance Resolution Format
Suggested canonical resolution structure:

1. Governance acknowledges that generic `live_order_execution` remains locked.
2. Governance decides whether a separately scoped bounded-pilot authorization path should exist.
3. If approved, Governance selects the semantic model for that path.
4. Governance records scope boundaries, prerequisites, and explicit non-goals.
5. Implementation work begins only under the selected decision and existing safety controls.

## Conclusion
The review package supports a formal governance decision for bounded-pilot live order execution.

Based on the current analysis:
- the need is real
- the decision surface is sufficiently defined
- the strongest path is to preserve generic live-execution semantics and introduce a bounded-pilot-specific governance key

Therefore, the recommended governance direction is:

**Option A — `live_order_execution_bounded_pilot`**

This recommendation is provided as a decision input only and does not itself authorize technical activation or operational go-live.

## Source Review Package
Reference review directory:

`docs/ops/reviews/bounded_pilot_live_governance_decision_package_review/`
