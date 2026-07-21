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

### TERMINAL_PASS (development) + holdout terminal technical failure

7. `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` —
   Development: `TERMINAL_PASS` / `ALL_PASS_REQUIRES_MET` (Wilder ADX(14) +DI/−DI
   direction confirmation; development run count 1/1; evidence under
   `docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1/`).
   Holdout: single authorized run consumed (`holdout_run_count=1`,
   `holdout_run_limit=1`); registry status
   `HOLDOUT_EVALUATION_EXECUTED_TERMINAL`; result class
   `ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN` after sealed-panel data access failed on
   MV2 replay signal-index mismatch (`mv2_replay_signal_index_mismatch`). Primary
   economic metrics were not produced (`evaluable=false`; no PASS / FAIL_ECONOMIC
   claim). Evidence:
   `docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v1/`.
   Provenance of count transition `0 → 1`: merge commit
   `0cd6e71d0d20345a5a66a23c5b63983effc20b1a` / PR `#5384`
   (prior count-zero preregistration commit
   `f9654e03acff05837cc6121bb6a5877bccd054ac` / PR `#5383`). Retry / second holdout
   run forbidden. Economic offline gate remains closed. Promotion remains closed.
   No second ADX DI development evaluation run is permitted.

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
- No holdout use / no second ADX DI holdout run (slot already consumed terminal)
- No candidate combination / multi-gate stacks
- No reprioritization without a separate versioned governance PR
- Development PASS does not open the economic offline gate
- Holdout technical failure does not open the economic offline gate
- Runtime / shadow / paper / testnet / live / orders remain locked
- `exactly_one_next_eligible_for_preregistration=false` while open queue is empty
- `open_candidate_count_min=0`

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`
- `EVALUATION_EXECUTED=false` (for any remaining open work; ADX DI development 1/1
  and holdout 1/1 already consumed)
- `DEVELOPMENT_RUN_COUNT=0` (backlog-level)
- `RERUN_ALLOWED=false` for the ADX DI holdout run-id
  `evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v1`

## Next step

`REVIEW_TERMINAL_HOLDOUT_ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN_NO_RETRY`

Do **not** re-run the ADX DI holdout evaluation. Further research candidates require a
separate PR and operator GO. No reopen of terminal hypotheses without a new
hypothesis id.
