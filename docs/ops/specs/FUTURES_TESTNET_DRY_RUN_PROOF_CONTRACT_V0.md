# Futures Testnet Dry-run Proof Contract v0

## Purpose

This contract defines the minimum proof required before Peak_Trade can treat a futures or perpetual path as a valid testnet or dry-run futures candidate.

It supports the F6 Testnet / Dry-run Proof stage in the Futures Capability Spec v0.

The contract exists to prevent labels such as `testnet`, `dry-run`, or `kraken_futures_testnet` from being interpreted as proof that a futures exchange adapter, sandbox endpoint, order payload, risk/safety boundary, or execution path is governed and safe.

## Non-authority note

This is a docs-only testnet and dry-run proof contract.

It does not implement exchange adapters, testnet sessions, dry-run sessions, order routing, dashboards, evidence capture, or Live paths.

It does not grant Master V2 approval, Double Play authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, testnet execution permission, or Live permission.

It does not permit orders, exchange calls, market-data fetches, execution sessions, bounded-pilot sessions, Paper, Shadow, Testnet, or Live.

## Scope

This contract applies when any surface claims or implies futures testnet or futures dry-run readiness.

It covers:

- adapter binding proof,
- sandbox endpoint isolation,
- dry-run semantics,
- futures order payload proof,
- position / margin / funding / liquidation behavior,
- risk / safety / KillSwitch checks,
- no-production-fallback proof,
- operator approval and evidence boundaries.

It does not authorize running the proof. It defines what a future governed proof must contain.

## Required prerequisites

A futures testnet/dry-run proof requires completed or explicitly referenced:

1. F1 Instrument Metadata:
   - instrument id,
   - exchange,
   - market type,
   - contract type,
   - contract size,
   - settlement currency,
   - margin/leverage metadata.
2. F2 Market Data Provenance:
   - source,
   - freshness,
   - mark/index/last price semantics,
   - funding availability,
   - cache/write policy.
3. F3 Backtest Realism:
   - futures realism status,
   - missing/incomplete assumptions,
   - stress coverage if strategy behavior is evaluated.
4. F4 Risk / Safety / KillSwitch:
   - notional/leverage/margin/liquidation/funding risk controls,
   - SafetyGuard/RiskGate/KillSwitch boundaries.
5. F5 Read-only Dashboard:
   - display-only semantics,
   - no order/session/control UI.

Missing prerequisites must block a futures testnet/dry-run proof or mark it incomplete.

## Required adapter binding proof

A future proof must show:

- exact adapter module/class/function,
- exact exchange product surface,
- supported market type,
- sandbox/testnet support,
- order entry function,
- cancel/replace function if applicable,
- position read function,
- balance/margin read function,
- instrument metadata source,
- funding data source when applicable.

Rules:

- `env_name` is not adapter binding.
- A registry label is not adapter binding.
- A CLI help string is not adapter binding.
- A dashboard label is not adapter binding.
- `kraken_futures_testnet` remains metadata/label unless a governed adapter proof binds it to an implementation.

## Required sandbox / endpoint isolation proof

A future proof must show:

- sandbox/testnet base URL,
- production base URL,
- hard separation between sandbox and production,
- no production fallback,
- credential namespace separation,
- no implicit environment-variable fallback to production,
- fail-closed behavior when sandbox credentials/endpoints are missing,
- logs that identify sandbox/testnet mode without exposing secrets.

Rules:

- Testnet label is not endpoint isolation.
- Dry-run flag is not endpoint isolation.
- Unknown endpoint status must fail closed.

## Required dry-run semantics

Dry-run semantics must define:

- whether orders are constructed but not sent,
- whether exchange clients are instantiated,
- whether market data is fetched,
- whether positions are simulated or read,
- whether balances are simulated or read,
- whether fills are simulated,
- whether cache/evidence/artifacts are written,
- whether any external API calls occur.

Rules:

- Dry-run must not be assumed no-write unless documented.
- Dry-run must not be assumed no-exchange-call unless documented.
- Dry-run must not bypass risk/safety checks.
- Dry-run does not imply testnet readiness.

## Required order-payload proof

A futures testnet/dry-run proof must include payload handling for:

- side,
- quantity,
- price,
- order type,
- time in force,
- reduce-only,
- post-only where used,
- close-position behavior where applicable,
- stop-market where used,
- take-profit-market where used,
- client order id,
- leverage/margin mode dependencies if required by the venue.

Rules:

- Spot order payloads are not futures order payloads.
- Unsupported flags must fail closed.
- Reduce-only behavior must be explicit before any close/emergency-exit logic is trusted.

## Required position / margin / funding / liquidation proof

A futures testnet/dry-run proof must show handling for:

- position quantity,
- long/short semantics,
- position mode,
- notional exposure,
- margin mode,
- leverage,
- initial margin,
- maintenance margin,
- liquidation price or distance,
- funding rate,
- funding interval,
- funding PnL,
- stale/missing data behavior.

Rules:

- Missing margin/funding/liquidation behavior makes the proof incomplete.
- Unknown position mode must fail closed.
- Liquidation-adjacent states must not continue silently.

## Required risk / safety / KillSwitch proof

A future proof must show:

- RiskGate status,
- SafetyGuard status,
- KillSwitch status,
- LiveRiskLimits status when relevant,
- risk_hook behavior if used,
- no-order boundary when blocked,
- fail-closed behavior on missing risk inputs,
- no bypass route for futures-specific execution.

Rules:

- Diagnostics are not enforcement.
- Dashboard display is not enforcement.
- RiskGate pass is not Live authorization.
- KillSwitch must be able to block futures-specific paths.

## Required no-production-fallback proof

A future proof must demonstrate:

- production endpoint cannot be reached from testnet config,
- production credentials are not used,
- missing testnet credentials fail closed,
- unknown environment fails closed,
- exchange/product mismatch fails closed,
- adapter/product mismatch fails closed.

Rules:

- Any production fallback makes the proof invalid.
- Any ambiguous endpoint makes the proof invalid.
- Any unknown product type makes the proof invalid.

## Required operator approval and evidence boundary

A future testnet/dry-run proof requires explicit operator approval before execution.

Evidence must record:

- candidate id,
- git head,
- config version,
- adapter binding,
- sandbox endpoint proof,
- instrument metadata reference,
- market data provenance reference,
- risk/safety results,
- order-payload contract result,
- no-production-fallback result,
- dry-run/testnet mode,
- operator signoff,
- reviewer signoff,
- archive/checksum records if artifacts are captured.

Repo docs alone cannot satisfy G4-G8.

## Dashboard display boundary

A dashboard may display futures testnet/dry-run status only as read-only state.

Allowed display:

- adapter proof status,
- sandbox endpoint status,
- dry-run status,
- testnet proof status,
- missing requirements,
- no-live banner.

Forbidden dashboard behavior:

- start proof,
- start session,
- send order,
- toggle testnet,
- toggle Live,
- toggle RiskGate,
- toggle SafetyGuard,
- toggle KillSwitch,
- write evidence,
- write archives.

## Fail-closed semantics

A futures testnet/dry-run proof must fail closed when:

- adapter binding is missing,
- sandbox endpoint is unknown,
- production fallback is possible,
- credentials are ambiguous,
- order payload support is incomplete,
- reduce-only support is unknown when required,
- position mode is unknown,
- margin mode is unknown,
- liquidation handling is missing,
- funding handling is missing for perpetuals,
- risk/safety status is unavailable,
- KillSwitch status is unavailable,
- provenance is missing,
- operator approval is missing.

Fail-closed means no order-capable or exchange-contacting path proceeds.

## Validation / future tests

Future tests should prove:

1. `env_name` cannot imply adapter binding.
2. `kraken_futures_testnet` renders as metadata/label unless adapter proof exists.
3. Missing sandbox endpoint fails closed.
4. Production endpoint fallback fails closed.
5. Missing reduce-only support fails closed when required.
6. Missing margin/liquidation/funding proof marks the testnet candidate incomplete.
7. Dry-run semantics state whether exchange calls/writes occur.
8. Dashboard cannot start testnet/dry-run proof.
9. KillSwitch blocks futures-specific execution paths.
10. No testnet proof grants Live authorization.

## References

- [Futures Capability Spec v0](FUTURES_CAPABILITY_SPEC_V0.md)
- [Futures Instrument Metadata Contract v0](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md)
- [Futures Market Data Provenance Contract v0](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md)
- [Futures Backtest Realism Contract v0](FUTURES_BACKTEST_REALISM_CONTRACT_V0.md)
- [Futures Risk Safety KillSwitch Contract v0](FUTURES_RISK_SAFETY_KILLSWITCH_CONTRACT_V0.md)
- [Futures Read-only Market Dashboard Contract v0](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md)
- [Session env_name and exchange surfaces non-authority v0](SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md)
- [Futures Trading Readiness Runbook v0](../runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md)
