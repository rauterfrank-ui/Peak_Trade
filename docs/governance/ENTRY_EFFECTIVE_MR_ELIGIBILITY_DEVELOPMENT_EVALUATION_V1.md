# Entry-effective MR eligibility — DEVELOPMENT evaluation v1

## Status

`DEVELOPMENT_EVALUATION_EXECUTED` — single preregistered offline panel run
completed. Evidence under
`docs/evidence/evaluate_entry_effective_mr_eligibility_development_v1/`.
`RESULT_CLASS=FAIL` (`NET_PROFIT_FACTOR_NOT_IMPROVED`);
`ENTRY_ELIGIBILITY_DIVERGENCE=true`; `entries_blocked_by_gate=310`;
`PROMOTION_ELIGIBLE=false`; holdout not accessed.

## Binding

- Contract: `config/research/entry_effective_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Preregistration module: `src/research/entry_effective_mr_eligibility_hypothesis_preregistration_v1.py`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable control arm)
- Treatment: research-only `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER` — frozen
  ATR(14) rolling percentile-rank (100h) mid-band filter, **STRICT** bounds
  (`25 < rank < 75`, NOT the inclusive `>=`/`<=` bounds used by
  `VolRegimeFilter.generate_signals`)
- Filter ID: `canonical_vol_regime_filter_atr_percentile_midband_v1`
- Decision segment: `final_development_confirmation` only
- Seed: `20220601`
- Entry-eligibility divergence between control and treatment is a hard
  measurement condition: absence of divergence is a locked `FAIL`
  (`identical_arms_no_entry_eligibility_divergence`), independent of economics.

## Distinction from the prior failed regime-gated gate

- Does not reuse or retune the three-feature absolute-threshold
  `RANGE_BOUND`/`TREND_STRONG` classifier from
  `regime_gated_standaside_mr_development_evaluation_v1`.
- Uses the repo-canonical `vol_regime_filter` ATR-percentile primitive instead.
- The prior failed evaluation's shared portfolio equity aggregation helper
  (`shared_portfolio_equity_research_v1.py`) is imported **read-only**; none of
  the `regime_gated_standaside_mr_development_evaluation_v1` package files are
  mutated by this evaluation.

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- Holdout untouched (`HOLDOUT_ACCESSED=false`)
- No runtime / shadow / testnet / live / orders
- No productive Master-V2 / Double-Play / risk / sizing / execution mutation

## Command (single authorized run)

```bash
PYTHONPATH=src:. python3 scripts/research/run_evaluate_entry_effective_mr_eligibility_development_v1.py \
  --output-dir docs/evidence/evaluate_entry_effective_mr_eligibility_development_v1
```

## Evidence

`docs/evidence/evaluate_entry_effective_mr_eligibility_development_v1/` (populated by the runner)
