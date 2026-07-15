"""
Peak_Trade Backtest Engine - Registry Integration (dead-path removed)

Slice-3 classic caller canonicalization removed the unused registry-engine
entrypoints:

* run_portfolio_from_registry (C1)
* run_single_strategy_from_registry (C2)

Use instead:

* Legacy/research (RAW_SIGNAL_RESEARCH / LEGACY_NON_AUTHORITATIVE):
  ``src.backtest.engine.run_single_strategy_from_registry`` /
  ``src.backtest.engine.run_portfolio_from_config``
* Canonical system economic evidence:
  ``src.backtest.mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1``
  with ``engine_signal_source=mv2_decision_replay_series``
"""
