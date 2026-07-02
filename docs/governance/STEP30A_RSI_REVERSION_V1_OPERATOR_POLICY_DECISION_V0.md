# STEP30A RSI Reversion v1 Operator Policy Decision v0

## Scope
- Slice: `RUNBOOK_STEP_30A`
- Strategy: `rsi_reversion` (`v1`)
- Instrument: `inst-eth-usdt-perp` on `OKX`
- Research GO token: `GO_BOUNDED_STEP30A_RSI_REVERSION_V1_EXTENDED_HOLDOUT_SEPARATED_FUTURES_ECONOMIC_RESEARCH_V0`
- Evaluation GO token (consumed): `GO_BOUNDED_STEP30A_SINGLE_ECONOMIC_EVALUATION_POST_RUNNER_MERGE_V1`
- Policy-fail accept GO token (ratified): `GO_STEP30A_RSI_REVERSION_V1_POLICY_FAIL_ACCEPT_AND_NO_NEW_CANDIDATE_HOLD_V0`

## Ratified Fixed Parameters
- `rsi_window=14`
- `lower=30.0`
- `upper=70.0`
- `price_col=close`
- `use_trend_filter` is forbidden in `strategy_params` for this slice

## Holdout and Dataset Binding
- Frozen holdout: `2026-06-17 10:07:00+00:00..2026-07-01 10:07:00+00:00`
- Training period: `2026-04-02 10:07:00+00:00..2026-05-18 23:59:00+00:00`
- Validation period: `2026-05-19 00:00:00+00:00..2026-06-16 23:59:00+00:00`
- Dataset version binding: `v2` (`inst-eth-usdt-perp`)

## Economic Evaluation Closeout (Ratified 2026-07-02)

Operator policy decision: `STEP30A_RSI_REVERSION_V1_POLICY_FAIL_ACCEPT_AND_NO_NEW_CANDIDATE_HOLD`

| Field | Value |
|---|---|
| `STEP30A_STATUS` | `COMPLETE_POLICY_FAIL` |
| `STEP30A_TECHNICAL_EVALUATION_STATUS` | `PASS` |
| `STEP30A_ECONOMIC_VALIDITY_STATUS` | `FAIL` |
| `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false` |
| `STEP30A_EVALUATION_ID` | `econ_evidence_eval_v1_37eb167cdade6c63` |
| `STEP30A_BINDING_FULL_DIGEST` | `37eb167cdade6c63f20af71abfeda7e987782685eb793a7baac772b7e30b1999` |
| `STEP30A_BINDING_DISPOSITION` | `TERMINAL_NEGATIVE_EVIDENCE` |
| `RSI_REVERSION_V1_EVALUATED_BINDING_STATUS` | `TERMINAL_NEGATIVE_EVIDENCE` |

### Policy-Fail Reason Codes
- `METRIC_MISSING:parameter_neighbor_degradation`
- `METRIC_MISSING:single_regime_profit_contribution`
- `METRIC_MISSING:single_trade_profit_contribution`
- `MONTE_CARLO_FAILED`
- `NET_EXPECTANCY_BELOW_THRESHOLD`
- `PROFIT_FACTOR_BELOW_THRESHOLD`
- `STRESS_FAILED`

### Semantic Clarifications
- `TECHNICAL_CAPABILITY_PRESENT != ECONOMIC_VALIDITY_PROVEN`
- `NEGATIVE_CANDIDATE_EVIDENCE != WHOLE_SYSTEM_UNPROFITABLE`

The result is candidate-specific negative evidence for `rsi_reversion` v1 on `inst-eth-usdt-perp` v2. It must not be interpreted as proof that Peak_Trade as a whole is unprofitable.

## Governance and Authority
- `evaluation_authorized=false`
- `promotion_authorized=false`
- `runtime_authorized=false`
- `parameter_tuning_allowed=false`
- `threshold_tuning_allowed=false`
- `dataset_replacement_allowed=false`
- `retry_allowed=false`
- `reevaluation_allowed=false`
- `consumed_go_reusable=false`
- `NO_NEW_CANDIDATE_HOLD=ACTIVE`
- `STEP29N_PROMOTION_GATE_STATUS=FAIL_CLOSED_BLOCKED`
- `STEP29R_RUNTIME_REWIRE_ADMISSIBLE=false`
- `DOWNSTREAM_AUTHORITY_EFFECT=NONE`

## Durable Evidence References
- Evaluation bundle: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/economic_evaluation/step30a_rsi_reversion_v1/econ_evidence_eval_v1_37eb167cdade6c63` (`MANIFEST_VERIFY_RC=0`)
- Policy-fail closeout bundle: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/bounded_step30a_rsi_reversion_v1_economic_policy_fail_closeout_and_operator_policy_decision_read_only_v0_20260702T164520Z` (`MANIFEST_VERIFY_RC=0`)

## Derivation References
- `operator_policy_decision:STEP30A_RSI_REVERSION_V1`
- `fleet_precedent:macd_v3_post_risk_limits_rewire`
