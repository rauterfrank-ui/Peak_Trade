# Timing proof — OBL_B05 ENTRY_EXIT optional side carrier

- SELECTOR_MODE: `PR_BOUNDED_FULL`
- SELECTOR_REASON: `category_config_paths_requires_full`
- TIMING_WALLCLOCK_SECONDS: `56.6`
- TIMING_TARGET_MAX_SECONDS: `840`
- TIMING_HARD_STOP_SECONDS: `900`
- TIMING_SAFETY_MARGIN_SECONDS: `180`
- TIMING_EXIT: `0`
- TEST_COUNT: `791`
- TIMING_PROOF_STATUS: `PASS`

Command:

```text
python3 -m pytest -q --tb=line \
  tests/backtest/test_entry_exit_optional_side_carrier_contract_v1.py \
  tests/backtest/test_mv2_composition_directional_asymmetry_wiring_repair_v1.py \
  tests/backtest/test_strategy_signal_suitability_agreement_adapter_v1.py \
  tests/trading/master_v2/test_strategy_suitability_agreement_consumer_contract_v1.py \
  tests/trading/master_v2/test_strategy_suitability_agreement_static_contract_v1.py \
  tests/trading/master_v2/test_suitability_regime_wildcard_integrated_counterfactual_v1.py \
  tests/ci/test_ci_diff_aware_test_selection_v1.py \
  tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py \
  tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py \
  tests/ci/test_pr_head_sha_required_checks_liveness_guard.py \
  tests/ci/test_required_checks_config.py \
  tests/ci/test_required_checks_hygiene.py \
  tests/ci/test_workflows_no_pull_request_target_contract_v0.py \
  tests/test_data_contracts.py \
  tests/test_error_taxonomy.py \
  tests/test_resilience.py \
  tests/test_stability_smoke.py \
  tests/governance/test_technical_canonical_wiring_authorization_bound_to_boundary_guard_v1.py
```
