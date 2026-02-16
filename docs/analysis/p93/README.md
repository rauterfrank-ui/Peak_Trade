# P93 — Online Readiness Status Dashboard v1

## Goal

One-shot, pinned status snapshot of the running shadow supervisor:

- launchd status
- P79 health gate
- P90 metrics
- latest P76 result
- latest P91 audit snapshot pointers
- tail of `SHADOW_SOAK_INDEX.ndjson`

## Run

```bash
OUT_DIR="out&#47;ops&#47;online_readiness_supervisor&#47;run_YYYYMMDDTHHMMSSZ" \
MODE=shadow MAX_AGE_SEC=900 MIN_TICKS=2 \
bash scripts/ops/p93_online_readiness_status_dashboard_v1.sh
```

## Output

- `out&#47;ops&#47;p93_online_readiness_status_<TS>&#47;` — evidence dir (META.txt, LAUNCHD_STATUS.txt, P79_GATE.log, P90_METRICS.json, manifest.json, SHA256SUMS.txt, …)
- `out&#47;ops&#47;p93_online_readiness_status_<TS>.bundle.tgz` — tarball bundle
- `out&#47;ops&#47;P93_STATUS_DASHBOARD_DONE_<TS>.txt` — pin file
