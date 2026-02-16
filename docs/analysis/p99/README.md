# P99 — Ops Loop CLI + launchd v1

## CLI (one-shot)

```bash
DRY_RUN=YES python3 -m src.ops.p99.ops_loop_cli_v1 --mode shadow
```

Writes an evidence dir under `out&#47;ops&#47;p99_ops_loop_run_<TS>&#47;` and pins `out&#47;ops&#47;P99_OPS_LOOP_DONE_<TS>.txt`.

## launchd

Use the LaunchAgent template to run every 5 minutes.

## Guarded launchd Ops-Loop (safe defaults)

A hardened wrapper exists:

- `scripts&#47;ops&#47;p99_ops_loop_launchd_guard_v1.sh`
  - forces `MODE=shadow`
  - forces `DRY_RUN=YES`
  - fails (exit 3) if typical live/exec or secret exchange env vars are set
  - requires `OUT_DIR` to be under `out&#47;ops&#47;*`

A guarded LaunchAgent template (macOS) uses this wrapper:

- Label: `com.peaktrade.p99-ops-loop-guarded`
- Interval: 300s
- Logs:
  - `out&#47;ops&#47;online_readiness_supervisor&#47;LAUNCHD_P99_OPS_LOOP_GUARDED.out.log`
  - `out&#47;ops&#47;online_readiness_supervisor&#47;LAUNCHD_P99_OPS_LOOP_GUARDED.err.log`
