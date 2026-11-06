# P31 — Backtest Metrics v1 (Equity → KPIs)

## Goal
Provide a minimal, deterministic metrics layer for backtest equity curves (P30 output).
Pure functions, no I/O, no state, no external deps beyond stdlib.

## Inputs / Assumptions
- `equity`: list of floats, representing per-step account equity (cash + positions marked-to-market).
- Steps are equally spaced (per bar / per tick in the caller's semantics).

## Non-goals
- Multi-asset portfolio aggregation
- Annualization / calendar-aware scaling
- Plotting/reporting
- Optimization / parameter search

## API
All functions are deterministic and side-effect free.

### `compute_returns(equity: list[float]) -> list[float]`
Simple returns per step: `r_t = equity[t]&#47;equity[t-1] - 1`
- If `len(equity) < 2`: returns `[]`
- Rejects non-positive `equity[t-1]` via `ValueError` (undefined division / invalid equity)

### `max_drawdown(equity: list[float]) -> float`
Peak-to-trough max drawdown computed on equity:
- Returns `0.0` for `len(equity) < 2`
- Drawdown is expressed as a **positive fraction** in `[0, +inf)`:
  `dd_t = 1 - equity[t]&#47;peak_so_far` for `equity[t] <= peak_so_far`
- Rejects non-positive peaks via `ValueError`

### `sharpe(returns: list[float], risk_free: float=0.0) -> float`
Per-step Sharpe ratio:
- Excess returns: `excess = r - risk_free`
- Uses population std-dev (ddof=0) for determinism and simplicity
- Returns `0.0` when `len(returns) < 2` or std-dev is 0

### `summary_kpis(equity: list[float], risk_free: float=0.0) -> dict[str, float]`
Returns:
- `total_return`: `equity[-1]&#47;equity[0] - 1` (requires len>=2 and equity[0]>0)
- `max_drawdown`: from `max_drawdown`
- `sharpe`: sharpe of `compute_returns(equity)`
- `n_steps`: float(len(equity))

## Invariants
- Deterministic outputs for identical inputs
- No mutation of inputs
- Stable float computations; comparisons in tests should use tolerances
