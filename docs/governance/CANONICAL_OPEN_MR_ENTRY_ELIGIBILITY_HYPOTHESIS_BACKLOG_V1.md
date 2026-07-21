# Canonical open MR entry-eligibility hypothesis backlog v1

## Status

`OPEN_BACKLOG` — versioned canonical SSOT for open Mean-Reversion entry-eligibility
research candidates. Definition-only governance. No preregistration, no evaluation,
no backtest, no holdout access, no runtime activation, no productive trading-logic
mutation in this slice.

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

Semantic duplicates and parameter retunes of these terminals are forbidden.

## Open candidates (deterministic priority)

Priority criteria are locked a priori (semantic distance, entry-effectiveness,
measurability, low complexity, low overfit risk, repo support). No performance-based
selection. No ties.

| Rank | Hypothesis ID | Queue |
|---:|---|---|
| 1 | `MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` | `NEXT_ELIGIBLE_FOR_PREREGISTRATION` |
| 2 | `MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` | `QUEUED` |
| 3 | `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` | `QUEUED` |

All open candidates are `OPEN_UNPREREGISTERED`.

## Governance rules

- At most one open preregistration at a time
- Exactly one development run per hypothesis
- No retuning after FAIL
- No holdout use
- No candidate combination / multi-gate stacks
- No reprioritization without a separate versioned governance PR
- Evaluation only after a separate preregistration PR and operator GO
- Runtime / shadow / paper / testnet / live / orders remain locked

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`
- `EVALUATION_EXECUTED=false`
- `DEVELOPMENT_RUN_COUNT=0`

## Next step

After merge + operator GO: open a separate definition-only preregistration PR for
`MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` only.
