# PR_XXXX MERGE LOG

## Summary
Contract-lock for registry backtest CLI + SSOT portfolio profile resolver + config resolution observability and sanity warnings; docs drift fixed.

## Why
Prevent future divergence between CLI and engine portfolio profile resolution and harden CLI contracts (limit/timeframe/regime/config priority) with tests and explicit documentation.

## Changes
- **Code**:
  - **SSOT portfolio resolver**: `src/backtest/portfolio_resolver.py`
  - **Dedup imports**: `scripts/run_registry_portfolio_backtest.py`, `src/backtest/engine.py`
  - **Config resolution logging + `strategies.available` sanity warnings**: `src/core/config_registry.py`
- **Docs**:
  - `docs/REGISTRY_BACKTEST_CLI.md` (contracts + profiles + config priority)
  - `docs/REGISTRY_BACKTEST_API.md` (TODO drift fix)
  - `docs/REGISTRY_BACKTEST_IMPLEMENTATION.md` (TODO drift fix)
- **Tests**:
  - `tests/test_registry_portfolio_backtest_cli_contracts.py`

## Verification
- `python3 -m pytest -q tests/test_portfolio_backtest_smoke.py tests/test_backtest_smoke.py` → PASS (13 passed)
- `python3 -m pytest -q tests/test_registry_portfolio_backtest_cli_contracts.py` → PASS (7 passed)

## Risk
LOW. No changes to execution/risk/governance subsystems. Refactor to SSOT + additive logs/warnings. Covered by smoke + contract tests.

## Operator How-To
- Follow CLI contracts in `docs/REGISTRY_BACKTEST_CLI.md`
- Config priority: `PEAK_TRADE_CONFIG` > `config/config.toml` > `config.toml`

## References
- PR: #XXXX
