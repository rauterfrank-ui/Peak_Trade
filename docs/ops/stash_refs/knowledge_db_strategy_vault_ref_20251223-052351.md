# Stash Reference Export — knowledge_db_strategy_vault_ref

- **Export time:** 20251223-052351
- **Stash:** `stash@{0}` (matched keyword: `knowledge-db`)
- **Branch:** feat/knowledge-db-strategy-vault-v0
- **Date:** ~22. Dezember 2025

## Context

This stash was triaged on 23. Dezember 2025:

- Total: 137 files changed, 365 insertions(+), 78 deletions(-)
- Most files: whitespace/trailing-newlines only (+1 line)
- Only 2 files had significant changes (>= 50 lines)
- **Conclusion:** Features were already implemented in main in different form
  - src/live/status_providers.py (new in main)
  - src/webui/services/live_panel_data.py (new in main)
  - docs/webui/LIVE_STATUS_PANELS.md (new in main)

**Rationale for export:**
- Keep a durable reference without keeping a live stash forever
- Preserve significant implementation details for archaeological purposes
- Allow safe stash deletion after export

## Selected files (exported in patch)

- src/reporting/live_status_snapshot_builder.py
- src/webui/health_endpoint.py

### File Details

#### src/reporting/live_status_snapshot_builder.py
- Changes: +64 lines (refactoring)
- Main changes:
  - Auto-discovery function: `build_live_status_snapshot_auto()`
  - Separation: `get_auto_panel_providers()` vs `get_default_panel_providers()`
  - Panel providers now required (not optional)

#### src/webui/health_endpoint.py
- Changes: +154 lines (new features)
- Main changes:
  - Panel status integration in `/health/detailed`
  - New `overall_status` logic: ok/degraded/blocked
  - HTTP status codes based on panel status
  - New `_get_panel_status()` function

## Full stash stat

```
 .../regime_aware_portfolio_conservative.toml       |   1 +
 config/sweeps/regime_neutral_scale_sweep.toml      |   1 +
 config/sweeps/regime_threshold_robustness.toml     |   1 +
 docs/CASE_STUDY_REGIME_ANALYSIS_BTCUSDT.md         |   1 +
 docs/CASE_STUDY_REGIME_BTCUSDT_V1.md               |   1 +
 docs/DEV_GUIDE_ADD_EXCHANGE.md                     |   1 +
 docs/DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md              |   1 +
 docs/DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md             |   1 +
 docs/DEV_GUIDE_ADD_STRATEGY.md                     |   1 +
 docs/DEV_WORKFLOW_SHORTCUTS.md                     |   1 +
 docs/INCIDENT_DRILL_LOG.md                         |   1 +
 docs/INCIDENT_SIMULATION_AND_DRILLS.md             |   1 +
 docs/LIVE_STATUS_REPORTS.md                        |   1 +
 docs/OBSERVABILITY_AND_MONITORING_PLAN.md          |   1 +
 docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md            |   1 +
 docs/PHASE_16A_EXECUTION_PIPELINE.md               |   1 +
 ...E_47_PORTFOLIO_ROBUSTNESS_AND_STRESS_TESTING.md |   1 +
 ...48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md |   1 +
 docs/PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md     |   1 +
 docs/PHASE_51_LIVE_OPS_CLI.md                      |   1 +
 docs/PHASE_72_LIVE_OPERATOR_CONSOLE.md             |   1 +
 docs/PHASE_73_LIVE_DRY_RUN_DRILLS.md               |   1 +
 docs/PHASE_74_LIVE_AUDIT_EXPORT.md                 |   1 +
 docs/PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md      |   1 +
 docs/PHASE_REGIME_AWARE_PORTFOLIOS.md              |   1 +
 docs/PHASE_REGIME_AWARE_SWEEPS_AND_PRESETS.md      |   1 +
 ...PHASE_STRATEGY_EXPANSION_BREAKOUT_VOL_REGIME.md |   1 +
 docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md       |   1 +
 docs/PROMOTION_LOOP_SAFETY_FEATURES.md             |   1 +
 docs/Peak_Trade_Gesamtstatus_2025-12-07.md         |   1 +
 docs/REFERENCE_SCENARIO_MULTI_STYLE_MODERATE.md    |   1 +
 docs/ai/CLAUDE_GUIDE.md                            |   1 +
 .../BOUNDED_AUTO_SAFETY_PLAYBOOK.md                |   1 +
 .../OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1.md        |   1 +
 docs/runbooks/OFFLINE_TRIGGER_TRAINING_DRILL_V1.md |   1 +
 .../INTEGRATION_EXAMPLE_SNIPPET.md                 |   1 +
 docs/trigger_training/README.md                    |   1 +
 .../TRIGGER_TRAINING_REPORTS_V1.md                 |   1 +
 .../WORKFLOW_MULTI_SESSION_REPORTS.md              |   1 +
 pyproject.toml                                     |   1 +
 run_regime_experiments.sh                          |   1 +
 scripts/generate_live_status_report.py             |   1 +
 scripts/generate_operator_meta_report.py           |   1 +
 scripts/live_operator_status.py                    |   1 +
 scripts/ops/create_and_open_merge_log_pr.sh        |   1 +
 scripts/profile_research_and_portfolio.py          |   1 +
 scripts/run_live_dry_run_drills.py                 |   1 +
 scripts/run_offline_realtime_ma_crossover.py       |   1 +
 scripts/run_regime_btcusdt_experiments.sh          |   1 +
 scripts/run_strategy_switch_sanity_check.py        |   1 +
 scripts/run_stress_tests.py                        |   1 +
 .../armstrong_elkaroui_combi_experiment.py         |   1 +
 src/experiments/portfolio_robustness.py            |   1 +
 src/experiments/regime_aware_portfolio_sweeps.py   |   1 +
 src/governance/strategy_switch_sanity_check.py     |   1 +
 src/infra/escalation/__init__.py                   |   1 +
 src/infra/escalation/manager.py                    |   1 +
 src/infra/escalation/models.py                     |   1 +
 src/infra/escalation/providers.py                  |   1 +
 src/live/alert_rules.py                            |   1 +
 src/live/alert_storage.py                          |   1 +
 src/live/audit.py                                  |   1 +
 src/live/drills.py                                 |   1 +
 src/live/portfolio_monitor.py                      |   1 +
 src/live/testnet_orchestrator.py                   |   1 +
 src/reporting/live_status_snapshot_builder.py      |  64 +++++----
 src/reporting/monte_carlo_report.py                |   1 +
 src/reporting/offline_paper_trade_report.py        |   1 +
 src/reporting/portfolio_robustness_report.py       |   1 +
 src/reporting/status_snapshot_schema.py            |  10 +-
 src/reporting/stress_test_report.py                |   1 +
 src/reporting/walkforward_report.py                |   1 +
 src/research/__init__.py                           |   1 +
 src/research/ml/__init__.py                        |   1 +
 src/research/ml/labeling/__init__.py               |   1 +
 src/research/ml/labeling/triple_barrier.py         |   1 +
 src/research/ml/meta/__init__.py                   |   1 +
 src/research/ml/meta/meta_labeling.py              |   1 +
 src/strategies/armstrong/cycle_model.py            |   1 +
 src/strategies/bouchaud/__init__.py                |   1 +
 .../bouchaud/bouchaud_microstructure_strategy.py   |   1 +
 src/strategies/ehlers/__init__.py                  |   1 +
 .../ehlers/ehlers_cycle_filter_strategy.py         |   1 +
 src/strategies/el_karoui/vol_model.py              |   1 +
 src/strategies/gatheral_cont/__init__.py           |   1 +
 .../gatheral_cont/vol_regime_overlay_strategy.py   |   1 +
 src/strategies/lopez_de_prado/__init__.py          |   1 +
 .../lopez_de_prado/meta_labeling_strategy.py       |   1 +
 src/trigger_training/session_store.py              |   1 +
 src/webui/alerts_api.py                            |  30 ++--
 src/webui/health_endpoint.py                       | 154 ++++++++++++++++++---
 src/webui/live_track.py                            |  23 ++-
 .../r_and_d_experiment_comparison.html             |   1 +
 tests/governance/__init__.py                       |   1 +
 .../test_strategy_switch_sanity_check.py           |   1 +
 tests/notifications/__init__.py                    |   1 +
 tests/notifications/test_slack_notifier.py         |   1 +
 tests/ops/test_test_health_triggers.py             |   1 +
 tests/reporting/__init__.py                        |   1 +
 .../test_offline_paper_trade_integration.py        |   1 +
 tests/reporting/test_offline_paper_trade_report.py |   1 +
 tests/reporting/test_trigger_training_report.py    |   1 +
 tests/strategies/armstrong/__init__.py             |   1 +
 .../armstrong/test_armstrong_cycle_strategy.py     |   1 +
 tests/strategies/armstrong/test_cycle_model.py     |   1 +
 tests/strategies/el_karoui/__init__.py             |   1 +
 .../test_el_karoui_volatility_strategy.py          |   1 +
 tests/strategies/el_karoui/test_vol_model.py       |   1 +
 tests/test_alerts_api.py                           |   1 +
 tests/test_armstrong_elkaroui_combi_experiment.py  |   1 +
 tests/test_escalation_manager.py                   |   1 +
 tests/test_generate_live_status_report_cli.py      |   1 +
 tests/test_live_alerts_basic.py                    |   1 +
 tests/test_live_ops_cli.py                         |   1 +
 tests/test_live_portfolio_monitor.py               |   1 +
 tests/test_live_risk_limits_portfolio_bridge.py    |   1 +
 tests/test_live_session_runner.py                  |   1 +
 tests/test_live_status_report.py                   |   1 +
 tests/test_live_status_snapshot_builder.py         |  21 ++-
 tests/test_monte_carlo_robustness.py               |   1 +
 tests/test_offline_realtime_ma_crossover_script.py |   1 +
 tests/test_phase72_live_operator_status.py         |   1 +
 tests/test_phase73_live_dry_run_drills.py          |   1 +
 tests/test_phase74_live_audit_export.py            |   1 +
 tests/test_portfolio_robustness.py                 |   1 +
 tests/test_preview_live_portfolio.py               |   1 +
 tests/test_profile_research_and_portfolio_cli.py   |   1 +
 tests/test_regime_aware_portfolio.py               |   1 +
 tests/test_regime_aware_portfolio_sweeps.py        |   1 +
 tests/test_risk_scenarios.py                       |   1 +
 tests/test_risk_severity.py                        |   1 +
 tests/test_stress_tests.py                         |   1 +
 tests/test_walkforward_backtest.py                 |   1 +
 tests/trigger_training/__init__.py                 |   1 +
 tests/trigger_training/test_session_store.py       |   1 +
 .../test_trigger_training_hooks.py                 |   1 +
 uv.lock                                            |  11 ++
 137 files changed, 365 insertions(+), 78 deletions(-)
```

## Related

- Triage report: [STASH_TRIAGE_SESSION_20251223-051920.md](../STASH_TRIAGE_SESSION_20251223-051920.md)
- Patch file: [`knowledge_db_strategy_vault_ref_20251223-052351.patch`](./knowledge_db_strategy_vault_ref_20251223-052351.patch)

---
**Export method:** Selective patch export (threshold: >= 50 lines changed)
