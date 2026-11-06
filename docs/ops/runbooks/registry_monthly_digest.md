# Registry Monthly Digest (local)

Purpose: 30-day rolling digest derived from the local DONE registry.

Inputs:
- `out&#47;ops&#47;registry&#47;morning_one_shot_done_registry.jsonl` (untracked)

Outputs:
- `out&#47;ops&#47;registry&#47;reports&#47;monthly_digest_latest.md`
- `out&#47;ops&#47;registry&#47;reports&#47;monthly_digest_latest.json`

Run:
- `python3 scripts&#47;ops&#47;registry_monthly_digest.py --days 30 --outdir out&#47;ops&#47;registry&#47;reports`

Notes:
- --days is a window size (rolling). It does not mutate the registry.
