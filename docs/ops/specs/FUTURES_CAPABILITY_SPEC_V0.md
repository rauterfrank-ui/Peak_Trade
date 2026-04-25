# Futures Capability Spec v0

## Purpose

This specification defines the minimum capability ladder required before Peak_Trade can treat futures or perpetual markets as supported trading surfaces.

It is intentionally staged. Futures support is not “spot plus leverage”; it requires explicit instrument metadata, margin semantics, liquidation handling, funding, order flags, risk controls, testnet proof, provenance, and candidate-specific evidence.

## Non-authority note

This is a docs-only, non-authoritative capability specification.

It does not grant Master V2 approval, Double Play authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, testnet execution permission, or Live permission.

It does not permit orders, exchange calls, market-data fetches, execution sessions, bounded-pilot sessions, Paper, Shadow, Testnet, or Live.

Any future implementation must adapt to Master V2 / Double Play governance, Scope / Capital Envelope, Risk / Exposure Caps, Safety / Kill-Switches, staged Execution Enablement, and candidate-specific operator evidence.

## Current repo classification

Current static audits classify the repo as futures-aware in some isolated or planning surfaces, but not crypto-futures-trading-ready.

Known current classification:

| Surface | Classification | Notes |
|---|---|---|
| CME / NQ / MNQ style surfaces | partial / offline futures-like | Not equivalent to crypto futures exchange execution. |
| Crypto execution / backtest | generic or spot/cash-style unless proven otherwise | Not sufficient for futures readiness. |
| `kraken_futures_testnet` | metadata / label surface | Not proven Kraken Futures adapter support. |
| `env_name` | metadata unless bound by governed adapter contract | Not execution authority. |
| Market Dashboard | future candidate | May be read-only capability display only. |
| Live futures | absent / not authorized | Explicitly out of scope. |

## Capability levels

### F0 — Inventory

Goal: know what futures-related docs, code, configs, tests, labels, and adapters exist.

Exit criteria:

- futures-related surfaces inventoried,
- spot/generic/futures-aware classifications recorded,
- label-only surfaces separated from executable adapter surfaces,
- no Live or testnet readiness claimed from names alone.

### F1 — Instrument metadata

Goal: define a futures instrument metadata contract.

Required fields include:

- instrument type,
- exchange,
- symbol,
- base currency,
- quote currency,
- settle currency,
- contract type,
- perpetual vs expiry,
- expiry when applicable,
- contract size,
- tick size,
- lot size,
- min notional,
- price precision,
- quantity precision.

Exit criteria:

- schema or model exists,
- tests prove required fields,
- dashboard can display missing/unknown fields safely.

### F2 — Market data provenance

Goal: distinguish market-data read surfaces from cache/report/artifact write surfaces.

Required fields include:

- data source,
- symbol / instrument id,
- market type,
- timestamp range,
- candle interval,
- mark / index / last price availability,
- funding rate availability,
- cache status,
- local write status,
- provenance metadata.

Exit criteria:

- provenance display is read-only,
- cache writes are explicit and never implied by a dashboard view,
- no S3/archive/evidence write occurs without governed approval.

### F3 — Backtest realism

Goal: futures backtests must model futures-specific mechanics.

Required mechanics include:

- futures fees,
- slippage,
- leverage,
- initial margin,
- maintenance margin,
- margin mode,
- liquidation price or liquidation distance,
- funding rate,
- funding interval,
- funding PnL,
- contract size,
- notional exposure,
- reduce-only close behavior.

Exit criteria:

- backtests fail closed when required futures metadata is missing,
- fees/slippage/funding/margin assumptions are explicit,
- stress tests include liquidation-adjacent scenarios,
- no backtest result implies Live readiness.

### F4 — Risk and safety contracts

Goal: ensure futures risk is governed before any testnet or live-like path.

Required controls include:

- max notional exposure,
- max leverage,
- max margin usage,
- liquidation-distance floor,
- funding-risk cap,
- per-instrument exposure cap,
- portfolio exposure cap,
- reduce-only enforcement for emergency exits,
- fail-closed risk checks,
- kill-switch compatibility,
- no-order safety guard.

Exit criteria:

- risk contracts are explicit and tested,
- SafetyGuard / RiskGate / KillSwitch boundaries remain separate,
- diagnostics are not treated as enforcement,
- Live remains blocked.

### F5 — Read-only dashboard

Goal: expose futures capability and state without controls or mutation.

Allowed dashboard behavior:

- display instrument metadata,
- display provenance,
- display cache status,
- display capability status,
- display risk/safety status,
- display no-live banner,
- display missing fields as missing.

Forbidden dashboard behavior:

- place orders,
- start sessions,
- arm execution,
- enable testnet,
- enable Live,
- toggle risk gates,
- toggle kill switches,
- write evidence,
- write archive/S3,
- fetch market data through write-enabled paths.

Exit criteria:

- dashboard is read-only,
- futures surfaces are labeled unsupported/partial/supported with evidence,
- no UI control implies execution authority.

### F6 — Testnet / dry-run proof

Goal: prove a futures testnet path without Live authority.

Required proof includes:

- explicit adapter binding,
- sandbox/testnet endpoint separation,
- credential safety,
- dry-run boundary,
- order payload tests,
- position/margin/funding tests,
- no-Live checks,
- audit logs,
- fail-closed behavior.

Exit criteria:

- testnet proof is candidate-specific,
- no production endpoint is reachable from testnet config,
- operator approval exists,
- no Live authorization is implied.

### F7 — Candidate evidence package

Goal: produce candidate-specific evidence for the governed readiness ladder.

Required evidence includes:

- candidate id,
- git head,
- config version,
- instrument metadata,
- testnet/dry-run proof,
- risk/safety proof,
- provenance,
- checksums,
- operator signoff,
- reviewer signoff.

Exit criteria:

- evidence is operator-held,
- archive/provenance paths are clear,
- gate status is not inferred from repo docs alone.

### F8 — Live governance, not now

Live futures trading is explicitly out of scope for this spec.

Before Live, Peak_Trade requires:

- Master V2 / Double Play governance,
- PRE_LIVE completion,
- explicit First-Live signoff,
- Scope / Capital Envelope approval,
- Risk / Exposure Caps approval,
- Safety / Kill-Switch validation,
- staged Execution Enablement,
- candidate-specific evidence,
- operator confirmation,
- no unresolved futures capability gaps.

## Required futures capability matrix

| Capability | Dashboard | Backtest | Testnet | Live | Current requirement |
|---|---:|---:|---:|---:|---|
| Instrument type | required | required | required | required | Must distinguish spot, futures, perpetual. |
| Futures symbol naming | required | required | required | required | Must not infer futures from string alone. |
| Contract metadata | required | required | required | required | Contract size, tick, lot, settle currency. |
| Leverage | display only | required | required | required | Must include cap and configured leverage. |
| Margin mode | display only | required | required | required | Isolated/cross must be explicit. |
| Maintenance margin | display missing/known | required | required | required | Needed for liquidation risk. |
| Liquidation price/distance | display missing/known | required | required | required | Must fail closed if unknown for execution. |
| Funding rate | display missing/known | required | required | required | Funding PnL required for realism. |
| Contract size | required | required | required | required | Needed for notional exposure. |
| Futures fees | optional display | required | required | required | Explicit schedule required. |
| Slippage | optional display | required | required | required | Stress-tested assumptions required. |
| Reduce-only orders | prohibited controls | required for sim | required | required | Must be modeled before execution. |
| Post-only orders | prohibited controls | optional | required if used | required if used | Must be explicit. |
| Stop-market / take-profit-market | prohibited controls | optional | required if used | required if used | Must be exchange-specific. |
| Position mode | display missing/known | required | required | required | One-way/hedge must be explicit. |
| Testnet adapter | display unsupported/partial | not required | required | required before Live | Must be real adapter binding. |
| Exchange sandbox safety | display status | not required | required | required before Live | Must prevent production endpoint use. |
| Risk caps | display only | required | required | required | Notional/margin/liquidation/funding caps. |
| Kill switch | display only | required | required | required | Must be futures-aware. |
| Provenance/cache boundary | required | required | required | required | No implicit write surfaces. |
| No-live gate | required | required | required | required | Live remains blocked unless governed. |

## Spot vs futures / perpetual distinction

A spot market position owns or represents the underlying asset exposure directly.

A futures or perpetual position is a derivative contract with distinct mechanics, including margin, liquidation risk, contract metadata, funding, position mode, and exchange-specific order semantics.

Peak_Trade must never treat a spot symbol, generic OHLCV series, or futures-like label as futures capability without explicit metadata and governed adapter proof.

## Kraken / `kraken_futures_testnet` classification

`kraken_futures_testnet` is currently classified as metadata / label surface unless a future governed adapter slice proves otherwise.

Rules:

1. `kraken_futures_testnet` must not be shown as supported futures trading capability by name alone.
2. `env_name=kraken_futures_testnet` is not execution authority.
3. `mode=testnet` and `env_name=kraken_futures_testnet` are separate concerns.
4. A Kraken spot/testnet client is not a Kraken Futures derivatives adapter.
5. Any future Kraken Futures path must prove adapter binding, order payloads, instrument metadata, margin/funding/liquidation semantics, risk/safety contracts, testnet proof, and candidate evidence.

## CME offline futures surface distinction

CME futures-like surfaces may be valuable for offline research or market-specific modeling.

They are not proof of crypto futures exchange readiness.

Do not use CME/NQ/MNQ-style support as evidence that crypto perpetuals, Kraken Futures, Binance Futures, Bybit, OKX, or any other derivatives exchange path is supported.

## Dashboard implications

Market Dashboard v0 may be futures-aware only as a read-only capability display.

It may show:

- exchange,
- instrument type,
- symbol,
- capability status,
- adapter status,
- testnet status,
- margin model status,
- leverage cap status,
- funding model status,
- liquidation model status,
- provenance status,
- cache/write status,
- risk/safety status,
- no-live banner.

It must not provide controls for orders, sessions, execution, testnet activation, Live activation, risk-gate toggles, kill-switch toggles, evidence writes, archive writes, or market-data writes.

## Testnet implications

A testnet label does not prove testnet readiness.

Before any futures testnet run, require:

- explicit adapter path,
- exchange sandbox endpoint proof,
- no production endpoint fallback,
- credentials isolation,
- dry-run/testnet-only config,
- futures instrument metadata,
- order payload contract tests,
- position/margin/funding/liquidation tests,
- risk/safety/kill-switch checks,
- operator approval,
- audit trail.

## Risk / Safety / KillSwitch requirements

Futures risk controls must account for:

- notional exposure,
- leverage,
- margin usage,
- maintenance margin,
- liquidation distance,
- funding risk,
- contract size,
- position mode,
- reduce-only exit behavior,
- exchange-level risk limits,
- portfolio exposure.

SafetyGuard, RiskGate, LiveRiskLimits, KillSwitch, diagnostics, and dashboard labels must remain distinct surfaces.

## Backtest realism requirements

A futures backtest must include:

- exchange fee model,
- slippage model,
- funding model,
- leverage model,
- margin model,
- liquidation model,
- contract size,
- notional exposure,
- stop / take-profit semantics if used,
- stress and Monte-Carlo style robustness checks.

Backtest success is not testnet readiness and is not Live readiness.

## Evidence / provenance requirements

Futures capability evidence must be candidate-specific.

Required evidence categories include:

- config version,
- git head,
- instrument metadata,
- data provenance,
- backtest assumptions,
- testnet proof if applicable,
- risk/safety proof,
- operator signoff,
- reviewer signoff,
- archive/checksum records.

Repo docs alone cannot satisfy G4-G8.

## Explicitly out of scope

Out of scope for this spec:

- implementing futures adapters,
- enabling testnet,
- enabling Live,
- placing orders,
- changing strategy logic,
- changing execution logic,
- changing risk logic,
- fetching market data,
- writing evidence,
- writing archives,
- changing dashboards,
- changing configs.

## Acceptance criteria before implementation

Before implementation starts, require:

1. This spec exists and is linked from the futures runbook or nearby ops/specs surface.
2. `kraken_futures_testnet` remains classified as label/metadata unless proven otherwise.
3. Required futures capability matrix is agreed.
4. Dashboard v0 scope is read-only.
5. No-live boundary is explicit.
6. Implementation branch has a single clear slice:
   - spec,
   - model,
   - tests,
   - dashboard,
   - or adapter,
   not all at once.

## References

- `docs/ops/runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md`
- `docs/ops/specs/SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md`
- local operator audit bundle: `peak_trade_futures_repo_inventory_v0` <!-- pt:ref-target-ignore --> (local /tmp audit artifact, not a repo reference)
- local operator audit bundle: `peak_trade_kraken_futures_testnet_read_only_audit_v0` <!-- pt:ref-target-ignore --> (local /tmp audit artifact, not a repo reference)
