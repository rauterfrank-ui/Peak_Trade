# Review Pack – Risk (Phase C)

## Read order
1) `src/risk/var_core.py`
2) `scripts/risk_cli.py`
3) `tests/risk/test_var_core.py` + `tests/risk/test_risk_cli_smoke.py`
4) `docs/ops/drills/PHASE_C_RISK_CLI_EVIDENCE.md`
5) `docs/ops/drills/PHASE_C4_RESTACK_RISK_ON_MAIN.md`

## Diff
- Use GitHub PR diff view; or generate a core patch locally:
  - `git diff --patch origin/feat/research-cli-evidence-chain...HEAD -- src/risk scripts/risk_cli.py tests/risk docs/ops/drills/PHASE_C*`
