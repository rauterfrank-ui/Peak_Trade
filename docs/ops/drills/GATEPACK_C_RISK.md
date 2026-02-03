# Gate Pack – C (risk VaR core + risk_cli evidence)

## Must-pass checks
- `python scripts/risk_cli.py --run-id smoke_c var --returns-file tests/fixtures/returns_normal_5k.txt --alpha 0.99 --method historical` exits 0
- Evidence: `artifacts/risk/smoke_c/meta.json` and `artifacts/risk/smoke_c/results/var.json` exist
- Tests: `python -m pytest -q tests/risk/test_var_core.py tests/risk/test_risk_cli_smoke.py --maxfail=1` passes

## Commands
```bash
python scripts/risk_cli.py --run-id smoke_c var --returns-file tests/fixtures/returns_normal_5k.txt --alpha 0.99 --method historical
test -f artifacts/risk/smoke_c/meta.json
test -f artifacts/risk/smoke_c/results/var.json
jq -r '.var,.sample_size' artifacts/risk/smoke_c/results/var.json
python -m pytest -q tests/risk/test_var_core.py tests/risk/test_risk_cli_smoke.py --maxfail=1
```
