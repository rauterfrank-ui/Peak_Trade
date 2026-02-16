# P83 — FINAL_DONE Pin v1

## Goal
Canonical, deterministic `FINAL_DONE` pin + evidence bundle.

## Entrypoint
- `scripts/ops/final_done_pin_v1.sh`

## Outputs
- Pin: `out/ops/FINAL_DONE.txt` + `.sha256`
- Evidence: `out/ops/final_done_<TS>/`
- Bundle: `out/ops/final_done_<TS>.bundle.tgz`

## Notes
- `OPEN_PRS.json` is best-effort. If `gh` is unavailable/TLS-broken, it is recorded as `[]`.
