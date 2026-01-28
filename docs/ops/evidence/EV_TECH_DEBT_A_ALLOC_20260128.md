# EV_TECH_DEBT_A_ALLOC_20260128

PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1030
Merge Commit: af02a6d562e84c9405017016f734b96072b3b444

## Scope
Item A1/A2: Implement two-pass portfolio allocation methods in the backtest engine (engine pipeline only)
- Adds risk_parity and sharpe_weighted allocations without silent equal-weight fallback.
- Uses preview estimation (first N bars) to derive deterministic weights.
- Enforces a single weighting point at portfolio combine (no double scaling).

## Changes (main)
- `src/backtest/engine.py`
  - New config knobs:
    - `allocation_estimation_bars` (default 500)
    - `risk_free_rate` (default 0.0)
  - Two-pass flow:
    - Preview -> weights -> full runs -> combine
  - Allocation algorithms (v1):
    - risk_parity: inverse-vol weights (std-floor epsilon)
    - sharpe_weighted: Sharpe -> clip(0,+inf) -> renorm; ValueError if all weights are 0
  - Combine semantics:
    - portfolio_equity[t] = Σ w_i * equity_i[t] (single weighting point; no initial_cash scaling)
  - Failure modes:
    - explicit ValueError on insufficient preview data / invalid weight vectors (no silent fallback)

- Tests:
  - `tests/backtest/test_engine_allocations.py`
  - (Optional additional test file if present in PR: `tests/backtest/test_engine_two_pass_allocation.py`)

## Tests executed
- CI required checks: PASS (Lint Gate, tests (3.11), etc.)
- Local (pre-PR):
  - `uv run pytest -q tests/backtest/test_engine_allocations.py`
  - `uv run ruff format --check src/backtest/engine.py tests/backtest/test_engine_allocations.py`

## Verification result
- PASS: weights deterministic, finite, sum to 1; long-only; explicit errors instead of silent fallback.
- PASS: single weighting point combine (no double weighting).

## Risk / NO-LIVE
LOW. Backtest-only engine change + tests. No live/execution code touched.
