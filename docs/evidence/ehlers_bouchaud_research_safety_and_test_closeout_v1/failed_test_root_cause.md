# Failed Test Root Cause (Audit POST_AUDIT_TESTS=FAIL)

Reproduced on `main` @ `f43822f972cc41542d16d56f5657d3ae3b84abe1` before safety edits. Raw log: `digest_failure_repro.txt`.

| Test | Error | Expected semantics | Root cause | Domain | Action in this slice |
|---|---|---|---|---|---|
| `tests/ops/test_step29m_ehlers_cycle_filter_v1_offline_economic_baseline_materialization_v0_contract.py::test_config_and_strategy_params_digests_unchanged_on_main_config` | computed config digest `89d00a3e…` ≠ pin `c4db0a42…` | Pin matches live eval config digest | **Stale/pinned digest drift** vs live `config/ops/step29m_okx_inst_eth_usdt_perp_ehlers_cycle_filter_v1_economic_evaluation_v1.json` (contains absolute archive `dataset_path`) | Shared STEP29M research infra (not signal safety) | Document only — no digest re-pin |
| `tests/backtest/test_step29m_ehlers_cycle_filter_v1_economic_evaluation_admissibility_contract_v1.py::test_versioned_bindings_materialized` | binding pin `c4db…` ≠ live compute `89d00…` | Binding digest_bindings match live config | Same config-digest drift between versioned binding and eval config | Research infra | Document only |
| `tests/ops/...bouchaud...::test_config_digest_matches_binding` | live `09aa6f52…` ≠ pin `a3af9505…` | Eval config digest == binding pin | Absolute `dataset_path` / config content drift | Research infra | Document only |
| `tests/ops/...bouchaud...::test_implementation_digest_stable_and_matches_binding` | live `20a4dbd1…` ≠ pin `e76f7d06…` | Implementation surface hash == binding | Surfaces include engine/scripts/strategy; prior main drift already (before this slice) | Research infra | Document only; safety edits will further change strategy-file surface hash if re-run |
| `tests/ops/...bouchaud...::test_binding_digest_roundtrip_deterministic` | recomputed binding digest ≠ stored `binding_digest` | Roundtrip identity | Cascades from component digest / formula drift in stored binding | Research infra | Document only |
| `tests/backtest/...bouchaud...::test_versioned_binding_matches_research_scope` | `economic_evaluation_executed is True` but test expects `False` | Flag false until authorized eval | Binding JSON flag drift vs contract expectation | Research infra / binding metadata | Document only |

## Classification

- Not caused by Ehlers/Bouchaud **signal** safety gaps.
- Not fixed here: updating STEP29M digests / evaluation flags would be a separate research-binding repair slice and is out of the allowed minimal safety scope.
- Safety closeout tests (new) + strategy unit/gating/grammar regressions: **PASS** (125).

## FAIL_CLOSED_ON_MISSING_INPUT (audit finding)

Was `false` because invalid NaN/Inf/volume/index cases could still emit Long intent or polluted filter state. Addressed in strategy input gates (Flat / raise on missing `close`).
