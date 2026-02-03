# Gate Pack – B1 (research_cli evidence-chain)

## Must-pass checks
- `python scripts/research_cli.py --help` shows `--run-id`
- Smoke: `python scripts/research_cli.py --run-id smoke_b1 run-experiment --list-presets` exits 0
- Evidence: `artifacts/research/smoke_b1/meta.json` exists and contains `run_id`, `git_sha`, `command`

## Commands
```bash
python scripts/research_cli.py --help | rg -- "--run-id"
python scripts/research_cli.py --run-id smoke_b1 run-experiment --list-presets
test -f artifacts/research/smoke_b1/meta.json
jq -r '.run_id,.git_sha,.command' artifacts/research/smoke_b1/meta.json
```
