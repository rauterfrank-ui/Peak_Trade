# ADX range-admission MR eligibility — preregistered hypothesis and measurement v1

## Status

`DEFINITION_ONLY` — hypothesis and measurement contract preregistered; no evaluation.

## Binding

- Hypothesis: `ADX_RANGE_ADMISSION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
- Contract: `adx_range_admission_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Multiple-testing budget: `1`
- Authorized later development evaluation runs: `1`
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Treatment: `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER` (not implemented in this slice)
- Primary decision metric: `NET_PROFIT_FACTOR` (joint PASS requires all locked economic companions)

## Filter (ex ante, deterministic)

Canonical ADX range-admission from repo SSOT defaults in
`config&#47;config.toml` `[strategies.trend_following.defaults]`, computed via
`src&#47;strategies&#47;trend_following.py` (`TrendFollowingStrategy._compute_adx`)
(Wilder ewm, `alpha=1&#47;period`, `adjust=False`):

- `adx_period=14`
- `adx_threshold=25.0`
- `eligibility_comparator=lt` (ELIGIBLE iff ADX &lt; 25)
- `warmup_bars=28` (2 × period)

Eligibility rule: at finalized bar t, before any new entry decision, compute
ADX(14). ELIGIBLE iff ADX is finite and ADX &lt; 25; otherwise STAND_ASIDE.
First 28 bars of warmup are STAND_ASIDE.

`ENTRY_ELIGIBILITY_DIVERGENCE_REQUIRED=true` — absence ⇒ `RESULT_CLASS=FAIL`.

Does not change direction/side: only blocks entry when ADX indicates a strong
trend. Bollinger `entry_side=NONE` unchanged; Master V2 / Double-Play remain sole
direction authority.

## Orthogonality — distinction from prior FAILs

This is a single-feature Wilder-ADX range-admission mechanism, orthogonal to three
prior FAILs:

1. `regime_gated_standaside_mr_preregistered_economic_hypothesis_measurement_contract.v1`
   — FAIL: `identical_arms_gate_inactive_on_entries` (absolute-threshold
   multi-feature regime classifier).
2. `entry_effective_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
   — FAIL: `net_profit_factor_not_improved_despite_entry_eligibility_divergence`
   (ATR(14) rolling-percentile mid-band).
3. `rsi_exhaustion_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
   — FAIL: `net_profit_factor_not_improved_despite_entry_eligibility_divergence`
   (RSI(14) exhaustion).

This contract does not reuse, rename, or retune any prior mechanism's features or
thresholds. Range admission is the complement of TrendFollowing's ADX &gt; 25 trend
entry — not a retune of the failed multi-feature RANGE_BOUND classifier.

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- On FAIL: retuning forbidden; holdout forbidden
- No runtime / shadow / testnet / live / orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`

## Next step

Review and merge this definition-only PR before any development evaluation.
