# Conclusions — Canonical Fill-Conversion Ledger Long-Panel v1

## Observation (directly evidenced)

1. Panel probe over 118 binding members recorded **4226** entry intents,
   **4226** mapped nonzero bars, **4226** engine nonzero bars, and **69**
   total trades (`probe_summary.json`, `instrument_fill_conversion.csv`).
2. Mechanical mismatch sums are **0** for Intent→Map and Map→Engine; funnel and
   engine series match on every instrument.
3. **52** instruments have enter intents and `total_trades=0`, all classified
   `ENGINE_SIGNAL_PRESENT_LEDGER_ZERO_TRADE` with
   `first_drop_boundary=backtest_engine_fill_or_roundtrip_ledger`.
4. For that zero-trade cohort, median enter-impulse length is **1.0** bar
   (max observed impulse length **5**).
5. Dominant enter side by intent count is **SHORT** (4157 vs LONG 69).
6. Chain binding proof records `canonical_engine_signal_source=mv2_decision_replay_series`,
   `authority_effect=NONE`, `runtime_effect=NONE`.
7. Slice contract remains `RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED`,
   `LIVE_AUTHORIZED=false`, `ORDERS=false`, `PRODUCTIVE_FILES_CHANGED=false`.

## Inference (bounded, from observations)

1. The first value-loss boundary for residual enter+zero-trade cases is the
   offline **engine fill / roundtrip ledger** stage after engine signals are
   already present — not Intent generation, not map adapter drop, not a second
   authority/classic bypass.
2. Using the established A–I legend from
   `docs/evidence/canonical_chain_economic_reevaluation_v1/instrument_classification.md`
   (A–G reused without redefinition), the primary class is **E**
   (`LOW_SAMPLE_OR_FIXTURE_INSUFFICIENCY`): sparse trade materialization relative
   to enter/engine signal presence.
3. Class **D** (`EXIT_DOMINANCE_OR_PREMATURE_EXIT`) is a plausible secondary
   annotation because exit/reduce counts dominate entry counts, but it is not
   the first loss boundary for the 52 enter+zero-trade instruments (engine
   nonzero already reached).

## A–G classification record

| Class | Status | Basis |
|:-----:|--------|-------|
| A | excluded | Binding proof + `mv2_decision_replay_series` on all rows |
| B | excluded | Market/scope path produced enters on 115/118 |
| C | excluded | Entry intents present; only LUNA/TRX/USDC are `NO_ENTRY_INTENT` |
| D | secondary only | Exit/reduce dominance annotation |
| **E** | **primary** | Low trade sample / sparse ledger conversion |
| F | not_observed | No cost-decomposition fields on this harness |
| G | not_observed | No per-trade gross-edge economics in this slice |

## Not evidenced / hypotheses (do not treat as findings)

1. **Hypothesis (unproven):** single-bar enter impulses are *causally* rejected by
   a specific fill rule inside `BacktestEngine.run_realistic`. The probe classifies
   the boundary but does **not** record per-bar fill reject codes or fill IDs.
2. **Hypothesis (unproven):** raising impulse length or changing exit policy would
   increase trade count. No parameter experiment was run (and none is authorized
   by this evidence-only closeout).
3. **Unobserved:** exchange/venue reject taxonomy; long_trades vs short_trades
   ledger side columns; per-bar timestamps / order IDs for enter impulses.
4. **Not claimed:** productive bug, authority defect, LONG default, runtime/live
   activation, or requirement that every enter must open a trade.

## Mechanical defect

`MECHANICAL_DEFECT_FOUND=false` — no Intent→Map / Map→Engine / funnel-alignment
anomaly instruments (`mechanical_defect_instruments=0`).

## Closeout implication

Evidence hygiene for PR #5343 can document class **E** at
`backtest_engine_fill_or_roundtrip_ledger` without changing productive code,
parameters, assertions, or authority surfaces.
