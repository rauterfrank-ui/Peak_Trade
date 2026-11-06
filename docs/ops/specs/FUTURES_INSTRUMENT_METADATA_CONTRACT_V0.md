# Futures Instrument Metadata Contract v0

## Purpose

This contract defines the minimum metadata required before Peak_Trade can treat a futures or perpetual instrument as a futures-aware surface.

It supports the F1 Instrument Metadata stage in the Futures Capability Spec v0.

The contract exists to prevent futures capability from being inferred from symbol strings, session labels, exchange names, or dashboard labels alone.

## Non-authority note

This is a docs-only metadata contract.

It does not implement an instrument model, exchange adapter, dashboard, backtest engine, testnet path, or Live path.

It does not grant Master V2 approval, Double Play authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, testnet execution permission, or Live permission.

It does not permit orders, exchange calls, market-data fetches, execution sessions, bounded-pilot sessions, Paper, Shadow, Testnet, or Live.

## Scope

This contract applies to futures, perpetual swaps, and derivative-like instruments.

It does not replace spot-market metadata. It extends the required metadata surface when an instrument is presented as futures-aware, perpetual-aware, or derivatives-aware.

This contract is required before:

- futures-aware dashboard support,
- futures-realistic backtests,
- futures dry-run or testnet proof,
- futures risk and safety contracts,
- futures candidate evidence,
- any future Live consideration.

## Required instrument identity fields

| Field | Required | Description |
|---|---:|---|
| `instrument_id` | yes | Stable internal id for the instrument. |
| `exchange` | yes | Exchange or venue name. |
| `market_type` | yes | One of `spot`, `futures`, `perpetual`, `swap`, or explicitly documented equivalent. |
| `symbol` | yes | Exchange-facing symbol. |
| `base_currency` | yes | Base asset. |
| `quote_currency` | yes | Quote currency. |
| `settle_currency` | yes for futures/perps | Settlement currency. |

Rules:

- `symbol` alone is never enough to prove futures capability.
- `market_type` must be explicit.
- `settle_currency` must be explicit for futures/perpetuals.
- If `market_type` is unknown, execution/testnet/live must fail closed.

## Required market / contract fields

| Field | Required | Description |
|---|---:|---|
| `contract_type` | yes | Contract class such as `linear_perpetual`, `inverse_perpetual`, `dated_future`, or equivalent. |
| `is_perpetual` | yes | Boolean perpetual flag. |
| `expiry_utc` | conditional | Required for dated futures; `null` only for perpetuals. |
| `contract_size` | yes | Size multiplier for notional exposure. |
| `contract_unit` | yes | Unit represented by one contract. |

Rules:

- Perpetual status must not be inferred from the symbol alone.
- Dated futures require expiry metadata.
- Contract size is required before notional exposure, margin, liquidation, or PnL can be trusted.

## Required precision / sizing fields

| Field | Required | Description |
|---|---:|---|
| `tick_size` | yes | Minimum price increment. |
| `lot_size` | yes | Minimum quantity increment. |
| `min_qty` | yes | Minimum order quantity. |
| `min_notional` | yes | Minimum notional value if provided by the venue. |
| `price_precision` | yes | Price precision. |
| `qty_precision` | yes | Quantity precision. |

Rules:

- Dashboard may display missing sizing fields as missing.
- Backtest/testnet/live must not silently invent sizing values.
- Order construction requires explicit precision and sizing metadata.

## Required margin / leverage fields

| Field | Required | Description |
|---|---:|---|
| `margin_mode_allowed` | yes | Allowed modes such as `isolated`, `cross`, or both. |
| `max_leverage` | yes | Maximum allowed leverage. |
| `initial_margin_rate` | yes | Initial margin requirement. |
| `maintenance_margin_rate` | yes | Maintenance margin requirement. |
| `liquidation_model` | yes | Reference to the liquidation model or explicit `not_available`. |

Rules:

- Missing margin fields make futures execution/testnet/live unsupported.
- Backtests with missing margin fields must fail closed or mark futures realism incomplete.
- Dashboard may display missing margin fields, but must show unsupported/partial status.
- Leverage limits must be treated as risk inputs, not strategy permission.

## Required funding fields

| Field | Required | Description |
|---|---:|---|
| `funding_rate_available` | yes | Whether funding data is available. |
| `funding_interval` | conditional | Required for perpetuals when funding applies. |
| `funding_source` | conditional | Source of funding data if available. |

Rules:

- Perpetuals require explicit funding semantics.
- Funding absence must be visible in dashboard and backtest outputs.
- Funding PnL must not be ignored in futures-realistic backtests unless explicitly marked incomplete.

## Required lifecycle fields

| Field | Required | Description |
|---|---:|---|
| `status` | yes | Instrument status such as `active`, `paused`, `expired`, `delisted`, or `unknown`. |
| `listing_time_utc` | optional | Listing timestamp if known. |
| `delisting_time_utc` | conditional | Required if status is expired/delisted. |
| `last_metadata_refresh_utc` | yes | Timestamp of metadata refresh. |
| `metadata_source` | yes | Source of metadata. |
| `provenance_ref` | yes | Reference to provenance for the metadata snapshot. |

Rules:

- Stale metadata must be visible.
- Expired/delisted instruments must not be treated as tradable.
- Provenance is required before metadata can be used in governed testnet/live contexts.

## Unknown / missing field semantics

Unknown or missing fields must be explicit.

Allowed values:

- `unknown`
- `not_available`
- `not_applicable`
- `not_verified`

Rules:

1. Unknown fields are acceptable for inventory and dashboard display.
2. Unknown fields are not acceptable for execution, testnet proof, or Live.
3. Backtests with unknown required fields must either fail closed or mark futures realism incomplete.
4. Risk/Safety/KillSwitch contracts must not use invented defaults for required futures fields.
5. Missing metadata is not a reason to fall back to spot behavior.

## Dashboard display contract

A futures-aware dashboard may display instruments with incomplete metadata only if it clearly marks capability status.

Required dashboard fields:

- instrument id,
- exchange,
- market type,
- symbol,
- contract type,
- settlement currency,
- contract size,
- funding availability,
- max leverage,
- margin mode availability,
- liquidation model status,
- metadata source,
- provenance reference,
- last metadata refresh,
- capability status,
- no-live banner.

Dashboard status values should include:

- `spot_only`,
- `futures_metadata_missing`,
- `futures_metadata_partial`,
- `futures_metadata_complete_unproven_adapter`,
- `testnet_candidate_only`,
- `unsupported_for_live`.

Dashboard must not provide controls for orders, session starts, testnet enablement, Live enablement, risk-gate toggles, kill-switch toggles, evidence writes, archive writes, or market-data writes.

## Backtest contract

A futures-realistic backtest requires:

- complete contract metadata,
- leverage assumptions,
- margin model,
- maintenance margin model,
- liquidation model or liquidation-distance proxy,
- funding model for perpetuals,
- fee model,
- slippage model,
- contract size,
- notional exposure calculation,
- precision/sizing rules.

If required metadata is missing, the backtest must not be reported as futures-realistic.

## Testnet contract

A futures testnet candidate requires:

- complete futures instrument metadata,
- explicit exchange sandbox/testnet endpoint proof,
- adapter binding,
- no production endpoint fallback,
- order payload contract,
- position/margin/funding/liquidation handling,
- risk/safety/kill-switch checks,
- operator approval,
- audit trail.

A testnet label is not testnet proof.

## Live boundary

Live futures trading is out of scope for this contract.

Before Live, require:

- Master V2 / Double Play governance,
- PRE_LIVE completion,
- First-Live signoff,
- Scope / Capital Envelope approval,
- Risk / Exposure Caps approval,
- Safety / Kill-Switch validation,
- staged Execution Enablement,
- candidate-specific evidence,
- operator confirmation,
- no unresolved futures metadata gaps.

## Validation / future tests

Future tests should prove:

1. Required fields are enforced by any future schema/model.
2. Missing required fields fail closed for execution/testnet/live.
3. Dashboard labels unknown fields as unknown rather than supported.
4. Backtests cannot claim futures realism without required metadata.
5. `market_type` cannot be inferred from symbol alone.
6. `env_name` cannot imply futures support.

## References

- [Futures Capability Spec v0](FUTURES_CAPABILITY_SPEC_V0.md)
- [Session env_name and exchange surfaces non-authority v0](SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md)
- [Futures Trading Readiness Runbook v0](../runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md)
