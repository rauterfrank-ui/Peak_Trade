# Reconciliation Flow Spec

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Canonical reconciliation flow specification for bounded pilot and execution safety
docs_token: DOCS_TOKEN_RECONCILIATION_FLOW_SPEC

## Intent
This document defines how Peak_Trade should reason about reconciliation when local state, broker/exchange state, balances, positions, or evidence trails may diverge.

## Core Principle
When reconciliation is incomplete or ambiguous, the system posture must degrade to `NO_TRADE` / safe stop until the ambiguity is resolved.

## Reconciliation Objects
- orders
- fills
- positions
- balances
- transfers
- session state
- evidence trail

## Reconciliation Triggers
- order acknowledgement timeout
- reject after unclear local state
- partial fill with stale follow-up state
- restart during active session
- session end
- stale balance / stale position detection
- degraded exchange or telemetry
- unexpected exposure
- transfer ambiguity

## Canonical Flow

### 1. Detect
Identify that local state and external state may differ or be incomplete.

### 2. Freeze Risk Expansion
Do not place new risk-increasing actions while reconciliation is unresolved.

### 3. Gather Truth Sources
Collect the best available current truth from:
- broker/exchange order state
- fill history
- positions
- balances
- transfer history
- local evidence trail / logs / telemetry

### 4. Classify State
Classify the situation as one of:
- reconciled
- partially reconciled
- ambiguous
- degraded dependency
- operator escalation required

### 5. Apply Safe Posture
- `reconciled` -> proceed only if all gates remain valid
- `partially reconciled` -> remain bounded and avoid new risk expansion
- `ambiguous` -> `NO_TRADE` / safe stop
- `degraded dependency` -> prefer `NO_TRADE` / safe stop
- `operator escalation required` -> block progression pending review

### 6. Record Evidence
Record:
- trigger
- observed divergence
- truth sources consulted
- final classification
- operator escalation if any
- final posture

### 7. Resume Criteria
Resume only when:
- order / fill / position / balance state is coherent enough
- no unresolved ambiguity remains
- current gates and pilot caps remain valid
- evidence trail is intact

## Flow by Domain

### Orders / Fills
- reconcile order acknowledgement, reject, cancel/replace, partial fill
- never assume a retry is safe until duplicate risk is addressed

### Positions
- position truth must be explicit after restart, partial fill, or degraded exchange behavior

### Balances / Treasury
- trading balance and treasury balance must not be conflated
- stale or ambiguous balances block progression

### Transfers
- unresolved transfer state blocks new dependent action

### Session End
- unresolved closeout mismatch blocks next session progression

## Failure Outcomes
- unresolved ambiguity -> `NO_TRADE`
- stale critical state -> `NO_TRADE`
- degraded truth source with unknown exposure -> `NO_TRADE`
- missing evidence continuity -> escalation and blocked progression

## Operator Expectations
The operator should be able to answer:
- what triggered reconciliation
- which truth sources were consulted
- what remains unresolved
- why the current posture is safe

## Relationship to Other Documents
This spec should be used together with:
- `docs/ops/specs/PILOT_READY_EXECUTION_REVIEW_SPEC.md`
- `docs/ops/specs/PILOT_EXECUTION_EDGE_CASE_MATRIX.md`
- `docs/ops/specs/PILOT_GO_NO_GO_CHECKLIST.md`

## Explicit Non-Goals
- no direct execution authority
- no bypass of enabled / armed / confirm-token / dry-run / kill-switch controls
- no claim of broad live readiness
