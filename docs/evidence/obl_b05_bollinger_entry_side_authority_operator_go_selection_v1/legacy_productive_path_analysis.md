# Legacy Productive Path Analysis (LEGACY_PRODUCTIVE_COUNT=1)

## Exact path

| Field | Value |
|-------|-------|
| File | `src/trading/master_v2/double_play_composition.py` |
| Function | `compose_double_play_decision` |
| Classification (prior reaudit) | **LEGACY_PRODUCTIVE** |
| Role | Residual model-level composer consuming `SideState` (incl. `CHOP_GUARD_BLOCK`) |

## Reachability / callers

| Caller | Nature |
|--------|--------|
| `src/webui/double_play_dashboard_display_json_route_v0.py` | Productive display path (read-only JSON / fixture composition) |
| `tests/trading/master_v2/test_double_play_composition.py` | Tests |
| `tests/trading/master_v2/test_double_play_dashboard_display.py` | Tests |
| `tests/trading/master_v2/test_double_play_pure_stack_contract.py` | Tests |
| Docs handoff references | Documentation |

**Not** on the offline economic orchestrator path that uses `double_play_composition_matrix_v1` as composition SSOT.

## Bollinger / agreement impact

| Question | Answer |
|----------|--------|
| Affects Bollinger `entry_side`? | **No** |
| Direction/Agreement authority for strategy signals? | **No** — consumes already-produced `SideState` / transition / survival / suitability inputs |
| Can invent LONG/SHORT for Bollinger ENTRY? | **No** |
| Competing SideState writer? | **No** — residual **consumer** of CHOP SideState labels |

## Implementation-slice guidance

| Action | Guidance |
|--------|----------|
| Change in entry-side activation slice? | **Leave unchanged** |
| Quarantine required for Bollinger GO? | **No** (orthogonal) |
| Future hygiene (separate GO) | Optional: document as legacy compose vs matrix SSOT; do not couple to Bollinger side work |

```text
LEGACY_PRODUCTIVE_PATH=src/trading/master_v2/double_play_composition.py::compose_double_play_decision
LEGACY_PATH_AFFECTS_BOLLINGER_SIDE=false
```
