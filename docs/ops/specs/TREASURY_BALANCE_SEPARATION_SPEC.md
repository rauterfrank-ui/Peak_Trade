# Treasury Balance Separation Spec

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Canonical definition of trading balance vs treasury balance; execution must use trading balance only
docs_token: DOCS_TOKEN_TREASURY_BALANCE_SEPARATION_SPEC

## Intent
This document defines the separation between trading balance and treasury balance so that execution and risk decisions use the correct basis. It complements the operations-level treasury separation (withdraw/transfer blocking) with a data-model-level rule.

## Core Rule
**Execution and risk decisions must use trading balance only.** Treasury balance must not be conflated with trading balance.

## Definitions

### Trading Balance
- Balance visible to the bot key at the exchange
- Used for order placement, position sizing, exposure caps
- Source: trading account / spot-futures margin for the bot key
- Must be the sole basis for execution decisions

### Treasury Balance
- Balance associated with treasury operations (withdrawals, deposits, internal transfers)
- Not visible or usable by the bot key in normal operation
- Treasury key has access; bot key must not use it for execution

## Relationship to Operations Separation
- `src&#47;ops&#47;treasury_separation_gate.py` blocks withdraw, deposit_address, internal_transfer in bot mode
- `config&#47;security&#47;keys.toml` defines bot vs treasury roles
- This spec adds the **balance** rule: even if both balances were queryable, execution must use trading balance only

## Failure Mode
**Wrong balance basis:** Using treasury balance (or an undifferentiated mix) for execution leads to incorrect position sizing, cap violations, or double-counting. Pilot must be blocked until separation is explicit.

## Ops Cockpit
- `guard_state.treasury_separation` = enforced (policy constant)
- Exposure and caps are derived from live_runs / trading context
- No treasury balance is displayed or used in execution path

## Related Documents
- `docs&#47;ops&#47;runbooks&#47;treasury_separation.md` — Operations separation (bot vs treasury key)
- `docs&#47;ops&#47;specs&#47;RECONCILIATION_FLOW_SPEC.md` — Balances/Treasury: must not be conflated
- `docs&#47;ops&#47;specs&#47;PILOT_EXECUTION_EDGE_CASE_MATRIX.md` — Treasury/trading separation unclear → Critical

## Explicit Non-Goals
- no direct execution authority
- no replacement for treasury_separation_gate
- no claim of full balance-model implementation (Phase 0 may not have real exchange balance)
