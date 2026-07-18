# OBL_B06 — Bollinger Strategy Semantic Ratification v1

```text
STATUS=PARTIAL
BOLLINGER_SEMANTICS_CONFIRMED=false
PRODUCTIVE_SIDE_ACTIVATED=false
ENTRY_SIDE_REMAINS=NONE
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
```

## Scope

Offline, fail-closed forensic ratification of Bollinger **Strategy Intent** vs raw signal vs entry_side.
No live/orders/shadow/testnet. No parameter optimization. No merge.

## Verdict (one line)

Bollinger `-1` is confirmed EXIT and `+1` is confirmed ENTRY-event geometry, but LONG/SHORT Strategy Intent and `entry_side` remain unratified (`CONTRACT_REMAINS_AMBIGUOUS`); Classic LONG reinterpretation is not Integrated-canonical — keep `entry_side=NONE`.

## Artifacts

| File | Purpose |
|------|---------|
| `repo_state.txt` | HEAD / origin/main / stash baseline |
| `search_inventory.txt` | Search scope and hits |
| `semantic_authority_map.md` | Layered authorities + blocker |
| `signal_truth_table.md` | Rohsignal → Intent → Side matrix |
| `classic_vs_integrated_interpretation.md` | Path split evidence |
| `test_results.txt` | Focused pytest |
| `ruff_results.txt` | Ruff on changed Python |
| `diff_summary.txt` | Diff scope |
| `verdict.txt` | Machine-readable closeout |

## Productive code

None. No Strategy-Semantic-Contract activation; no adapter mutation.

## Tests added

`tests/backtest/test_obl_b06_bollinger_strategy_semantic_ratification_v1.py` — locks blocker / NONE / EXIT / path-split invariants.

## Next recommended action

Operator-GO choosing exactly one ratification variant (LONG_ONLY vs EVENT_ONLY vs future symmetric SHORT geometry), then a separate bounded activation slice.
