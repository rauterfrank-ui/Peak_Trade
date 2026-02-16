# P96 — P91 Kickstart When Ready v1

## Goal

Prevent early P91 kickstarts that fail with `no_ticks_found` by enforcing a minimum tick-count guard.

## Behavior

- **OUT_DIR selection:** If `OUT_DIR` is not set, use the newest `out&#47;ops&#47;online_readiness_supervisor&#47;run_*`.
- **Condition:** At least `MIN_TICKS` tick directories under `OUT_DIR` (default: 2).
- **Action:** `launchctl kickstart -k` for P91 launchd job.
- **Exit code 3:** `out_dir_missing` or `insufficient_ticks`.

## Usage

```bash
bash scripts&#47;ops&#47;p91_kickstart_when_ready_v1.sh
OUT_DIR="out&#47;ops&#47;online_readiness_supervisor&#47;run_YYYYMMDDTHHMMSSZ" bash scripts&#47;ops&#47;p91_kickstart_when_ready_v1.sh
```
