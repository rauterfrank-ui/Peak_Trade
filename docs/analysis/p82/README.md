# P82 — Supervisor Service Units v1

## Goal
Provide **launchd** (macOS) and **systemd** (Linux) unit files to run the online readiness supervisor as a managed service.

## Artifacts
- `docs/ops/services/launchd_online_readiness_supervisor_v1.plist` — macOS LaunchAgent template
- `docs/ops/services/systemd_online_readiness_supervisor_v1.service` — Linux systemd unit template
- `docs/ops/ai/online_readiness_supervisor_service_runbook_v1.md` — runbook (install, start, stop, logs)

## Safety
- MODE is paper|shadow only. Units must never set live/record.
- Operator must edit WorkingDirectory, User, log paths before use.
