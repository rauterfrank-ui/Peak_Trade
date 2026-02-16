# P81 — Supervisor Service Hardening v1

## Goal
Harden the P78/P80 supervisor with:
- **flock/lockfile**: prevent double-start without pidfile race
- **trap cleanup**: pidfile + lockfile removed on exit
- **rotate policy**: MAX_LOGS, MAX_TICK_DIRS configurable
- **jitter/backoff**: BACKOFF_SEC sleep after transient P76 failure
- **structured META**: `supervisor_meta.json` with last_tick pointer
- **exit codes**: 0 ok, 2 usage, 3 not_allowed, 4 gate_fail, 5 internal

## Env
- `LOCKFILE` — advisory lock path (default `&#47;tmp&#47;p78_online_readiness_supervisor.lock`)
- `MAX_TICK_DIRS` — max tick_* dirs to retain (default 100)
- `BACKOFF_SEC` — sleep after failed tick (default 5)

## Exit Codes
- 0: success
- 2: usage/config error
- 3: not_allowed (mode, already running, lock)
- 4: gate_fail
- 5: internal
