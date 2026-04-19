# MASTER V2 — Scope Capital Envelope Clarification v1 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-19
owner: Peak_Trade
purpose: Canonical docs-only clarification of Scope and Capital Envelope semantics in the Master V2 path
docs_token: DOCS_TOKEN_MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1

## 1) Executive Summary

This specification clarifies Scope and Capital Envelope as a dedicated Master V2 mapping block.

It is mapping-only and non-authorizing. The goal is legibility and auditability of capital-path semantics, not live enablement or runtime authority.

## 2) Scope and Non-Goals

In scope:

- canonical clarification of Scope and Capital Envelope terminology and layering
- explicit separation between Scope semantics and downstream Risk and Exposure Caps
- explicit mapping of what is confirmed versus unclear in repository-visible artifacts

Out of scope:

- runtime rewiring or implementation changes
- live authorization
- gate closure by assertion
- reuse and rewire inventory work
- risk-limit implementation details

## 3) Canonical Clarification

Canonical terms for this slice:

- Account Equity and Wallet Balance: capital-state inputs that bound feasible deployment space
- Tradable Scope: strategy and market domain in which trading is allowed in principle
- Deployable Scope: tradable subset that is currently eligible after policy, readiness, and authority constraints
- Per-Market, Per-Side, Per-Signal allowance: narrower allowance semantics applied within deployable scope

Clarification lock:

- Scope and Capital Envelope are conceptually upstream of downstream Risk and Exposure Caps
- Scope semantics and generic risk limits must not be treated as equivalent without explicit repo evidence

## 4) Capital-Path Layering

| capital-path layer | canonical role | relation to next layer |
|---|---|---|
| Account Equity and Wallet Balance | capital-state basis for potential deployment | bounds Tradable Scope formation |
| Tradable Scope | strategic and market-level eligibility surface | constrains Deployable Scope candidates |
| Deployable Scope | currently eligible capital deployment subset | consumed by downstream cap enforcement |
| downstream Risk and Exposure Caps | hard limit enforcement over candidate deployment | can veto or reduce deployable actions |
| Safety and Kill-Switch veto shell | fail-closed safety boundary over all lower layers | may block execution regardless of prior allowance |

## 5) Repo-Evidence Mapping Table

| concept | canonical meaning | nearest repo evidence | what is confirmed | what remains unclear | confidence |
|---|---|---|---|---|---|
| Scope and Capital Envelope | capital and mandate envelope distinct from risk limits | [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | explicit vocabulary distinction exists | consolidated canonical owner chain is not unified | partial |
| Account Equity and Wallet Balance input role | equity and wallet context informs envelope determination | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md](../runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) | equity-context dependency is documented | one canonical field contract for equity-to-scope handoff is not materialized | partial |
| Tradable Scope | in-principle tradable domain before final deployment eligibility | [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | concept is present in canonical vocabulary and stage mapping | exact repo-wide tradable-scope schema is not consolidated | unclear |
| Deployable Scope | tradable subset eligible for candidate deployment | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md) | deployable-scope proposal appears as stage output | closure criteria from proposal to approved deployable set remain partial | partial |
| Per-Market, Per-Side, Per-Signal allowance | finer-grained allowance semantics inside deployable scope | [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | market and side contribution surfaces are documented | one canonical allowance grammar tying market, side, and signal is not explicit | unclear |
| downstream Risk and Exposure Caps | hard limit enforcement on candidate deployment | [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md](../runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) | cap enforcement is explicitly downstream and limit-enforcing | handoff boundaries from scope decider to cap enforcer are partially mapped | partial |
| Safety and Kill-Switch veto shell | fail-closed veto boundary outside strategy allowance | [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | veto precedence is explicit and non-equivalent to strategic scope decisions | exact operator-to-runtime veto trace is not one consolidated chain | partial |

## 6) Distinction from Risk and Exposure Caps

Scope and Capital Envelope must be kept distinct from:

- max notional
- max order size
- max position
- leverage cap
- loss limits
- generic live risk limits

Boundary rule for this slice:

- downstream caps limit what can be executed, but they do not define the full upstream Scope semantics by themselves
- cap compliance is not equivalent to Scope correctness

## 7) Decision and Authority Implications

- Scope-setting intent appears conceptually upstream in decision-stage mapping, but a single canonical authoritative decider remains partial.
- Risk-cap enforcement authority is stronger in repo evidence, yet this role is limit-enforcing and not equivalent to scope-defining authority.
- Safety and Kill-Switch authority is explicit as veto/fail-closed boundary and remains separate from scope-definition logic.
- Current authority visibility is therefore mixed: partial for scope-defining chain, stronger for downstream cap and safety veto enforcement.

## 8) Ambiguity, Confusion, and Interpretation Risk Map

- Scope and Capital Envelope versus risk caps: frequent collapse risk; semantics must remain separate.
- deployable capital versus allowed order size: order-size limits are downstream controls, not full deployable-scope semantics.
- strategic capital scoping versus safety veto: safety veto can block execution without redefining scope.
- operator-config intent versus authoritative runtime enforcement: documented intent does not automatically prove runtime authoritative ownership.
- documented target semantics versus visible implementation: concept clarity can be stronger than currently consolidated runtime traceability.

## 9) Non-Authorizing Constraint

This specification authorizes nothing.

It only clarifies Scope and Capital Envelope semantics and boundary interpretation.

Live remains separately gated and separately authorized by existing governance, safety, risk, and operator authority sources.

Clarified or verified mapping wording in this document is not equivalent to runtime materialization.

## 10) Evidence and Closure Criteria

Confirmed by this specification:

- Scope and Capital Envelope is now explicitly materialized as a dedicated Master V2 clarification block.
- upstream-versus-downstream layering is explicit and reviewable.
- distinction from downstream risk-cap semantics is explicit and canonical.

Still open:

- one consolidated canonical authority chain for scope-definition ownership
- one compact contract for translating equity-context inputs into deployable-scope decisions
- one explicit allowance grammar for per-market, per-side, and per-signal boundaries

Potential follow-up slice (separate topic):

- docs-only scope authority-chain clarification focused on ownership and handoff criteria, without runtime changes

## 11) Cross-References

- [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md)
- [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md)
- [MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md)
- [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md)
- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [MASTER_V2_REUSE_REWIRE_INVENTORY_V1.md](MASTER_V2_REUSE_REWIRE_INVENTORY_V1.md)
- [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)
- [RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md](../runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md)
