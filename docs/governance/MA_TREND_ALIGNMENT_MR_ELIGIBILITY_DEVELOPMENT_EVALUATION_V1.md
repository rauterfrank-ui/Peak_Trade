# MA trend-alignment MR eligibility — DEVELOPMENT evaluation v1

## Status

`DEVELOPMENT_EVALUATION_EXECUTED` — single preregistered offline panel run
completed. Evidence under
`docs/evidence/evaluate_ma_trend_alignment_mr_eligibility_development_v1/`.

## Binding

- Contract: `config/research/ma_trend_alignment_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Preregistration module: `src/research/ma_trend_alignment_mr_eligibility_hypothesis_preregistration_v1.py`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable control arm)
- Treatment: research-only `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER` — frozen
  SMA(50) side-aware with-trend admission via
  `src&#47;strategies&#47;rsi_reversion.py` (`price.rolling(window=50).mean()`)
- Filter ID: `canonical_ma_trend_alignment_entry_eligibility_v1`
- Decision segment: `final_development_confirmation` only
- Seed: `20220601`
- Primary decision metric: `NET_PROFIT_FACTOR`

## Side-aware eligibility rule

Long entry-candidate (mapped signal `+1`): `ELIGIBLE` iff `close > SMA(50)`.
Short entry-candidate (mapped signal `-1`): `ELIGIBLE` iff `close < SMA(50)`.
First `warmup_bars=50` bars are always `STAND_ASIDE`. Mapped `0` (flat/exit)
always passes through unchanged. The gate acts on the MV2-mapped position
signal (post-map, pre-order), not on the raw configured-strategy signal
series, and is evaluated per candidate side — never against a single
OR-combined bar mask.

## Distinction from prior failed gates

- Does not reuse or retune the three-feature absolute-threshold classifier,
  ATR-percentile mid-band filter, RSI exhaustion filter, or ADX(14) level
  range-admission filter.
- Decision / generic mapped-signal gate helpers and the prior failed
  evaluation's shared portfolio equity aggregation helper are imported
  **read-only**.

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- Holdout untouched (`HOLDOUT_ACCESSED=false`)
- No runtime / shadow / testnet / live / orders
- No productive Master-V2 / Double-Play / risk / sizing / execution mutation

## Command (single authorized run)

```bash
PYTHONPATH=src:. python3 scripts/research/run_evaluate_ma_trend_alignment_mr_eligibility_development_v1.py \
  --output-dir docs/evidence/evaluate_ma_trend_alignment_mr_eligibility_development_v1
```

## Evidence

`docs/evidence/evaluate_ma_trend_alignment_mr_eligibility_development_v1/` (populated by the runner)
