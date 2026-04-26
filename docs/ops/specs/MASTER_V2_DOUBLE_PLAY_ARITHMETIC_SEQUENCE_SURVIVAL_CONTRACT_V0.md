---
title: "Master V2 Double Play Arithmetic Sequence Survival Contract v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-26"
docs_token: "DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0"
---

# Master V2 Double Play Arithmetic Sequence Survival Contract v0

## 1. Purpose

This contract defines how **Futures arithmetic truth** and **sequence-of-returns (path) survival** requirements integrate with the Master V2 **Double Play** trading logic:

- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) (State-Switch Logic, dynamic scope, hot-path boundaries).

**Core rule:**

```text
Master V2 / Double Play may only switch Long/Bull and Short/Bear sides inside an arithmetic-true and sequence-survivable envelope.
```

**Alpha or directional skill alone is insufficient** if the implementation cannot demonstrate correct futures economic arithmetic and survivable path properties under the governed envelope.

## 2. Non-authority note

This file is **docs-only** and **non-authorizing**. It does **not**:

- grant order placement, execution, or session permission
- authorize testnet, live, or bounded real-money operation
- replace Risk/Safety, governance, or evidence authorities
- assert that any candidate or run satisfies these requirements

If text here appears to conflict with a higher-priority **contract** or **manifest**, the stricter or more specific binding document **wins** (fail-closed).

## 3. Scope

**In scope:**

- Contractual **integration vocabulary** between Double Play, **Futures arithmetic**, and **sequence survival** metrics
- **Pre-arm / runtime envelope** role of arithmetic and sequence inputs (as **inputs** to a pre-authorized envelope, not as hot-path recompute)
- **Layer-specific** and **pair-level** requirements for Long/Bull and Short/Bear
- **Stress path** classes that State-Switch must survive in analysis (not in hot path)
- Boundaries: hot path, promotion, dashboard, fail-closed semantics

**Out of scope:**

- Concrete implementation code, exchange adapters, or strategy logic changes
- Live authorization, testnet go, or evidence writes
- Replacing the Double Play **state machine** manifest; this document **complements** it

## 4. Core synthesis

Double Play is not only **which side is active** (State-Switch), but **whether the switch can be sustained** under:

1. **Futures-arithmetic-correct** economics (fees, slippage, funding, margin, contract constraints).
2. **Path survival** of equity/margin under realistic **ordering** of shocks (sequence risk), including switch clusters and near-liquidation paths.

The **Double Play Survival Envelope** (§8) is the conceptual **join** of:

- the **Dynamic Scope Envelope** (from the trading-logic manifest)
- a **Futures arithmetic kernel** (§6) — authoritative treatment of notional, contract size, fees, slippage, funding, margin, liquidation distance, effective leverage, rounding (see §4 of purpose list)
- a **Sequence Survival** assessment layer (§7) — path metrics (see §3 of required content list in brief)

## 5. Architecture position

| Layer (conceptual) | Role | Hot path? |
|--------------------|------|-----------|
| **State-Switch** | Side activation / blocking / pending (manifest) | **Lightweight** state updates only |
| **Dynamic Scope Envelope** | Pre-authorized bounds; trailing/bounded scope | **Lightweight** boundary state |
| **Arithmetic Kernel** | **Correct** PnL economics for futures, per fill and mark | **Not** a full re-audit every tick; **pre-compiled** into envelope where possible |
| **Sequence Survival** | Path metrics, stress orderings, fragility / near-miss | **Pre-arm** and **governance**; not continuous heavy compute in the switch **tick** |
| **Risk/Safety** | Hard limits, Kill-All, pre-authorization | As in existing contracts |

## 6. Arithmetic Kernel role

The **Arithmetic Kernel** (future implementation) is the **authoritative** place for **Futures economic truth** as applied to Double Play, including at minimum:

- **notional** and **contract size** (and any contract multiplier)
- **fees** (maker/taker or venue model as contractually defined)
- **slippage** (model and units consistent with venue)
- **funding** (accrual sign and timing conventions)
- **margin** and **maintenance** versus **mark**
- **liquidation distance** (or equivalent) under the venue model
- **effective leverage** (definition fixed per contract family)
- **exchange constraints**: tick/step size, **min_notional** / **min_qty**, **rounding** policy

**Requirement:** Long and Short layers each require a distinct **arithmetic fingerprint** (inputs, assumptions, and stress bands) that can be **compared** for symmetry errors before promotion.

**Not hot path:** the kernel does not imply running a **full** inventory, **backtest**, or **reconciliation** on every **State-Switch** tick. Outputs must be **vetted pre-arm** or reduced to **O(1)** updates of **already-authorized** bounds.

## 7. Sequence Survival Layer role

The **Sequence Survival** layer (future implementation) captures **order-dependent** path risk, including:

- **Path survival ratio** (or defined survival functional — exact definition in a later versioned contract)
- **Early loss toxicity** (loss mass before any recovery, under defined path classes)
- **Margin buffer at risk** (statistic of buffer erosion along path)
- **Sequence fragility index** (sensitivity to reordering of shocks)
- **Liquidation near-miss profile** (bucketed distance events)
- **Governance breach frequency** (in simulation / replay only — not an authority to waive limits)

**Requirement:** these are **pre-arm** / **governance** / **evidence** inputs unless explicitly reduced to a **lightweight** scalar already embedded in the runtime envelope. They are **not** a substitute for the **Kill-All** or **hard** Risk/Safety **block**.

## 8. Double Play Survival Envelope

The **Double Play Survival Envelope** is the **combined** pre-authorized envelope that must be satisfied to **arm** or **retain** side switches:

- **State-Switch** eligibility from the [trading logic manifest](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md)
- **Static hard limits** and **dynamic scope rules** (as there)
- **Arithmetic truth** constraints from §6 (all relevant futures fields **consistent** and **bounded**)
- **Sequence survival** thresholds from §7 (per promotion tier or candidate class — exact numeric gates are **governance** and **out of this doc**)

**Pair requirement:** the Long/Bull and Short/Bear **pair** must have **defined Double Play pair survival metrics** (joint stress under shared instrument and margin model).

## 9. Long/Bull layer arithmetic requirements

The Long/Bull **layer** (strategy family or bundle under governance) must have:

- explicit **arithmetic assumptions** (fee tier, slippage model, funding sign convention)
- **isolated** stress results under the Arithmetic Kernel (no hidden cross-subsidy from the Short side)
- documented **fingerprint** suitable for **diff** against Short/Bear assumptions

**Insufficient:** PnL that only matches **spot-style** or **omits funding** for perpetuals, unless the manifest explicitly **scopes** a non-perp instrument (separate path).

## 10. Short/Bear layer arithmetic requirements

The Short/Bear **layer** must meet the same class of requirements as §9, with **short-specific** sign conventions for PnL, margin, and funding.

**Asymmetry:** any intentional asymmetry (e.g. different fee tier assumptions) must be **declared** and **bounded** in the envelope, not as implicit alpha.

## 11. State-switch sequence survival requirements

**State-Switch** paths (manifest §3–4) must be **stress-testable** under these **orderings** (list is **exemplary**, not exhaustive):

- Long **loss** then Short **loss** (same session / simulation horizon as defined in governance)
- Short **loss** then Long **loss**
- **Chop / ping-pong** switch clusters (rapid bull/bear flips) under widened spread or **spread expansion during switch**
- **Funding shock** path (jumps in funding accrual)
- **Margin compression** path (tighter buffer while active)
- **Liquidation near-miss** path (close approach without relying on ad-hoc rescue)

**Outcome:** the switch machinery must be shown **compatible** with survival constraints — not only that each side is profitable in isolation.

## 12. Pre-arm / runtime envelope integration

- **Pre-arm:** Arithmetic fingerprints and **baseline** sequence metrics are **ingested** before the hot path is allowed to take **State-Switch** actions beyond observe/neutral, per governance.
- **Runtime:** only **pre-authorized** updates (lightweight) are allowed on the **hot path** (as in the **Hot-path boundary** section of the [manifest](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) §14): **no** heavy recompute, **no** new governance decisions per tick, **no** backtest, **no** exchange I/O, **no** evidence writes.

**Risk/Safety** remains a **pre-authorized** **runtime** envelope: limits are **vetted** out-of-band, not re-derived from scratch in the **switch** window.

## 13. Hot-path boundary

In the **hot path**, the system **must not** run (non-exhaustive, aligned with manifest spirit):

- full **sequence stress** re-evaluation, **arithmetic inventory** reconciliation, or **backtests**
- **AI** / full **selector** / **governance** recomputation
- **exchange** calls, **evidence** or **S3** writes, **MLflow** experiment writes, or **registry** mutation

**Lightweight** updates of **scope** / **counter** / **anchor** / **chop** state, as pre-authorized, remain in scope of the [manifest](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md).

## 14. Promotion / governance gates

- Promotion, bounded pilot, and live-adjacent **gates** are **external** to this contract’s authority.
- This contract **informs** what **evidence** and **invariants** must be reviewable: arithmetic **parity** and **sequence survival** **must** be **auditable** before any later execution slice is considered **candidates-ready**.

## 15. Dashboard display boundary

Dashboards and operator surfaces may **display** envelope status, **non-authority** **metrics** strings, and **banners** (e.g. no-live) per existing cockpit contracts.

They **must not** **authorize** side switches, **override** Risk/Safety, or **assert** that arithmetic/sequence **proof** is **complete** unless backed by **governed** evidence **outside** this file.

## 16. Fail-closed semantics

If **any** of the following is **unknown** or **invalid** under the venue model, the implementation **must** **fail closed** to **no new** side **activation** (interpretation: block **arming** of the next side, or force **neutral/observe** per manifest state machine, per governed wiring — exact runtime mapping is **not** this doc):

- **invalid** **envelope** (limits or arithmetic constraints not satisfied)
- **missing** **funding** or **margin** parameters required by the **Arithmetic Kernel** contract family
- **sequence survival** **below** the **governed** **threshold** for the **candidate** **class**

**No live** interpretation of this file may bypass Risk/Safety or Kill-All.

## 17. Validation / future tests

**Future** tests (out of scope for this **docs** commit) should **include** (non-exhaustive):

- **invariant** tests for **futures** PnL sign and **funding** accrual under fixed **golden** vectors
- **regression** on **notional** / **qty** / **round** to **min** **tick** and **min_notional**
- **order-sensitive** path tests for **pair** survival and **State-Switch** **stress** **orderings** (§11)
- **no** test may **imply** **live** **go**

## 18. Implementation staging

1. **Inventory** of existing PnL/fee/margin/rounding code paths and gaps (read-only, completed or parallel).
2. **Arithmetic Kernel** contract family / module boundaries (separate follow-on contracts as needed).
3. **Sequence Survival** **metrics** **definitions** (versioned) and **governance** tie-in.
4. **Pure** models and **adapters** with **no** **hot-path** **heavy** **compute** **by default**.

## 19. References

- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) — Double Play state machine, **Scope**, **Kill-All** vs **State-Switch**, **hot** **path** rules.
- [MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md) — strategy **suitability** **projection** (metadata; **not** **activation** or **registry** **authority**).
- [MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md) — **capital** **slot** **ratchet** / **release** (docs-only; may interact with **survival** / **governance** **interpretation**; **not** **Live** or **order** **permission**).
- [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md) — strategy / Master V2 **boundary** (docs-only).
- [FUTURES_BACKTEST_REALISM_CONTRACT_V0.md](FUTURES_BACKTEST_REALISM_CONTRACT_V0.md) — futures **realism** **discipline** (if present; **read** for alignment).
- [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md) — **tick** / **step** / **metadata** (if present; **read** for alignment).
- [FUTURES_RISK_SAFETY_KILLSWITCH_CONTRACT_V0.md](FUTURES_RISK_SAFETY_KILLSWITCH_CONTRACT_V0.md) — **Risk** and **safety** **posture** (if present; **read** for alignment).
