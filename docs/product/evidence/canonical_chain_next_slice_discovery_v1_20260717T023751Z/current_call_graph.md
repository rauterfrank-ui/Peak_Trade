# Current Call Graph (reconciled main)

## Canonical system path
```
execute_configured_strategy_signal_series_v1
  -> normalize_strategy_signal_to_suitability_agreement_material_v1
  -> build_integrated_offline_replay_input_v1(... strategy_suitability_agreement_material=...)
  -> run_integrated_offline_trading_logic_replay_v1
  -> map_decision_evidence_to_position_signal_v1
  -> BacktestEngine.run_realistic  # fill / cost / equity simulator only
```

## Market context path (parallel, not strategy-fed)
```
bars -> bind_*_canonical_market_context_v1 -> CanonicalMarketContextV1
  -> IntegratedOfflineReplayInputV1.canonical_market_context
```

## Legacy raw-signal research path (intentional, non-system)
```
strategy_signal_fn
  -> declare_legacy_raw_signal_research_path_v1
  -> BacktestEngine.run_realistic  # decisions = raw strategy; orchestrator not invoked
```

## Runtime bridge
```
run_canonical_core_runtime_integration_bridge_v0
  -> offline replay only
  -> integration_status = BOUND_NOT_ACTIVATED  # always
```
