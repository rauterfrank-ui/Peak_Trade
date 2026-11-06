# P94 — P93 Status Dashboard Retention v1

## Goal

Keep `out&#47;ops&#47;` from growing unbounded by deleting older **P93 status dashboard** artifacts.

## What it deletes

For each timestamp `TS` older than the newest `KEEP_N`:

- `out&#47;ops&#47;p93_online_readiness_status_TS&#47;`
- `out&#47;ops&#47;p93_online_readiness_status_TS.bundle.tgz` + `.sha256`
- `out&#47;ops&#47;P93_STATUS_DASHBOARD_DONE_TS.txt` + `.sha256`

## Usage

```bash
KEEP_N=48 bash scripts/ops/p94_p93_status_dashboard_retention_v1.sh
```

## Options

- `KEEP_N` — number of snapshots to retain (default: 48)
- `OPS_DIR` — ops directory (default: `out&#47;ops&#47;`)
