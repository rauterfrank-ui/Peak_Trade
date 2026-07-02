# STEP30A RSI Reversion v1 Operator Policy Decision v0

## Scope
- Slice: `RUNBOOK_STEP_30A`
- Strategy: `rsi_reversion` (`v1`)
- Instrument: `inst-eth-usdt-perp` on `OKX`
- GO token: `GO_BOUNDED_STEP30A_RSI_REVERSION_V1_EXTENDED_HOLDOUT_SEPARATED_FUTURES_ECONOMIC_RESEARCH_V0`

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

## Governance and Authority
- `evaluation_authorized=false`
- `promotion_authorized=false`
- `runtime_authorized=false`
- `parameter_tuning_allowed=false`
- `threshold_tuning_allowed=false`
- `dataset_replacement_allowed=false`

## Derivation References
- `operator_policy_decision:STEP30A_RSI_REVERSION_V1`
- `fleet_precedent:macd_v3_post_risk_limits_rewire`
