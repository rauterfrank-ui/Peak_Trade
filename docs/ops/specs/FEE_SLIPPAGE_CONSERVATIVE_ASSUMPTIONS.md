# Fee / Slippage Conservative Assumptions

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Canonical documentation of conservative fee and slippage assumptions for pilot go/no-go
docs_token: DOCS_TOKEN_FEE_SLIPPAGE_CONSERVATIVE_ASSUMPTIONS

## Intent
This document provides the single source of truth for conservative fee and slippage assumptions used in paper trading, backtest accounting, and pilot execution. It satisfies the evidence requirement for PILOT_GO_NO_GO Row 7 (Fee/Slippage Realism) and the Fill/Execution edge case in PILOT_EXECUTION_EDGE_CASE_MATRIX.

## Relationship
- Evidence for: `PILOT_GO_NO_GO_OPERATIONAL_SLICE` Row 7
- Implements: `PILOT_EXECUTION_EDGE_CASE_MATRIX` Fill/Execution row (Fee/slippage underestimation)
- Config sources: `config.toml` [live], `config/risk/fees.toml`, `config/risk/slippage.toml`

## Canonical Defaults

| Parameter | Default | Unit | Rationale |
|-----------|---------|------|-----------|
| fee_bps | 10.0 | basis points (0.10%) | Conservative for Kraken taker; typical range 0.05%–0.25% |
| fee_min_per_order | 0.0 | base currency | No minimum; configurable if exchange imposes |
| slippage_bps | 5.0 | basis points (0.05%) | Conservative for liquid pairs (BTC/EUR, ETH/EUR); typical 1–5 bps |

## Formulas

### Fee
```
fee = notional * (fee_bps / 10000)
```
With optional minimum: `fee = max(variable_fee, fee_min_per_order)` when `fee_min_per_order > 0`.

### Slippage (Fill Price)
```
BUY:  fill_price = reference_price * (1 + slippage_bps / 10000)
SELL: fill_price = reference_price * (1 - slippage_bps / 10000)
```
- Reference price: last/market price at execution decision
- Slippage always unfavorable to the trader (BUY pays more, SELL receives less)

## Config Locations

| Config | Path | Keys |
|--------|------|------|
| Live/Paper | `config.toml` [live] | fee_bps, fee_min_per_order, slippage_bps |
| Risk (Phase B) | `config/risk/fees.toml` | maker_bps, taker_bps, min_fee_quote, cap_fraction |
| Risk (Phase B) | `config/risk/slippage.toml` | default_bps, cap_bps, buy_bps, sell_bps |

## Why Conservative

- **Fee 10 bps:** Kraken taker typically 0.16%–0.26%; 0.10% is mid-to-conservative for planning
- **Slippage 5 bps:** Liquid crypto pairs (BTC/EUR, ETH/EUR) typically 1–5 bps; 5 bps avoids underestimation
- **Deterministic:** Same inputs → same outputs; no randomness in fee/slippage calculation

## Backtest Note

The legacy BacktestEngine (docs/BACKTEST_ENGINE.md) does **not** simulate slippage in v1. For realistic strategy evaluation, use Paper-Trading or ExecutionPipeline with fee/slippage enabled. Slippage simulation is planned for Backtest v2.
