# Online Readiness Supervisor — Service Units Runbook v1 (P82)

## Safety (NON-NEGOTIABLE)
- **MODE**: paper|shadow only. live/record are hard-blocked.
- Service units must set `MODE=shadow` (or `MODE=paper`). Never `live` or `record`.

## Prerequisites
- Peak_Trade repo cloned
- `scripts/ops/online_readiness_supervisor_v1.sh` executable
- Env: MODE, OUT_DIR, INTERVAL, ITERATIONS (see supervisor script)

## macOS (launchd)
1. Copy `docs/ops/services/launchd_online_readiness_supervisor_v1.plist` to `~/Library/LaunchAgents/`
2. Edit `WorkingDirectory` to your repo root (e.g. `/Users/you/Peak_Trade`)
3. Validate: `plutil -lint ~/Library/LaunchAgents/launchd_online_readiness_supervisor_v1.plist`
4. Load: `launchctl load ~/Library/LaunchAgents/launchd_online_readiness_supervisor_v1.plist`
5. Stop: `launchctl unload ...` or `STOP=1 bash scripts/ops/online_readiness_supervisor_v1.sh`

## Linux (systemd)
1. Copy `docs/ops/services/systemd_online_readiness_supervisor_v1.service` to `/etc/systemd/system/`
2. Edit `WorkingDirectory`, `User`, `Group`, log paths
3. Validate: `systemd-analyze verify systemd_online_readiness_supervisor_v1.service`
4. Enable: `systemctl enable online_readiness_supervisor_v1`
5. Start: `systemctl start online_readiness_supervisor_v1`
6. Stop: `systemctl stop ...` or `STOP=1 bash scripts/ops/online_readiness_supervisor_v1.sh`

## Logs
- launchd: `StandardOutPath` / `StandardErrorPath` in plist (default `/tmp/...`)
- systemd: `StandardOutput` / `StandardError` in service file
- Evidence: `OUT_DIR/tick_*`, `OUT_DIR/P78_SUPERVISOR.ndjson`, `OUT_DIR/supervisor_meta.json`
