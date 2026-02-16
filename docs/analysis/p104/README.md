# P104 — Soak Watch v1

## Goal
Run a periodic **shadow/paper-only** health heartbeat (P95) during long soaks.
On first failure: capture an incident snapshot (P93 + P91 guard) and execute the stop playbook.

## Hard guardrails
- MODE: `shadow` or `paper` only
- DRY_RUN: must be `YES`
- Disallowed env vars: `LIVE`, `RECORD`, `TRADING_ENABLE`, `EXECUTION_ENABLE`, `PT_ARMED`, API keys, etc.

## Usage
One-shot (3 iterations, 5s):
```bash
MODE=shadow DRY_RUN=YES SLEEP_SEC=5 ITERATIONS=3 bash scripts&#47;ops&#47;p104_soak_watch_v1.sh
```

Background (30-min heartbeat, forever):
```bash
nohup bash -c 'cd "$(git rev-parse --show-toplevel)" && MODE=shadow DRY_RUN=YES SLEEP_SEC=1800 ITERATIONS=0 bash scripts&#47;ops&#47;p104_soak_watch_v1.sh' \
  > out&#47;ops&#47;soak_watch_v1.nohup.log 2>&1 &
```

## Install (launchd)
```bash
bash scripts&#47;ops&#47;install_launchd_p104_soak_watch_v1.sh
```

## Files
- `scripts&#47;ops&#47;p104_soak_watch_v1.sh` — canonical script
- `docs&#47;ops&#47;services&#47;launchd_p104_soak_watch_v1.template.plist` — launchd template
