# RSI-exhaustion MR eligibility — preregistered hypothesis and measurement v1

## Status

`DEFINITION_ONLY` — hypothesis and measurement contract preregistered; no evaluation.

## Binding

- Hypothesis: `RSI_EXHAUSTION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
- Contract: `rsi_exhaustion_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Multiple-testing budget: `1`
- Authorized later development evaluation runs: `1`
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Treatment: `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER` (not implemented in this slice)

## Filter (ex ante, deterministic)

Canonical `rsi_exhaustion_filter` from repo SSOT defaults where
`config/config.toml` `[strategy.rsi_strategy]` and `[strategy.rsi_reversion_v1]`
agree, computed via the causal `src/strategies/rsi.py::calculate_rsi` (EWM,
`span=14`, `adjust=False`) — the Wilder-smoothing strategy-class variant is
explicitly excluded:

- `rsi_period=14`
- `oversold=30`, `overbought=70`
- `use_wilder=false`, `calculator=ewm_causal_span`

Eligibility rule: at finalized bar t, before any new entry decision, compute
RSI(14). ELIGIBLE iff RSI is finite and (RSI <= 30 or RSI >= 70); otherwise
STAND_ASIDE. First 14 bars of warmup are STAND_ASIDE.

`ENTRY_ELIGIBILITY_DIVERGENCE_REQUIRED=true` — absence ⇒ `RESULT_CLASS=FAIL`.

Does not change direction/side: only blocks entry when RSI shows no exhaustion.
Bollinger `entry_side=NONE` unchanged; Master V2 / Double-Play remain sole
direction authority.

## Orthogonality — distinction from prior FAILs

This is a momentum-exhaustion mechanism, orthogonal to two prior FAILs:

1. `regime_gated_standaside_mr_preregistered_economic_hypothesis_measurement_contract.v1`
   — FAIL: `identical_arms_gate_inactive_on_entries` (absolute-threshold
   multi-feature regime classifier: `realized_vol_168h`, `range_compression_72h`,
   `trend_strength_168h`).
2. `entry_effective_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
   (PR #5361) — FAIL: `net_profit_factor_not_improved_despite_entry_eligibility_divergence`
   (ATR(14) rolling-percentile mid-band (25,75) `vol_regime_filter` primitive:
   `atr_14h`, `atr_14h_rolling_percentile_rank_100h`).

This contract does not reuse, rename, or retune either prior mechanism's
features or thresholds. It requires observed entry-eligibility divergence
between treatment and control as a hard measurement condition, independently
computed from RSI(14) rather than ATR percentile rank.

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- No runtime / shadow / testnet / live / orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`

## Next step

Review and merge this definition-only PR before any development evaluation.
