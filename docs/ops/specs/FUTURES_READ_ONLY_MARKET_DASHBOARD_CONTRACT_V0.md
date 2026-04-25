# Futures Read-only Market Dashboard Contract v0

## Purpose

This contract defines the minimum boundary for a futures-aware Market Dashboard in Peak_Trade.

It supports the F5 Read-only Dashboard stage in the Futures Capability Spec v0.

The dashboard may display futures capability, metadata, provenance, backtest-realism, and risk/safety status. It must not become an execution, testnet, Live, evidence, archive, or control surface.

## Non-authority note

This is a docs-only dashboard contract.

It does not implement a dashboard, API endpoint, exchange adapter, data fetcher, backtest engine, testnet path, or Live path.

It does not grant Master V2 approval, Double Play authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, testnet execution permission, or Live permission.

It does not permit orders, exchange calls, market-data fetches, execution sessions, bounded-pilot sessions, Paper, Shadow, Testnet, or Live.

## Scope

This contract applies to any dashboard, WebUI, API, or report surface that displays futures or perpetual market capability.

It covers display semantics only.

It does not authorize:

- data fetching,
- cache writes,
- evidence writes,
- archive writes,
- session starts,
- order placement,
- testnet activation,
- Live activation,
- risk-control toggles,
- kill-switch toggles.

## Required prerequisites

A futures-aware dashboard must consume or display status from the staged contracts:

1. F1 Instrument Metadata:
   - instrument type,
   - contract metadata,
   - precision/sizing,
   - margin/leverage metadata.
2. F2 Market Data Provenance:
   - source,
   - freshness,
   - cache/write status,
   - last/mark/index price availability,
   - funding availability.
3. F3 Backtest Realism:
   - realism status,
   - missing assumptions,
   - stress coverage,
   - funding/liquidation/notional metrics when available.
4. F4 Risk / Safety / KillSwitch:
   - risk-cap status,
   - SafetyGuard status,
   - KillSwitch status,
   - missing/unknown futures risk fields.

The dashboard must display missing prerequisites as missing, not infer support.

## Allowed dashboard displays

A futures-aware dashboard may display:

- exchange,
- instrument id,
- symbol,
- market type,
- contract type,
- capability status,
- adapter status,
- testnet status,
- metadata completeness,
- data provenance,
- cache/write status,
- freshness status,
- funding availability,
- leverage cap,
- margin mode,
- liquidation-model status,
- backtest realism status,
- risk/safety status,
- no-live banner.

It may display historical values, static fixtures, read-only cached values, or status summaries only when their source and freshness are visible.

## Required dashboard status model

Dashboard status values must be explicit.

Recommended statuses:

| Status | Meaning |
|---|---|
| `spot_only` | Spot support only; not futures. |
| `generic_market` | Generic market data without futures semantics. |
| `metadata_label_only` | Label/registry/env-name exists but no proven adapter. |
| `futures_metadata_missing` | F1 metadata missing. |
| `futures_metadata_partial` | Some F1 metadata present, incomplete. |
| `provenance_missing` | F2 provenance missing. |
| `provenance_partial` | Some F2 provenance present, incomplete. |
| `backtest_realism_incomplete` | F3 missing required assumptions. |
| `risk_safety_incomplete` | F4 missing risk/safety requirements. |
| `testnet_candidate_only` | Candidate may be eligible for testnet review, not Live. |
| `unsupported_for_live` | Not Live-capable. |

Dashboard copy must avoid green/ready styling for partial states unless the relevant evidence exists.

## Required instrument metadata display

The dashboard must display or mark missing:

- instrument id,
- exchange,
- market type,
- symbol,
- base currency,
- quote currency,
- settle currency,
- contract type,
- perpetual flag,
- expiry where applicable,
- contract size,
- tick size,
- lot size,
- max leverage,
- margin modes,
- liquidation model status,
- metadata source,
- provenance reference.

Unknown or missing values must be visible.

## Required market-data/provenance display

The dashboard must display or mark missing:

- data source,
- fetch mode,
- cache status,
- local write status,
- artifact write status,
- evidence write status,
- S3 write status,
- last price availability,
- mark price availability,
- index price availability,
- funding rate availability,
- last refresh timestamp,
- freshness status,
- provenance reference.

Read-only dashboard v0 must not call write-enabled fetch/cache paths.

## Required backtest-realism display

The dashboard may display futures backtest status only if it includes:

- realism status,
- dataset id,
- instrument id,
- strategy/config version if available,
- fee model status,
- slippage model status,
- funding model status,
- margin model status,
- liquidation model status,
- notional exposure status,
- stress coverage status,
- missing field summary.

The dashboard must not present a spot/cash backtest as futures-realistic.

## Required risk/safety display

The dashboard may display:

- RiskGate status,
- SafetyGuard status,
- KillSwitch status,
- LiveRiskLimits status,
- notional exposure status,
- leverage status,
- margin usage status,
- liquidation-distance status,
- funding-risk status,
- missing/unknown risk fields.

The dashboard must also state that display is not enforcement.

Diagnostics and dashboard display are not risk enforcement.

## Kraken / env_name display rules

`kraken_futures_testnet` must be displayed as:

- metadata / label surface,
- not a proven Kraken Futures adapter,
- not futures-testnet execution proof,
- not futures trading capability,
- not Live or testnet authorization.

Any dashboard row/card for this value must include a warning equivalent to:

> Metadata label only. No governed Kraken Futures adapter or futures execution path proven.

`env_name` must never be displayed as execution authority.

`mode` and `env_name` must remain separate concepts.

## Explicitly prohibited controls

A futures-aware dashboard must not include controls for:

- placing orders,
- cancelling orders,
- starting sessions,
- starting backtests,
- refreshing market data through write-enabled paths,
- enabling testnet,
- enabling Live,
- arming execution,
- toggling RiskGate,
- toggling SafetyGuard,
- toggling KillSwitch,
- changing leverage,
- changing margin mode,
- writing evidence,
- writing archives,
- uploading to S3,
- changing configs.

If any future UI adds controls, that must be a separate governed slice, not part of read-only dashboard v0.

## API / endpoint boundary

Dashboard APIs must be read-only.

Allowed:

- return static capability summaries,
- return read-only cached/fixture summaries,
- return status derived from repo/config metadata without mutation,
- return explicit unknown/missing states.

Forbidden:

- exchange calls,
- market-data fetches through write-enabled paths,
- cache writes,
- evidence writes,
- archive writes,
- session starts,
- order placement,
- config mutation,
- workflow dispatch,
- hidden background jobs.

API responses must include no-live and no-order boundaries where futures capability is displayed.

## UI copy / banner requirements

Every futures dashboard view must include a visible banner:

> Futures dashboard is read-only. No orders, no sessions, no testnet activation, no Live authorization.

For incomplete capability states, the UI must include:

- missing field summary,
- status explanation,
- next required contract/stage,
- provenance freshness,
- no-live banner.

Avoid labels such as `ready`, `supported`, `production`, or `live-ready` unless the exact governed evidence exists.

## Fail-closed display semantics

The dashboard must fail closed in display semantics:

- missing metadata → show unsupported/partial,
- missing provenance → show unsupported/partial,
- missing funding → show incomplete for perpetuals,
- missing liquidation model → show incomplete for futures risk,
- missing KillSwitch status → show risk/safety incomplete,
- unknown adapter binding → show metadata/label only,
- stale data → show stale.

Fail-closed display does not enforce trading. It prevents misleading UI claims.

## Validation / future tests

Future tests should prove:

1. Dashboard futures surfaces are read-only.
2. No dashboard endpoint calls exchange clients.
3. No dashboard endpoint writes cache/evidence/archive/S3.
4. `kraken_futures_testnet` renders as metadata label only.
5. Unknown F1 metadata renders unsupported/partial.
6. Unknown F2 provenance renders unsupported/partial.
7. Unknown F3 realism renders incomplete.
8. Unknown F4 risk/safety renders incomplete.
9. No UI state implies Live authorization.
10. No UI control exists for orders, sessions, testnet, Live, RiskGate, SafetyGuard, or KillSwitch toggles.

## References

- [Futures Capability Spec v0](FUTURES_CAPABILITY_SPEC_V0.md)
- [Futures Instrument Metadata Contract v0](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md)
- [Futures Market Data Provenance Contract v0](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md)
- [Futures Backtest Realism Contract v0](FUTURES_BACKTEST_REALISM_CONTRACT_V0.md)
- [Futures Risk Safety KillSwitch Contract v0](FUTURES_RISK_SAFETY_KILLSWITCH_CONTRACT_V0.md)
- [Session env_name and exchange surfaces non-authority v0](SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md)
- [Futures Trading Readiness Runbook v0](../runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md)
