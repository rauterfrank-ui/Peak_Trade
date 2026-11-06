# Metrics definitions — post-#5348 measurement repair

## Scope

Audit and repaired measurement of exported panel metrics from
`docs/evidence/canonical_economic_reevaluation_post_5348_v1/README.md`
against the canonical offline roundtrip ledger produced by
`run_mv2_research_backtest_wiring_v1` → `step_legacy_realistic_bar_v1`
(seed 42).

## First cost-loss boundary (repaired)

| Item | Value |
|---|---|
| Boundary | `src&#47;backtest&#47;backtest_engine_position_feedback_adapter_v1.py` function `_close_current_trade` |
| Prior defect | Called `_emit_legacy_trade_accounting_fields_v0` with default `LEGACY_PATH_COST_APPLICATION=False` → `entry_cost=exit_cost=0`, `pnl==gross` |
| Repair | Pass `legacy_path_cost_application=True`; reuse `_compute_roundtrip_fee_slippage_components_v0` / `compute_effective_*_cost_bps` |
| Fill prices | Unchanged bar/stop closes (no second slippage layer in prices) |
| Cost model owner | `src/backtest/cost_config_v0.py` + `src/backtest/engine.py` roundtrip helpers |

## Per-metric contract

| Metric | Formula | Unit | Aggregation | Denominator | Annualization | Parallel instruments | Open positions | Ledger source |
|--------|---------|------|-------------|-------------|---------------|----------------------|----------------|---------------|
| gross_pnl | Σ trade.gross_pnl × scale | currency | shared book (CRS) | n/a | none | scale=`shared&#47;(N×sleeve_cash)` | closed roundtrips | trade.gross_pnl |
| fees_total | Σ trade.fee_total × scale | currency | shared book | n/a | none | CRS scale | closed | trade.fee_total |
| slippage_total | Σ trade.slippage_total × scale | currency | shared book | n/a | none | CRS scale | closed | trade.slippage_total |
| net_pnl | Σ trade.pnl × scale | currency | shared book | n/a | none | CRS scale | closed | trade.pnl |
| cost_drag | gross_pnl − net_pnl | currency | shared book | n/a | none | derived | closed | identity |
| portfolio equity | equal-weight normalize-and-combine of sleeve curves | currency | **shared** | initial 10000 | n/a | research model | MTM in sleeve curves | BacktestResult.equity_curve |
| net_return | final_equity / initial_capital − 1 | return | shared portfolio | 10000 | none | one book | from equity path | portfolio equity |
| profit_factor_net | Σ net_wins / \|Σ net_losses\| | ratio | trade net legs | n/a | none | pooled (unscaled legs) | closed | trade.pnl |
| sharpe_net | mean(r)·P / (std(r)·√P), P=8760 | ratio | hourly portfolio returns | portfolio equity | hourly→year | shared curve only | n/a | portfolio equity |
| max_drawdown_net | min(equity/peak − 1) | return | shared equity | peak equity | none | shared curve | path | portfolio equity |

## Portfolio aggregation

`RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1` — research measurement model only,
not runtime / sizing / risk authority. Shared `initial_capital=10000` once.
Sleeve runs remain sized at `sleeve_initial_cash=10000` for signal/risk fidelity;
pnl/fee/exposure reports apply CRS scale `1&#47;N`.

## Prior invalid exports (superseded)

| Prior export | Status |
|---|---|
| `NET_RETURN≈0.507` (sum of instrument returns) | INVALID — capital double-count |
| `SHARPE≈0.041` (cross-section mean/std) | INVALID |
| `COST_DRAG=0` with fee_bps=10 / slip_bps=5 | INVALID — costs not applied |
| Equal-capital proxy `sum(pnl)&#47;(N×10000)` alone | SUPERSEDED by shared portfolio equity |

## Safety

`ECONOMIC_GATE_OPENED=false`, `PROMOTION_ELIGIBLE=false`.
