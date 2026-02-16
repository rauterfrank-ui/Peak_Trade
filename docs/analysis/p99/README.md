# P99 — Ops Loop CLI + launchd v1

## CLI (one-shot)

```bash
DRY_RUN=YES python3 -m src.ops.p99.ops_loop_cli_v1 --mode shadow
```

Writes an evidence dir under `out/ops/p99_ops_loop_run_<TS>/` and pins `out/ops/P99_OPS_LOOP_DONE_<TS>.txt`.

## launchd

Use the LaunchAgent template to run every 5 minutes.
