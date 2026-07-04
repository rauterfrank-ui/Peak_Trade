# Versioned Final Fleet Bindings and Offline Evaluation Scope v0

---
docs_token: DOCS_TOKEN_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_V0
STATUS: VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Dieses Dokument ratifiziert versionierte Final-Fleet-Bindings und den bounded Offline-Economic-Evaluation-Scope nach PR #4825. Es ersetzt **keine** authoritative Registry-, Contract- oder Evidence-Owner. Keine Runtime-, Order-, Promotion- oder Evaluation-Execution-Authority in diesem Scope.

## A. Scope Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFIED` |
| `PROCESS_CLASSIFICATION` | `BOUNDED_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_V0` |
| `SCOPE_CLASSIFICATION` | `GOVERNANCE_AND_BINDING_ONLY_OFFLINE_EVALUATION_PREP` |
| `BASELINE_ORIGIN_MAIN` | `8b2175bfe1715a17e737be47db772ed230a87b03` |
| `PR4825_MERGE_COMMIT` | `8b2175bfe1715a17e737be47db772ed230a87b03` |
| `FUTURES_ONLY` | `true` |
| `BITCOIN_DIRECTION_ALLOWED` | `false` |
| `SPOT_ALLOWED` | `false` |
| `SYNTHETIC_SPOT_ALLOWED` | `false` |
| `FINAL_RESEARCH_FLEET` | `trend_following,bollinger_bands,momentum_1h` |
| `FINAL_RESEARCH_FLEET_BINDING_READY` | `true` |
| `NEW_CANDIDATES_RATIFIED` | `true` |
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `EVALUATION_EXECUTED_THIS_SCOPE` | `false` |
| `OFFLINE_EVALUATION_SCOPE_RATIFIED` | `true` |
| `OFFLINE_EVALUATION_EXECUTION_ALLOWED` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `LIVE_AUTHORIZED` | `false` |
| `CORE_SYSTEM_MUTATION_ALLOWED` | `false` |
| `CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED` | `false` |
| `MASTER_V2_MUTATION_ALLOWED` | `false` |
| `DOUBLE_PLAY_MUTATION_ALLOWED` | `false` |
| `RISK_SIZING_MUTATION_ALLOWED` | `false` |
| `SAFETY_RUNTIME_MUTATION_ALLOWED` | `false` |
| `FAILED_BINDINGS_ARE_NEGATIVE_EVIDENCE` | `true` |
| `FAILED_BINDINGS_MAY_NOT_BE_RETRIED_UNCHANGED` | `true` |
| `POLICY_CHANGE_DOES_NOT_CHANGE_HISTORICAL_EVIDENCE` | `true` |
| `UNMODIFIED_RE_EXECUTION_ADMISSIBLE` | `false` |
| `PARAMETER_OPTIMIZATION_ALLOWED` | `false` |
| `THRESHOLD_LOWERING_ALLOWED` | `false` |
| `RESULT_RESCUE_ALLOWED` | `false` |
| `CANDIDATE_SPECIFIC_POLICY_LOWERING_ALLOWED` | `false` |
| `runtime_effect` | `NONE` |
| `promotion_effect` | `NONE` |
| `rewire_effect` | `NONE` |
| `evaluation_executed` | `false` |
| `live_authorized` | `false` |

**Authoritative owners (reuse, nicht ersetzen):**

- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`
- Prior scope definition (PR #4825): `docs/governance/POST_PR4824_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0.md`
- Fleet binding completion: `config/research/final_research_fleet_versioned_binding_completion_v0.json`
- Offline evaluation scope ratification: `config/research/final_research_fleet_offline_economic_evaluation_scope_ratification_v0.json`
- Fleet ratification envelope: `config/research/final_research_fleet_v0_fleet_ratification_v0.json`
- Binding manifest contract: `src/research/final_research_fleet_v0_versioned_binding_manifest_contract_v0.py`

## B. Read-Only Inventory Summary

| Owner-Surface | trend_following | bollinger_bands | momentum_1h |
|---|---|---|---|
| Strategy registry | `src/strategies/registry.py` → `TrendFollowingStrategy` | `src/strategies/registry.py` → `BollingerBandsStrategy` | `src/strategies/registry.py` → `MomentumStrategy` |
| STEP31F evaluation config | `config/ops/step31f_okx_inst_eth_usdt_perp_trend_following_v1_economic_evaluation_v1.json` | `config/ops/step31f_okx_inst_eth_usdt_perp_bollinger_bands_v1_economic_evaluation_v1.json` | `config/ops/step31f_okx_inst_eth_usdt_perp_momentum_1h_v1_economic_evaluation_v1.json` |
| Binding completion record | `final_research_fleet_versioned_binding_completion_v0.json` candidate `trend_following/v1` | same owner, candidate `bollinger_bands/v1` | same owner, candidate `momentum_1h/v1` |
| Manifest contract | `final_research_fleet_v0_versioned_binding_manifest_contract_v0.py` | same | same |
| Shared dataset envelope | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` / `cross_sectional_research_staging_v1` | same | same |
| Shared instrument policy | `production_pit_universe_manifest_v1` (6 non-Bitcoin OKX linear perpetuals) | same | same |
| Shared period binding | `pit_cross_sectional_research_chronological_holdout_v1` | same | same |
| Economic policy | `economic_validity_policy_v1` (fleet-wide, no candidate abatement) | same | same |

**Reuse-first binding artifacts:** Alle Pflicht-Bindings pro Kandidat sind repo-evident über `config/research/final_research_fleet_versioned_binding_completion_v0.json` (completion_digest `161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1`) und die referenzierten STEP31F-Configs. Keine neuen Strategy-Implementierungen, keine Parameterfindung, keine Evaluation in diesem Scope.

**Excluded failed historical candidates (retry forbidden):** `macd/v1`, `macd/v2`, `macd/v3`, `breakout_donchian/v1`, `ma_crossover/v1`, `rsi_reversion/step30a`, `composite_breakout_confirmation_vol_gated_donchian_v1/v1`.

## C. Candidate Binding Tables

### C.1 trend_following

| Feld | Wert |
|---|---|
| `strategy_id` | `trend_following` |
| `strategy_version` | `v1` |
| `parameter_binding` | `{"adx_period":14,"adx_threshold":25.0,"exit_threshold":20.0,"ma_period":50,"use_ma_filter":true}` (schema: `step31f_trend_following_v1_economic_evaluation_admissibility_v1`) |
| `dataset_binding` | `dataset_id=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1`, `dataset_version=v1`, `dataset_profile=cross_sectional_research_staging_v1`, `bar_granularity=PT1H`, `data_digest=815b33162adaa2ffd0834f129621f1942b8cb61bc19a6d6220b81b15b65578cc` |
| `period_binding` | `pit_cross_sectional_research_chronological_holdout_v1`, coverage `2024-05-25T00:00:00Z..2024-06-01T01:00:00Z`, `period_digest=7f12bc0a9590b19f6fa8a6f01705ac661e6095c6d7502c8a770ecf12e430137c` |
| `instrument_binding` | `production_universe_manifest_cross_sectional`, 6 eligible non-Bitcoin OKX linear perpetuals (ADA/AVAX/DOT/ETH/LINK/SOL-USDT-SWAP), `futures_only=true`, manifest digest `9c81ca3b0d69dfe610f511ce50ff19b127bc91165b81d82eb7385422bf39a298` |
| `fee_model_binding` | `backtest_fee_taker_symmetric_v0`, `fee_bps=10.0` |
| `slippage_model_binding` | `backtest_slippage_symmetric_v0`, `slippage_bps=5.0` |
| `funding_model_binding` | `backtest_funding_perpetual_interval_v1`, `bind=true` |
| `execution_model_binding` | `backtest_execution_v0`, `roundtrip_cost_bps=40.0` |
| `economic_policy_binding` | `economic_validity_policy_v1` |
| `implementation_digest` | `8bc31d6d5c8bce8fbcf9eb1ff5f9e679695e4538af46f542db91aedcccc8588b` |
| `config_digest` | `dbb246f649709e370c69a63cf3e741878a29bb053374134e702d2c344cbe71d0` |
| `data_digest` | `815b33162adaa2ffd0834f129621f1942b8cb61bc19a6d6220b81b15b65578cc` |
| `binding_status` | `VERSIONED_BINDINGS_RATIFIED` |
| `evidence_source` | `config/research/final_research_fleet_versioned_binding_completion_v0.json`; `config/ops/step31f_okx_inst_eth_usdt_perp_trend_following_v1_economic_evaluation_v1.json`; `src/research/final_research_fleet_v0_versioned_binding_manifest_contract_v0.py` |
| `blocking_gaps` | `none` |

### C.2 bollinger_bands

| Feld | Wert |
|---|---|
| `strategy_id` | `bollinger_bands` |
| `strategy_version` | `v1` |
| `parameter_binding` | `{"bb_period":20,"bb_std":2.0,"entry_threshold":0.95,"exit_threshold":0.5}` (schema: `step31f_bollinger_bands_v1_economic_evaluation_admissibility_v1`) |
| `dataset_binding` | `dataset_id=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1`, `dataset_version=v1`, `dataset_profile=cross_sectional_research_staging_v1`, `bar_granularity=PT1H`, `data_digest=815b33162adaa2ffd0834f129621f1942b8cb61bc19a6d6220b81b15b65578cc` |
| `period_binding` | `pit_cross_sectional_research_chronological_holdout_v1`, coverage `2024-05-25T00:00:00Z..2024-06-01T01:00:00Z`, `period_digest=7f12bc0a9590b19f6fa8a6f01705ac661e6095c6d7502c8a770ecf12e430137c` |
| `instrument_binding` | `production_universe_manifest_cross_sectional`, 6 eligible non-Bitcoin OKX linear perpetuals, `futures_only=true`, manifest digest `9c81ca3b0d69dfe610f511ce50ff19b127bc91165b81d82eb7385422bf39a298` |
| `fee_model_binding` | `backtest_fee_taker_symmetric_v0`, `fee_bps=10.0` |
| `slippage_model_binding` | `backtest_slippage_symmetric_v0`, `slippage_bps=5.0` |
| `funding_model_binding` | `backtest_funding_perpetual_interval_v1`, `bind=true` |
| `execution_model_binding` | `backtest_execution_v0`, `roundtrip_cost_bps=40.0` |
| `economic_policy_binding` | `economic_validity_policy_v1` |
| `implementation_digest` | `2bc0f51f29587670878d7bfae66c3aac1e8c8ae48865f083c3d98611aa0dcb38` |
| `config_digest` | `cb9873d09e762ae9d3155b64be444cd7d317865645a1c3c14028ba2e0cf44b5a` |
| `data_digest` | `815b33162adaa2ffd0834f129621f1942b8cb61bc19a6d6220b81b15b65578cc` |
| `binding_status` | `VERSIONED_BINDINGS_RATIFIED` |
| `evidence_source` | `config/research/final_research_fleet_versioned_binding_completion_v0.json`; `config/ops/step31f_okx_inst_eth_usdt_perp_bollinger_bands_v1_economic_evaluation_v1.json`; `src/research/final_research_fleet_v0_versioned_binding_manifest_contract_v0.py` |
| `blocking_gaps` | `none` |

### C.3 momentum_1h

| Feld | Wert |
|---|---|
| `strategy_id` | `momentum_1h` |
| `strategy_version` | `v1` |
| `parameter_binding` | `{"entry_threshold":0.02,"exit_threshold":-0.01,"lookback_period":20}` (schema: `step31f_momentum_1h_v1_economic_evaluation_admissibility_v1`) |
| `dataset_binding` | `dataset_id=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1`, `dataset_version=v1`, `dataset_profile=cross_sectional_research_staging_v1`, `bar_granularity=PT1H`, `data_digest=815b33162adaa2ffd0834f129621f1942b8cb61bc19a6d6220b81b15b65578cc` |
| `period_binding` | `pit_cross_sectional_research_chronological_holdout_v1`, coverage `2024-05-25T00:00:00Z..2024-06-01T01:00:00Z`, `period_digest=7f12bc0a9590b19f6fa8a6f01705ac661e6095c6d7502c8a770ecf12e430137c` |
| `instrument_binding` | `production_universe_manifest_cross_sectional`, 6 eligible non-Bitcoin OKX linear perpetuals, `futures_only=true`, manifest digest `9c81ca3b0d69dfe610f511ce50ff19b127bc91165b81d82eb7385422bf39a298` |
| `fee_model_binding` | `backtest_fee_taker_symmetric_v0`, `fee_bps=10.0` |
| `slippage_model_binding` | `backtest_slippage_symmetric_v0`, `slippage_bps=5.0` |
| `funding_model_binding` | `backtest_funding_perpetual_interval_v1`, `bind=true` |
| `execution_model_binding` | `backtest_execution_v0`, `roundtrip_cost_bps=40.0` |
| `economic_policy_binding` | `economic_validity_policy_v1` |
| `implementation_digest` | `a31f196354e1fac7f7d5f56e1d02c5b2d466c7dde935b0d8fb26985f40cd4c38` |
| `config_digest` | `d92f0542eb680df599cfac4cc7b3dadc2a7d17ffa0ebe963ea75a30d2714c244` |
| `data_digest` | `815b33162adaa2ffd0834f129621f1942b8cb61bc19a6d6220b81b15b65578cc` |
| `binding_status` | `VERSIONED_BINDINGS_RATIFIED` |
| `evidence_source` | `config/research/final_research_fleet_versioned_binding_completion_v0.json`; `config/ops/step31f_okx_inst_eth_usdt_perp_momentum_1h_v1_economic_evaluation_v1.json`; `src/research/final_research_fleet_v0_versioned_binding_manifest_contract_v0.py` |
| `blocking_gaps` | `none` |

## D. Offline Evaluation Scope Ratification (Execution Forbidden Here)

Der später separat auszuführende bounded Offline-Economic-Evaluation-Scope ist ratifiziert über `config/research/final_research_fleet_offline_economic_evaluation_scope_ratification_v0.json` (ratification_digest `2fab224e9dc4a85de85b71269355b82a7385d00dfb6d4f9ef991c38012e8c65f`).

| Evaluation-Stage | Ratifiziert | In diesem Scope ausgeführt |
|---|---|---|
| `OFFLINE_BACKTEST` | `true` | `false` |
| `WALK_FORWARD` | `true` | `false` |
| `MONTE_CARLO` | `true` | `false` |
| `STRESS` | `true` | `false` |
| `PARAMETER_SENSITIVITY` | `true` | `false` |
| `ECONOMIC_VIABILITY_EVIDENCE` | `true` | `false` |

**PASS/FAIL/INCONCLUSIVE-Semantik:**

- **PASS:** Nur bei vollständigem Economic Validity Gate für alle required Dimensionen pro Kandidat.
- **FAIL:** Negative Netto-Edge, Robustness-/Cost-/OOS-/Stress-Failure, oder unveränderte Re-Execution gescheiterter Bindings.
- **INCONCLUSIVE:** Unzureichende Trade Count, fehlende Daten, unvollständige Bindings oder nicht-admissible Evidence.

Kein PASS erzeugt Promotion, Runtime-Rewire oder Live Authority. Runtime-Rewire bleibt separat gegated.

## E. Explizit Ausgeschlossen (Dieser Scope)

```text
NO_CORE_SYSTEM_CHANGE
NO_CANONICAL_TRADING_LOGIC_CHANGE
NO_MASTER_V2_CHANGE
NO_DOUBLE_PLAY_CHANGE
NO_RISK_SIZING_CHANGE
NO_SAFETY_RUNTIME_CHANGE
NO_RUNTIME_REWIRE
NO_SHADOW
NO_PAPER
NO_TESTNET
NO_SCHEDULER
NO_ADAPTER_SUBMISSION
NO_ORDERS
NO_CREDENTIALS
NO_ARMING
NO_CANARY
NO_LIVE
NO_OFFLINE_EVALUATION_EXECUTION_THIS_SCOPE
NO_BACKTEST_EXECUTION_THIS_SCOPE
NO_WALK_FORWARD_EXECUTION_THIS_SCOPE
NO_MONTE_CARLO_EXECUTION_THIS_SCOPE
NO_STRESS_EXECUTION_THIS_SCOPE
NO_PARAMETER_SENSITIVITY_EXECUTION_THIS_SCOPE
```

| Ausführungsklasse | Autorisiert in diesem Scope |
|---|---|
| Offline Evaluation Execution | `false` |
| Backtest Execution | `false` |
| Walk-Forward Execution | `false` |
| Monte-Carlo Execution | `false` |
| Stress Execution | `false` |
| Parameter Sensitivity Execution | `false` |
| Runtime / Shadow / Paper / Testnet / Live | `false` |

## F. Safe Next Action

```text
SAFE_NEXT_ACTION=REQUEST_OPERATOR_GO_FOR_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0
```

Alle drei Final-Fleet-Kandidaten haben vollständige repo-evidente Bindings (`FINAL_RESEARCH_FLEET_BINDING_READY=true`). Der admissible Folgepfad ist ausschließlich ein separater Operator-GO für bounded Offline-Economic-Evaluation-Execution — **nicht** automatisch aus dieser Ratifikation.

**Explizit nicht admissibel:**

- Unveränderte Re-Execution der historischen terminal FAIL 0/3 Final Research Fleet
- Kandidatenspezifische Policy-Absenkung oder Threshold-Rettung
- Runtime-Rewire, Promotion oder Live Authority aus Binding-Ratifikation allein
