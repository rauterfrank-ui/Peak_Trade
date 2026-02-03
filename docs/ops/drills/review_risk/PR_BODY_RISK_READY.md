## Scope
- Add deterministic VaR core API (`src/risk/var_core.py`) + unit tests
- Add offline `risk_cli var ...` that writes an evidence pack under `artifacts/risk/<run_id>/`
- Add Phase C docs/drills for risk evidence and restacking plan

## Evidence
- VaR core: `src/risk/var_core.py`
- Tests: `tests/risk/test_var_core.py`, `tests/risk/test_risk_cli_smoke.py`
- Risk CLI: `scripts/risk_cli.py`
- Evidence drill: `docs/ops/drills/PHASE_C_RISK_CLI_EVIDENCE.md`
- Restack drill (when B1 is merged): `docs/ops/drills/PHASE_C4_RESTACK_RISK_ON_MAIN.md`

## Notes
- This PR is currently stacked on B1 (`feat/research-cli-evidence-chain`). After B1 is merged, rebase this branch onto `origin/main` per the C4 drill to make it a clean main-target PR.
- No live execution changes; offline-only.
