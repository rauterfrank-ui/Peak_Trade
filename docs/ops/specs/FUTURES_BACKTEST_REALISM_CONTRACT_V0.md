# Futures Backtest Realism Contract v0

## Purpose

This contract defines the minimum assumptions, mechanics, and reporting requirements before a Peak_Trade backtest can be called futures-realistic.

It supports the F3 Backtest Realism stage in the Futures Capability Spec v0.

The contract exists to prevent spot/cash-style backtests, generic OHLCV simulations, or fee/slippage-only simulations from being interpreted as futures/perpetual readiness.

## Non-authority note

This is a docs-only backtest realism contract.

It does not implement a backtest engine, exchange adapter, dashboard, testnet path, or Live path.

It does not grant Master V2 approval, Double Play authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, testnet execution permission, or Live permission.

It does not permit orders, exchange calls, market-data fetches, execution sessions, bounded-pilot sessions, Paper, Shadow, Testnet, or Live.

## Scope

This contract applies when a run, report, dashboard, experiment, or operator review claims futures realism for a futures, perpetual, swap, or derivative-like instrument.

It does not prevent spot/cash-style backtests from existing. It requires them to be labeled correctly.

A backtest may be:

- `spot_realistic`,
- `generic_market_simulation`,
- `futures_incomplete`,
- `futures_realism_candidate`,
- `futures_realistic_verified`.

Only the final category may be used as an input to futures testnet readiness, and even then it is not Live readiness.

## Required prerequisites

A futures-realistic backtest requires:

1. F1 instrument metadata:
   - instrument identity,
   - contract type,
   - contract size,
   - tick/lot sizing,
   - settlement currency,
   - margin/leverage metadata.
2. F2 market data provenance:
   - dataset id,
   - exchange,
   - market type,
   - OHLCV source,
   - price source,
   - funding source where applicable,
   - cache/write state,
   - freshness state.
3. Explicit strategy/config version.
4. Explicit fee/slippage/funding/margin assumptions.
5. Explicit fail-closed behavior for missing required fields.

## Required market data assumptions

A futures-realistic backtest must record:

- dataset id,
- instrument id,
- exchange,
- market type,
- symbol,
- time range,
- candle interval,
- OHLCV source,
- price source,
- mark/index/last price assumptions,
- funding source where applicable,
- freshness status,
- provenance reference.

Rules:

- Spot OHLCV is not futures OHLCV.
- Last price is not automatically mark price.
- Mark/index price assumptions must be explicit when used for liquidation or margin logic.
- Missing market type or provenance makes the run futures-incomplete.

## Required fee / slippage assumptions

A futures-realistic backtest must record:

- exchange fee schedule or explicit fee model,
- maker/taker distinction where applicable,
- funding-related costs separately from trading fees,
- slippage model,
- stress slippage model,
- commission currency,
- fee application timing.

Rules:

- `fee_bps` plus `slippage_bps` alone is not sufficient to claim futures realism.
- Fees and slippage must be applied to notional exposure using contract metadata.
- Stress slippage must be considered for liquidation-adjacent scenarios.

## Required contract / notional assumptions

A futures-realistic backtest must model:

- contract size,
- contract unit,
- settlement currency,
- position quantity,
- notional exposure,
- mark-to-market behavior,
- PnL currency,
- precision and sizing constraints.

Rules:

- Quantity times price is not necessarily notional exposure without contract size.
- Missing contract size makes futures realism incomplete.
- PnL currency must be explicit for inverse or settled contracts.

## Required leverage / margin assumptions

A futures-realistic backtest must record:

- leverage,
- maximum leverage cap,
- margin mode,
- initial margin,
- maintenance margin,
- margin usage over time,
- available equity assumptions,
- margin call or fail-closed behavior.

Rules:

- Leverage is risk exposure, not performance decoration.
- Missing margin mode makes futures realism incomplete.
- Cross/isolated margin must not be inferred.

## Required liquidation assumptions

A futures-realistic backtest must model or explicitly mark missing:

- liquidation price,
- liquidation distance,
- maintenance margin threshold,
- liquidation fee or penalty if modeled,
- forced-exit behavior,
- fail-closed behavior when liquidation cannot be computed.

Rules:

- A futures backtest without liquidation semantics is futures-incomplete.
- Liquidation-adjacent stress scenarios must be reported separately.
- Dashboard or reports must not hide missing liquidation logic.

## Required funding assumptions

A perpetual futures backtest must model or explicitly mark missing:

- funding rate,
- funding interval,
- next funding time,
- funding PnL,
- funding source,
- funding timestamp coverage.

Rules:

- Ignoring funding for perpetuals makes futures realism incomplete unless explicitly justified and labeled.
- Funding must be separated from trading fees.
- Funding assumptions must be included in reports.

## Required position / order behavior assumptions

A futures-realistic backtest must define:

- position mode,
- long/short handling,
- reduce-only behavior,
- close behavior,
- stop-market behavior if used,
- take-profit-market behavior if used,
- partial fills if modeled,
- order sizing precision,
- unavailable order type behavior.

Rules:

- Reduce-only/close behavior cannot be assumed from spot order semantics.
- Position mode must be explicit.
- Unsupported order types must fail closed or be excluded.

## Stress / robustness requirements

A futures-realism candidate must include stress coverage for:

- fee increase,
- slippage expansion,
- funding spike,
- leverage cap reduction,
- margin requirement increase,
- mark/last price divergence,
- liquidation-distance compression,
- data staleness,
- missing funding data,
- gap move.

Recommended robustness layers:

- walk-forward validation,
- Monte Carlo perturbation,
- adversarial fee/slippage stress,
- liquidation-adjacent scenario replay,
- funding-regime scenario replay.

## Metrics / reporting requirements

Reports must include:

- total return,
- Sharpe or equivalent risk-adjusted return,
- max drawdown,
- profit factor,
- win/loss statistics,
- turnover,
- fees paid,
- slippage impact,
- funding PnL,
- liquidation events,
- liquidation-distance minimum,
- max notional exposure,
- max leverage used,
- max margin usage,
- data freshness status,
- missing/incomplete futures fields.

Any missing required field must be visible in the report.

## Fail-closed and incomplete-realism semantics

A backtest must fail closed or mark `futures_realism_status=futures_incomplete` if any required futures field is missing.

Examples that must not be reported as futures-realistic:

- no contract size,
- no margin mode,
- no maintenance margin,
- no liquidation model,
- no funding model for perpetuals,
- no market type provenance,
- spot OHLCV used as futures data without explicit labeling,
- generic fee/slippage-only simulation,
- unknown cache/write provenance.

## Dashboard / testnet / live boundary

A dashboard may display backtest realism status, but must not:

- start backtests,
- run sessions,
- place orders,
- enable testnet,
- enable Live,
- write evidence,
- write archives,
- hide incomplete futures realism.

A futures-realistic backtest is not testnet readiness.

A futures-realistic backtest is not Live readiness.

Testnet and Live require separate governance, adapter proof, risk/safety proof, and candidate-specific evidence.

## Validation / future tests

Future tests should prove:

1. Futures-realism reports require F1 instrument metadata.
2. Futures-realism reports require F2 market data provenance.
3. Missing contract size marks the run incomplete or fails closed.
4. Missing liquidation model marks the run incomplete or fails closed.
5. Missing funding model for perpetuals marks the run incomplete or fails closed.
6. Fee/slippage-only runs cannot claim futures realism.
7. Backtest reports expose funding PnL and liquidation-distance metrics when applicable.
8. Spot/cash backtests cannot be promoted to futures realism by label alone.

## References

- [Futures Capability Spec v0](FUTURES_CAPABILITY_SPEC_V0.md)
- [Futures Instrument Metadata Contract v0](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md)
- [Futures Market Data Provenance Contract v0](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md)
- [Session env_name and exchange surfaces non-authority v0](SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md)
- [Futures Trading Readiness Runbook v0](../runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md)
