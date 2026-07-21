# Canonical open MR entry-eligibility hypothesis backlog v1

## Status

`OPEN_BACKLOG` — versioned canonical SSOT for open Mean-Reversion entry-eligibility
research candidates. Definition-only governance. No further evaluation, no holdout
access, no runtime activation, no productive trading-logic mutation in this slice.
Open candidates are empty. Exactly zero hypotheses are `DEFINITION_ONLY_PREREGISTERED`.

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

## Terminal hypotheses

### TERMINAL_FAIL (unchanged)

1. `REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1`
2. `ENTRY_EFFECTIVE_MR_ELIGIBILITY_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1`
3. `RSI_EXHAUSTION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
4. `ADX_RANGE_ADMISSION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
5. `MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
6. `MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`

### TERMINAL_PASS

7. `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` —
   PASS / `ALL_PASS_REQUIRES_MET` (Wilder ADX(14) +DI/−DI direction confirmation;
   development run count 1/1; evidence under
   `docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1/`).
   Economic offline gate remains closed. Promotion remains closed. Holdout remains
   forbidden without a separate operator GO. No second ADX DI evaluation run is
   permitted.

Semantic duplicates and parameter retunes of these terminals are forbidden.
`adx_di_direction_confirmation` remains forbidden for any future open candidates.

## Preregistered

None. `preregistered_hypotheses=[]`.

## Open candidates

None. `open_candidates=[]`. No `NEXT_ELIGIBLE_FOR_PREREGISTRATION`.

## Governance rules

- At most one open preregistration at a time
- Exactly one development run per hypothesis
- No retuning after FAIL
- No holdout use without separate operator GO
- No candidate combination / multi-gate stacks
- No reprioritization without a separate versioned governance PR
- Development PASS does not open the economic offline gate
- Runtime / shadow / paper / testnet / live / orders remain locked
- `exactly_one_next_eligible_for_preregistration=false` while open queue is empty
- `open_candidate_count_min=0`

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`
- `EVALUATION_EXECUTED=false` (for any remaining open work; ADX DI consumed 1/1)
- `DEVELOPMENT_RUN_COUNT=0` (backlog-level)

## Next step

`REVIEW_AND_MERGE_ADX_DI_DEVELOPMENT_EVALUATION_THEN_SEPARATE_HOLDOUT_GO_IF_AUTHORIZED`

Any holdout use or further research candidates require a separate PR and operator GO.
No second ADX DI evaluation run is permitted. No reopen of terminal hypotheses.
