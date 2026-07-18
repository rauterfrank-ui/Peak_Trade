# A–G Classification — Fill / Roundtrip / Ledger Boundary Trace v1

## Legend (exact reuse)

Source: `docs/evidence/canonical_chain_economic_reevaluation_v1/instrument_classification.md`

| Class | Meaning |
|:-----:|---------|
| A | CHAIN/BINDING_BLOCKER |
| B | MARKET_CONTEXT_OR_SCOPE_BLOCKER |
| C | ENTRY_GENERATION_BLOCKER |
| D | EXIT_DOMINANCE_OR_PREMATURE_EXIT |
| E | LOW_SAMPLE_OR_FIXTURE_INSUFFICIENCY |
| F | COST_DOMINATED |
| G | NEGATIVE_GROSS_EDGE |

(H/I exist in the source legend but are out of scope for this A–G application.)

---

## Observed loss paths

| Scenario | First-loss boundary | Class | Kind |
|:--------:|---------------------|:-----:|------|
| A | NONE (complete LONG RT) | none | healthy path |
| B | `backtest_engine_fill_or_roundtrip_ledger` | **E** (+ contract ambiguity) | fail-closed long-only open vs SHORT map |
| C | NONE (expected zero) | none | fail-closed `entry_side=NONE` |
| D | `backtest_engine_fill_or_roundtrip_ledger` | E-like | legitimate sizing reject |
| E | NONE / not separable | none | no distinct fill layer |
| F | NONE (EOD completes RT) | none | unmatched signal-exit ≠ drop |
| G | NONE / not separable | none | exit appends completed trade |
| H | ledger only if materializer skipped | none | reporting-only when not called |
| I | NONE (unsupported) | none | contract: partial false |
| J | NONE | none / not F | costs change economics, not existence |
| K | NONE | none | no cross-instrument match |
| L | NONE | none | stable ids |

---

## Why class E remains primary

1. PR #5343 already showed Intent→Mapped→Engine mechanically intact and residual enter+zero-trade at `backtest_engine_fill_or_roundtrip_ledger`.
2. This trace reproduces the dominant mechanism: `enter_short` → mapped `-1` → legacy engine no-op when flat → zero fills/roundtrips/ledger.
3. That is **fixture/path insufficiency for SHORT (and sparse LONG) trade materialization** on the canonical legacy long-open-only simulator — matching **E** (`LOW_SAMPLE_OR_FIXTURE_INSUFFICIENCY`), not a chain/binding break.
4. No scenario produced a silent mechanical drop of an already-completed LONG roundtrip or a ledger row when materialization was invoked.

## Why class D remains secondary

- Panel-level exit/reduce ≫ entry remains a valid **annotation** (PR #5343 / economic reevaluation).
- It is not the first loss for the SHORT-mapped zero-trade path: loss occurs at engine fill/open, before exit dominance can act on an open book.
- Status: **secondary annotation only**.

## Classes excluded

| Class | Status | Why |
|:-----:|--------|-----|
| A | excluded | Static + dynamic binding proof: map/wiring/replay owners intact; harness non-authoritative |
| B | excluded | Scenarios reach mapped decisions/signals without CMC/scope denial |
| C | excluded | Entry intents/decisions present (`enter_long` / `enter_short` map correctly) |
| F | not observed | Nonzero fees/slippage (scenario J) preserve trade existence |
| G | not observed | No per-trade gross-edge panel economics in this slice |

## Mechanical defects vs fail-closed contract

| Observation | Classification |
|-------------|----------------|
| SHORT map → zero trades on legacy | **Fail-closed / contract asymmetry** (long-open-only), class E — **not** mechanical defect |
| `entry_side=NONE` → no direction | **Legitimate fail-closed** |
| Sizing reject → blocked_trades | **Legitimate fail-closed** |
| Partial unsupported | **Contract** |
| Ledger missing only if not called | **Reporting-only** (not engine defect) |
| Fill without position / fills without RT | **Not separable** on legacy path — not a reproducible defect |

## Not decidable in this slice

- Whether a future ratified short-capable execution path should become the MV2 research default (requires separate operator GO; out of scope).
- Panel-wide economic optimality of exit/reduce density (class D annotation only).
