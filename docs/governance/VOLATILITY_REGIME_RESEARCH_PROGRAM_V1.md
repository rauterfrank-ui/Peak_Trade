# VOLATILITY_REGIME_RESEARCH_PROGRAM_V1

Status: `DEFINITION_ONLY_PROGRAM_OPEN`

## Active preregistered hypothesis

- Strategy: `VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1`
- Hypothesis: `VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_NON_BITCOIN_PERPETUALS_V1`
- Target: `VOLATILITY_EXPANSION_THEN_FAILED_CONTINUATION_FADE`
- Lane backlog: `OPEN_BACKLOG`
- `strategy_implementation_present=true`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=true` (surfaces; execution still requires separate GO)
- `DEVELOPMENT_EVALUATION_EXECUTED=false`
- `DEVELOPMENT_RUN_COUNT=0` / `RUN_SLOT_CONSUMED=false`

## Lifecycle

- CREATE_SUCCESSOR applied after DECLARE_AWAITING; CLOSE_LANE not applied
- Strategy implementation present; next step is bounded Development evaluation execution
- Predecessor VEPC remains terminal `CONSUMED_NO_RETRY`
- Causal claim opposite to VEPC: fade failed continuation vs continue after pullback

## Safety

LIVE/ORDERS/SHADOW/PAPER/TESTNET/SCHEDULER/HOLDOUT closed. No evaluation executed in this slice.

docs_token: DOCS_TOKEN_VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
