# ADX range-admission MR eligibility — DEVELOPMENT evaluation v1

## Status

`DEVELOPMENT_EVALUATION_EXECUTED` — single preregistered offline panel run
completed. Evidence under
`docs/evidence/evaluate_adx_range_admission_mr_eligibility_development_v1/`.
`RESULT_CLASS=FAIL` (`NET_PROFIT_FACTOR_NOT_IMPROVED`);
`ENTRY_ELIGIBILITY_DIVERGENCE=true`;
`PROMOTION_ELIGIBLE=false`; holdout not accessed.

## Binding

- Contract: `config/research/adx_range_admission_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Preregistration module: `src/research/adx_range_admission_mr_eligibility_hypothesis_preregistration_v1.py`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable control arm)
- Treatment: research-only `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER` — frozen
  ADX(14) range admission (`ADX < 25`) via
  `src&#47;strategies&#47;trend_following.py` (`TrendFollowingStrategy._compute_adx`)
  (Wilder ewm)
- Filter ID: `canonical_adx_range_admission_entry_eligibility_v1`
- Decision segment: `final_development_confirmation` only
- Seed: `20220601`
- Primary decision metric: `NET_PROFIT_FACTOR`

## Distinction from prior failed gates

- Does not reuse or retune the three-feature absolute-threshold classifier,
  ATR-percentile mid-band filter, or RSI exhaustion filter.
- Decision / generic mapped-signal gate helpers and the prior failed evaluation's
  shared portfolio equity aggregation helper are imported **read-only**.

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- Holdout untouched (`HOLDOUT_ACCESSED=false`)
- No runtime / shadow / testnet / live / orders
- No productive Master-V2 / Double-Play / risk / sizing / execution mutation

## Command (single authorized run)

```bash
PYTHONPATH=src:. python3 scripts/research/run_evaluate_adx_range_admission_mr_eligibility_development_v1.py \
  --output-dir docs/evidence/evaluate_adx_range_admission_mr_eligibility_development_v1
```

## Evidence

`docs/evidence/evaluate_adx_range_admission_mr_eligibility_development_v1/` (populated by the runner)
