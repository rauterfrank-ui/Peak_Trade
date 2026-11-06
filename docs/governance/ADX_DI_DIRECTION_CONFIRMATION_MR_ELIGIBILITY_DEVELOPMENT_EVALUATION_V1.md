# ADX DI direction confirmation MR eligibility — DEVELOPMENT evaluation v1

## Status

`DEVELOPMENT_EVALUATION_EXECUTED` — single preregistered offline panel run
completed with `RESULT_CLASS=PASS` / `ALL_PASS_REQUIRES_MET`. Evidence under
`docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1/`.

## Binding

- Contract: `config/research/adx_di_direction_confirmation_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Preregistration module: `src/research/adx_di_direction_confirmation_mr_eligibility_hypothesis_preregistration_v1.py`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable control arm)
- Treatment: research-only `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER` — frozen
  Wilder ADX(14) +DI/−DI direction-confirmation admission via
  `src&#47;strategies&#47;trend_following.py` (`TrendFollowingStrategy._compute_adx`)
- Filter ID: `canonical_adx_di_direction_confirmation_entry_eligibility_v1`
- Decision segment: `final_development_confirmation` only
- Seed: `20220601`
- Primary decision metric: `NET_PROFIT_FACTOR`
- Evaluation run count: `1` / limit `1`

## Side-aware eligibility rule

Long entry-candidate (mapped signal `+1`): `ELIGIBLE` iff both DI finite and
`minus_DI > plus_DI`. Short entry-candidate (mapped signal `-1`): `ELIGIBLE`
iff both DI finite and `plus_DI > minus_DI`. Tie / non-finite → `STAND_ASIDE`.
First `warmup_bars=28` bars are always `STAND_ASIDE`. ADX level unused.

## Result (mechanical; no post-result tuning)

- `RESULT_CLASS=PASS`
- `REASON=ALL_PASS_REQUIRES_MET`
- Control trades `117` → treatment `100`
- Control net PF `0.732436` → treatment `0.810055`
- Divergence observed (`entries_blocked_by_gate=256`)

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed (`ECONOMIC_GATE_OPENED=false`)
- Holdout untouched (`HOLDOUT_ACCESSED=false`)
- No runtime / shadow / testnet / live / orders
- No productive Master-V2 / Double-Play / risk / sizing / execution mutation
- No second evaluation run authorized

## Command (single authorized run)

```bash
PYTHONPATH=src:. python3 scripts/research/run_evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1.py \
  --output-dir docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1
```
