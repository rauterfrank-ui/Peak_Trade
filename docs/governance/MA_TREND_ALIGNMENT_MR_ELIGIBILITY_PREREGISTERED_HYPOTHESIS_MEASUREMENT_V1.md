# MA trend-alignment MR eligibility — preregistered hypothesis and measurement v1

## Status

`DEFINITION_ONLY` — hypothesis and measurement contract preregistered; no evaluation.

## Binding

- Hypothesis: `MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
- Contract: `ma_trend_alignment_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Multiple-testing budget: `1`
- Authorized later development evaluation runs: `1`
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Treatment: `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER` (not implemented in this slice)
- Primary decision metric: `NET_PROFIT_FACTOR` (joint PASS requires all locked economic companions)

## Filter (ex ante, deterministic)

Canonical SMA(50) side-aware with-trend admission from repo SSOT defaults in
`config&#47;config.toml` `[strategies.rsi_reversion.defaults]` (`trend_ma_window=50`),
computed via `src&#47;strategies&#47;rsi_reversion.py` (`price.rolling` SMA):

- `ma_period=50`
- `ma_type=SMA`
- `side_aware=true`
- `warmup_bars=50`

Eligibility rule: at finalized bar t, before any new entry decision, compute
SMA(50) of close. For a long entry-candidate (mapped position intent +1):
ELIGIBLE iff close &gt; SMA(50). For a short entry-candidate (mapped position
intent -1): ELIGIBLE iff close &lt; SMA(50). Otherwise STAND_ASIDE. First 50 bars
of warmup are STAND_ASIDE. Does not change direction&#47;side — admission only.

`ENTRY_ELIGIBILITY_DIVERGENCE_REQUIRED=true` — absence ⇒ `RESULT_CLASS=FAIL`.

Bollinger `entry_side=NONE` unchanged; Master V2 / Double-Play remain sole
direction authority.

## Orthogonality — distinction from prior FAILs

This is a single-feature price-vs-SMA(50) side-aware with-trend admission
mechanism, orthogonal to four prior FAILs:

1. `regime_gated_standaside_mr_preregistered_economic_hypothesis_measurement_contract.v1`
   — FAIL: `identical_arms_gate_inactive_on_entries` (absolute-threshold
   multi-feature regime classifier).
2. `entry_effective_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
   — FAIL: `net_profit_factor_not_improved_despite_entry_eligibility_divergence`
   (ATR(14) rolling-percentile mid-band).
3. `rsi_exhaustion_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
   — FAIL: `net_profit_factor_not_improved_despite_entry_eligibility_divergence`
   (RSI(14) exhaustion).
4. `adx_range_admission_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
   — FAIL: `net_profit_factor_not_improved_despite_entry_eligibility_divergence`
   (ADX(14) level range admission).

This contract does not reuse, rename, or retune any prior mechanism's features or
thresholds. It is a `price_vs_ma` mechanism — not an ADX level, RSI exhaustion,
ATR percentile mid-band, or multi-feature absolute regime classifier.

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- On FAIL: retuning forbidden; holdout forbidden
- No runtime / shadow / testnet / live / orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`

## Next step

Review and merge this definition-only PR before any development evaluation.
