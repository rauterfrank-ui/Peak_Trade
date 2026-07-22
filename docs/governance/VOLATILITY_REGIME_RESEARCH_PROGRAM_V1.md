# VOLATILITY_REGIME_RESEARCH_PROGRAM_V1

Definition-only research-program SSOT for operator-authorized volatility-regime hypotheses.

## Active identity

- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Strategy: `VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1`
- Hypothesis: `VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- Target: `VOLATILITY_EXPANSION_THEN_LIMITED_PULLBACK_CONTINUATION`
- Slice: historical development slot `CONSUMED_NO_RETRY`; no evaluation retry
- `strategy_implementation_present=true`
- Canonical entry point: `scripts/research/run_evaluate_volatility_expansion_pullback_continuation_development_v1.py`

## Terminal predecessors (retry forbidden)

Includes VCB, VEP, VDB, VDBX, and `VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1` (`FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`).

## Safety

- `DEVELOPMENT_RUN_COUNT=1`
- `DEVELOPMENT_SLOT_CONSUMED=true`
- `DEVELOPMENT_EVALUATION_EXECUTED=false`
- `HISTORICAL_VEPC_SLOT_STATUS=CONSUMED_NO_RETRY`
- `EVALUATION_RETRY_AUTHORIZED=false`
- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- `HOLDOUT_ACCESSED=false`
- Master V2 / Double-Play / Risk / Sizing / Execution unchanged

## Next step

Separate operator GO required for any successor hypothesis or further infrastructure scope.
No VEPC evaluation retry.

docs_token: DOCS_TOKEN_VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
