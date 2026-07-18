# Instrument Classification (A–I)

## Class legend

| Class | Meaning |
|-------|---------|
| A | CHAIN/BINDING_BLOCKER |
| B | MARKET_CONTEXT_OR_SCOPE_BLOCKER |
| C | ENTRY_GENERATION_BLOCKER |
| D | EXIT_DOMINANCE_OR_PREMATURE_EXIT |
| E | LOW_SAMPLE_OR_FIXTURE_INSUFFICIENCY |
| F | COST_DOMINATED |
| G | NEGATIVE_GROSS_EDGE |
| H | ECONOMICALLY_POSITIVE_PRELIMINARY |
| I | TERMINAL_INCONCLUSIVE |

## Per-instrument primary class

| Instrument | Class | Primary blocking boundary | Rationale |
|------------|:-----:|---------------------------|-----------|
| 1INCH | **E** | `trade_sample_insufficiency_with_exit_dominance` | 1 trade (&lt;20); exit/reduce 2492 vs entry 9; single trade gross/net −50 |
| BONK | **E** | `trade_sample_insufficiency_with_exit_dominance` | 0 trades; 52 enter_short intents fail to fill; exit-heavy |
| AVAX | **E** | `trade_sample_insufficiency_with_exit_dominance` | 0 trades; 8 entry intents; exit-heavy |
| SOL | **E** | `trade_sample_insufficiency_with_exit_dominance` | 0 trades; 2 entry intents; exit-heavy |

## Secondary annotations (not primary)

| Instrument | Annotation | Note |
|------------|------------|------|
| All | D-like exit pressure | ADVERSE_EXIT / DOWNSCOPE reduce intents ≫ entry intents; valid market-context signals, economically premature/frequent relative to fills |
| 1INCH | G-like single-trade gross | One losing trade with gross=net=−50; insufficient for class G |
| BONK/AVAX/SOL | Fill-conversion gap | `enter_*` &gt; 0 but `trades=0` — ledger/execution conversion sparse, not a chain value-loss |

## Cross-cutting answers

1. **Zero-trade systemwide technically lifted?** Yes — not systemwide zero (`TOTAL_TRADES=1` on 1INCH). BONK/AVAX/SOL remain zero-trade.
2. **Bottleneck systemwide or instrument-dependent?** Systemwide **economic** bottleneck is low fill density + exit dominance; magnitude of entry intents is instrument-dependent (BONK 52 vs SOL 2).
3. **Both trade directions executed?** No. SHORT SideState reachable on all four; no classified SHORT/LONG ledger sides on the single trade.
4. **`ENTRY_SIDE=NONE` still correct?** Yes — `entry_side_other=0` on all hooked agreement materials; no hidden LONG default in agreement carrier.
5. **Entry∶Exit intent ratio** ≈ 71∶9448 (~1∶133).
6. **Exit-policy signals vs trades** ≈ 9448 signals / 1 trade.
7. **ADVERSE_EXIT / DOWNSCOPE** are valid context signals post-#5340; they drive reduce-heavy outcomes and dominate economics via opportunity reduction, not via a binding bug.
8. **Trade poverty source** — primarily Intent→Ledger/execution fill conversion under exit-heavy policy, not Strategy-signal absence or composition unavailability (composition selects long/short on all four).
9. **First economic opportunity-reduction boundary** — `evaluate_double_play_entry_exit_policy_v0` / adverse-scope reduce path (exit dominance), then offline fill conversion. Not classified as a productive bug.

## Overall primary

`PRIMARY_BLOCKER_CLASS=E`  
`PRIMARY_BLOCKING_BOUNDARY=trade_sample_insufficiency_with_exit_dominance`

## Robustness (Phase D)

Not applicable: no instrument reached ≥20 trades. Sharpe / walk-forward / cost-stress sweeps not run (fail-closed low-sample).
