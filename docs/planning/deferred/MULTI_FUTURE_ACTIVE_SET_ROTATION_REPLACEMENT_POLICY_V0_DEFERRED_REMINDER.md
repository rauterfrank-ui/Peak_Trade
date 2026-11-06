# Multi-Future Active Set Rotation / Replacement Policy v0 — Deferred Reminder

## Status

```text
DOCUMENT_CLASS=TARGET_ARCHITECTURE
PROCESS_CLASSIFICATION=DEFERRED_DESIGN_REMINDER_ONLY
CLASSIFICATION=REMINDER_ONLY
AUTHORITY_SUPERSEDED_BY_CANONICAL_REGISTER=true
CANONICAL_REGISTER=docs/governance/PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md
CANONICAL_REGISTER_JSON=docs/governance/deferred_work_recovery_register_v1.json
REGISTERED_AS=DEFERRED_REQUIRED_CAPABILITY
TOP20_TO_TOP5_PRODUCTIVE_ROTATION=false
TOP5_PRODUCTIVE=false
TOP5_REGRESSED=false
TOP5_IS_NOT_EXISTING_PRODUCTIVE_OR_REGRESSED_FUNCTION=true
SCOPE_CLASSIFICATION=MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0_REMINDER_NO_IMPLEMENTATION_NO_RUNTIME_NO_ECONOMIC_EVAL_NO_AUTHORITY
REMINDER_ID=MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0
IMPLEMENTATION_STARTED=false
RUNTIME_AUTHORITY_CREATED=false
REMINDER_TRIGGER_BOUND=true
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false
ECONOMIC_EVALUATION_AUTHORIZED=false
RUNTIME_REWIRE_ADMISSIBLE=false
```

This document remains a **deferred design reminder only** (`REMINDER_ONLY`). Canonical deferred-capability authority for roadmap recovery is the Deferred-Work Recovery Register:

- [`docs/governance/PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md`](../../governance/PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md)
- [`docs/governance/deferred_work_recovery_register_v1.json`](../../governance/deferred_work_recovery_register_v1.json)

There the workstream is registered as `DEFERRED_REQUIRED_CAPABILITY` (Phase 6) with machine-readable dependencies and an event-based review trigger. This reminder does **not** implement portfolio rotation, active-set allocation, Multi-Future runtime, economic evaluation, or any trading authority. It does **not** modify Backtest Parity Surface work, scheduler, credentials, orders, adapters, shadow, paper, testnet, canary, live, Master V2, Double Play, Risk/Sizing, Safety, Reconciliation, Promotion, or canonical trading logic.

## Purpose

Ensure Peak Trade does not forget the later portfolio active-set replacement policy before any Multi-Future runtime work begins.

## Required Future Slice

Before implementation may start, the governed slice **`MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0`** must be explicitly ratified and designed as a separate scope — not inferred from ranking, selection, or replacement heuristics alone.

## Mandatory Cursor / Operator Gate

Before **any** of the following scopes, Cursor must surface:

```text
OPERATOR_INPUT_REQUIRED_MULTI_FUTURE_ROTATION_POLICY_REMINDER=true
```

**In-scope triggers (any one activates the gate):**

- `PORTFOLIO_RISK_BINDING_SCOPE_REACHED=true`
- `MULTI_FUTURE_RUNTIME_DESIGN_SCOPE_REACHED=true`
- `MAX_POSITIONS_INCREASE_OPERATOR_RATIFIED=true`
- `MULTI_FUTURE_GOVERNANCE_RATIFIED=true`

**Applies before:**

- Multi-Future runtime design or wiring
- Active-set allocator implementation
- `MAX_POSITIONS` increase beyond Phase-1 safety bounds
- Top20→TopN active trading implementation

## Hard Policy (Non-Negotiable)

1. **Ranking erzeugt keine Runtime-Authority.** Rankings, scores, and universe ordering are research/observation inputs only until separately ratified.
2. **Portfolio Selection erzeugt keine Order-Authority.** Selecting an active set does not authorize entries, exits, or sizing.
3. **Replacement erzeugt keine direkte Order.** Rotation/replacement decisions must not emit orders directly.
4. **Incumbent Exit** must run **reduce-only** through the canonical Exit / Safety / Reconciliation policy chain — never as an ad-hoc replacement shortcut.
5. **New Candidate Entry** is allowed only after:
   - reconciled flat on the incumbent slot, **and**
   - a separate Double Play / Survival / Suitability / Risk / Sizing / Safety pass.
6. **Anti-churn controls are mandatory:** Hysterese, Score-Delta thresholds, Persistenz, Cooldown, and Turnover-Budget must be specified and enforced before any active-set rotation is admissible.

## Explicit Forbidden Flags (This Reminder Scope)

```text
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false
ECONOMIC_EVALUATION_AUTHORIZED=false
RUNTIME_REWIRE_ADMISSIBLE=false
```

## Reuse-First Notes

- Reuse existing governance, Safety, Reconciliation, Double Play, and portfolio research surfaces.
- Do **not** create a parallel rotation SSOT or implicit order path from ranking/selection.
- Extend [`docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`](../../governance/PEAK_TRADE_MAP_OF_TRUTH.md) / Multi-Future Clarification only when the future slice is explicitly opened — not via this reminder.

## No Implementation Statement

```text
NO_IMPLEMENTATION_IN_THIS_SLICE=true
NO_RUNTIME_MUTATION=true
NO_ECONOMIC_EVALUATION=true
NO_AUTHORITY_CREATED=true
```
