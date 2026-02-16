# P83 — FINAL_DONE Pin v1

## Goal
Canonical, deterministic `FINAL_DONE` pin + evidence bundle.

## Entrypoint
- `scripts&#47;ops&#47;final_done_pin_v1.sh`

## Outputs
- Pin: `out&#47;ops&#47;FINAL_DONE.txt` + `.sha256`
- Evidence: `out&#47;ops&#47;final_done_<TS>&#47;`
- Bundle: `out&#47;ops&#47;final_done_<TS>.bundle.tgz`

## Notes
- `OPEN_PRS.json` is best-effort. If `gh` is unavailable/TLS-broken, it is recorded as `[]`.
