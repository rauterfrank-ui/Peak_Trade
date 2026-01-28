# EV_TECH_DEBT_C_20260128

PR: `https://github.com/rauterfrank-ui/Peak_Trade/pull/1023`  
Merge Commit: `d218e20158f84408dfbbe627084d3a61aff24970`

## Scope
Item C: Equity-Curve Loader for Experiments (Monte-Carlo + Stress Tests)
- Adds a shared equity loader and wires experiments to load equity → returns.
- Removes placeholder None path (Monte-Carlo) and silent dummy fallback (Stress Tests) on the standard path.

## Changes (main)
- New: `src&#47;experiments&#47;equity_loader.py`
  - candidates priority v1: `events.parquet` first, then `*equity.csv`
  - strict: no None/dummy default; helpful exceptions on missing/unloadable artifacts
- Updated: `src&#47;experiments&#47;monte_carlo.py`
  - `load_returns_for_experiment_run`: `experiments_dir &#47; experiment_id` → load equity → returns
- Updated: `src&#47;experiments&#47;stress_tests.py`
  - `load_returns_for_top_config`: resolves Top-N config via `load_top_n_configs_for_sweep` and uses `config_id` as run_dir name under `experiments_dir`
  - dummy returns only when `use_dummy_data=True`
- Tests:
  - `tests&#47;experiments&#47;test_equity_loader.py`

v1 supported artifacts (deterministic selection):
- `events.parquet` (requires `equity` + timestamp column)
- `*equity.csv` (requires `equity` + datetime column, or datetime-like first column)
Not in v1: `equity_curve.jsonl` (deferred)

## Tests executed
- CI required checks: PASS (Lint Gate, docs-reference-targets-gate, tests (3.11), etc.)
- Local (pre-PR):
  - ```bash
    uv run pytest -q tests/experiments/test_equity_loader.py
    uv run pytest -q tests/test_stress_tests.py::test_load_returns_for_top_config_dummy
    ```

## Verification result
- PASS: loader loads supported artifacts and raises on missing artifacts (no silent fallback).
- PASS: experiments no longer use placeholder None / silent dummy fallback on standard path.
- PASS: dummy returns only when explicitly enabled.

## Risk / NO-LIVE
LOW. Research-only behavior. No live exchange writes. Failure modes are explicit (exceptions) instead of silent fallbacks.
