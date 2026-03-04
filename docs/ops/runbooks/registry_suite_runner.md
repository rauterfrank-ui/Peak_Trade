# Registry Suite Runner — Runbook

Purpose
- One-shot generation of all local registry reports (trend, weekly, monthly).
- Optional `RUN_ONE_SHOT=true` to append a fresh DONE entry first.

Inputs
- `out&#47;ops&#47;registry&#47;morning_one_shot_done_registry.jsonl`

Command
- `scripts&#47;ops&#47;run_registry_suite.sh`

Optional
- `RUN_ONE_SHOT=true scripts&#47;ops&#47;run_registry_suite.sh`

Outputs (untracked)
- `out&#47;ops&#47;registry&#47;reports&#47;trend_report_latest.md`
- `out&#47;ops&#47;registry&#47;reports&#47;weekly_digest_latest.md`
- `out&#47;ops&#47;registry&#47;reports&#47;monthly_digest_latest.md`
(and matching `.json`)
