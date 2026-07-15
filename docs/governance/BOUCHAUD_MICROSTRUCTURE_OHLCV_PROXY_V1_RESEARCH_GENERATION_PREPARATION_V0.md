# Bouchaud Microstructure OHLCV Proxy v1 — Research Generation Preparation v0

## Scope

Offline-only research generation preparation for `bouchaud_microstructure_ohlcv_proxy&#47;v1`.
This slice binds a deterministic OHLCV microstructure proxy feature matrix hypothesis for
later linear-evidence diagnostics. It does **not** execute economic evaluation, walk-forward,
Monte Carlo, stress, promotion, or any runtime authority action.

## Operator GO

`GO_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_DISTINCT_RESEARCH_GENERATION_HYPOTHESIS_AND_IMPLEMENTATION_READINESS`

## Explicit Non-Claim

`OHLCV_PROXY_IS_NOT_TRUE_ORDER_BOOK_MICROSTRUCTURE=true`

OHLCV-derived proxies do not provide actual order-book imbalance, true trade-sign
classification, tick-level impact, or L2 depth reconstruction.

## Hypothesis

Deterministic OHLCV-derived microstructure proxy features inspired by market impact and
order-flow-imbalance concepts may contain incremental predictive information for forward
returns under explicit cost-survival review.

## Feature Families (DETERMINISTIC_OHLCV_PROXY)

1. `signed_return_volume_pressure`
2. `volatility_normalized_price_impact`
3. `volume_conditioned_return_response`
4. `kyle_lambda_proxy`
5. `imbalance_persistence_proxy`
6. `transient_permanent_impact_ratio`
7. `liquidity_resilience_proxy`

## Target Binding

- `TARGET_NAME=forward_return_1bar`
- `TARGET_SHIFT=1`
- `VALIDATION_SPLIT=TIME_ORDERED`
- Random validation split forbidden

## Dataset Binding

- `DATASET_ID=inst-eth-usdt-perp_v1`
- `futures_only=true`
- `bitcoin_present=false`
- Finalized bars only (`is_final=true`)

## Distinctness

This preparation slice is materially distinct from prior strategy-threshold economic
evaluation of the same research scope. It introduces a feature-matrix research generation
path without retrying the unchanged strategy binding or economic evaluation.

## Runtime / Authority Boundary

| Field | Value |
|---|---|
| `RUNTIME_EFFECT` | `NONE` |
| `AUTHORITY_EFFECT` | `NONE` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `ORDERS_ALLOWED` | `false` |
| `LIVE_AUTHORIZED` | `false` |

## Canonical Owner

`src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0`

## Next Action

`WAIT_FOR_OPERATOR_SIGNAL_CHECKS_GREEN_THEN_MERGE_CLOSEOUT`
