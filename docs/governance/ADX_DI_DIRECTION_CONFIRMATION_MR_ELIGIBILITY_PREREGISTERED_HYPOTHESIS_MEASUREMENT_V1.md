# ADX DI direction confirmation MR eligibility — preregistered hypothesis and measurement v1

## Status

`DEFINITION_ONLY` — hypothesis and measurement contract preregistered; no evaluation.

## Binding

- Hypothesis: `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
- Contract: `adx_di_direction_confirmation_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Multiple-testing budget: `1`
- Authorized later development evaluation runs: `1`
- Evaluation run count now: `0`
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Treatment: `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER` (not implemented in this slice)
- Primary decision metric: `NET_PROFIT_FACTOR` (joint PASS requires all locked economic companions)

## Filter (ex ante, deterministic)

Canonical Wilder ADX(14) +DI/−DI direction-confirmation admission from repo SSOT
defaults in `config/config.toml` `[strategies.trend_following.defaults]`, computed via
`src/strategies/trend_following.py` (`TrendFollowingStrategy._compute_adx`):

- `adx_period=14`
- `uses_adx_level=false`
- `uses_di_order_only=true`
- `side_aware=true`
- `warmup_bars=28`
- Tie: `plus_DI == minus_DI` → `STAND_ASIDE`
- NaN / non-finite DI → `STAND_ASIDE`

Eligibility rule: at finalized bar t, before any new entry decision, compute
+DI/−DI. For a long entry-candidate (mapped position intent +1):
ELIGIBLE iff `minus_DI > plus_DI`. For a short entry-candidate (mapped position
intent −1): ELIGIBLE iff `plus_DI > minus_DI`. Otherwise STAND_ASIDE. First 28 bars
of warmup are STAND_ASIDE. Does not change direction/side — admission only.
ADX magnitude / `adx_threshold` is intentionally unused.

`ENTRY_ELIGIBILITY_DIVERGENCE_REQUIRED=true` — absence ⇒ `RESULT_CLASS=FAIL`.

## Orthogonality — distinction from prior FAILs

Orthogonal to six prior FAILs: regime-gated multi-feature classifier, ATR percentile
mid-band, RSI exhaustion, ADX(14) level range admission (`ADX < 25`), SMA(50)
with-trend admission, and MACD histogram-sign countertrend. This contract does not
reuse, rename, or retune any prior mechanism's features or thresholds — especially
not the ADX-level FAIL.

## Declared future evaluation targets (unauthorized here)

- Runner: `scripts/research/run_evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1.py`
- Package: `src/research/adx_di_direction_confirmation_mr_eligibility_development_evaluation_v1/`
- Evidence: `docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1/`

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- On FAIL: retuning forbidden; holdout forbidden
- No runtime / shadow / testnet / live / orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`
- `NO EVALUATION EXECUTED`

## Next step

Review and merge this definition-only PR before any development evaluation.
