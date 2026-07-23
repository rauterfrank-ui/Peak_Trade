# VOLATILITY_REGIME_RESEARCH_PROGRAM_V1

Status: `DEFINITION_ONLY_PROGRAM_OPEN`

## Active preregistered hypothesis

- Strategy: `VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1`
- Hypothesis: `VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_NON_BITCOIN_PERPETUALS_V1`
- Target: `VOLATILITY_EXPANSION_THEN_FAILED_CONTINUATION_FADE`
- Lane backlog: `OPEN_BACKLOG`
- `strategy_implementation_present=true`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=true`
- `DEVELOPMENT_EVALUATION_EXECUTED=true`
- `DEVELOPMENT_RUN_COUNT=1` / `RUN_SLOT_CONSUMED=true`
- Terminal development verdict: `DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;FAIL`

## Lifecycle

- CREATE_SUCCESSOR applied after DECLARE_AWAITING; CLOSE_LANE not applied
- Bounded DEVELOPMENT evaluation executed once; gates failed; retry forbidden
- Predecessor VEPC remains terminal `CONSUMED_NO_RETRY`
- Causal claim opposite to VEPC: fade failed continuation vs continue after pullback

## Safety

LIVE/ORDERS/SHADOW/PAPER/TESTNET/SCHEDULER/HOLDOUT closed. Economic/promotion gates closed.

docs_token: DOCS_TOKEN_VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
