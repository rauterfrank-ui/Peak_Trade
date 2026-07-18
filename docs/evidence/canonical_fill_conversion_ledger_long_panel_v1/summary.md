# Summary — Canonical Fill-Conversion Ledger Long-Panel v1

```text
SLICE=CANONICAL_FILL_CONVERSION_LEDGER_LONG_PANEL_V1
PR_NUMBER=5343
PR_HEAD_DOCUMENTED=9320cd3848786cd0a5f7dedfd9dd6a5fed76758f
BASE_SHA=14e1b8a94add3fa31eb21fa71fb5dae405ea413b
BRANCH=audit/canonical-fill-conversion-ledger-long-panel-v1
PRODUCTIVE_FILES_CHANGED=false
PRIMARY_BLOCKER_CLASS=E
FIRST_VALUE_LOSS_BOUNDARY=backtest_engine_fill_or_roundtrip_ledger
MECHANICAL_DEFECT_FOUND=false
ENTRY_SIDE=NONE
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
LIVE_AUTHORIZED=false
ORDERS=false
```

## Verdict

On the durable offline 118-member futures panel, Intent→Mapped-Signal→Engine-Signal
conversion is mechanically intact (`enter_map_mismatch_sum=0`,
`enter_engine_mismatch_sum=0`, funnel↔engine parity on all instruments). Residual
enter+zero-trade cases (52/118) drop at `backtest_engine_fill_or_roundtrip_ledger`
under sparse single-bar enter impulses (median impulse length 1.0). Primary
blocker class is **E** (`LOW_SAMPLE_OR_FIXTURE_INSUFFICIENCY`). No productive
authority/binding defect was found.

## Panel totals (observed)

| Metric | Value |
|--------|------:|
| Instruments | 118 |
| Bars | 348454 |
| Entry intents | 4226 (long 69 / short 4157) |
| Exit/reduce | 240230 |
| Mapped nonzero bars | 4226 |
| Engine nonzero bars | 4226 |
| Total trades | 69 |
| Instruments with enter | 115 |
| Instruments with trades | 63 |
| Enter+zero-trade | 52 |
| Mechanical defects | 0 |

## A–G classification (repo legend)

Legend reused exactly from
`docs/evidence/canonical_chain_economic_reevaluation_v1/instrument_classification.md`
(A–I table; A–G applied here without redefinition):

| Class | Meaning | This slice |
|:-----:|---------|------------|
| A | CHAIN/BINDING_BLOCKER | **excluded** — chain bound (`mv2_decision_replay_series`) |
| B | MARKET_CONTEXT_OR_SCOPE_BLOCKER | **excluded** — enter intents on 115/118 |
| C | ENTRY_GENERATION_BLOCKER | **excluded** — 4226 entry intents present |
| D | EXIT_DOMINANCE_OR_PREMATURE_EXIT | **secondary annotation** — exit/reduce ≫ entry |
| **E** | **LOW_SAMPLE_OR_FIXTURE_INSUFFICIENCY** | **primary** — sparse engine→ledger conversion |
| F | COST_DOMINATED | **not_observed** on this harness |
| G | NEGATIVE_GROSS_EDGE | **not_observed** on this harness |

### Why E is primary

52 instruments show enter intents that map and reach engine nonzero bars, yet
`total_trades=0`. Aggregate trades remain low (69 / 4226 enters). That matches
class **E** (low sample / fixture insufficiency at fill/roundtrip ledger), not a
chain/binding (A), scope (B), or entry-generation (C) blocker.

### Secondary

Class **D** is observed only as exit-pressure annotation (`exit_or_reduce=240230`
vs `entry_intents=4226`). It is not primary because the first value-loss for the
zero-trade cohort is after engine signal presence.

## Safety / contract

- Evidence/docs/hygiene only for this closeout slice
- `entry_side=NONE`; no LONG default introduced
- Runtime bridge `BOUND_NOT_ACTIVATED`
- `LIVE_AUTHORIZED=false`, `ORDERS=false`
- No second authority / classic bypass (`classic_bypass` count = 0)

## Hygiene note

`instrument_fill_conversion.csv` line endings normalized CRLF→LF so
`git diff --check` passes. Semantic CSV cells unchanged (row/column equality
after newline normalization).
