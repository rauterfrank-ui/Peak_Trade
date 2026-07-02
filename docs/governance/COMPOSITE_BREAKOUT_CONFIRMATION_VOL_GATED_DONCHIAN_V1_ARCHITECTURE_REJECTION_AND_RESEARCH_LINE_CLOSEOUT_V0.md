# Composite Breakout Confirmation Vol-Gated Donchian v1 — Architecture Rejection and Research Line Closeout v0

## Scope

- Candidate: `composite_breakout_confirmation_vol_gated_donchian_v1`
- Instrument: `inst-eth-usdt-perp` on `OKX`
- Architecture GO token (consumed): `GO_BOUNDED_COMPOSITE_BREAKOUT_CONFIRMATION_VOL_GATED_DONCHIAN_V1_ARCHITECTURE_RATIFICATION_AND_BINDING_V0`
- Economic evaluation merge: PR `#4759` at `ec0842428b8420fb4d8193d69c307809bcabee75`
- Architecture binding merge: PR `#4758` at `5eb28206fb49062049c89f43d77da2899f22c93d`
- Closeout GO token (ratified): `GO_BOUNDED_COMPOSITE_BREAKOUT_CONFIRMATION_VOL_GATED_DONCHIAN_V1_ARCHITECTURE_REJECTION_RATIFICATION_AND_RESEARCH_LINE_CLOSEOUT_V0`

## Ratified Fixed Architecture Binding

- Composite type: `confirmed_filter_gated_signal_v1`
- Composition rule: `confirmed_signal_times_filter_mask`
- Signal: `breakout_donchian` (`lookback=20`, `price_col=close`)
- Filter: `vol_regime_filter` (ATR percentile gating)
- Confirmation epochs: `1`
- Sizing: `risk_per_trade=0.005`, `stop_pct=0.02`, `max_position_pct=0.25`, `oversize_policy=REJECT_OVERSIZE`

## Economic Evaluation Closeout (Ratified 2026-07-02)

| Field | Value |
|---|---|
| `CANDIDATE_ID` | `composite_breakout_confirmation_vol_gated_donchian_v1` |
| `ARCHITECTURE_BINDING_MERGE_COMMIT` | `5eb28206fb49062049c89f43d77da2899f22c93d` |
| `ECONOMIC_EVALUATION_MERGE_COMMIT` | `ec0842428b8420fb4d8193d69c307809bcabee75` |
| `ECONOMIC_EVALUATION_VERDICT` | `ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL` |
| `FAILURE_DECOMPOSITION_VERDICT` | `ECONOMIC_VALIDITY_FAILURE_DECOMPOSITION_COMPLETE` |
| `ARCHITECTURE_DISPOSITION` | `ARCHITECTURE_HYPOTHESIS_FALSIFIED` |
| `FINAL_RESEARCH_DISPOSITION` | `REJECTED_CLOSED` |
| `RESEARCH_LINE_STATUS` | `CLOSED_REJECTED` |
| `REJECTION_REASON` | `STRUCTURALLY_NEGATIVE_NET_EDGE_ACROSS_WALK_FORWARD_MONTE_CARLO_AND_STRESS` |
| `TECHNICAL_EVALUATION_STATUS` | `PASS` |
| `ECONOMIC_VALIDITY_STATUS` | `FAILED` |
| `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false` |
| `EVALUATION_ID` | `econ_evidence_eval_v1_d618bf84626619d6` |

### Headline evaluation results (immutable evidence; not recomputed)

| Metric | Value |
|---|---|
| Trade count | `217` |
| Net expectancy | `-1.0763` |
| Profit factor | `0.7394` |
| Sharpe | `-0.9290` |
| Walk-forward pass ratio | `0.20` |
| OOS pass ratio | `0.20` |
| Monte Carlo pass ratio | `0.0` |
| Monte Carlo median return | `-0.0205` |
| Stress scenarios negative | `4&#47;4` |
| Cost grid negative | `9&#47;9` |
| Gross return equals net return | `true` (structural edge absence) |

Primary failure cause: missing structural net edge, not cost drag, insufficient trade count, drawdown breach, or contract/data blocker.

## Architecture Rejection Ratification

Under fixed bindings on OKX ETH-USDT perpetual (~14-day economic research slice, `economic_validity_policy_v1`, realistic costs/funding/execution), admissible evidence falsifies the architecture hypothesis. The research line is closed as rejected.

`ARCHITECTURE_HYPOTHESIS_FALSIFIED=true`
`ARCHITECTURE_REJECTED=true`
`RETRY_ALLOWED=false`

## Governance and Authority

- `evaluation_authorized=false`
- `promotion_authorized=false`
- `runtime_authorized=false`
- `shadow_eligible=false`
- `paper_eligible=false`
- `testnet_eligible=false`
- `parameter_tuning_allowed=false`
- `threshold_relaxation_allowed=false`
- `dataset_substitution_allowed=false`
- `period_substitution_allowed=false`
- `holdout_allowed=false`
- `retry_allowed=false`
- `reevaluation_allowed=false`
- `NO_NEW_CANDIDATE_HOLD=ACTIVE`
- `STEP29N_PROMOTION_GATE_STATUS=FAIL_CLOSED_BLOCKED`
- `STEP29R_RUNTIME_REWIRE_ADMISSIBLE=false`
- `DOWNSTREAM_AUTHORITY_EFFECT=NONE`

No implicit follow-up candidate, retry, tuning, or promotion path is authorized.

## Durable Evidence References

- Architecture ratification: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/bounded_composite_breakout_confirmation_vol_gated_donchian_v1_architecture_ratification_and_binding_v0_20260702T183549Z`
- Offline evaluation: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/bounded_composite_breakout_confirmation_vol_gated_donchian_v1_offline_economic_validity_evaluation_v0_20260702T185926Z` (`MANIFEST_VERIFY_RC=0`)
- Economic evaluation merge closeout: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/bounded_composite_breakout_confirmation_vol_gated_donchian_v1_economic_evaluation_pr_squash_merge_and_post_merge_closeout_v0_20260702T191014Z`
- Failure decomposition: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/analysis/bounded_composite_breakout_confirmation_vol_gated_donchian_v1_economic_validity_failure_decomposition_and_research_disposition_read_only_v0_20260702T211530Z` (`MANIFEST_VERIFY_RC=0`)

## Derivation References

- `operator_policy_decision:COMPOSITE_BREAKOUT_CONFIRMATION_VOL_GATED_DONCHIAN_V1`
- `fleet_precedent:macd_v3_post_risk_limits_rewire`
