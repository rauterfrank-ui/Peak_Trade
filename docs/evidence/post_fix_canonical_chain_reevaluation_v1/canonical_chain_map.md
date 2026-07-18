# Canonical Chain Map

Executed research path (offline, `run_mv2_research_backtest_wiring_v1`):

```text
strategy signal (BollingerBandsStrategy.generate_signals)
  → research wiring (_build_replay_input + mark-relative BPS distances)
  → canonical market context (bind_canonical_market_context_event)
  → DynamicScopeUpdate (RuntimeScopeState / update_dynamic_boundaries)
  → ScopeEvent (generate_deterministic_scope_event)
  → map (_canonical_scope_event_to_scope_event)  [dual-dimension]
  → PolicySignal (derive_scope_adverse_exit_signal_v0)  [exit dimension]
  → transition_state (SideState sole owner)
  → composition matrix (evaluate_double_play_composition_matrix_v1)
  → entry/exit policy (evaluate_double_play_entry_exit_policy_v0)
  → offline execution simulation (mapped position / bar loop)
  → trade/result ledger (BacktestResult.trades / compute_backtest_stats)
```

## Boundary table

| Boundary | File | Symbol | Owner/Consumer | Active |
|----------|------|--------|----------------|--------|
| Strategy signal | `src/strategies/bollinger.py` | `generate_signals` | producer | active |
| Research wiring | `src/backtest/mv2_research_wiring_v1.py` | `_build_replay_input` / `compute_mv2_research_scope_distances_absolute_from_mark_v1` | distance owner | active |
| CMC | `src/trading/master_v2/canonical_market_context_v1.py` | `bind_canonical_market_context_event` | CMC owner | bound |
| Dynamic scope | `src/trading/master_v2/double_play_state.py` | `update_dynamic_boundaries` | trailing owner | active |
| ScopeEvent | `src/trading/master_v2/deterministic_scope_event_generator_v1.py` | `generate_deterministic_scope_event` / `_select_directional_kind` | scope owner | active |
| Dual map | `src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py` | `_canonical_scope_event_to_scope_event` | consumer map | active |
| Adverse PolicySignal | `src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py` | `derive_scope_adverse_exit_signal_v0` | exit dimension | active |
| SideState | `src/trading/master_v2/double_play_state.py` | `transition_state` | **CANONICAL_DIRECTION_OWNER** | active |
| Composition | `src/trading/master_v2/double_play_composition_matrix_v1.py` | `evaluate_double_play_composition_matrix_v1` | **CANONICAL_COMPOSITION_OWNER** | active |
| Entry/Exit | `src/trading/master_v2/double_play_entry_exit_policy_v0.py` | `evaluate_double_play_entry_exit_policy_v0` | intent owner | active |
| Execution sim | `src/backtest/mv2_research_wiring_v1.py` | offline bar loop | consumer | active offline |
| Ledger | `src/backtest/stats.py` | `compute_backtest_stats` | consumer | active |

## Authority contracts (unchanged)

- Direction/SideState owner: `trading.master_v2.double_play_state.transition_state`
- Composition owner: `trading.master_v2.double_play_composition_matrix_v1.evaluate_double_play_composition_matrix_v1`
- ScopeEvent ≠ PolicySignal (dual dimension)
- Runtime bridge: `BOUND_NOT_ACTIVATED`
- `entry_side=NONE`, `LIVE_AUTHORIZED=false`, `ORDERS=false`

## Bull/Bear asymmetry observed (1INCH)

Research seed starts `LONG_ARMED`. Post-fix, downscope-confirmed dominates → `short_active`
majority of hooked bars. Upscope path still emits (`upscope_confirmed=277`). Not a LONG-only
productive default after transitions begin.
