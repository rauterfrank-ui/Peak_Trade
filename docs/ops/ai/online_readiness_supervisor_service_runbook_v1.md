# Online Readiness Supervisor — Service Units Runbook v1 (P82/P84)

## Safety (NON-NEGOTIABLE)
- **MODE**: paper|shadow only. live/record are hard-blocked.
- Service units must set `MODE=shadow` (or `MODE=paper`). Never `live` or `record`.
- **P84**: Installable but not armed. Add `SUPERVISOR_ENABLE=YES` to unit/env to arm. Without it, the supervisor exits 0 (no-op).
- **OUT_DIR**: Must be set and under `out&#47;ops&#47;`. `MODE=paper` requires `SUPERVISOR_ALLOW_PAPER=YES`.

## Prerequisites
- Peak_Trade repo cloned
- `scripts&#47;ops&#47;online_readiness_supervisor_v1.sh` executable
- Env: MODE, OUT_DIR, INTERVAL, ITERATIONS (see supervisor script)

## macOS (launchd)
1. Copy `docs&#47;ops&#47;services&#47;launchd_online_readiness_supervisor_v1.plist` to `~&#47;Library&#47;LaunchAgents&#47;`
2. Edit `WorkingDirectory` to your repo root (e.g. `&#47;Users&#47;you&#47;Peak_Trade`)
3. **Arm**: Add `<key>SUPERVISOR_ENABLE</key><string>YES</string>` to `EnvironmentVariables` (P84)
4. Validate: `plutil -lint ~&#47;Library&#47;LaunchAgents&#47;launchd_online_readiness_supervisor_v1.plist`
5. Load: `launchctl load ~&#47;Library&#47;LaunchAgents&#47;launchd_online_readiness_supervisor_v1.plist`
6. Stop: `launchctl unload ...` or `STOP=1 bash scripts&#47;ops&#47;online_readiness_supervisor_v1.sh`

## Linux (systemd)
1. Copy `docs&#47;ops&#47;services&#47;systemd_online_readiness_supervisor_v1.service` to `&#47;etc&#47;systemd&#47;system&#47;`
2. Edit `WorkingDirectory`, `User`, `Group`, log paths
3. **Arm**: Add `Environment=SUPERVISOR_ENABLE=YES` (P84)
4. Validate: `systemd-analyze verify systemd_online_readiness_supervisor_v1.service`
5. Enable: `systemctl enable online_readiness_supervisor_v1`
6. Start: `systemctl start online_readiness_supervisor_v1`
7. Stop: `systemctl stop ...` or `STOP=1 bash scripts&#47;ops&#47;online_readiness_supervisor_v1.sh`

## Logs
- launchd: `StandardOutPath` &#47; `StandardErrorPath` in plist (default `&#47;tmp&#47;...`)
- systemd: `StandardOutput` &#47; `StandardError` in service file
- Evidence: `OUT_DIR&#47;tick_*`, `OUT_DIR&#47;P78_SUPERVISOR.ndjson`, `OUT_DIR&#47;supervisor_meta.json`
