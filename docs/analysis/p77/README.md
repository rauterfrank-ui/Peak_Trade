# P77 — Online Readiness Daemon v1

## Goal
Provide a **paper/shadow-only** daemon wrapper that repeatedly runs the canonical online readiness entry script
and writes each tick into an isolated `out&#47;ops&#47;...&#47;&lt;run_id&gt;&#47;` directory.

## Safety
- `MODE` is restricted to `shadow|paper`.
- The underlying stack hard-blocks `live|record` (PermissionError upstream).
- No model calls are performed unless explicitly enabled/armed/tokened (P49/P50 gates remain deny-by-default).
- Uses pidfile to prevent double-start.

## Entrypoints
- Bash (recommended for ops): `scripts&#47;ops&#47;online_readiness_daemon_v1.sh`
- Python (planning helper only): `src.ops.p77.build_daemon_plan_v1`

## Bash usage
Start (default: shadow, every 60s, forever):
```bash
MODE=shadow INTERVAL_SEC=60 OUT_DIR_BASE=out/ops/online_readiness_daemon \
  scripts/ops/online_readiness_daemon_v1.sh
```

Smoke (2 ticks, no sleep):
```bash
MODE=shadow MAX_TICKS=2 INTERVAL_SEC=0 OUT_DIR_BASE=out/ops/p77_smoke \
  scripts/ops/online_readiness_daemon_v1.sh
```

## Env vars
| Var | Default | Description |
|-----|---------|-------------|
| MODE | shadow | shadow\|paper only |
| INTERVAL_SEC | 60 | Sleep between ticks |
| MAX_TICKS | 0 | 0 = forever |
| OUT_DIR_BASE | out/ops/online_readiness_daemon | Base output dir |
| RUN_ID_PREFIX | p77 | Per-tick run_id prefix |
| PIDFILE | /tmp/peaktrade_online_readiness_daemon_v1.pid | Pidfile |
| LOGFILE | /tmp/peaktrade_online_readiness_daemon_v1.log | Daemon log |
