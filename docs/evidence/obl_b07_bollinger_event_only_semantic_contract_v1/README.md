# OBL_B07 — Bollinger EVENT_ONLY Semantic Contract v1

```text
OPERATOR_OPTION=OPTION_EVENT_ONLY
BOLLINGER_EVENT_ONLY_RATIFIED=true
STRATEGY_DIRECTION=NONE
ENTRY_SIDE=NONE
LONG_ONLY_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
```

## Scope

Operator-GO implementation: Bollinger remains a direction-neutral Entry&#47;Exit
event producer. No LONG&#47;SHORT side emission. No runtime&#47;orders&#47;economic activation.

## Artifacts

| File | Purpose |
|------|---------|
| `operator_decision.md` | OPTION_EVENT_ONLY ratification record |
| `authority_boundary.md` | What the contract may &#47; may not do |
| `event_truth_table.md` | Raw → Event → Direction → Side |
| `classic_integrated_boundary.md` | Classic LONG non-canonical for MV2 |
| `changed_files.txt` | Diff inventory |
| `test_results.txt` | Focused pytest |
| `ruff_results.txt` | Ruff on changed Python |
| `diff_summary.txt` | Selector &#47; scope summary |
| `verdict.txt` | Machine-readable closeout |

## Productive changes

- `src&#47;strategies&#47;bollinger_event_semantic_contract_v1.py` (new)
- Adapter binds Bollinger through EVENT_ONLY path; `entry_side` stays `NONE`
