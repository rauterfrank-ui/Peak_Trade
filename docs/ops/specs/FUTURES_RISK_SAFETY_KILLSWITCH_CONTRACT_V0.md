# Futures Risk Safety KillSwitch Contract v0

## Purpose

This contract defines the minimum risk, safety, and kill-switch requirements before Peak_Trade can treat futures or perpetual instruments as eligible for any futures-aware execution-like path.

It supports the F4 Risk and Safety stage in the Futures Capability Spec v0.

The contract exists to prevent futures risk from being treated as spot risk plus leverage. Futures risk requires explicit notional, contract, margin, liquidation, funding, order-behavior, and fail-closed controls.

## Non-authority note

This is a docs-only risk and safety contract.

It does not implement risk logic, SafetyGuard logic, RiskGate logic, KillSwitch logic, LiveRiskLimits logic, exchange adapters, dashboards, testnet paths, or Live paths.

It does not grant Master V2 approval, Double Play authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, testnet execution permission, or Live permission.

It does not permit orders, exchange calls, market-data fetches, execution sessions, bounded-pilot sessions, Paper, Shadow, Testnet, or Live.

## Scope

This contract applies to futures, perpetual swaps, and derivative-like instruments.

It defines what risk/safety semantics must exist before any futures-aware:

- dashboard risk display,
- backtest realism claim,
- dry-run candidate,
- testnet candidate,
- bounded-pilot candidate,
- operator evidence package,
- Live consideration.

It does not replace existing spot/cash risk controls. It adds the futures-specific requirements that must not be inferred from spot risk behavior.

## Required prerequisites

Futures risk/safety evaluation requires:

1. F1 instrument metadata:
   - market type,
   - contract type,
   - contract size,
   - settlement currency,
   - tick/lot sizing,
   - margin metadata.
2. F2 market data provenance:
   - last / mark / index price semantics,
   - funding availability,
   - freshness state,
   - cache/write state,
   - provenance reference.
3. F3 backtest realism assumptions when evaluating strategy behavior:
   - fees,
   - slippage,
   - funding,
   - margin,
   - liquidation,
   - notional exposure,
   - stress scenarios.
4. Explicit operator/governance boundary for anything beyond display.

Missing required prerequisites must fail closed for execution, testnet, bounded-pilot, or Live-like paths.

## Required futures risk inputs

A futures-aware risk check must receive or derive explicitly:

| Input | Required | Notes |
|---|---:|---|
| `instrument_id` | yes | Must bind to F1 metadata. |
| `market_type` | yes | Must be futures/perpetual/swap or explicit equivalent. |
| `contract_size` | yes | Required for notional exposure. |
| `settle_currency` | yes | Required for PnL and margin accounting. |
| `mark_price` | yes for margin/liquidation | Last price is not automatically mark price. |
| `index_price` | conditional | Required if used by liquidation/funding model. |
| `position_qty` | yes | Signed position quantity. |
| `notional_exposure` | yes | Must account for contract size. |
| `leverage` | yes | Effective and configured leverage. |
| `margin_mode` | yes | Isolated/cross or explicit equivalent. |
| `initial_margin` | yes | Initial margin requirement. |
| `maintenance_margin` | yes | Maintenance margin requirement. |
| `liquidation_price` | conditional | Required if the model computes it. |
| `liquidation_distance` | yes | Required for safety gating. |
| `funding_rate` | conditional | Required for perpetuals where available. |
| `funding_interval` | conditional | Required for perpetuals where applicable. |

Unknown values are acceptable for inventory and dashboard display, but not for order-capable paths.

## Required exposure and notional controls

Futures risk controls must include:

- max notional exposure per instrument,
- max notional exposure per venue,
- max notional exposure per strategy,
- max portfolio notional exposure,
- max directional exposure,
- max gross exposure,
- max net exposure,
- max concentration,
- max order notional,
- max daily notional turnover.

Rules:

- Position quantity alone is not exposure.
- Spot balance exposure is not futures notional exposure.
- Contract size and settlement currency must be included.
- Missing notional metadata must fail closed.

## Required leverage and margin controls

Futures risk controls must include:

- max configured leverage,
- max effective leverage,
- allowed margin modes,
- max margin usage,
- initial margin requirement,
- maintenance margin requirement,
- margin buffer,
- margin utilization warning threshold,
- margin utilization hard-stop threshold.

Rules:

- Leverage is not strategy permission.
- Cross margin and isolated margin must not be treated as equivalent.
- Missing margin mode must fail closed.
- Missing maintenance margin must fail closed for execution/testnet/live-like paths.

## Required liquidation controls

Futures risk controls must include:

- liquidation price or explicit model-unavailable state,
- liquidation distance,
- minimum liquidation distance,
- liquidation-distance warning threshold,
- liquidation-distance hard-stop threshold,
- forced-exit behavior,
- behavior under mark/last price divergence,
- liquidation fee or penalty if modeled.

Rules:

- A futures path without liquidation semantics is not execution-ready.
- Liquidation distance must be visible in dashboard/testnet evidence if used.
- Liquidation-adjacent scenarios must trigger fail-closed or reduce-only behavior according to the governed design.

## Required funding-risk controls

Perpetual futures risk controls must include:

- funding rate availability,
- funding interval,
- funding source,
- projected funding cost,
- funding spike threshold,
- missing funding behavior,
- stale funding behavior.

Rules:

- Funding risk is separate from trading fees.
- Missing funding for perpetuals must mark risk incomplete or fail closed.
- Funding spikes must be included in stress / safety scenarios.

## Required order/position safety controls

Futures order/position safety must define:

- reduce-only support,
- close-position behavior,
- post-only behavior if used,
- stop-market behavior if used,
- take-profit-market behavior if used,
- position mode,
- long/short semantics,
- partial close behavior,
- unavailable order type behavior,
- emergency exit path,
- stale position behavior.

Rules:

- Reduce-only / close behavior cannot be inferred from spot orders.
- Position mode must be explicit.
- Unsupported order flags must fail closed.
- Emergency exits must not bypass KillSwitch or SafetyGuard boundaries.

## RiskGate / SafetyGuard / KillSwitch / LiveRiskLimits surface boundaries

The following surfaces must remain distinct:

| Surface | Role |
|---|---|
| RiskGate | Evaluates risk permission / denial according to defined inputs. |
| SafetyGuard | Enforces safety constraints before any order-capable path. |
| KillSwitch | Stops or blocks execution when hard-stop conditions are active. |
| LiveRiskLimits | Defines live-capital limits when Live is governed and enabled. |
| Diagnostics | Observes and displays state; does not enforce. |
| Dashboard | Displays state; does not enforce or toggle controls. |
| risk_hook | Integration hook; not a policy authority by itself. |

Rules:

- Diagnostics are not enforcement.
- Dashboard labels are not enforcement.
- KillSwitch must not be bypassed by futures-specific routes.
- RiskGate pass alone is not Live authorization.
- LiveRiskLimits are not active-capital approval without governance.

## Dashboard display boundary

A futures-aware dashboard may display:

- notional exposure,
- leverage,
- margin usage,
- liquidation distance,
- funding risk,
- risk-cap status,
- SafetyGuard status,
- KillSwitch status,
- missing/unknown risk fields,
- no-live banner.

A dashboard must not:

- place orders,
- start sessions,
- enable testnet,
- enable Live,
- toggle RiskGate,
- toggle SafetyGuard,
- toggle KillSwitch,
- write evidence,
- write archives,
- hide missing futures risk fields.

## Testnet / dry-run boundary

A futures testnet/dry-run candidate requires:

- complete F1 metadata,
- complete F2 provenance,
- F3 realism assumptions if strategy behavior is evaluated,
- explicit futures risk inputs,
- risk-cap configuration,
- kill-switch state,
- no production endpoint fallback,
- no Live authorization,
- operator approval,
- audit trail.

A testnet label is not risk approval.

A dry-run flag is not risk approval.

## Evidence / operator signoff boundary

Future futures risk evidence must include:

- candidate id,
- git head,
- config version,
- instrument metadata reference,
- market-data provenance reference,
- backtest realism status if applicable,
- risk-cap values,
- notional/leverage/margin/liquidation/funding results,
- SafetyGuard result,
- KillSwitch result,
- operator signoff,
- reviewer signoff,
- archive/checksum records if artifacts are captured.

Repo docs alone cannot satisfy G4-G8.

## Fail-closed semantics

Execution/testnet/live-like paths must fail closed when:

- market type is unknown,
- contract size is missing,
- margin mode is missing,
- maintenance margin is missing,
- liquidation distance is unavailable,
- funding status is unknown for perpetuals,
- notional exposure cannot be computed,
- position mode is unknown,
- reduce-only close behavior is unavailable when required,
- SafetyGuard status is unavailable,
- KillSwitch status is unavailable,
- provenance is missing,
- Live authorization is absent.

Fail-closed means no order-capable path proceeds.

## Validation / future tests

Future tests should prove:

1. Missing contract size fails closed.
2. Missing margin mode fails closed.
3. Missing maintenance margin fails closed.
4. Missing liquidation distance fails closed.
5. Missing funding status for perpetuals fails closed or marks risk incomplete.
6. Dashboard can display missing fields without implying support.
7. RiskGate/SafetyGuard/KillSwitch remain separate surfaces.
8. KillSwitch blocks futures-specific routes.
9. Reduce-only assumptions cannot be inferred from spot behavior.
10. No `env_name` or dashboard label grants futures risk approval.

## References

- [Futures Capability Spec v0](FUTURES_CAPABILITY_SPEC_V0.md)
- [Futures Instrument Metadata Contract v0](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md)
- [Futures Market Data Provenance Contract v0](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md)
- [Futures Backtest Realism Contract v0](FUTURES_BACKTEST_REALISM_CONTRACT_V0.md)
- [Session env_name and exchange surfaces non-authority v0](SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md)
- [Futures Trading Readiness Runbook v0](../runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md)
