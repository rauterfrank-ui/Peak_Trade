---
title: "Master V2 Double Play Capital Slot Ratchet Release Contract v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-26"
docs_token: "DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0"
---

# Master V2 Double Play Capital Slot Ratchet Release Contract v0

## 1. Purpose

This contract defines **per-future capital slot** semantics for Master V2 / Double Play: how a **single selected future** receives a bounded slice of account equity, how that slice **ratchets** on **realized/settled** outcomes, how it **follows losses** without reserve **top-up**, and when **inactivity** or **opportunity-cost** conditions **release** capital back to **reserve or reallocation** without auto-selecting a new instrument.

The goal is to prevent silent **capital drag** from inactive, losing, choppy, or unproductive slots while keeping **Long/Bull** and **Short/Bear** layers on the **same selected future** **sharing one slot** (see [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md)).

## 2. Non-authority note

This file is **docs-only** and **non-authorizing**. It does not:

- implement allocation, sizing, margin, execution, exchange access, or session control
- implement State-Switch runtime, Strategy Suitability, Arithmetic Kernel, or Sequence Survival evaluation
- grant Master V2 approval, Double Play operational authority, PRE_LIVE completion, First-Live readiness, operator signoff, or production readiness
- authorize Testnet, Live, Paper, Shadow, bounded pilot, or real-money operation
- permit orders, exchange calls, market-data fetches, scanner runs, backtests, or mutation of `out/`, Paper, Shadow, Evidence, S3, or registry artifacts

## 3. Scope

**In scope:**

- vocabulary for per-future capital slots and conservative ratchet steps
- realized/settled reset basis (not unrealized mark-to-market alone)
- loss-following slot base and no auto top-up
- cashflow lock vs reinvest split (conceptual)
- inactivity and opportunity-cost release
- reallocation boundary (capital returns to pool; does not auto-trade)
- interactions with Universe Selector, State-Switch and dynamic scope, Arithmetic Sequence Survival, and dashboard display
- fail-closed interpretation for missing governance or evidence

**Out of scope:**

- concrete percentage tables beyond illustrative v0 examples (higher steps require separate governance)
- implementation in `src/` or wiring to runtime (separate slices)

## 4. Core concept

Double Play operates on **one selected future** per state-machine instance (per manifest). That future receives a **capital slot**: a bounded notional or equity slice of the account dedicated to that instrument’s Double Play layers.

The **Long/Bull** layer and **Short/Bear** layer **share the same slot**; they do not receive separate stacked slot sizes for the same selected future.

```text
selected_future_capital_slot
  -> long_bull_layer
  -> short_bear_layer
  -> state_switch_logic
  -> survival_envelope (governed elsewhere)
```

**Example (illustrative, not a mandate):** account equity 1000 EUR, selected-future slot 300 EUR — display labels only until a governed implementation and evidence exist.

## 5. Per-future capital slot

- A capital slot is **per selected future** (per Double Play instance), not an unbounded list of concurrent “full size” positions.
- Slot size is the maximum governed **active** capital envelope for that future’s Double Play context; exact mechanics (notional vs equity vs margin) are venue- and implementation-specific and outside this document.
- Registry names, dashboard labels, and config keys are not authority for slot size; only governed readiness and evidence may elevate operational use elsewhere.

## 6. Conservative ratchet ladder

- Ratcheting **raises the permitted active slot ceiling** when **realized/settled** performance supports it, in **staged** steps (conservative by default).
- Profit step v0 should start conservatively — e.g. an illustrative **10%** step on a governed basis (such as a fraction of **settled slot equity**), not as a trading signal.
- Higher steps (e.g. 15%, 20%, 30%) require later governance and maturity; this contract does not fix a ladder table as operational law.

## 7. Realized / settled reset basis

- Reset and ratchet targets must use **realized** or **settled** slot equity (or an equivalent governed definition), **not** unrealized PnL alone.
- Unrealized PnL may inform risk or observability but must not by itself reset the active slot base for ratchet eligibility under this contract v0.

## 8. Loss-following slot base

- Losses reduce the **effective** slot base following realized or settled outcomes (illustrative: base 300 → 270 after a realized loss).
- The next ratchet target is calculated from the current post-settlement base (e.g. the next step from 270, not from a stale 300).
- Definitional detail belongs in a future pure model or governed adapter; this file states principles only.

## 9. No auto top-up

- Losses do **not** trigger automatic top-up from reserve or unrelated buffers to restore a previous nominal slot ceiling.
- Re-increasing exposure requires explicit governed action and evidence outside this document; “silent refill” semantics are out of scope for authority here.

## 10. Cashflow lock / reinvest split

- Locked cashflow (e.g. externally restricted wallet semantics, if ever applicable) is not automatically part of the active trading slot base until explicitly governed.
- Reinvest vs reserve split must remain legible in governance design; this contract does not implement ledgering.

## 11. Inactivity release

- If the selected future becomes inactive, effectively dead per venue rules, choppy or unproductive beyond governed thresholds, or in operator-defined hazard states, a **hard inactivity release** may free the slot:
  - released capital returns to reserve or a reallocation pool (terminology illustrative);
  - there is no automatic selection of a new future from this release alone.

## 12. Opportunity-cost release

- Opportunity-cost release frees a slot when governed criteria show prolonged low value or better opportunity elsewhere, without this layer alone acting as authority for a new trade decision.

## 13. Reallocation boundary

- Released capital is not authorized to open a new position or select a new instrument by this contract alone; it re-enters a reallocation pool for separate governed Universe or session steps.

## 14. Interaction with Universe Selector

- Instrument selection and Universe Selector surfaces (where defined) own which future is eligible for Double Play context; this contract does not select instruments.
- A release does not imply any selector outcome; the default is no new selection from release only.

## 15. Interaction with State-Switch / Dynamic Scope

- State-Switch and dynamic scope (see the manifest) govern side transitions **within the same** selected future; slot size bounds and ratchet eligibility must stay consistent with pre-authorized envelopes defined elsewhere, without this file mutating runtime code.

## 16. Interaction with Arithmetic Sequence Survival

- Futures arithmetic and path or sequence survival ([MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md)) may block ratchet pre-authorization or slot consumption when envelope conditions fail; capital-slot semantics must not bypass survival governance.

## 17. Dashboard display boundary

- Dashboards may show slot notional labels, ratchet rungs, and release reasons as read-only context.
- UI must not imply Live permission, auto-rebalance, or selector authority from display alone.

## 18. Fail-closed semantics

- Unknown settlement state, missing realized basis, or conflicting governance inputs resolve **fail closed**: no new ratchet step and no implicit top-up (exact runtime mapping: quarantine or hold per governed wiring, not this document).
- This file grants no live authorization.

## 19. Validation / future tests

Future tests (out of scope for this docs slice) may include (non-exhaustive):

- golden vectors for ratchet from settled base changes
- invariant: unrealized PnL alone does not move ratchet eligibility
- invariant: release does not imply new instrument selection
- no test may imply live go

When this file changes, run `validate_docs_token_policy`, `verify_docs_reference_targets`, and `pt_docs_gates_snapshot` as for sibling ops specs.

## 20. Implementation staging

1. Docs — this contract and cross-links in a governed commit slice.
2. Pure model (future) — possible I/O-free helper under `src&#47;trading&#47;master_v2&#47;` (filename illustrative), aligned with the manifest and survival contracts.
3. Wiring (future) — only after Master V2 governance explicitly allows non-authoritative consumption.

## 21. References

- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) — Double Play State-Switch, one selected future, shared layers.
- [MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md) — survival envelope; blockers to operational interpretation elsewhere.
- [MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md) — suitability metadata boundary (read for alignment).
- [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md) — strategy and registry non-authority (read for alignment).
