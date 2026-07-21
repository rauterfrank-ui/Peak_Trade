# Canonical open MR entry-eligibility hypothesis backlog v1

## Status

`OPEN_BACKLOG` — versioned canonical SSOT for open Mean-Reversion entry-eligibility
research candidates. Definition-only governance. No evaluation, no backtest, no
holdout access, no runtime activation, no productive trading-logic mutation in this
slice. Open preregistrations are empty after the MACD histogram-countertrend
terminal FAIL.

## Binding

- SSOT: `config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json`
- Validator: `src/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.py`
- Baseline (immutable): `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Required treatment type for future preregistrations:
  `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
  (`DEVELOPMENT_ONLY`, OKX Linear-USDT Non-Bitcoin Perpetuals, PT1H)
- BTC excluded; Spot excluded
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only
- Economic gate closed; promotion closed

## Terminal hypotheses (referenced unchanged)

1. `REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1` —
   FAIL / `identical_arms_gate_inactive_on_entries`
2. `ENTRY_EFFECTIVE_MR_ELIGIBILITY_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1` —
   FAIL / `NET_PROFIT_FACTOR_NOT_IMPROVED` (ATR percentile mid-band)
3. `RSI_EXHAUSTION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` —
   FAIL / `NET_PROFIT_FACTOR_NOT_IMPROVED`
4. `ADX_RANGE_ADMISSION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` —
   FAIL / `NET_PROFIT_FACTOR_NOT_IMPROVED`
5. `MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` —
   FAIL / `NET_PROFIT_FACTOR_NOT_IMPROVED` (price-vs-SMA(50) with-trend admission;
   development run count 1/1; evidence under
   `docs/evidence/evaluate_ma_trend_alignment_mr_eligibility_development_v1/`)
6. `MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` —
   FAIL / `NET_PROFIT_FACTOR_NOT_IMPROVED` (MACD histogram-sign countertrend;
   development run count 1/1; evidence under
   `docs/evidence/evaluate_macd_histogram_countertrend_mr_eligibility_development_v1/`)

Semantic duplicates and parameter retunes of these terminals are forbidden.
`price_vs_ma_trend_alignment` and `macd_histogram_sign_countertrend` remain
forbidden for remaining open candidates.

## Preregistered

None. `preregistered_hypotheses=[]`.

## Open candidates (deterministic priority)

Priority criteria are locked a priori (semantic distance, entry-effectiveness,
measurability, low complexity, low overfit risk, repo support). No performance-based
selection. No ties. Evaluation of the next eligible candidate is **NOT authorized**
by this MACD evaluation transition.

| Rank | Hypothesis ID | Queue |
|---:|---|---|
| 1 | `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` | `NEXT_ELIGIBLE_FOR_PREREGISTRATION` |

All open candidates are `OPEN_UNPREREGISTERED`.

## Governance rules

- At most one open preregistration at a time
- Exactly one development run per hypothesis
- No retuning after FAIL
- No holdout use
- No candidate combination / multi-gate stacks
- No reprioritization without a separate versioned governance PR
- Evaluation only after a separate preregistration PR and operator GO
- No auto-evaluation of the next eligible candidate from this transition
- No reopen of terminal hypotheses
- Runtime / shadow / paper / testnet / live / orders remain locked

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`
- `EVALUATION_EXECUTED=false` (for remaining open candidates)
- `DEVELOPMENT_RUN_COUNT=0` (backlog-level; MACD consumed its single authorized run)

## Next step

`REQUEST_DEFINITION_ONLY_PREREGISTRATION_PR_FOR_ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_V1`

Definition-only preregistration of ADX DI direction confirmation (and any later
evaluation) requires a separate PR and operator GO. This MACD evaluation transition
does not authorize further preregistration, evaluation, holdout access, or productive
authority change. No second MACD evaluation run is permitted.
