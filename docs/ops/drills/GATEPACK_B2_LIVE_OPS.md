# Gate Pack – B2 (live_ops evidence-chain, NO-LIVE)

## Must-pass checks
- `python scripts/live_ops.py --help` shows `--run-id`
- Smoke: `python scripts/live_ops.py --run-id smoke_b2 health` exits 0
- Evidence: `artifacts&#47;live_ops&#47;smoke_b2&#47;meta.json` exists and contains `run_id`, `git_sha`, `command`, `mode` = `no_live`

## Commands
```bash
python scripts/live_ops.py --help | rg -- "--run-id"
python scripts/live_ops.py --run-id smoke_b2 health
test -f artifacts/live_ops/smoke_b2/meta.json
jq -r '.run_id,.git_sha,.command,.mode' artifacts/live_ops/smoke_b2/meta.json
```
