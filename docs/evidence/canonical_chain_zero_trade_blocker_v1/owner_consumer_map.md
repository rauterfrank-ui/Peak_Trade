# Owner → Consumer Map

| Role | Owner | Consumer(s) | Notes |
|------|-------|-------------|-------|
| Strategy raw signal | `backtest.strategy_signal_binding_v1.execute_configured_strategy_signal_series_v1` | Agreement adapter | Non-authority |
| Bollinger event semantics | `strategies.bollinger_event_semantic_contract_v1` | Adapter | EVENT_ONLY; side NONE |
| Agreement material | `backtest.strategy_signal_suitability_agreement_adapter_v1.normalize_...` | Wiring + suitability | `entry_side=NONE` for Bollinger |
| Directional cycle resolve | `backtest.mv2_research_wiring_v1.resolve_agreement_bound_directional_cycle_v1` | price_path projector | Explicit side only |
| Market/strategy price_path | `backtest.mv2_research_wiring_v1.project_mv2_agreement_bound_price_path_v1` | Integrated DA inputs | **fixed**: prior_mark market path |
| Prior mark trailing | `MV2IntegratedReplayBarSequenceStateV1.prior_mark_price` | `_build_replay_input` | **added** |
| CMC | `canonical_market_context_v1.bind_canonical_market_context_event` | Scope + DA trust gates | unchanged |
| Scope / RuntimeScope | `canonical_scope_initialization_v1` + `RuntimeScopeState` | ScopeEvent / trailing | unchanged |
| ScopeEvent | `deterministic_scope_event_generator_v1` | `transition_state` | unchanged |
| **Direction / Switch** | `double_play_state.transition_state` | Entry direction_state | sole authority |
| Suitability side agreement | `suitability_binding_v1.derive_effective_strategy_side_agreement_v1` | Suitability eligibility | **fixed**: entry_side-aware |
| **Composition** | `double_play_composition_matrix_v1.evaluate_double_play_composition_matrix_v1` | Entry/exit | sole composition authority |
| Entry eligibility | `double_play_entry_exit_policy_v0` | OI / evidence | unchanged |
| Order intent | `governance.canonical_order_intent_v1` via offline adapter | Plan-only | offline bind only |
| Orchestrator | `integrated_offline_trading_logic_replay_v1` | Research wiring | consumes intermediates |
| Quarantine / bridge | `double_play_sole_authority_quarantine_v1` | Status freeze | `BOUND_NOT_ACTIVATED` |

No new Direction or Composition authority introduced.
