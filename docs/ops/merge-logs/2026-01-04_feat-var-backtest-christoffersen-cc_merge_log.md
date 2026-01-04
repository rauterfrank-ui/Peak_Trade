# Merge Log — Christoffersen VaR Backtests

## Summary
Adds Christoffersen VaR backtests (coverage/independence), documentation, a runnable demo script, and targeted unit + CLI integration tests.

## Why
To harden VaR model validation with an established statistical backtest, improving auditability and reproducibility of the VaR backtest suite.

## Changes
- Docs: add Christoffersen guide; update risk README.
- Scripts: add demo runner for Christoffersen tests.
- Tests: add unit tests + CLI integration tests for the Christoffersen workflow.
- Phase artifacts: changed-files list, CLI integration notes, merge log.

## Verification
- ruff format --check .
- ruff check .
- pytest -q tests/risk_layer/var_backtest/test_christoffersen.py
- pytest -q tests/risk_layer/var_backtest/test_cli_integration.py

## Risk
Low–Medium. Additive changes in risk backtest suite; no live execution pathways touched.

## Operator How-To
- Run demo: python scripts/risk/run_christoffersen_demo.py
- Run tests: pytest -q tests/risk_layer/var_backtest/test_christoffersen.py

## References
- docs/risk/CHRISTOFFERSEN_TESTS_GUIDE.md
- tests/risk_layer/var_backtest/test_christoffersen.py
