# Phase D4 – Merge Status Dashboard

Script: `scripts/ops/merge_status_dashboard.sh`

## Purpose
Provide a single-command view of merge readiness for:
- Docs gatepacks
- B1 research_cli evidence hook
- B2 live_ops evidence hook (NO-LIVE)
- C risk var_core + risk_cli

## What it checks (semantic)
- **Docs gatepacks:** existence of:
  - `docs/ops/drills/GATEPACK_B1_RESEARCH_CLI.md`
  - `docs/ops/drills/GATEPACK_B2_LIVE_OPS.md`
  - `docs/ops/drills/GATEPACK_C_RISK.md`
- **B1:** `scripts/research_cli.py` contains `--run-id` and `artifacts/research`
- **Evidence helper:** `src/ops/evidence.py` exists
- **B2:** `scripts/live_ops.py` contains `--run-id` and `"mode": "no_live"`
- **C:** both `src/risk/var_core.py` and `scripts/risk_cli.py` exist

## Usage
```bash
bash scripts/ops/merge_status_dashboard.sh
```

Run from repo root (script checks out main and pulls before reporting).

## Post-merge on main (safe)
Run the dashboard only after the PR is merged (script exists on main):
```bash
cd "$(git rev-parse --show-toplevel)"
git checkout main
git pull --ff-only origin main
if [[ -x scripts/ops/merge_status_dashboard.sh ]]; then
  bash scripts/ops/merge_status_dashboard.sh
else
  echo "dashboard not on main yet (merge ops/merge-status-dashboard PR first)"
fi
```
