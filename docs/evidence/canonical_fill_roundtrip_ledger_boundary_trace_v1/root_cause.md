# Root Cause — Fill / Roundtrip / Ledger Boundary Trace v1

## Decision framework (strict)

| # | Class | Applied? |
|---|-------|----------|
| 1 | Mechanical defect | **No** (not reproduced) |
| 2 | Contract mismatch / asymmetry | **Yes** (secondary to E): SHORT map vs long-only open |
| 3 | Legitimate fail-closed behavior | **Yes** (`entry_side=NONE`, sizing reject, `-1` without open) |
| 4 | Missing market/price/state data | **No** in harness scenarios |
| 5 | Adapter / identifier loss | **No** (map 1:1; ledger ids stable) |
| 6 | Fill / position matching error | **No** (coupled; exit requires open) |
| 7 | Roundtrip aggregation error | **No** (full close = one trade) |
| 8 | Ledger persistence error | **No** (1:1 when materializer called) |
| 9 | Reporting-only loss | **Only if** materializer skipped (scenario H) |
| 10 | Not reproducible | Separable fill-without-position / fills-without-RT **not reproducible** as defects |

## Root-cause statement

On the canonical MV2 research path, decision outcomes are mapped by
`map_decision_evidence_to_position_signal_v1` (`enter_long→+1`, `enter_short→-1`).
The default fill simulator `BacktestEngine.run_realistic(use_execution_pipeline=False)`
opens **only** on `signal == +1` and treats `signal == -1` as exit **iff** a long is open.
Therefore SHORT-accepted intents reach engine-nonzero bars but produce **zero** fills,
roundtrips, and ledger trades. First value-loss boundary remains
`backtest_engine_fill_or_roundtrip_ledger`. Primary blocker class remains **E**;
secondary annotation **D** (exit dominance) is unchanged from PR #5343.

## Mechanical defect

`MECHANICAL_DEFECT_FOUND=false`

No productive path was found where:

- an accepted LONG open was dropped after fill,
- a completed roundtrip failed ledger materialization when invoked,
- or identifiers/sides were corrupted across instruments.

## If a repair is later authorized (not in this slice)

Minimal repair scope (recommendation only — **not implemented**):

1. Explicit contract ratification: either
   - document SHORT→legacy as non-materializing (fail-closed), or
   - bind a short-capable execution owner under separate operator GO.
2. Owners likely touched in a future repair GO:
   - `src/backtest/engine.py` and/or execution-pipeline binding in `mv2_research_wiring_v1.py`
   - map/parity contracts in `strategy_signal_binding_v1.py`
3. Tests to extend under that GO:
   - engine short-open contracts
   - funnel/trade alignment for `enter_short`
   - ledger side semantics for negative size

No productive repair in this audit PR.
