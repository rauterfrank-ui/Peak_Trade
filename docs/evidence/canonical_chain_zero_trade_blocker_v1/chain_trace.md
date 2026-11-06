# Chain Trace — Canonical Zero-Trade Blocker v1

Logical authority order toward a trade. Orchestrator still evaluates composition before `transition_state` in code order; entry policy consumes both.

| # | Boundary | Owner | Consumer | Before (OPTION_D leftover) | After (this slice) | Drop? |
|---|----------|-------|----------|----------------------------|--------------------|-------|
| 1 | Strategy signal | `execute_configured_strategy_signal_series_v1` | Agreement adapter | Bollinger ENTRY `+1` present | unchanged | no |
| 2 | Agreement material | `normalize_strategy_signal_to_suitability_agreement_material_v1` | Wiring / suitability | `event_kind=ENTRY`, `entry_side=NONE` | unchanged (OPTION_D) | no |
| 3 | Directional cycle | `resolve_agreement_bound_directional_cycle_v1` | price_path projector | `None` (correct; no side invention) | unchanged | no |
| 4 | **price_path** | `project_mv2_agreement_bound_price_path_v1` | DA dual-lane | **`(mark, mark)` flat** whenever cycle unbound | unbound + `prior_mark` → **`(prior, mark)` market path**; explicit cycle still relative impulse | **YES — first value loss** |
| 5 | CMC / Scope / ScopeEvent | CMC + `RuntimeScopeState` + generator | `transition_state` | bound | bound; `prior_mark_price` trailed bar-to-bar | no |
| 6 | `transition_state` | `double_play_state.transition_state` | entry direction_state | reached; initial often `LONG_ARMED` | unchanged owner | no |
| 7 | Suitability agreement | `derive_effective_strategy_side_agreement_v1` | Suitability binding | ENTRY `+1` → **AGREE LONG / DISAGREE SHORT** (invented LONG) | `entry_side=NONE` → **AGREE both** (timing-only); LONG/SHORT carriers remain asymmetric | **YES — bear asymmetry** |
| 8 | Composition | `evaluate_double_play_composition_matrix_v1` | entry/exit | observe / `selected_side=none` (no DA candidates) | bull/bear control → LONG/SHORT selected | recovered |
| 9 | Entry eligibility | `evaluate_double_play_entry_exit_policy_v0` | OI binding | no ENTER_* | bull → `enter_long`; bear → `enter_short` | recovered |
| 10 | Order intent | `build_canonical_order_intent_v1` via offline adapter | plan-only | not reached | bull control binds OI; execution still false | recovered (offline) |
| 11 | Integrated replay | `run_integrated_offline_trading_logic_replay_v1` | wiring / engine signal | consumed observe | consumes composition + transition + intent returns | no ignore |
| 12 | Runtime bridge | quarantine | live | `BOUND_NOT_ACTIVATED` | unchanged | n/a |

## First value-loss boundary

```text
FIRST_VALUE_LOSS_BOUNDARY=
  project_mv2_agreement_bound_price_path_v1
  → DirectionalAssessment / composition
```

Concrete: ENTRY present + `entry_side=NONE` → directional cycle `None` → **flat price_path** → DA strength `0` → composition `observe` → no Entry/Order intent.

Secondary loss (Bear): even with a bearish market path, suitability **DISAGREE SHORT** demoted the bear lane.

Stops/fees/slippage are **downstream** of intent formation and were not used as the zero-intent explanation.
